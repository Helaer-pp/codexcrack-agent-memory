"""Regression for invalid current P1/P2 isolation after initialization."""
from pathlib import Path
import json, os, sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "gate_adapt"))
sys.path.insert(0, str(ROOT / "src" / "python"))
import cv2
from crackv4 import frozen_a as api
from crackv4.dataset_policy import allowed
from all_groups import inventory

DLL = ROOT / "output" / "build" / "src" / "cpp" / "a" / "Release" / "CrackV4.dll"
api.BASE = DLL
api.EXPECTED_BASE = api.sha(DLL)
api._base = None


def main():
    groups = [g for g in ["group_a", "group_c", "ct2", "group_h", "three_point_bend", "group_x"] if allowed(g,'validation')]
    cases = {
        "nan": [[float("nan"), 1.0], [2.0, 2.0]],
        "outside": [[-10.0, -10.0], [999999.0, 999999.0]],
        "degenerate": [[10.0, 10.0], [10.5, 10.5]],
    }
    rows = []
    for group in groups:
        mode, seq = inventory()[group]
        ref = api.read(seq[0][0])
        base_points = np.asarray(seq[0][1], dtype=float)
        image = api.read(seq[1][0])
        valid_points = np.asarray(seq[1][1], dtype=float)
        for name, bad in cases.items():
            det = api.Baseline(ref, base_points, mode=mode)
            try:
                det.run(ref, base_points, is_reference=True)
                raw = det.run(image, bad, is_reference=False)
                geometry = json.loads(det.lib.CrackV4LastGeometryJson(det.handle))
                rows.append({"group": group, "case": name, "return_ok": 1,
                             "current_anchor_invalid": int(geometry.get("current_anchor_invalid", False)),
                             "tip_confirmed": int(raw["formal"]["confirmed_tip"]),
                             "failure": ""})
            except Exception as exc:
                rows.append({"group": group, "case": name, "return_ok": 0,
                             "current_anchor_invalid": None, "tip_confirmed": None,
                             "failure": type(exc).__name__ + ": " + str(exc)[:160]})
            finally:
                det.close()
        # Valid controls remain executable.
        det = api.Baseline(ref, base_points, mode=mode)
        try:
            det.run(ref, base_points, is_reference=True)
            raw = det.run(image, valid_points, is_reference=False)
            rows.append({"group": group, "case": "valid_control", "return_ok": 1,
                         "current_anchor_invalid": 0,
                         "tip_confirmed": int(raw["formal"]["confirmed_tip"]), "failure": ""})
        finally:
            det.close()
    bad = [r for r in rows if r["case"] != "valid_control" and not r["return_ok"]]
    assert not bad, bad
    assert all(r["current_anchor_invalid"] == 1 for r in rows if r["case"] != "valid_control")
    print(json.dumps({"passed": True, "rows": rows}, ensure_ascii=False))


if __name__ == "__main__":
    main()
