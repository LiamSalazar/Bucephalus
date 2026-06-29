from __future__ import annotations

import numpy as np
import polars as pl


EVENT_TYPES = {"Pass": 1, "Carry": 2, "Pressure": 3, "Duel": 4, "Shot": 5}


def build_sequence_dataset(events: pl.DataFrame, max_events: int = 12) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    if events.is_empty():
        return np.empty((0, 4)), np.empty((0,)), []
    features = []
    targets = []
    meta = []
    for key, group in events.sort(["match_id", "possession", "event_index"]).group_by(["match_id", "possession"], maintain_order=True):
        rows = group.to_dicts()
        if len(rows) < 2:
            continue
        prefix = rows[:max_events]
        type_mean = np.mean([EVENT_TYPES.get(r.get("type_name"), 0) for r in prefix]) / max(EVENT_TYPES.values())
        x_mean = np.mean([(r.get("location_x") or 60.0) / 120.0 for r in prefix])
        y_mean = np.mean([(r.get("location_y") or 40.0) / 80.0 for r in prefix])
        pressure = np.mean([float(bool(r.get("under_pressure"))) for r in prefix])
        target = float(any(r.get("type_name") == "Shot" for r in rows[max_events:]) or rows[-1].get("type_name") == "Shot")
        features.append([type_mean, x_mean, y_mean, pressure])
        targets.append(target)
        meta.append({"match_id": key[0], "possession": key[1], "events_used": len(prefix)})
    return np.asarray(features, dtype=float), np.asarray(targets, dtype=float), meta


def build_padded_sequence_dataset(events: pl.DataFrame, max_events: int = 12) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    if events.is_empty():
        return np.empty((0, max_events, 8)), np.empty((0,)), np.empty((0, max_events)), []
    sequences, targets, masks, meta = [], [], [], []
    for key, group in events.sort(["match_id", "possession", "event_index"]).group_by(["match_id", "possession"], maintain_order=True):
        rows = group.to_dicts()
        if len(rows) < 2:
            continue
        prefix = rows[:max_events]
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
        target = float(any(r.get("type_name") == "Shot" for r in rows[max_events:]) or rows[-1].get("type_name") == "Shot")
        sequences.append(encoded)
        masks.append(mask)
        targets.append(target)
        meta.append({"match_id": key[0], "possession": key[1], "events_used": min(len(prefix), max_events)})
    return np.asarray(sequences, dtype=np.float32), np.asarray(targets, dtype=np.float32), np.asarray(masks, dtype=np.float32), meta


def _zone(x: float) -> float:
    if x < 40:
        return 0.0
    if x < 80:
        return 0.5
    return 1.0
