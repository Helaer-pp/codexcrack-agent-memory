"""Compare a public runner replay with the corresponding sealed stage and media."""
import argparse
import csv
import json
from pathlib import Path
import cv2
from PIL import Image


def check(run, predictions, placement, first_baseline_frame):
    settings = json.loads((run/"run.json").read_text(encoding="utf8"))["settings"]
    with (run/"paths.jsonl").open(encoding="utf8") as lines:
        rows = [json.loads(line) for line in lines]
    with (run/"results.csv").open(encoding="utf-8-sig", newline="") as f:
        csv_rows = list(csv.DictReader(f))
    if not rows or len(csv_rows) != len(rows):
        raise ValueError("Incomplete replay")
    first = first_baseline_frame if first_baseline_frame is not None else rows[0]["frame"]
    with predictions.open(encoding="utf8") as f:
        for _ in range(first-1):
            next(f)
        for i, (row, csvrow) in enumerate(zip(rows, csv_rows)):
            golden = json.loads(next(f))
            expected = golden["placements"][placement][row["stage"]]["full"]
            assert golden["frame"] == first+i and row["frame"] == rows[0]["frame"]+i
            assert int(csvrow["frame"]) == row["frame"] and csvrow["status"] == row["status"]
            tip = [row["tip_x"], row["tip_y"]] if row["tip_x"] is not None else None
            assert tip == expected["tip"], (row["image"], tip, expected["tip"])
            for key in ("status", "points", "path_length_px", "projected_length_px"):
                assert row[key] == expected[key], (row["image"], key)
            for option,key in (("save_comparisons","comparison"),("save_differences","difference")):
                if settings[option]:
                    with Image.open(run/row[key]) as image:
                        image.verify()
    if settings["save_video"]:
        capture = cv2.VideoCapture(str(run/"results.mp4"))
        count = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            assert frame.shape[:2] == (764,2000)
            count += 1
        capture.release()
        assert count == len(rows), (count,len(rows))
    print(f'{len(rows)} frames matched sealed paths, tips and lengths. Enabled media verified.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--placement", default="original")
    parser.add_argument("--first-baseline-frame", type=int)
    a = parser.parse_args()
    check(a.run, a.predictions, a.placement, a.first_baseline_frame)
