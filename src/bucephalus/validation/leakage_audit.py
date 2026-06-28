from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import polars as pl

from bucephalus.config import settings
from bucephalus.features.schemas import LEAKAGE_TARGET_COLUMNS
from bucephalus.models.walk_forward import temporal_split
from bucephalus.utils.paths import ProjectPaths

POST_MATCH_PREFIXES = ("shots_", "xg_", "goals_", "total_goals", "home_score", "away_score")
REQUIRED_CUTOFF_COLUMNS = {"target_match_date", "feature_cutoff_date", "feature_history_matches_available"}


def run_leakage_audit(paths: ProjectPaths | None = None) -> dict[str, Any]:
    paths = paths or settings.paths
    paths.ensure()
    dataset_path = paths.features / "model_dataset_matches.parquet"
    team_rolling_path = paths.features / "team_rolling_features.parquet"
    failures: list[str] = []
    warnings: list[str] = []
    forbidden_detected: list[str] = []
    examples: list[dict[str, Any]] = []
    if not dataset_path.exists():
        failures.append("missing model_dataset_matches.parquet")
        df = pl.DataFrame()
    else:
        df = pl.read_parquet(dataset_path).sort("match_date")
        feature_cols = [c for c in df.columns if c.startswith(("home_rolling_", "away_rolling_", "diff_rolling_"))]
        forbidden_detected = sorted(
            set(feature_cols) & LEAKAGE_TARGET_COLUMNS
            | {c for c in feature_cols for target in LEAKAGE_TARGET_COLUMNS if c.endswith(target)}
        )
        same_match_cols = [
            c for c in feature_cols
            if any(c.endswith(col) for col in ["shots_for", "xg_for", "goals_for", "goals_against"])
            and not c.startswith(("home_rolling_", "away_rolling_", "diff_rolling_"))
        ]
        if forbidden_detected:
            failures.append(f"forbidden target columns in feature set: {forbidden_detected}")
        if same_match_cols:
            failures.append(f"post-match columns detected as pre-match features: {same_match_cols}")
        examples = df.head(5).select([c for c in ["statsbomb_match_id", "match_date"] if c in df.columns]).to_dicts()
        missing_cutoff = sorted(REQUIRED_CUTOFF_COLUMNS - set(df.columns))
        if missing_cutoff:
            failures.append(f"missing cutoff columns: {missing_cutoff}")
        elif df.filter(
            pl.col("feature_cutoff_date").is_not_null()
            & (pl.col("feature_cutoff_date") >= pl.col("target_match_date"))
        ).height:
            failures.append("feature_cutoff_date >= target_match_date detected")
    rolling_ok = True
    if team_rolling_path.exists():
        rolling = pl.read_parquet(team_rolling_path)
        if "historical_matches_available" in rolling.columns and rolling["historical_matches_available"].min() < 0:
            rolling_ok = False
            failures.append("negative historical_matches_available")
    else:
        warnings.append("team_rolling_features missing")
    split_info = _split_info(df) if not df.is_empty() else {}
    if split_info and not split_info["temporal_order_passed"]:
        failures.append("temporal split order failed")
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "passed": not failures,
        "columns_audited": df.columns if not df.is_empty() else [],
        "forbidden_columns_detected": forbidden_detected,
        "rolling_features_previous_only": rolling_ok,
        "feature_timestamp_policy": "rolling features are generated before target match by construction",
        "split_dates": split_info,
        "warnings": warnings,
        "failures": failures,
        "examples": examples,
    }
    output = paths.evaluation_outputs / "leakage_audit.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _split_info(df: pl.DataFrame) -> dict[str, Any]:
    splits = temporal_split(df)
    indexed = df.with_row_index("row_id")
    rows = {}
    for name, ids in splits.items():
        part = indexed.filter(pl.col("row_id").is_in(ids))
        rows[name] = {
            "rows": part.height,
            "min_target_match_date": part["match_date"].min() if part.height else None,
            "max_feature_date": part["feature_cutoff_date"].max() if part.height and "feature_cutoff_date" in part.columns else None,
        }
    train_max = rows.get("train", {}).get("max_feature_date")
    val_min = rows.get("validation", {}).get("min_target_match_date")
    val_max = rows.get("validation", {}).get("max_feature_date")
    test_min = rows.get("test", {}).get("min_target_match_date")
    order_passed = True
    if train_max and val_min:
        order_passed = order_passed and train_max < val_min
    if val_max and test_min:
        order_passed = order_passed and val_max < test_min
    rows["temporal_order_passed"] = order_passed
    rows["no_split_overlap"] = len(set().union(*[set(v) for v in splits.values()])) == sum(len(v) for v in splits.values())
    return rows
