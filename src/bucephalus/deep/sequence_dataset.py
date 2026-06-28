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
