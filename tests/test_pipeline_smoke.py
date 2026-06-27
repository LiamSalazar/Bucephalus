from __future__ import annotations

from bucephalus.data.download_statsbomb import download_sample
from bucephalus.data.duckdb_catalog import build_duckdb_catalog, list_catalog_views
from bucephalus.data.entity_resolution import build_master_entities
from bucephalus.data.process_statsbomb import process_raw_to_parquet
from bucephalus.data.validation import validate_data_quality
from bucephalus.eda.distributions import run_eda
from bucephalus.features.build_basic_features import build_basic_features
from bucephalus.utils.paths import ProjectPaths


def test_pipeline_smoke_with_fallback(tmp_path) -> None:
    paths = ProjectPaths(data_root=tmp_path / "data")
    download_sample(paths=paths, max_matches=2, force_fallback=True)
    process_raw_to_parquet(paths)
    validate_data_quality(paths)
    build_master_entities(paths)
    build_basic_features(paths)
    run_eda(paths)
    build_duckdb_catalog(paths)
    assert (paths.processed / "data_manifest.json").exists()
    assert (paths.quality_outputs / "data_quality_summary.json").exists()
    assert (paths.processed / "external_entity_links.parquet").exists()
    assert (paths.features / "team_profiles_baseline.parquet").exists()
    assert (paths.eda_tables / "fat_tail_summary.parquet").exists()
    assert "events" in list_catalog_views(paths)
