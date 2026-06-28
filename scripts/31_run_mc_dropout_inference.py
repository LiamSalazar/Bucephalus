from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.deep.inference import run_mc_dropout
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--n-mc-samples", type=int, default=50)
    args = parser.parse_args()
    print(run_mc_dropout(ProjectPaths(data_root=args.data_root), n_mc_samples=args.n_mc_samples))


if __name__ == "__main__":
    main()
