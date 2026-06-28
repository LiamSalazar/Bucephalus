from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.calibration.bootstrap import bootstrap_tactical_parameters
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--n-bootstraps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(bootstrap_tactical_parameters(ProjectPaths(data_root=args.data_root), args.n_bootstraps, args.seed))


if __name__ == "__main__":
    main()
