from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths


def build_tactical_engine_inputs(paths: ProjectPaths | None = None) -> dict:
    paths = paths or settings.paths
    paths.ensure()
    tactical = pl.read_parquet(paths.features / "tactical_team_profiles.parquet")
    percentiled = _with_percentiles(tactical)
    out = percentiled.with_columns(
        ((pl.col("data_coverage_score").fill_null(0) * 0.55) + (pl.min_horizontal(pl.col("matches_count") / 10, pl.lit(1)) * 0.45)).alias("reliability_score"),
        (pl.col("matches_count") < 5).alias("sample_size_warning"),
    ).with_columns(
        pl.struct(percentiled.columns + ["sample_size_warning"]).map_elements(_label, return_dtype=pl.Utf8).alias("tactical_identity_label")
    ).select(
        "bucephalus_team_id", "team_name", "matches_count", "data_coverage_score",
        "possession_baseline", "pressing_baseline", "directness_baseline", "transition_baseline", "width_baseline",
        "centrality_baseline", "set_piece_dependency_baseline", "late_goal_for_baseline", "late_goal_against_baseline",
        "second_half_intensity_baseline", "defensive_exposure_baseline", "xg_for_baseline", "xg_against_baseline",
        "reliability_score", "sample_size_warning", "tactical_identity_label",
    )
    out.write_parquet(paths.features / "tactical_engine_inputs.parquet")
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": out.height,
        "source": "data/features/tactical_team_profiles.parquet",
        "label_policy": "interpretable percentile rules, no clustering",
        "warnings": ["sample_size_warning marks teams with fewer than 5 matches"],
    }
    (paths.features / "tactical_engine_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _with_percentiles(df: pl.DataFrame) -> pl.DataFrame:
    cols = [c for c in df.columns if c.endswith("_baseline") or c == "data_coverage_score"]
    out = df
    for col in cols:
        lo, hi = out[col].quantile(0.1), out[col].quantile(0.9)
        if hi is None or lo is None or hi == lo:
            out = out.with_columns(pl.lit(0.5).alias(col))
        else:
            out = out.with_columns(((pl.col(col) - lo) / (hi - lo)).clip(0, 1).alias(col))
    return out


def _label(row: dict) -> str:
    if row.get("sample_size_warning"):
        return "insufficient_data"
    if row.get("set_piece_dependency_baseline", 0) > 0.75:
        return "set_piece_dependent"
    if row.get("pressing_baseline", 0) > 0.7:
        return "high_press"
    if row.get("transition_baseline", 0) > 0.7:
        return "transition_attack"
    if row.get("directness_baseline", 0) > 0.7:
        return "direct_play"
    if row.get("possession_baseline", 0) > 0.7:
        return "possession_control"
    if row.get("defensive_exposure_baseline", 1) < 0.35 and row.get("transition_baseline", 0) > 0.55:
        return "low_block_counter"
    return "balanced"
