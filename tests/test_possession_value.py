from __future__ import annotations

import polars as pl

from bucephalus.models.possession_value import build_possession_value_samples
from bucephalus.utils.paths import ProjectPaths


def test_possession_value_formula_has_survival_guard(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame({"match_id": [1], "possession": [1], "team_id": [1], "event_id": ["e1"], "event_index": [1], "minute": [1], "second": [1], "actual": [0], "shot_probability": [0.5], "turnover_probability": [0.2], "box_entry_probability": [0.1], "final_third_entry_probability": [0.3]}).write_parquet(paths.evaluation_outputs / "hazard_predictions.parquet")
    pl.DataFrame({"match_id": [1], "possession": [1], "team_id": [1], "event_id": ["shot1"], "event_index": [3], "conditional_xg": [0.25], "model_id": ["xg_logistic_v1"]}).write_parquet(paths.evaluation_outputs / "xg_predictions.parquet")
    payload = build_possession_value_samples(paths)
    out = pl.read_parquet(paths.evaluation_outputs / "epv_predictions.parquet")
    assert payload["survival_bias_guard"] is True
    assert out["xg_source"][0] == "xg_logistic_v1"
    assert out["hazard_source"][0] == "hazard_logistic_next_5_events"
    assert out["conditional_xg"][0] == 0.25
    assert out["expected_possession_value"][0] == out["shot_probability"][0] * out["conditional_xg"][0] - out["counterattack_risk"][0] + out["progression_value"][0]
