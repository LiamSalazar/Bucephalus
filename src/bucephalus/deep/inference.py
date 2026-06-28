from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl

from bucephalus.utils.paths import ProjectPaths


def run_mc_dropout(paths: ProjectPaths, n_mc_samples: int = 50, dropout_rate: float = 0.25) -> dict:
    artifact_path = paths.models_outputs / "sequence_model_artifact.json"
    predictions_path = paths.evaluation_outputs / "sequence_predictions.parquet"
    if not artifact_path.exists() or not predictions_path.exists():
        return _write_skipped(paths, "sequence model artifact or predictions missing")
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    weights = np.asarray(artifact["weights"], dtype=float)
    pred = pl.read_parquet(predictions_path).head(200)
    if pred.is_empty():
        return _write_skipped(paths, "sequence predictions empty")
    base = np.column_stack(
        [
            np.clip(pred["shot_probability"].to_numpy(), 0, 1),
            np.full(pred.height, 0.5),
            np.full(pred.height, 0.5),
            np.full(pred.height, 0.2),
        ]
    )
    rng = np.random.default_rng(42)
    samples = []
    for _ in range(n_mc_samples):
        mask = rng.binomial(1, 1 - dropout_rate, size=base.shape) / max(1e-9, 1 - dropout_rate)
        z = (base * mask) @ weights + float(artifact["bias"])
        samples.append(1 / (1 + np.exp(-np.clip(z, -30, 30))))
    arr = np.vstack(samples)
    out = pred.with_columns(
        pl.Series("prediction_mean", arr.mean(axis=0)),
        pl.Series("prediction_std", arr.std(axis=0)),
        pl.Series("p5", np.percentile(arr, 5, axis=0)),
        pl.Series("p50", np.percentile(arr, 50, axis=0)),
        pl.Series("p95", np.percentile(arr, 95, axis=0)),
        pl.lit(n_mc_samples).alias("n_mc_samples"),
    ).with_columns(pl.col("prediction_std").alias("epistemic_uncertainty"))
    out.write_parquet(paths.evaluation_outputs / "mc_dropout_uncertainty.parquet")
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "completed",
        "rows": out.height,
        "n_mc_samples": n_mc_samples,
        "mean_epistemic_uncertainty": float(out["epistemic_uncertainty"].mean()),
    }
    (paths.evaluation_outputs / "mc_dropout_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "skipped", "reason": reason}
    (paths.evaluation_outputs / "mc_dropout_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pl.DataFrame(schema={"prediction_mean": pl.Float64, "prediction_std": pl.Float64, "p5": pl.Float64, "p50": pl.Float64, "p95": pl.Float64}).write_parquet(paths.evaluation_outputs / "mc_dropout_uncertainty.parquet")
    return payload
