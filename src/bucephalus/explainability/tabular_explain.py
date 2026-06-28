from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def build_tabular_explanations(paths: ProjectPaths) -> dict:
    metrics_path = paths.evaluation_outputs / "xg_metrics.json"
    if not metrics_path.exists():
        return _write_skipped(paths, "xG metrics missing")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    features = metrics.get("features", [])
    rows = [
        {"feature": feature, "importance": float(1 / (idx + 1)), "method": "ranked_proxy_permutation_fallback"}
        for idx, feature in enumerate(features)
    ]
    out_dir = paths.outputs / "explainability"
    out_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows or [{"feature": "none", "importance": 0.0, "method": "skipped"}]).write_csv(out_dir / "tabular_feature_importance.csv")
    sample = {
        "generated_at": datetime.now(UTC).isoformat(),
        "model": "xg_v1_logistic",
        "top_features": rows[:5],
        "warning": "Permutation/SHAP not run; fallback ranks available model features.",
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
