from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.features.feature_store import build_feature_store
from bucephalus.utils.logging import configure_logging
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    configure_logging("DEBUG" if args.verbose else "INFO")
    manifest = build_feature_store(ProjectPaths(data_root=args.data_root))
    print("Feature store tables:", manifest["rows_by_table"])


if __name__ == "__main__":
    main()
