from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

from bucephalus.utils.paths import ProjectPaths


def build_hazard_frame(events: pl.DataFrame, horizon_events: int = 5) -> pl.DataFrame:
    if events.is_empty():
        return pl.DataFrame()
    rows = []
    for _, group in events.sort(["match_id", "possession", "event_index"]).group_by(["match_id", "possession"], maintain_order=True):
        items = group.to_dicts()
        for idx, row in enumerate(items[:-1]):
            future = items[idx + 1 : idx + 1 + horizon_events]
            rows.append(
                {
                    "match_id": row.get("match_id"),
                    "event_id": row.get("event_id"),
                    "minute": row.get("minute") or 0,
                    "location_x": row.get("location_x") or 60.0,
                    "location_y": row.get("location_y") or 40.0,
                    "under_pressure_int": int(bool(row.get("under_pressure"))),
                    "is_pass": int(row.get("type_name") == "Pass"),
                    "is_carry": int(row.get("type_name") == "Carry"),
                    "is_pressure": int(row.get("type_name") == "Pressure"),
                    "shot_in_next_5_events": int(any(f.get("type_name") == "Shot" for f in future)),
                }
            )
    return pl.DataFrame(rows)


def train_hazard_model(paths: ProjectPaths) -> dict:
    paths.ensure()
    events_path = paths.processed / "events.parquet"
    if not events_path.exists():
        return _write_skipped(paths, "events.parquet missing")
    frame = build_hazard_frame(pl.read_parquet(events_path))
    if frame.height < 500 or frame["shot_in_next_5_events"].n_unique() < 2:
        return _write_skipped(paths, f"insufficient hazard rows/classes: rows={frame.height}")
    features = ["minute", "location_x", "location_y", "under_pressure_int", "is_pass", "is_carry", "is_pressure"]
    split = int(frame.height * 0.75)
    x = frame.select(features).fill_null(0).to_numpy()
    y = np.array(frame["shot_in_next_5_events"].to_list())
    scaler = StandardScaler()
    x_train = scaler.fit_transform(x[:split])
    x_test = scaler.transform(x[split:])
    model = LogisticRegression(max_iter=300, class_weight="balanced")
    model.fit(x_train, y[:split])
    prob = model.predict_proba(x_test)[:, 1]
    metrics = {
        "status": "trained",
        "rows": int(frame.height),
        "positive_rate": float(y.mean()),
        "roc_auc": float(roc_auc_score(y[split:], prob)) if len(set(y[split:])) > 1 else None,
        "pr_auc": float(average_precision_score(y[split:], prob)),
        "brier_score": float(brier_score_loss(y[split:], prob)),
        "log_loss": float(log_loss(y[split:], prob, labels=[0, 1])),
        "horizon": "next_5_events_proxy",
    }
    pl.DataFrame({"actual": y[split:], "shot_probability": prob}).write_parquet(paths.evaluation_outputs / "hazard_predictions.parquet")
    (paths.evaluation_outputs / "hazard_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    registry = {
        "generated_at": datetime.now(UTC).isoformat(),
        "models": [
            {
                "model_id": "hazard_logistic_next_5_events",
                "model_type": "LogisticRegression",
                "training_data_hash": _hash_frame(frame.select(features + ["shot_in_next_5_events"])),
                "feature_set_version": "event_hazard_v0",
                "train_period": None,
                "validation_period": None,
                "hyperparameters": {"class_weight": "balanced"},
                "metrics": metrics,
                "created_at": datetime.now(UTC).isoformat(),
            }
        ],
    }
    (paths.models_outputs / "hazard_model_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return metrics


def evaluate_hazard_model(paths: ProjectPaths) -> dict:
    path = paths.evaluation_outputs / "hazard_metrics.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else train_hazard_model(paths)


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "skipped", "reason": reason}
    (paths.evaluation_outputs / "hazard_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pl.DataFrame(schema={"actual": pl.Int8, "shot_probability": pl.Float64}).write_parquet(paths.evaluation_outputs / "hazard_predictions.parquet")
    (paths.models_outputs / "hazard_model_registry.json").write_text(json.dumps({"models": [{"status": "skipped", "reason": reason}]}, indent=2), encoding="utf-8")
    return payload


def _hash_frame(df: pl.DataFrame) -> str:
    import hashlib

    return hashlib.sha256(df.write_csv().encode("utf-8")).hexdigest()
