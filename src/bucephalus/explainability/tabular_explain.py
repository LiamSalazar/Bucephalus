from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.preprocessing import StandardScaler

from bucephalus.models.xg_features import build_xg_training_frame, feature_columns

from bucephalus.utils.paths import ProjectPaths


def build_tabular_explanations(paths: ProjectPaths) -> dict:
    shots_path = paths.processed / "shots.parquet"
    if not shots_path.exists():
        return _write_skipped(paths, "shots.parquet missing")
    rows = _permutation_importance(pl.read_parquet(shots_path))
    out_dir = paths.outputs / "explainability"
    out_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows or [{"feature": "none", "importance": 0.0, "method": "skipped"}]).write_csv(out_dir / "tabular_feature_importance.csv")
    sample = {
        "generated_at": datetime.now(UTC).isoformat(),
        "model": "xg_v1_logistic",
        "top_features": rows[:5],
        "warning": "Permutation importance computed on local logistic xG refit; SHAP not required.",
    }
    (out_dir / "xg_explanation_sample.json").write_text(json.dumps(sample, indent=2), encoding="utf-8")
    return sample


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    out_dir = paths.outputs / "explainability"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"status": "skipped", "reason": reason}
    (out_dir / "xg_explanation_sample.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pl.DataFrame([{"feature": "none", "importance": 0.0, "method": "skipped"}]).write_csv(out_dir / "tabular_feature_importance.csv")
    return payload


def _permutation_importance(shots: pl.DataFrame) -> list[dict]:
    df = build_xg_training_frame(shots).drop_nulls(["is_goal"])
    if df.height < 50 or df["is_goal"].n_unique() < 2:
        return [{"feature": "insufficient_data", "importance": 0.0, "method": "permutation_importance_skipped"}]
    features = feature_columns(df)
    split = int(df.height * 0.75)
    x = df.select(features).fill_null(0).to_numpy()
    y = np.asarray(df["is_goal"].to_list())
    scaler = StandardScaler()
    x_train = scaler.fit_transform(x[:split])
    x_test = scaler.transform(x[split:])
    model = LogisticRegression(max_iter=300)
    model.fit(x_train, y[:split])
    base_prob = model.predict_proba(x_test)[:, 1]
    base_loss = log_loss(y[split:], base_prob, labels=[0, 1])
    rng = np.random.default_rng(42)
    rows = []
    for idx, feature in enumerate(features):
        x_perm = x_test.copy()
        x_perm[:, idx] = rng.permutation(x_perm[:, idx])
        perm_loss = log_loss(y[split:], model.predict_proba(x_perm)[:, 1], labels=[0, 1])
        rows.append({"feature": feature, "importance": float(max(0.0, perm_loss - base_loss)), "method": "permutation_importance"})
    return sorted(rows, key=lambda row: row["importance"], reverse=True)
