from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def build_possession_value_samples(paths: ProjectPaths) -> dict:
    paths.ensure()
    hazard_path = paths.evaluation_outputs / "hazard_predictions.parquet"
    if not hazard_path.exists():
        return _write_skipped(paths, "hazard predictions missing")
    hazard = pl.read_parquet(hazard_path)
    if hazard.is_empty():
        return _write_skipped(paths, "hazard predictions empty")
    out = _attach_conditional_xg(paths, hazard).with_columns(
        (pl.col("turnover_probability") * 0.08).alias("counterattack_risk"),
        (pl.col("final_third_entry_probability") * 0.025 + pl.col("box_entry_probability") * 0.035).alias("progression_value"),
        pl.lit("hazard_logistic_next_5_events").alias("hazard_source"),
    ).with_columns(
        (pl.col("shot_probability") * pl.col("conditional_xg") - pl.col("counterattack_risk") + pl.col("progression_value")).alias("expected_possession_value"),
        pl.lit(True).alias("survival_bias_guard"),
    )
    out.write_parquet(paths.evaluation_outputs / "epv_predictions.parquet")
    out.sort("expected_possession_value", descending=True).head(25).write_csv(paths.evaluation_outputs / "epv_top_possessions.csv")
    metrics = {
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": out.height,
        "mean_epv": float(out["expected_possession_value"].mean()),
        "survival_bias_guard": True,
        "alignment_keys": ["match_id", "possession", "team_id", "event_id", "event_index", "minute", "second"],
        "xg_sources": sorted(set(out["xg_source"].to_list())) if "xg_source" in out.columns else [],
        "hazard_source": "hazard_logistic_next_5_events",
    }
    (paths.evaluation_outputs / "epv_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    # Backward-compatible aliases.
    out.write_parquet(paths.evaluation_outputs / "possession_value_samples.parquet")
    (paths.evaluation_outputs / "possession_value_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "skipped", "reason": reason, "survival_bias_guard": True}
    schema = {"match_id": pl.Int64, "possession": pl.Int64, "team_id": pl.Int64, "event_id": pl.Utf8, "event_index": pl.Int64, "minute": pl.Int64, "second": pl.Int64, "shot_probability": pl.Float64, "conditional_xg": pl.Float64, "turnover_probability": pl.Float64, "counterattack_risk": pl.Float64, "progression_value": pl.Float64, "expected_possession_value": pl.Float64, "survival_bias_guard": pl.Boolean, "xg_source": pl.Utf8, "hazard_source": pl.Utf8}
    pl.DataFrame(schema=schema).write_parquet(paths.evaluation_outputs / "epv_predictions.parquet")
    pl.DataFrame(schema=schema).write_parquet(paths.evaluation_outputs / "possession_value_samples.parquet")
    (paths.evaluation_outputs / "epv_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (paths.evaluation_outputs / "possession_value_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _attach_conditional_xg(paths: ProjectPaths, hazard: pl.DataFrame) -> pl.DataFrame:
    candidates = [
        (paths.evaluation_outputs / "tabular_predictions.parquet", "tabular_xg_v2_hgb"),
        (paths.evaluation_outputs / "xg_predictions.parquet", "xg_logistic_v1"),
    ]
    for path, source in candidates:
        if not path.exists():
            continue
        pred = pl.read_parquet(path)
        required = {"match_id", "possession", "team_id", "conditional_xg"}
        if pred.is_empty() or not required.issubset(set(pred.columns)):
            continue
        grouped = pred.group_by(["match_id", "possession", "team_id"]).agg(pl.col("conditional_xg").mean().alias("conditional_xg_model"))
        joined = hazard.join(grouped, on=["match_id", "possession", "team_id"], how="left")
        proxy = (0.04 + 0.16 * joined["box_entry_probability"] + 0.05 * joined["final_third_entry_probability"]).clip(0.01, 0.6)
        return joined.with_columns(
            pl.when(pl.col("conditional_xg_model").is_not_null())
            .then(pl.col("conditional_xg_model"))
            .otherwise(pl.Series("conditional_xg_proxy", proxy))
            .alias("conditional_xg"),
            pl.when(pl.col("conditional_xg_model").is_not_null()).then(pl.lit(source)).otherwise(pl.lit("event_context_proxy")).alias("xg_source"),
        ).drop("conditional_xg_model")
    proxy = (0.04 + 0.16 * hazard["box_entry_probability"] + 0.05 * hazard["final_third_entry_probability"]).clip(0.01, 0.6)
    return hazard.with_columns(pl.Series("conditional_xg", proxy), pl.lit("event_context_proxy").alias("xg_source"))
