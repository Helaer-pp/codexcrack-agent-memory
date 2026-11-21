"""当前裂纹识别与结果渲染。修改下方设置，保存后直接运行或双击 CrackTipRunner.exe。"""

# ==================== 手动设置区 ====================
# Windows 路径可直接粘贴在 r"..." 内。相对路径以本脚本所在目录为起点。
SETTINGS = {
    "reference_image": r"D:/datasets\1-引伸计\1-裂纹\2-验证组C\三点弯\三点弯\46.bmp",  # 参考图
    "image_input":     r"D:/datasets\1-引伸计\1-裂纹\2-验证组C\三点弯\三点弯",  # 待测文件夹，也可填单张图
    "output_dir":      r"D:/datasets\1-引伸计\1-裂纹\2-验证组C\三点弯\crack_tip_runs",                    # 结果保存目录

    # 原图坐标，左上角为原点。先填上面的 P1，再填下面的 P2。
    "reference_points": [[1477.15, 2561.95], [1475.03, 2848.53]],    # 参考帧 [P1, P2]
    "point_mode": "table",  # table 读取逐帧坐标表；ncc 从参考点自动匹配；fixed 使用手填点
    "points_file": r"data/anchors/三点弯_基准点坐标.txt",             # table 模式使用
    "current_points": None,  # fixed 模式可填 [[P1x, P1y], [P2x, P2y]]，None 表示沿用参考点

    "first_frame": 1,        # 起始帧，从 1 开始
    "last_frame": None,      # 结束帧，None 表示到最后一张
    "roi": None,             # 自动计算，或填 [左, 上, 右, 下]
    "title": "裂纹识别",
    "save_comparisons": True,  # 逐帧四联对比图
    "save_differences": True,  # 逐帧参考差分图
    "save_video": True,
    "video_fps": 10,

    "use_validation_candidate": False,  # True 运行本轮验证候选；False 使用通过底线的默认版本

    # 进阶设置
    "table_first_index": 0,    # TXT 表中对应第一张图的 num 编号
    "ncc_radius": 15, "ncc_search": 32, "ncc_min": 0.65,
    "bright_profile": "auto",  # 登记的验证组C目录自动使用亮区配置，也可填配置文件路径
    "feature_scale_px": None,  # 跟随当前算法版本
    "extensions": [".bmp", ".png", ".tif", ".tiff", ".jpg", ".jpeg"],
    "ffmpeg": r"third_party/ffmpeg/ffmpeg.exe",
}
# ==================== 手动设置区结束 ====================

import argparse
import csv
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "output/cache/matplotlib"))
sys.dont_write_bytecode = True

import cv2
import numpy as np
from PIL import Image, ImageDraw
from research import current_crack_tip

FIELDS = ("frame", "image", "version", "stage", "status", "reason", "tip_x", "tip_y",
          "path_length_px", "projected_length_px", "reference_xy", "mapping_status",
          "input_current_points", "input_reference_points", "current_points", "reference_points",
          "roi", "comparison", "difference")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def resolve(base, value):
    return (base / Path(os.path.expandvars(str(value))).expanduser()).resolve()


def natural(path):
    return [int(x) if x.isdecimal() else x.casefold() for x in re.split(r"(\d+)", path.name)]


def pixels(path):
    data = path.read_bytes()
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED) if data else None
    if image is None or image.dtype != np.uint8:
        raise ValueError(f"无法解码为 8 位图像：{path}")
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY if image.shape[2] == 4 else cv2.COLOR_BGR2GRAY)
    return image, hashlib.sha256(data).hexdigest()


def points(value, shape):
    a = np.asarray(value, dtype=float)
    h, w = shape
    if (a.shape != (2, 2) or not np.isfinite(a).all() or (a < 0).any()
            or (a[:, 0] >= w).any() or (a[:, 1] >= h).any()
            or a[0, 1] >= a[1, 1] or np.linalg.norm(a[1]-a[0]) < 20):
        raise ValueError(f"P1、P2 须在图内，P1 在上，间距至少 20 px：{value}")
    return a


def load_table(file, files, first):
    if file.suffix.lower() == ".csv":
        rows = {}
        with file.open(encoding="utf-8-sig", newline="") as stream:
            for r in csv.DictReader(stream):
                key = r["image"].casefold()
                if key in rows:
                    raise ValueError(f"坐标表文件名重复：{key}")
                rows[key] = [[r["x0"], r["y0"]], [r["x1"], r["y1"]]]
        return rows
    if file.suffix.lower() != ".txt":
        raise ValueError("坐标表需为 CSV 或 num 编号的 TXT")
    values = {}
    for line in file.read_bytes().splitlines():
        if not line.strip():
            continue
        # These legacy records have ASCII numeric fields and a locale-dependent label.
        index = re.match(rb"\s*num\s*:\s*(\d+)", line)
        if not index:
            raise ValueError("TXT 行缺少 num 编号")
        key = int(index[1])
        coords = [float(x) for x in line.split()[-4:]]
        if key in values or len(coords) != 4:
            raise ValueError(f"TXT 坐标行无效：{key}")
        values[key] = [coords[:2], coords[2:]]
    return {f.name.casefold(): values[i] for i, f in enumerate(files, first) if i in values}


def known_group(path, registry):
    for g in registry:
        if path.is_relative_to(Path(g["images"]).resolve()):
            return g["id"]
    return None


def main(settings=None, *, candidate=False, version_only=False):
    settings_file = Path(__file__).resolve() if settings is None else Path(settings).resolve()
    cfg = SETTINGS if settings is None else read_json(settings_file)
    release = current_crack_tip.choose(candidate or cfg.get("use_validation_candidate", False))
    if version_only:
        print(f"{release.version} {release.stage}")
        return 0
    base = settings_file.parent
    ref_file = resolve(base, cfg["reference_image"])
    source = resolve(base, cfg["image_input"])
    destination = resolve(base, cfg["output_dir"])
    registry = read_json(ROOT / "config/datasets.json")["groups"]
    roles = read_json(ROOT / "config/dataset_usage_policy.json")["groups"]

    def permitted(path):
        g = known_group(path, registry)
        if roles.get(g) == "EXCLUDED" or "排除组X" in str(path) or "group_x" in str(path).casefold():
            raise ValueError(f"数据策略已排除此路径：{path}")
        return g

    group = permitted(source)
    permitted(ref_file)
    if known_group(destination, registry):
        raise ValueError("请将结果保存到原始实验数据目录之外")
    exts = {s.casefold() for s in cfg["extensions"]}
    files = sorted((p for p in source.iterdir() if p.is_file() and p.suffix.lower() in exts), key=natural) if source.is_dir() else [source]
    if not files or not source.exists():
        raise ValueError(f"没有找到输入图像：{source}")
    for file in files:
        permitted(file.resolve())
    mode = cfg["point_mode"]
    if mode not in ("fixed", "ncc", "table"):
        raise ValueError("point_mode 须为 fixed、ncc 或 table")
    if mode != "fixed" and cfg["current_points"] is not None:
        raise ValueError("要使用手填的 current_points，请将 point_mode 设置为 fixed")
    first = int(cfg["table_first_index"])
    table = load_table(resolve(base, cfg["points_file"]), files, first) if mode == "table" else {}
    ref, ref_sha = pixels(ref_file)
    rp = points(cfg["reference_points"], ref.shape)
    static = points(cfg["current_points"], ref.shape) if cfg["current_points"] is not None else rp
    roi = cfg["roi"]
    if roi is not None:
        if not (len(roi) == 4 and all(type(a) is int for a in roi) and
                0 <= roi[0] < roi[2] <= ref.shape[1] and 0 <= roi[1] < roi[3] <= ref.shape[0]):
            raise ValueError("roi 须为图内的 [左,上,右,下] 原图整数坐标，右下界不含")
    scale = release.default_scale if cfg["feature_scale_px"] is None else float(cfg["feature_scale_px"])
    fps = float(cfg["video_fps"])
    if not (math.isfinite(scale) and scale >= 20 and math.isfinite(fps) and fps > 0):
        raise ValueError("feature_scale_px 应至少为 20，video_fps 应为正数")
    bright = cfg["bright_profile"]
    if bright == "auto":
        bright = str(ROOT / "config/crack_tip_group_c_bright.json") if group == "group_c" else None
    if bright:
        bright = read_json(resolve(base, bright))
        if bright.get("reference_sha") and bright["reference_sha"] != ref_sha:
            raise ValueError("亮区配置绑定了另一张参考图，请提供与本次参考图对应的亮区配置")
    if mode == "ncc":
        from paired_p1p2_roi_easy_edit import track_reference_point
        radius, search, threshold = int(cfg["ncc_radius"]), int(cfg["ncc_search"]), float(cfg["ncc_min"])
        if radius < 1 or search < 0 or not -1 <= threshold <= 1:
            raise ValueError("NCC 半径、搜索范围或相关系数非法")
    start, end = int(cfg["first_frame"]), cfg["last_frame"]
    end = len(files) if end is None else int(end)
    if not 1 <= start <= end <= len(files):
        raise ValueError(f"帧范围应落在 1 到 {len(files)}")
    ffmpeg = resolve(base, cfg["ffmpeg"]) if cfg["save_video"] else None
    if ffmpeg and not ffmpeg.is_file():
        raise ValueError(f"视频编码器不存在：{ffmpeg}")
    cv2.setNumThreads(1)
    out = destination / (datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8])
    out.mkdir(parents=True)
    print(f"{release.version} {release.stage}  输出目录 {out}", flush=True)
    (out/"run.json").write_text(json.dumps(dict(settings=cfg, settings_file=str(settings_file),
        version=release.version, stage=release.stage, source=str(source), reference=str(ref_file),
        reference_sha256=ref_sha, dataset=group, bright_profile_used=bright), ensure_ascii=False, indent=2), encoding="utf8")
    errors = 0
    with TemporaryDirectory(dir=out) as temp, (out/"results.csv").open("w", newline="", encoding="utf-8-sig") as csvfile, (out/"paths.jsonl").open("w", encoding="utf8") as paths:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDS)
        writer.writeheader()
        frames = out/"comparisons" if cfg["save_comparisons"] else Path(temp)
        diffs = out/"differences"
        need_card = cfg["save_comparisons"] or bool(ffmpeg)
        if need_card:
            frames.mkdir(exist_ok=True)
        if cfg["save_differences"]:
            diffs.mkdir()
        for number in range(start, end+1):
            file = files[number-1]
            stem = f"{number:06d}"
            row = dict(frame=number, image=file.name, version=release.version, stage=release.stage,
                       input_reference_points=rp.tolist())
            line = []
            try:
                img, sha = pixels(file)
                if img.shape != ref.shape:
                    raise ValueError("当前图和参考图的分辨率不同")
                if mode == "table":
                    key = file.name.casefold()
                    if key not in table:
                        raise ValueError(f"坐标表缺少 {file.name}")
                    cp = points(table[key], img.shape)
                elif mode == "ncc" and sha != ref_sha:
                    cp = points([track_reference_point(ref, img, p, radius, search, threshold)[0] for p in rp], img.shape)
                else:
                    cp = static
                row["input_current_points"] = cp.tolist()
                result = release.analyze(img, ref, cp, rp, scale=scale, roi=roi, bright=bright)
                m, box, actual_cp, actual_rp, _ = result
                line = m["points"]
                tip = m["tip"] or [None, None]
                row.update(status=m["status"], reason=m["diagnostics"]["dual"]["stop"],
                           tip_x=tip[0], tip_y=tip[1], path_length_px=m["path_length_px"],
                           projected_length_px=m["projected_length_px"], roi=box,
                           current_points=actual_cp.tolist(), reference_points=actual_rp.tolist())
            except (OSError, ValueError, cv2.error) as exc:
                errors += 1
                row.update(status="INPUT_ERROR", reason=str(exc))
                print(f"帧 {number} {file.name} 输入异常：{exc}", flush=True)
            if row["status"] != "INPUT_ERROR" and (need_card or cfg["save_differences"]):
                card, diff, info = release.render(result, img, ref, sha, ref_file, ref_sha, number,
                                                   len(files), cfg["title"])
                row.update(reference_xy=info["ref_xy"] if m["tip"] is not None else None, mapping_status=info["status"])
                if cfg["save_differences"]:
                    row["difference"] = "differences/"+stem+".png"
                    diff.save(out/row["difference"])
            elif need_card:
                card = Image.new("RGB", (2000,764), "white")
                from research.notch_identity_v34.reference_views import font
                draw = ImageDraw.Draw(card)
                draw.text((24,30), f"{release.version} {release.stage}    第 {number} 帧    {file.name}", font=font(28), fill="black")
                draw.text((24,90), "输入异常    "+row["reason"], font=font(22), fill="black")
            if need_card:
                card.save(frames/(stem+".jpg"), quality=93, subsampling=0)
                if cfg["save_comparisons"]:
                    row["comparison"] = "comparisons/"+stem+".jpg"
            writer.writerow(row)
            paths.write(json.dumps(dict(**row, points=line), ensure_ascii=False, allow_nan=False)+"\n")
            if number % 25 == 0:
                print(f"{number}/{end}", flush=True)
        if ffmpeg:
            subprocess.run([str(ffmpeg), "-v","error","-framerate",str(fps),"-start_number",str(start),
                            "-i",str(frames/"%06d.jpg"),"-frames:v",str(end-start+1),"-c:v","libx264",
                            "-pix_fmt","yuv420p","-movflags","+faststart",str(out/"results.mp4")], check=True)
    print(f"完成 {end-start+1} 帧，输入异常 {errors} 帧。{out}", flush=True)
    return 2 if errors else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="可选：指定一份完整的 UTF-8 JSON 配置。省略时读取脚本顶部设置")
    parser.add_argument("--candidate", action="store_true", help="使用本轮验证候选及其配套渲染")
    parser.add_argument("--version", action="store_true", help="显示所选算法版本和阶段")
    args = parser.parse_args()
    sys.exit(main(args.config, candidate=args.candidate, version_only=args.version))
