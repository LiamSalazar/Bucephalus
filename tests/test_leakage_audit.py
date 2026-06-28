from __future__ import annotations

import polars as pl

from bucephalus.utils.paths import ProjectPaths
from bucephalus.validation.leakage_audit import run_leakage_audit


def test_leakage_audit_detects_target_suffix_in_rolling_feature(tmp_path) -> None:
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame(
        {
            "statsbomb_match_id": [1, 2, 3],
            "match_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "home_score": [1, 2, 0],
            "away_score": [0, 1, 1],
            "home_rolling_home_score": [None, 1, 2],
        }
    ).write_parquet(paths.features / "model_dataset_matches.parquet")
    pl.DataFrame({"statsbomb_match_id": [1], "bucephalus_team_id": ["a"], "historical_matches_available": [0]}).write_parquet(paths.features / "team_rolling_features.parquet")
    result = run_leakage_audit(paths)
    assert not result["passed"]
    assert "home_rolling_home_score" in result["forbidden_columns_detected"]
