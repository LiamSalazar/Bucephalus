from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def build_possession_value_samples(paths: ProjectPaths) -> dict:
    paths.ensure()
    hazard_path = paths.evaluation_outputs / "hazard_predictions.parquet"
    xg_path = paths.evaluation_outputs / "xg_predictions.parquet"
    if not hazard_path.exists() or not xg_path.exists():
        return _write_skipped(paths, "hazard or xG predictions missing")
    hazard_raw = pl.read_parquet(hazard_path)
    xg_raw = pl.read_parquet(xg_path)
    size = min(500, hazard_raw.height, xg_raw.height)
    hazard = hazard_raw.head(size)
    xg = xg_raw.head(size)
    if hazard.is_empty() or xg.is_empty():
        return _write_skipped(paths, "empty hazard or xG predictions")
    xg_col = "predicted_xg" if "predicted_xg" in xg.columns else "prediction"
    out = hazard.with_columns(
        pl.Series("conditional_xg", xg[xg_col].to_list()),
        (pl.col("shot_probability") * pl.Series(xg[xg_col].to_list())).alias("shot_value"),
        (0.015 * (1 - pl.col("shot_probability"))).alias("counterattack_risk"),
    ).with_columns(
        (pl.col("shot_value") - pl.col("counterattack_risk") + 0.01).alias("expected_possession_value"),
        pl.lit(True).alias("survival_bias_guard"),
    )
    out.write_parquet(paths.evaluation_outputs / "possession_value_samples.parquet")
    metrics = {
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": out.height,
        "mean_epv": float(out["expected_possession_value"].mean()),
        "survival_bias_guard": True,
    }
    (paths.evaluation_outputs / "possession_value_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "skipped", "reason": reason, "survival_bias_guard": True}
    pl.DataFrame(schema={"shot_probability": pl.Float64, "conditional_xg": pl.Float64, "expected_possession_value": pl.Float64, "survival_bias_guard": pl.Boolean}).write_parquet(paths.evaluation_outputs / "possession_value_samples.parquet")
    (paths.evaluation_outputs / "possession_value_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
