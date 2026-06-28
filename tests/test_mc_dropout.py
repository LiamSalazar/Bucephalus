from __future__ import annotations

import json

import polars as pl

from bucephalus.deep.inference import run_mc_dropout
from bucephalus.utils.paths import ProjectPaths


def test_mc_dropout_produces_variance(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    (paths.models_outputs / "sequence_model_artifact.json").write_text(json.dumps({"weights": [1, 1, 1, 1], "bias": 0.0}), encoding="utf-8")
    pl.DataFrame({"shot_probability": [0.2, 0.8], "conditional_xg": [0.1, 0.2], "expected_possession_value": [0.01, 0.1]}).write_parquet(paths.evaluation_outputs / "sequence_predictions.parquet")
    payload = run_mc_dropout(paths, n_mc_samples=10)
    assert payload["status"] == "completed"
    assert payload["mean_epistemic_uncertainty"] > 0
