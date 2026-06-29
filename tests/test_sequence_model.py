from __future__ import annotations

import json


def test_sequence_registry_metadata_if_present():
    path = "outputs/models/sequence_model_registry.json"
    try:
        registry = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return
    assert "models" in registry
    assert "training_data_hash" in json.dumps(registry) or "skipped" in json.dumps(registry)


def test_sequence_temporal_split_if_present():
    path = "outputs/evaluation/sequence_temporal_split.json"
    try:
        split = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return
    if split.get("status") == "skipped":
        return
    assert split["no_temporal_overlap"] is True
    assert split["fallback_index_split"] is False
    assert split["train_end_date"] < split["validation_start_date"]
    assert split["validation_end_date"] < split["test_start_date"]
