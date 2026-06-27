from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.data.process_statsbomb import process_raw_to_parquet
from bucephalus.data.validation import validate_data_quality
from bucephalus.utils.logging import configure_logging
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    configure_logging("DEBUG" if args.verbose else "INFO")
    paths = ProjectPaths(data_root=args.data_root)
    process_raw_to_parquet(paths)
    validate_data_quality(paths)


if __name__ == "__main__":
    main()
