from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from bucephalus.models.xg_features import build_xg_training_frame, feature_columns
from bucephalus.utils.paths import ProjectPaths


def train_tabular_models(paths: ProjectPaths) -> dict:
    paths.ensure()
    shots_path = paths.processed / "shots.parquet"
    if not shots_path.exists():
        return _write_skipped(paths, "shots.parquet missing")
    df = build_xg_training_frame(pl.read_parquet(shots_path)).drop_nulls(["is_goal"])
    if df.height < 200 or df["is_goal"].n_unique() < 2:
        return _write_skipped(paths, f"insufficient shots/classes: rows={df.height}")
    features = feature_columns(df)
    split = int(df.height * 0.75)
    x = df.select(features).fill_null(0).to_numpy()
    y = np.array(df["is_goal"].to_list())
    model = HistGradientBoostingClassifier(max_iter=80, learning_rate=0.05, random_state=42)
    model.fit(x[:split], y[:split])
    prob = model.predict_proba(x[split:])[:, 1]
    metrics = {
        "status": "trained",
        "model_type": "hist_gradient_boosting_xg_v2",
        "rows": int(df.height),
        "features": features,
        "log_loss": float(log_loss(y[split:], prob, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y[split:], prob)),
        "roc_auc": float(roc_auc_score(y[split:], prob)) if len(set(y[split:])) > 1 else None,
    }
    meta_cols = [c for c in ["match_id", "event_id", "possession", "team_id", "player_id", "event_index", "minute", "second"] if c in df.columns]
    df.slice(split).select(meta_cols).with_columns(
        pl.Series("actual", y[split:]),
        pl.Series("prediction", prob),
        pl.Series("conditional_xg", prob),
        pl.lit("tabular_xg_v2_hgb").alias("model_id"),
    ).write_parquet(paths.evaluation_outputs / "tabular_predictions.parquet")
    (paths.evaluation_outputs / "tabular_model_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    comparison = pl.DataFrame([{"model": "hist_gradient_boosting_xg_v2", **{k: v for k, v in metrics.items() if isinstance(v, int | float | str | type(None))}}])
    comparison.write_csv(paths.evaluation_outputs / "tabular_model_comparison.csv")
    registry = {
        "generated_at": datetime.now(UTC).isoformat(),
        "models": [
            {
                "model_id": "tabular_xg_v2_hgb",
                "model_type": "HistGradientBoostingClassifier",
                "training_data_hash": _hash_frame(df.select(features + ["is_goal"])),
                "feature_set_version": "xg_v1_features_plus_categoricals",
                "train_period": None,
                "validation_period": None,
                "model_hyperparameters": {"max_iter": 80, "learning_rate": 0.05},
                "metrics": metrics,
                "created_at": datetime.now(UTC).isoformat(),
                "artifact_path": str(paths.evaluation_outputs / "tabular_predictions.parquet"),
                "status": "candidate",
                "limitations": ["advanced tabular xG must beat baseline before champion promotion"],
            }
        ],
    }
    (paths.models_outputs / "tabular_model_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    return metrics


def evaluate_tabular_models(paths: ProjectPaths) -> dict:
    path = paths.evaluation_outputs / "tabular_model_metrics.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else train_tabular_models(paths)


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "skipped", "reason": reason}
    (paths.evaluation_outputs / "tabular_model_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pl.DataFrame([{"model": "tabular_xg_v2", "status": "skipped", "reason": reason}]).write_csv(paths.evaluation_outputs / "tabular_model_comparison.csv")
    (paths.models_outputs / "tabular_model_registry.json").write_text(json.dumps({"models": [{"status": "skipped", "reason": reason}]}, indent=2), encoding="utf-8")
    return payload


def _hash_frame(df: pl.DataFrame) -> str:
    import hashlib

    return hashlib.sha256(df.write_csv().encode("utf-8")).hexdigest()
