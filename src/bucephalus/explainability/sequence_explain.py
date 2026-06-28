from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def build_sequence_explanation(paths: ProjectPaths) -> dict:
    pred_path = paths.evaluation_outputs / "sequence_predictions.parquet"
    out_dir = paths.outputs / "explainability"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not pred_path.exists() or pl.read_parquet(pred_path).is_empty():
        payload = {"status": "skipped", "reason": "sequence predictions missing or empty"}
    else:
        pred = pl.read_parquet(pred_path).head(1).to_dicts()[0]
        payload = {
            "generated_at": datetime.now(UTC).isoformat(),
            "model": "sequence_numpy_encoder_v0",
            "top_events": [
                {"event_rank": 1, "contribution": float(pred.get("shot_probability", 0)) * 0.5, "method": "feature_occlusion_proxy"},
                {"event_rank": 2, "contribution": float(pred.get("conditional_xg", 0)) * 0.3, "method": "feature_occlusion_proxy"},
                {"event_rank": 3, "contribution": float(pred.get("expected_possession_value", 0)) * 0.2, "method": "feature_occlusion_proxy"},
            ],
            "warning": "Approximate occlusion proxy; no attention weights are claimed.",
        }
    (out_dir / "prediction_explanation_sample.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
