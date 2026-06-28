from __future__ import annotations

import polars as pl

from bucephalus.features.incremental_store import update_incremental_feature_store
from bucephalus.utils.paths import ProjectPaths


def test_incremental_update_no_changes_does_not_recompute_all(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame({"provider_match_id": ["1"], "checksum": ["abc"]}).write_parquet(paths.processed / "ingestion_manifest.parquet")
    pl.DataFrame({"statsbomb_match_id": [1], "bucephalus_team_id": ["t1"]}).write_parquet(paths.features / "team_match_features.parquet")
    payload = update_incremental_feature_store(paths)
    assert payload["new_matches_count"] == 0
    assert payload["recomputed_full"] is False
    assert payload["preserved_versions"]
