from __future__ import annotations

import polars as pl

from bucephalus.models.possession_value import build_possession_value_samples
from bucephalus.utils.paths import ProjectPaths


def test_possession_value_formula_has_survival_guard(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame({"actual": [0], "shot_probability": [0.5]}).write_parquet(paths.evaluation_outputs / "hazard_predictions.parquet")
    pl.DataFrame({"actual_goal": [0], "predicted_xg": [0.2]}).write_parquet(paths.evaluation_outputs / "xg_predictions.parquet")
    payload = build_possession_value_samples(paths)
    out = pl.read_parquet(paths.evaluation_outputs / "possession_value_samples.parquet")
    assert payload["survival_bias_guard"] is True
    assert out["expected_possession_value"][0] == out["shot_value"][0] - out["counterattack_risk"][0] + 0.01
