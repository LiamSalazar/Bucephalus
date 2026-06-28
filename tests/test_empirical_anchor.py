from __future__ import annotations

import polars as pl

from bucephalus.simulation.empirical_anchor import build_empirical_anchor
from tests.test_tactical_sliders import _state
from bucephalus.utils.paths import ProjectPaths


def test_empirical_anchor_uses_team_match_features(tmp_path) -> None:
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    home = _state().model_copy(update={"team_id": "h"})
    away = _state().model_copy(update={"team_id": "a"})
    pl.DataFrame({"bucephalus_team_id": ["h", "a"], "xg_for": [1.4, 0.8], "goals_for": [2, 1]}).write_parquet(paths.features / "team_match_features.parquet")
    anchor = build_empirical_anchor(home, away, paths)
    assert anchor["anchor_source"] == "team_match_empirical_means"
    assert anchor["base_home_xg"] == 1.4
