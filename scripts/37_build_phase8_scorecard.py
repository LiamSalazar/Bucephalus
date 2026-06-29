from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.models.model_scorecard import build_phase8_scorecard
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    print(build_phase8_scorecard(ProjectPaths(data_root=args.data_root)))


if __name__ == "__main__":
    main()
