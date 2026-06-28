from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.models.hazard_model import evaluate_hazard_model
from bucephalus.models.possession_value import build_possession_value_samples
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    print(evaluate_hazard_model(paths))
    print(build_possession_value_samples(paths))


if __name__ == "__main__":
    main()
