from __future__ import annotations

import polars as pl

from bucephalus.models.team_strength import build_team_strength_timeseries
from bucephalus.utils.paths import ProjectPaths


def test_team_strength_updates_forward_only(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame(
        [
            {"bucephalus_team_id": "t1", "team_name": "A", "match_date": "2024-01-01", "goals_for": 1, "goals_against": 0, "xg_for": 1.0, "xg_against": 0.5},
            {"bucephalus_team_id": "t1", "team_name": "A", "match_date": "2024-01-02", "goals_for": 3, "goals_against": 1, "xg_for": 2.0, "xg_against": 0.8},
        ]
    ).write_parquet(paths.features / "team_match_features.parquet")
    build_team_strength_timeseries(paths)
    out = pl.read_parquet(paths.features / "team_strength_timeseries.parquet").sort("match_date")
    assert out["matches_observed_before"].to_list() == [0, 1]
    assert out["pre_match_attack_uncertainty"].to_list()[1] < out["pre_match_attack_uncertainty"].to_list()[0]
