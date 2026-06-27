from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import polars as pl

from bucephalus.features.schemas import LEAKAGE_TARGET_COLUMNS
from bucephalus.utils.paths import ProjectPaths

FEATURE_TABLES = [
    "match_features.parquet",
    "team_match_features.parquet",
    "player_match_features.parquet",
    "team_rolling_features.parquet",
    "player_rolling_features.parquet",
    "tactical_team_profiles.parquet",
    "model_dataset_matches.parquet",
    "model_dataset_team_matches.parquet",
    "feature_manifest.json",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    failures = []
    for path in [
        paths.quality_outputs / "research_dataset_summary.json",
        paths.models_outputs / "baseline_registry.json",
        paths.evaluation_outputs / "baseline_metrics.json",
        paths.evaluation_outputs / "leakage_check.json",
        paths.evaluation_outputs / "model_comparison.csv",
    ]:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    for table in FEATURE_TABLES:
        if not (paths.features / table).exists():
            failures.append(f"missing feature table: {table}")
    model_path = paths.features / "model_dataset_matches.parquet"
    if model_path.exists():
        cols = set(pl.read_parquet(model_path, n_rows=0).columns)
        feature_cols = {c for c in cols if c.startswith(("home_rolling_", "away_rolling_", "diff_rolling_"))}
        if feature_cols & LEAKAGE_TARGET_COLUMNS:
            failures.append("target columns leaked into feature-prefixed columns")
    if not args.skip_tests:
        result = subprocess.run([sys.executable, "-m", "pytest"], cwd=paths.root, check=False)
        if result.returncode != 0:
            failures.append("pytest failed")
    if failures:
        print("PHASE 4-5 CHECK: FAIL")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("PHASE 4-5 CHECK: PASS")


if __name__ == "__main__":
    main()
