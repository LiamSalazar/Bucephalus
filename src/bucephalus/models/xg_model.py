from __future__ import annotations

import json
from datetime import UTC, datetime

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from bucephalus.models.calibration_curves import calibration_summary
from bucephalus.models.xg_features import build_xg_training_frame, feature_columns
from bucephalus.utils.paths import ProjectPaths

MIN_SHOTS_FOR_MODEL = 100


def train_xg_model(paths: ProjectPaths) -> dict:
    shots_path = paths.processed / "shots.parquet"
    paths.ensure()
    if not shots_path.exists():
        return _write_insufficient(paths, "shots.parquet missing")
    df = build_xg_training_frame(pl.read_parquet(shots_path)).drop_nulls(["is_goal"])
    if df.height < MIN_SHOTS_FOR_MODEL or df["is_goal"].n_unique() < 2:
        return _write_insufficient(paths, f"insufficient shots/classes: rows={df.height}")
    features = feature_columns(df)
    x = df.select(features).fill_null(0).to_numpy()
    y = np.array(df["is_goal"].to_list())
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, shuffle=False)
    scaler = StandardScaler()
    x_train_s = scaler.fit_transform(x_train)
    x_test_s = scaler.transform(x_test)
    model = LogisticRegression(max_iter=500)
    model.fit(x_train_s, y_train)
    prob = model.predict_proba(x_test_s)[:, 1]
    global_rate = float(y_train.mean())
    baseline_prob = np.full_like(prob, global_rate, dtype=float)
    metrics = {
        "status": "trained",
        "rows": int(df.height),
        "features": features,
        "log_loss": float(log_loss(y_test, prob, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y_test, prob)),
        "roc_auc": float(roc_auc_score(y_test, prob)) if len(set(y_test)) > 1 else None,
        "avg_predicted_xg": float(prob.mean()),
        "actual_goal_rate": float(y_test.mean()),
        "baseline_global_log_loss": float(log_loss(y_test, baseline_prob, labels=[0, 1])),
    }
    predictions = pl.DataFrame({"actual_goal": y_test, "predicted_xg": prob})
    predictions.write_parquet(paths.evaluation_outputs / "xg_predictions.parquet")
    cal = calibration_summary(y_test.tolist(), prob.tolist())
    cal.write_csv(paths.evaluation_outputs / "xg_calibration_summary.csv")
    _plot_reliability(cal, paths.evaluation_outputs / "figures" / "xg_reliability_curve.png")
    (paths.evaluation_outputs / "xg_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    registry = {"generated_at": datetime.now(UTC).isoformat(), "models": [{"model_name": "logistic_regression_xg", "status": "trained", "features": features}]}
    (paths.models_outputs / "xg_model_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return metrics


def evaluate_xg_model(paths: ProjectPaths) -> dict:
    metrics_path = paths.evaluation_outputs / "xg_metrics.json"
    if not metrics_path.exists():
        return train_xg_model(paths)
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def _write_insufficient(paths: ProjectPaths, reason: str) -> dict:
    paths.ensure()
    metrics = {"status": "skipped", "reason": reason, "log_loss": None, "brier_score": None, "roc_auc": None}
    (paths.evaluation_outputs / "xg_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (paths.models_outputs / "xg_model_registry.json").write_text(json.dumps({"models": [{"model_name": "xg_logistic", "status": "skipped", "reason": reason}]}, indent=2), encoding="utf-8")
    pl.DataFrame(schema={"actual_goal": pl.Int8, "predicted_xg": pl.Float64}).write_parquet(paths.evaluation_outputs / "xg_predictions.parquet")
    pl.DataFrame(schema={"bin_lower": pl.Float64, "bin_upper": pl.Float64, "count": pl.Int64, "mean_prediction": pl.Float64, "actual_rate": pl.Float64}).write_csv(paths.evaluation_outputs / "xg_calibration_summary.csv")
    return metrics


def _plot_reliability(cal: pl.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5, 4))
    if not cal.is_empty():
        plt.plot(cal["mean_prediction"], cal["actual_rate"], marker="o")
    plt.plot([0, 1], [0, 1], linestyle="--")
    plt.xlabel("mean predicted xG")
    plt.ylabel("actual goal rate")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
