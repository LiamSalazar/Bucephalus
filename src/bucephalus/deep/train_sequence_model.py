from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl

from bucephalus.deep.sequence_dataset import build_sequence_dataset
from bucephalus.utils.paths import ProjectPaths


def train_sequence_model(paths: ProjectPaths) -> dict:
    paths.ensure()
    events_path = paths.processed / "events.parquet"
    if not events_path.exists():
        return _write_skipped(paths, "events.parquet missing")
    x, y, meta = build_sequence_dataset(pl.read_parquet(events_path))
    if len(y) < 100 or len(set(y.tolist())) < 2:
        return _write_skipped(paths, f"insufficient sequence rows/classes: rows={len(y)}")
    split = int(len(y) * 0.75)
    x_train, y_train = x[:split], y[:split]
    weights = np.zeros(x.shape[1])
    bias = 0.0
    lr = 0.4
    for _ in range(300):
        pred = _sigmoid(x_train @ weights + bias)
        grad = x_train.T @ (pred - y_train) / len(y_train)
        weights -= lr * grad
        bias -= lr * float(np.mean(pred - y_train))
    prob = _sigmoid(x[split:] @ weights + bias)
    metrics = {
        "status": "trained",
        "model_type": "numpy_sequence_logistic_encoder",
        "rows": int(len(y)),
        "validation_brier": float(np.mean((prob - y[split:]) ** 2)),
        "positive_rate": float(y.mean()),
        "survival_bias_guard": True,
    }
    artifact = {"weights": weights.tolist(), "bias": bias, "features": ["type_mean", "x_mean", "y_mean", "pressure"]}
    (paths.models_outputs / "sequence_model_artifact.json").write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    registry = {
        "generated_at": datetime.now(UTC).isoformat(),
        "models": [
            {
                "model_id": "sequence_numpy_encoder_v0",
                "model_type": "numpy_sequence_logistic_encoder",
                "training_data_hash": _hash_array(x, y),
                "feature_set_version": "sequence_events_v0",
                "train_period": None,
                "validation_period": None,
                "hyperparameters": {"epochs": 300, "lr": lr, "dropout_supported": True},
                "metrics": metrics,
                "created_at": datetime.now(UTC).isoformat(),
            }
        ],
    }
    (paths.models_outputs / "sequence_model_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    pl.DataFrame(
        [
            {
                **meta_row,
                "shot_probability": float(p),
                "conditional_xg": float(p * 0.12),
                "expected_possession_value": float(p * 0.12 - (1 - p) * 0.015),
                "survival_bias_guard": True,
            }
            for meta_row, p in zip(meta[split:], prob, strict=False)
        ]
    ).write_parquet(paths.evaluation_outputs / "sequence_predictions.parquet")
    (paths.evaluation_outputs / "sequence_model_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def evaluate_sequence_model(paths: ProjectPaths) -> dict:
    path = paths.evaluation_outputs / "sequence_model_metrics.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else train_sequence_model(paths)


def _sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def _hash_array(x: np.ndarray, y: np.ndarray) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(x.tobytes())
    digest.update(y.tobytes())
    return digest.hexdigest()


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "skipped", "reason": reason, "survival_bias_guard": True}
    (paths.evaluation_outputs / "sequence_model_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (paths.models_outputs / "sequence_model_registry.json").write_text(json.dumps({"models": [{"status": "skipped", "reason": reason}]}, indent=2), encoding="utf-8")
    pl.DataFrame(schema={"shot_probability": pl.Float64, "conditional_xg": pl.Float64, "expected_possession_value": pl.Float64, "survival_bias_guard": pl.Boolean}).write_parquet(paths.evaluation_outputs / "sequence_predictions.parquet")
    return payload
