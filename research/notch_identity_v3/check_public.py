"""Reproduce the frozen synthetic matrix without experimental data."""
import csv
from pathlib import Path
from . import probes


def main():
    probes.RUN.mkdir(parents=True, exist_ok=True)
    probes.run(["s1", "s2", "s3", "s3t"])
    expected = Path(__file__).resolve().parents[2] / "evidence/v3/probes.csv"
    def load(path):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    actual = load(probes.RUN / "probes.csv")
    reference = load(expected)
    if len(actual) != 420 or actual != reference:
        raise SystemExit("Synthetic results differ from the frozen 420-row matrix")
    print("Verified all 420 synthetic results")


if __name__ == "__main__":
    main()
