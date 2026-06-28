from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.calibration.bootstrap import bootstrap_tactical_effects, bootstrap_tactical_parameters
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--n-bootstraps", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    print(bootstrap_tactical_parameters(paths, args.n_bootstraps, args.seed))
    print(bootstrap_tactical_effects(paths, args.n_bootstraps, args.seed))


if __name__ == "__main__":
    main()
