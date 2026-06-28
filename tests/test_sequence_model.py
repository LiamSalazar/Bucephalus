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
