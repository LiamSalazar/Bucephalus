from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths

REQUIRED_COLUMNS = {
    "competitions": {"competition_id", "competition_name", "season_id", "season_name"},
    "matches": {
        "match_id",
        "match_date",
        "competition_id",
        "season_id",
        "home_team_id",
        "home_team_name",
        "away_team_id",
        "away_team_name",
        "home_score",
        "away_score",
    },
    "events": {"match_id", "event_id", "index", "period", "minute", "second", "type_name", "team_id", "team_name"},
    "shots": {"match_id", "event_id", "team_id", "player_id", "shot_outcome", "shot_statsbomb_xg"},
    "passes": {"match_id", "event_id", "team_id", "player_id", "pass_end_x", "pass_end_y"},
}

CRITICAL_KEYS = {
    "competitions": ["competition_id", "season_id"],
    "matches": ["match_id"],
    "events": ["match_id", "event_id"],
    "shots": ["match_id", "event_id"],
    "passes": ["match_id", "event_id"],
}


def validate_required_columns(path: Path, required: set[str]) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    columns = set(pl.read_parquet(path, n_rows=0).columns)
    missing = required - columns
    if missing:
        raise ValueError(f"{path.name} missing columns: {sorted(missing)}")


def validate_processed_dataset(processed_dir: Path) -> None:
    paths = ProjectPaths(data_root=processed_dir.parent)
    summary = validate_data_quality(paths)
    if not summary["passed"]:
        raise ValueError(f"Data quality failed: {summary['errors']}")


def validate_data_quality(paths: ProjectPaths | None = None, fail_on_error: bool = True) -> dict[str, Any]:
    paths = paths or settings.paths
    paths.ensure()
    tables: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []

    for table, required in REQUIRED_COLUMNS.items():
        path = paths.processed / f"{table}.parquet"
        result = _validate_table(path, required, CRITICAL_KEYS.get(table, []))
        tables[table] = result
        if result["missing_columns"]:
            errors.append(f"{table}: missing columns {result['missing_columns']}")
        if result["duplicate_critical_keys"] > 0:
            errors.append(f"{table}: duplicate critical keys {result['duplicate_critical_keys']}")
        for column, null_count in result["nulls_critical"].items():
            if null_count > 0:
                errors.append(f"{table}: critical nulls in {column}={null_count}")
        if result["rows"] == 0:
            warnings.append(f"{table}: table is empty")

    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "passed": not errors,
        "tables_verified": sorted(REQUIRED_COLUMNS),
        "tables": tables,
        "warnings": warnings,
        "errors": errors,
    }
    output_path = paths.quality_outputs / "data_quality_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if fail_on_error and errors:
        raise ValueError(f"Data quality failed: {errors}")
    return summary


def _validate_table(path: Path, required: set[str], critical_keys: list[str]) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "rows": 0,
            "columns": [],
            "missing_columns": sorted(required),
            "nulls_critical": {},
            "duplicate_critical_keys": 0,
        }
    df = pl.read_parquet(path)
    columns = set(df.columns)
    missing = sorted(required - columns)
    available_keys = [column for column in critical_keys if column in columns]
    nulls = {}
    for column in available_keys:
        nulls[column] = int(df.select(pl.col(column).is_null().sum()).item())
    duplicate_count = 0
    if available_keys and not df.is_empty():
        duplicate_count = int(df.group_by(available_keys).len().filter(pl.col("len") > 1).height)
    return {
        "exists": True,
        "rows": df.height,
        "columns": sorted(df.columns),
        "missing_columns": missing,
        "nulls_critical": nulls,
        "duplicate_critical_keys": duplicate_count,
    }
