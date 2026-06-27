from __future__ import annotations

import polars as pl

from bucephalus.data.download_statsbomb import download_sample
from bucephalus.data.entity_resolution import build_master_entities
from bucephalus.data.process_statsbomb import process_raw_to_parquet
from bucephalus.features.feature_store import build_feature_store
from bucephalus.utils.paths import ProjectPaths


def test_feature_store_builds_minimum_tables_and_prior_rolling(tmp_path) -> None:
    paths = ProjectPaths(data_root=tmp_path / "data")
    download_sample(paths=paths, max_matches=2, force_fallback=True)
    process_raw_to_parquet(paths)
    build_master_entities(paths)
    build_feature_store(paths)
    team = pl.read_parquet(paths.features / "team_match_features.parquet")
    rolling = pl.read_parquet(paths.features / "team_rolling_features.parquet")
    assert {"goals_for", "shots_for", "possession_proxy"}.issubset(team.columns)
    assert "rolling_goals_for_3" in rolling.columns
    assert rolling.sort(["bucephalus_team_id", "statsbomb_match_id"])["historical_matches_available"].min() == 0
    assert (paths.features / "feature_manifest.json").exists()
