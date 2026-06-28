from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.simulation.markov_calibration import calibrate_markov_matrix
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    print(calibrate_markov_matrix(ProjectPaths(data_root=args.data_root)))


if __name__ == "__main__":
    main()
