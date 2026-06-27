from __future__ import annotations

from pathlib import Path

import polars as pl


def validate_required_columns(path: Path, required: set[str]) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    columns = set(pl.read_parquet(path, n_rows=0).columns)
    missing = required - columns
    if missing:
        raise ValueError(f"{path.name} missing columns: {sorted(missing)}")


def validate_processed_dataset(processed_dir: Path) -> None:
    validate_required_columns(processed_dir / "matches.parquet", {"match_id", "home_team_id", "away_team_id"})
    validate_required_columns(processed_dir / "events.parquet", {"match_id", "event_id", "event_type"})
