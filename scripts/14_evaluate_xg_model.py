from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.models.xg_model import evaluate_xg_model
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    print(evaluate_xg_model(ProjectPaths(data_root=args.data_root)))


if __name__ == "__main__":
    main()
