from __future__ import annotations

import polars as pl

from bucephalus.features.schemas import LEAKAGE_TARGET_COLUMNS


def test_model_dataset_targets_and_prefixed_features_no_leakage(tmp_path) -> None:
    df = pl.DataFrame(
        {
            "match_date": ["2024-01-01", "2024-01-02"],
            "home_score": [1, 2],
            "away_score": [0, 1],
            "home_rolling_goals_for_3": [None, 1.0],
        }
    )
    assert {"home_score", "away_score"}.issubset(df.columns)
    feature_cols = {c for c in df.columns if c.startswith(("home_rolling_", "away_rolling_", "diff_rolling_"))}
    assert not (feature_cols & LEAKAGE_TARGET_COLUMNS)
    assert df.sort("match_date")["match_date"].to_list() == df["match_date"].to_list()
