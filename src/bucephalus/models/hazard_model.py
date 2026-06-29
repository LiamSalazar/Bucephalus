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
                    "team_id": row.get("team_id"),
                    "possession": row.get("possession"),
                    "event_index": row.get("event_index"),
                    "second": row.get("second") or 0,
                    "shot_in_next_5_events": int(any(f.get("type_name") == "Shot" for f in future)),
                    "turnover_in_next_5_events": int(any(f.get("type_name") in {"Interception", "Duel"} and f.get("team_id") != row.get("team_id") for f in future)),
                    "box_entry_in_next_5_events": int(any((f.get("location_x") or 0) >= 102 for f in future)),
                    "final_third_entry_in_next_5_events": int(any((f.get("location_x") or 0) >= 80 for f in future)),
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
    turnover_prob = _rate_by_zone(frame[:split], frame[split:], "turnover_in_next_5_events")
    box_prob = _rate_by_zone(frame[:split], frame[split:], "box_entry_in_next_5_events")
    final_third_prob = _rate_by_zone(frame[:split], frame[split:], "final_third_entry_in_next_5_events")
    metrics = {
        "status": "trained",
        "rows": int(frame.height),
        "positive_rate": float(y.mean()),
        "roc_auc": float(roc_auc_score(y[split:], prob)) if len(set(y[split:])) > 1 else None,
        "pr_auc": float(average_precision_score(y[split:], prob)),
        "brier_score": float(brier_score_loss(y[split:], prob)),
        "log_loss": float(log_loss(y[split:], prob, labels=[0, 1])),
        "calibration_error": _calibration_error(y[split:], prob),
        "horizon": "next_5_events_proxy",
        "hazard_time_mode": "event_horizon_proxy",
        "targets": ["shot_in_next_5_events", "turnover_in_next_5_events", "box_entry_in_next_5_events", "final_third_entry_in_next_5_events"],
    }
    pred_meta = frame[split:].select(["match_id", "possession", "team_id", "event_id", "event_index", "minute", "second"]).with_columns(
        pl.Series("actual", y[split:]),
        pl.Series("shot_probability", prob),
        pl.Series("turnover_probability", turnover_prob),
        pl.Series("box_entry_probability", box_prob),
        pl.Series("final_third_entry_probability", final_third_prob),
    )
    pred_meta.write_parquet(paths.evaluation_outputs / "hazard_predictions.parquet")
    _calibration(pred_meta, paths)
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
                "model_hyperparameters": {"class_weight": "balanced"},
                "metrics": metrics,
                "created_at": datetime.now(UTC).isoformat(),
                "artifact_path": str(paths.evaluation_outputs / "hazard_predictions.parquet"),
                "status": "candidate",
                "limitations": ["event horizon proxy used when reliable seconds horizon is unavailable"],
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
    pl.DataFrame(schema={"match_id": pl.Int64, "possession": pl.Int64, "team_id": pl.Int64, "event_id": pl.Utf8, "event_index": pl.Int64, "minute": pl.Int64, "second": pl.Int64, "actual": pl.Int8, "shot_probability": pl.Float64, "turnover_probability": pl.Float64, "box_entry_probability": pl.Float64, "final_third_entry_probability": pl.Float64}).write_parquet(paths.evaluation_outputs / "hazard_predictions.parquet")
    pl.DataFrame(schema={"bin": pl.Int64, "count": pl.Int64, "mean_prediction": pl.Float64, "actual_rate": pl.Float64}).write_csv(paths.evaluation_outputs / "hazard_calibration_summary.csv")
    (paths.models_outputs / "hazard_model_registry.json").write_text(json.dumps({"models": [{"status": "skipped", "reason": reason}]}, indent=2), encoding="utf-8")
    return payload


def _hash_frame(df: pl.DataFrame) -> str:
    import hashlib

    return hashlib.sha256(df.write_csv().encode("utf-8")).hexdigest()


def _rate_by_zone(train: pl.DataFrame, test: pl.DataFrame, target: str) -> np.ndarray:
    rates = train.with_columns((pl.col("location_x") // 20).clip(0, 5).alias("zone")).group_by("zone").agg(pl.col(target).mean().alias("rate"))
    joined = test.with_columns((pl.col("location_x") // 20).clip(0, 5).alias("zone")).join(rates, on="zone", how="left")
    return np.asarray(joined["rate"].fill_null(float(train[target].mean())).to_list(), dtype=float)


def _calibration(pred: pl.DataFrame, paths: ProjectPaths) -> None:
    rows = []
    for i in range(10):
        lo, hi = i / 10, (i + 1) / 10
        part = pred.filter((pl.col("shot_probability") >= lo) & (pl.col("shot_probability") < hi))
        rows.append({"bin": i, "count": part.height, "mean_prediction": float(part["shot_probability"].mean() or 0), "actual_rate": float(part["actual"].mean() or 0)})
    pl.DataFrame(rows).write_csv(paths.evaluation_outputs / "hazard_calibration_summary.csv")


def _calibration_error(y_true: np.ndarray, prob: np.ndarray) -> float:
    error = 0.0
    total = len(prob)
    for i in range(10):
        lo, hi = i / 10, (i + 1) / 10
        mask = (prob >= lo) & (prob < hi)
        if mask.any():
            error += float(mask.mean()) * abs(float(prob[mask].mean()) - float(y_true[mask].mean()))
    return float(error if total else 0.0)
