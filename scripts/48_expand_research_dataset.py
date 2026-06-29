from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.data.expansion import write_data_expansion_report
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    print(write_data_expansion_report(ProjectPaths(data_root=args.data_root)))


if __name__ == "__main__":
    main()
