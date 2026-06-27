from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from bucephalus.data.download_statsbomb import download_sample
from bucephalus.data.duckdb_catalog import build_duckdb_catalog, list_catalog_views
from bucephalus.data.entity_resolution import build_master_entities
from bucephalus.data.process_statsbomb import process_raw_to_parquet
from bucephalus.data.validation import validate_data_quality
from bucephalus.eda.distributions import run_eda
from bucephalus.features.build_basic_features import build_basic_features
from bucephalus.utils.logging import configure_logging
from bucephalus.utils.paths import ProjectPaths

REQUIRED_PROCESSED = [
    "competitions.parquet",
    "matches.parquet",
    "events.parquet",
    "shots.parquet",
    "passes.parquet",
    "master_players.parquet",
    "master_teams.parquet",
    "master_competitions.parquet",
    "master_matches.parquet",
    "external_entity_links.parquet",
    "data_manifest.json",
]

REQUIRED_EDA = [
    "event_type_counts.parquet",
    "goals_by_match.parquet",
    "team_profiles_baseline.parquet",
    "fat_tail_summary.parquet",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--keep-data", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    configure_logging("DEBUG" if args.verbose else "INFO")
    paths = ProjectPaths(data_root=args.data_root)
    failures: list[str] = []
    try:
        if not args.keep_data and paths.data.exists():
            for child in [paths.raw, paths.interim, paths.processed, paths.features]:
                if child.exists():
                    shutil.rmtree(child)
        paths.ensure()
        for keep in [paths.raw, paths.interim, paths.processed, paths.features]:
            (keep / ".gitkeep").write_text("\n", encoding="utf-8")
        download_sample(paths=paths, max_matches=2, force_fallback=True, mode="fallback")
        process_raw_to_parquet(paths)
        validate_data_quality(paths)
        build_master_entities(paths)
        build_basic_features(paths)
        run_eda(paths)
        build_duckdb_catalog(paths)
        for name in REQUIRED_PROCESSED:
            if not (paths.processed / name).exists():
                failures.append(f"missing processed artifact: {name}")
        if not (paths.quality_outputs / "data_quality_summary.json").exists():
            failures.append("missing quality summary")
        for name in REQUIRED_EDA:
            if not (paths.eda_tables / name).exists():
                failures.append(f"missing EDA table: {name}")
        views = set(list_catalog_views(paths))
        for view in ["events", "matches", "master_players", "external_entity_links"]:
            if view not in views:
                failures.append(f"missing DuckDB view: {view}")
    except Exception as exc:
        failures.append(str(exc))

    if failures:
        print("PHASE 1-3 CHECK: FAIL")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("PHASE 1-3 CHECK: PASS")


if __name__ == "__main__":
    main()
