from __future__ import annotations

import json


def test_phase8_metadata_has_training_hash_if_registry_exists():
    for path in ["outputs/models/tabular_model_registry.json", "outputs/models/hazard_model_registry.json", "outputs/models/sequence_model_registry.json"]:
        try:
            payload = json.load(open(path, encoding="utf-8"))
        except FileNotFoundError:
            continue
        assert "training_data_hash" in json.dumps(payload) or "skipped" in json.dumps(payload)
