from __future__ import annotations

import polars as pl

from bucephalus.models.hazard_model import build_hazard_frame


def test_hazard_frame_uses_forward_horizon_only():
    events = pl.DataFrame(
        [
            {"match_id": 1, "possession": 1, "event_index": 1, "type_name": "Pass", "location_x": 50, "location_y": 40},
            {"match_id": 1, "possession": 1, "event_index": 2, "type_name": "Carry", "location_x": 70, "location_y": 40},
            {"match_id": 1, "possession": 1, "event_index": 3, "type_name": "Shot", "location_x": 100, "location_y": 40},
        ]
    )
    frame = build_hazard_frame(events, horizon_events=1)
    assert frame["shot_in_next_5_events"].to_list() == [0, 1]
    assert {"match_id", "possession", "team_id", "event_id", "event_index", "minute", "second"} & set(frame.columns)
