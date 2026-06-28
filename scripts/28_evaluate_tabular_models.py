from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.models.advanced_tabular import evaluate_tabular_models
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    print(evaluate_tabular_models(ProjectPaths(data_root=args.data_root)))


if __name__ == "__main__":
    main()
