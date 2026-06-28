from __future__ import annotations

import polars as pl

from bucephalus.models.xg_features import build_xg_training_frame


def test_xg_features_distance_and_angle_are_valid() -> None:
    shots = pl.DataFrame(
        {
            "shot_outcome": ["Goal"],
            "location_x": [108.0],
            "location_y": [40.0],
            "under_pressure": [False],
            "shot_type": ["Open Play"],
            "play_pattern_name": ["Regular Play"],
        }
    )
    df = build_xg_training_frame(shots)
    assert df["distance_to_goal"][0] == 12.0
    assert df["angle_to_goal"][0] > 0
    assert df["is_goal"][0] == 1
