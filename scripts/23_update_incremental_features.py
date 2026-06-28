from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.features.incremental_store import update_incremental_feature_store
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    print(update_incremental_feature_store(ProjectPaths(data_root=args.data_root)))


if __name__ == "__main__":
    main()
