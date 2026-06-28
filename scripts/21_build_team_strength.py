from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.models.team_strength import build_team_strength_timeseries
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    print(build_team_strength_timeseries(ProjectPaths(data_root=args.data_root)))


if __name__ == "__main__":
    main()
