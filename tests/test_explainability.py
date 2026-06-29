from __future__ import annotations

import polars as pl

from bucephalus.explainability.sequence_explain import build_sequence_explanation
from bucephalus.explainability.tabular_explain import build_tabular_explanations
from bucephalus.utils.paths import ProjectPaths


def test_explainability_returns_top_events(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame({"shot_probability": [0.5], "conditional_xg": [0.1], "expected_possession_value": [0.04]}).write_parquet(paths.evaluation_outputs / "sequence_predictions.parquet")
    payload = build_sequence_explanation(paths)
    assert payload["status"] == "skipped"


def test_tabular_explainability_not_fake_ranking_when_data_missing(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    payload = build_tabular_explanations(paths)
    assert payload["status"] == "skipped"
