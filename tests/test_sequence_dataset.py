from __future__ import annotations

import polars as pl

from bucephalus.deep.sequence_dataset import build_sequence_dataset


def test_sequence_dataset_builds_without_future_features():
    events = pl.DataFrame(
        [
            {"match_id": 1, "possession": 1, "event_index": 1, "type_name": "Pass", "location_x": 40, "location_y": 30},
            {"match_id": 1, "possession": 1, "event_index": 2, "type_name": "Carry", "location_x": 60, "location_y": 35},
            {"match_id": 1, "possession": 1, "event_index": 3, "type_name": "Shot", "location_x": 100, "location_y": 40},
        ]
    )
    x, y, meta = build_sequence_dataset(events, max_events=2)
    assert x.shape == (1, 4)
    assert y.tolist() == [1.0]
    assert meta[0]["events_used"] == 2
