from __future__ import annotations

import numpy as np
import polars as pl


EVENT_TYPES = {"Pass": 1, "Carry": 2, "Pressure": 3, "Duel": 4, "Shot": 5}
TARGET_TYPES = {
    "shot_in_horizon": lambda row: row.get("type_name") == "Shot",
    "turnover_in_horizon": lambda row: row.get("type_name") in {"Interception", "Duel"},
    "box_entry_in_horizon": lambda row: (row.get("location_x") or 0) >= 102,
    "final_third_entry_in_horizon": lambda row: (row.get("location_x") or 0) >= 80,
}


def build_sequence_dataset(events: pl.DataFrame, max_events: int = 12) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    if events.is_empty():
        return np.empty((0, 4)), np.empty((0,)), []
    features = []
    targets = []
    meta = []
    for _, rows, prefix_end, future in _iter_prefix_examples(events, horizon_events=5):
        prefix = rows[max(0, prefix_end - max_events + 1) : prefix_end + 1]
        type_mean = np.mean([EVENT_TYPES.get(r.get("type_name"), 0) for r in prefix]) / max(EVENT_TYPES.values())
        x_mean = np.mean([(r.get("location_x") or 60.0) / 120.0 for r in prefix])
        y_mean = np.mean([(r.get("location_y") or 40.0) / 80.0 for r in prefix])
        pressure = np.mean([float(bool(r.get("under_pressure"))) for r in prefix])
        target = float(any(r.get("type_name") == "Shot" for r in future))
        features.append([type_mean, x_mean, y_mean, pressure])
        targets.append(target)
        meta.append(_prefix_meta(rows, prefix_end, future, len(prefix)))
    return np.asarray(features, dtype=float), np.asarray(targets, dtype=float), meta


def build_padded_sequence_dataset(events: pl.DataFrame, max_events: int = 12) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    if events.is_empty():
        return np.empty((0, max_events, 8)), np.empty((0,)), np.empty((0, max_events)), []
    sequences, targets, masks, meta = [], [], [], []
    for _, rows, prefix_end, future in _iter_prefix_examples(events, horizon_events=5):
        prefix = rows[max(0, prefix_end - max_events + 1) : prefix_end + 1]
        encoded = []
        prev_x = prev_y = None
        prev_time = None
        for row in prefix:
            x = float(row.get("location_x") or 60.0)
            y = float(row.get("location_y") or 40.0)
            t = float(row.get("minute") or 0) * 60 + float(row.get("second") or 0)
            encoded.append(
                [
                    EVENT_TYPES.get(row.get("type_name"), 0) / max(EVENT_TYPES.values()),
                    x / 120.0,
                    y / 80.0,
                    0.0 if prev_x is None else (x - prev_x) / 120.0,
                    0.0 if prev_y is None else (y - prev_y) / 80.0,
                    0.0 if prev_time is None else min(30.0, max(0.0, t - prev_time)) / 30.0,
                    float(bool(row.get("under_pressure"))),
                    _zone(x),
                ]
            )
            prev_x, prev_y, prev_time = x, y, t
        mask = [1.0] * len(encoded)
        while len(encoded) < max_events:
            encoded.append([0.0] * 8)
            mask.append(0.0)
        target = float(any(r.get("type_name") == "Shot" for r in future))
        sequences.append(encoded)
        masks.append(mask)
        targets.append(target)
        meta.append(_prefix_meta(rows, prefix_end, future, min(len(prefix), max_events)))
    return np.asarray(sequences, dtype=np.float32), np.asarray(targets, dtype=np.float32), np.asarray(masks, dtype=np.float32), meta


def _zone(x: float) -> float:
    if x < 40:
        return 0.0
    if x < 80:
        return 0.5
    return 1.0


def _iter_prefix_examples(events: pl.DataFrame, horizon_events: int):
    sort_cols = [c for c in ["match_id", "possession", "event_index"] if c in events.columns]
    for key, group in events.sort(sort_cols).group_by(["match_id", "possession"], maintain_order=True):
        rows = group.to_dicts()
        if len(rows) < 2:
            continue
        # One example per prefix. The current event is included as context; target events
        # are strictly after the cutoff, preventing the shot itself from entering features.
        for prefix_end in range(len(rows) - 1):
            future = rows[prefix_end + 1 : prefix_end + 1 + horizon_events]
            if future:
                yield key, rows, prefix_end, future


def _prefix_meta(rows: list[dict], prefix_end: int, future: list[dict], sequence_length: int) -> dict:
    cutoff = rows[prefix_end]
    target = next((row for row in future if row.get("type_name") == "Shot"), None)
    cutoff_time = float(cutoff.get("minute") or 0) * 60 + float(cutoff.get("second") or 0)
    target_index = target.get("event_index") if target else None
    return {
        "match_id": cutoff.get("match_id"),
        "possession": cutoff.get("possession"),
        "team_id": cutoff.get("team_id"),
        "event_index": cutoff.get("event_index"),
        "prefix_end_event_id": cutoff.get("event_id"),
        "target_event_id": target.get("event_id") if target else None,
        "target_event_index": target_index,
        "target_type": "shot_in_horizon",
        "target_horizon": len(future),
        "target_horizon_mode": "event_horizon_proxy",
        "target_match_date": cutoff.get("match_date"),
        "feature_cutoff_event_index": cutoff.get("event_index"),
        "feature_cutoff_time": cutoff_time,
        "sequence_length": sequence_length,
        "events_used": sequence_length,
        "shot_in_horizon": int(any(TARGET_TYPES["shot_in_horizon"](row) for row in future)),
        "turnover_in_horizon": int(any(TARGET_TYPES["turnover_in_horizon"](row) and row.get("team_id") != cutoff.get("team_id") for row in future)),
        "box_entry_in_horizon": int(any(TARGET_TYPES["box_entry_in_horizon"](row) for row in future)),
        "final_third_entry_in_horizon": int(any(TARGET_TYPES["final_third_entry_in_horizon"](row) for row in future)),
        "survival_bias_guard": True,
    }
