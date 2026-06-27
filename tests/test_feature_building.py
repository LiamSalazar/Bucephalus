from __future__ import annotations

import polars as pl

from bucephalus.features.build_basic_features import build_player_match_basic, build_team_profiles


def test_build_team_profiles_from_events() -> None:
    events = pl.DataFrame(
        {
            "match_id": [1, 1, 1],
            "team_id": [10, 10, 10],
            "team_name": ["A", "A", "A"],
            "event_type": ["Pass", "Shot", "Pressure"],
            "shot_xg": [None, 0.2, None],
            "shot_type": [None, "Open Play", None],
            "location_x": [30.0, 100.0, 60.0],
            "location_y": [20.0, 40.0, 70.0],
            "pass_end_x": [50.0, None, None],
        }
    )
    profiles = build_team_profiles(events)
    assert profiles["matches_count"][0] == 1
    assert profiles["avg_shots"][0] == 1
    assert profiles["avg_pressures"][0] == 1


def test_build_player_match_basic() -> None:
    events = pl.DataFrame(
        {
            "match_id": [1, 1],
            "team_id": [10, 10],
            "team_name": ["A", "A"],
            "player_id": [7, 7],
            "player_name": ["P", "P"],
            "position_name": ["Forward", "Forward"],
            "event_type": ["Shot", "Pass"],
            "shot_xg": [0.4, None],
        }
    )
    features = build_player_match_basic(events)
    assert features["events"][0] == 2
    assert features["shots"][0] == 1
