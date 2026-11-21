"""Expanded current-anchor decoupling audit.

The reference image and reference P1/P2 stay fixed. Only current-frame P1/P2
are transformed. The endpoint contract compares confirmation state and tip
coordinates; path and complete length remain separate measurements.
"""
import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = os.environ.get("CRACK_STRICT_RUN", "anchor_decoupling_strict_20261110_r01")
OUT = ROOT / "output/runs" / RUN_ID
if Path(RUN_ID).name != RUN_ID:
    raise ValueError(RUN_ID)
os.environ["CRACK_SIX_ROI_DLL"] = str(ROOT / "output/build/src/cpp/a/Release/CrackV4.dll")
sys.path.insert(0, str(ROOT / "research/gate_adapt"))
from six_roi_replay import api, inventory  # noqa: E402

DLL = ROOT / "output/build/src/cpp/a/Release/CrackV4.dll"
api.BASE = DLL
api.EXPECTED_BASE = api.sha(DLL)
api._base = None


def variants(points):
    p = np.asarray(points, dtype=float)
    mid = p.mean(axis=0)
    vec = p[1] - p[0]
    out = {"measured": p.copy()}

    def rigid(name, dx=0, dy=0, scale=1, degrees=0):
        a = math.radians(degrees)
        c, s = math.cos(a), math.sin(a)
        r = np.array([[c, -s], [s, c]])
        out[name] = (mid + np.array([dx, dy]) + ((p - mid) * scale) @ r.T)

    for d in (40, 80, 120):
        rigid(f"tx+{d}", dx=d)
        rigid(f"tx-{d}", dx=-d)
        rigid(f"ty+{d}", dy=d)
        rigid(f"ty-{d}", dy=-d)
    for scale in (.50, .65, 1.35, 1.50):
        rigid(f"scale{scale:g}", scale=scale)
    for deg in (-15, -10, -5, 5, 10, 15):
        rigid(f"rot{deg:+d}", degrees=deg)
    rigid("combo+80_rot10", dx=80, dy=40, scale=1.35, degrees=10)
    rigid("combo-80_rot-10", dx=-80, dy=-40, scale=.65, degrees=-10)
    # Non-rigid endpoint perturbations: the two points move independently.
    out["p1+80"] = p + np.array([[80, 0], [0, 0]])
    out["p2-80"] = p + np.array([[0, 0], [-80, 0]])
    out["p1+40_p2-40"] = p + np.array([[40, 0], [-40, 0]])
    # Keep deterministic insertion order and avoid unused vec warnings.
    assert np.isfinite(vec).all()
    return out


def inside(p, shape):
    return bool(np.all(p[:, 0] >= 0) and np.all(p[:, 1] >= 0) and
                np.all(p[:, 0] < shape[1]) and np.all(p[:, 1] < shape[0]))


def run_group(group, frame_limit):
    mode, sequence = inventory()[group]
    sequence = sequence[:frame_limit] if frame_limit else sequence
    reference = api.read(sequence[0][0])
    base_points = np.asarray(sequence[0][1], dtype=float)
    names = list(variants(base_points))
    detectors = {name: api.Baseline(reference, base_points, mode=mode) for name in names}
    rows = []
    try:
        for i, (path, points, _) in enumerate(sequence):
            im = api.read(path)
            reference_points = np.asarray(points, dtype=float)
            vv = variants(reference_points)
            baseline = None
            for name in names:
                pp = vv[name]
                valid_input = inside(pp, im.shape)
                if not valid_input:
                    rows.append(dict(group=group, frame=i + 1, image=path.name, case=name,
                                     valid_input=0, process_ok=0, tip_valid=None,
                                     tip_x=None, tip_y=None, baseline_tip_valid=None,
                                     baseline_tip_x=None, baseline_tip_y=None,
                                     delta_px=None, state_equal=None, coordinate_equal=None,
                                     detector_ms=None, error="current_points_outside_image"))
                    continue
                try:
                    raw = detectors[name].run(im, pp, is_reference=i == 0)
                    tip = raw["formal"]["tip"]
                    tip_valid = bool(raw["formal"]["confirmed_tip"])
                    if baseline is None:
                        baseline = (tip_valid, tip)
                    bvalid, btip = baseline
                    delta = float(np.linalg.norm(np.asarray(tip) - btip)) if tip_valid and bvalid else None
                    state_equal = tip_valid == bvalid
                    coord_equal = (tip_valid and bvalid and np.allclose(tip, btip, atol=1e-9)) or (not tip_valid and not bvalid)
                    rows.append(dict(group=group, frame=i + 1, image=path.name, case=name,
                                     valid_input=1, process_ok=1, tip_valid=int(tip_valid),
                                     tip_x=tip[0] if tip_valid else None,
                                     tip_y=tip[1] if tip_valid else None,
                                     baseline_tip_valid=int(bvalid),
                                     baseline_tip_x=btip[0] if bvalid else None,
                                     baseline_tip_y=btip[1] if bvalid else None,
                                     delta_px=delta, state_equal=int(state_equal),
                                     coordinate_equal=int(coord_equal),
                                     detector_ms=raw["formal"].get("detector_ms"), error=""))
                except Exception as exc:
                    rows.append(dict(group=group, frame=i + 1, image=path.name, case=name,
                                     valid_input=1, process_ok=0, tip_valid=None,
                                     tip_x=None, tip_y=None, baseline_tip_valid=None,
                                     baseline_tip_x=None, baseline_tip_y=None,
                                     delta_px=None, state_equal=None, coordinate_equal=None,
                                     detector_ms=None, error=type(exc).__name__ + ": " + str(exc)[:160]))
    finally:
        for detector in detectors.values():
            detector.close()
    return rows


def summarize(rows):
    result = []
    for group in sorted({r["group"] for r in rows}):
        rr = [r for r in rows if r["group"] == group]
        for case in sorted({r["case"] for r in rr}):
            x = [r for r in rr if r["case"] == case]
            valid = [r for r in x if r["valid_input"]]
            executed = [r for r in valid if r["process_ok"]]
            comparable = [r for r in executed if r["state_equal"] is not None]
            deltas = [r["delta_px"] for r in comparable if r["delta_px"] is not None]
            result.append(dict(group=group, case=case, frames=len(x), valid_inputs=len(valid),
                               executed=len(executed), state_mismatches=sum(not r["state_equal"] for r in comparable),
                               coordinate_mismatches=sum(not r["coordinate_equal"] for r in comparable),
                               max_delta_px=max(deltas, default=None),
                               p95_delta_px=float(np.percentile(deltas, 95)) if deltas else None,
                               errors=sum(not r["process_ok"] for r in valid),
                               invalid_inputs=sum(not r["valid_input"] for r in x)))
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    groups = ["group_a", "group_c", "ct2", "group_h", "three_point_bend", "group_x", "ct3"]
    # Twelve chronological frames per large six-group sequence and all 136
    # frames for CT3, whose replay is small enough for the expanded matrix.
    all_rows = []
    limits = {"group_a": 252, "group_c": 25, "ct3": 136}
    for group in groups:
        print("running", group, flush=True)
        all_rows.extend(run_group(group, limits.get(group, 12)))
    api.csvout(OUT / "per_case_frame.csv", all_rows)
    summary = summarize(all_rows)
    api.csvout(OUT / "summary.csv", summary)
    manifest = dict(run=RUN_ID, dll=api.sha(ROOT / "output/build/src/cpp/a/Release/CrackV4.dll"),
                    groups=groups, frames_per_group=12, variants=len(set(r["case"] for r in all_rows)))
    api.save(OUT / "manifest.json", manifest)
    lines = ["# 严格基准点解耦验证", "", f"候选 DLL SHA-256：`{manifest['dll']}`", "",
             "本轮固定参考图和参考 P1/P2，只改变当前帧 P1/P2。扰动包括 ±40/80/120 px 平移、0.50/0.65/1.35/1.50 间距缩放、±5/10/15° 旋转、组合扰动和两个端点非刚性移动。开发组A运行到第 252 帧、验证组C运行到第 25 帧以覆盖已确认阶段，其余大图像序列取连续 12 帧；CT3 使用 136 帧全量回放。", "",
             "| 组别 | 扰动 | 有效输入 | 执行 | 状态变化 | 坐标变化 | 最大偏差 px |", "|---|---|---:|---:|---:|---:|---:|"]
    for r in summary:
        lines.append(f"| {r['group']} | {r['case']} | {r['valid_inputs']} | {r['executed']} | {r['state_mismatches']} | {r['coordinate_mismatches']} | {r['max_delta_px'] if r['max_delta_px'] is not None else '—'} |")
    lines += ["", "判定口径：尖端确认状态和尖端坐标必须与原始当前 P1/P2 相同。路径和完整长度仍属于主路径测量，不作为端点解耦唯一判据。", "", "原始逐帧数据见 `per_case_frame.csv`；汇总见 `summary.csv`。"]
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("STRICT ANCHOR AUDIT COMPLETE", flush=True)


if __name__ == "__main__":
    main()
