from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.data.duckdb_catalog import build_duckdb_catalog, list_catalog_views
from bucephalus.utils.logging import configure_logging
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    configure_logging("DEBUG" if args.verbose else "INFO")
    paths = ProjectPaths(data_root=args.data_root)
    build_duckdb_catalog(paths)
    print("DuckDB catalog views:", ", ".join(list_catalog_views(paths)))


if __name__ == "__main__":
    main()
