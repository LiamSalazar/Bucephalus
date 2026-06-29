from __future__ import annotations

import polars as pl

from bucephalus.deep.sequence_dataset import build_padded_sequence_dataset, build_sequence_dataset


def test_sequence_dataset_builds_without_future_features():
    events = pl.DataFrame(
        [
            {"match_id": 1, "possession": 1, "event_index": 1, "type_name": "Pass", "location_x": 40, "location_y": 30},
            {"match_id": 1, "possession": 1, "event_index": 2, "type_name": "Carry", "location_x": 60, "location_y": 35},
            {"match_id": 1, "possession": 1, "event_index": 3, "type_name": "Shot", "location_x": 100, "location_y": 40},
        ]
    )
    x, y, meta = build_sequence_dataset(events, max_events=2)
    assert x.shape[1] == 4
    assert 1.0 in y.tolist()
    positive = next(row for row in meta if row["shot_in_horizon"] == 1)
    assert positive["feature_cutoff_event_index"] < positive["target_event_index"]
    assert positive["survival_bias_guard"] is True


def test_padded_sequence_prefix_excludes_target_event():
    events = pl.DataFrame(
        [
            {"match_id": 1, "possession": 1, "team_id": 1, "event_id": "e1", "event_index": 1, "type_name": "Pass", "location_x": 40, "location_y": 30},
            {"match_id": 1, "possession": 1, "team_id": 1, "event_id": "e2", "event_index": 2, "type_name": "Carry", "location_x": 60, "location_y": 35},
            {"match_id": 1, "possession": 1, "team_id": 1, "event_id": "e3", "event_index": 3, "type_name": "Shot", "location_x": 100, "location_y": 40},
        ]
    )
    _, y, _, meta = build_padded_sequence_dataset(events, max_events=3)
    positive = next(row for row, target in zip(meta, y, strict=False) if target == 1)
    assert positive["prefix_end_event_id"] != positive["target_event_id"]
    assert positive["feature_cutoff_event_index"] < positive["target_event_index"]
