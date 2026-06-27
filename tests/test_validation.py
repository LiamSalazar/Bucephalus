from __future__ import annotations

import pytest
import polars as pl

from bucephalus.data.validation import validate_data_quality
from bucephalus.utils.paths import ProjectPaths


def test_validation_detects_missing_critical_columns(tmp_path) -> None:
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    pl.DataFrame({"competition_id": [1]}).write_parquet(paths.processed / "competitions.parquet")
    with pytest.raises(ValueError):
        validate_data_quality(paths)
    assert (paths.quality_outputs / "data_quality_summary.json").exists()
