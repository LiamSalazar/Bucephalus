from __future__ import annotations

import json
import subprocess
import sys


def test_model_registry_contains_hashes_after_script():
    result = subprocess.run([sys.executable, "scripts/24_build_model_registry.py"], check=True, capture_output=True, text=True)
    assert result.returncode == 0
    registry = json.load(open("outputs/models/model_registry.json", encoding="utf-8"))
    assert registry["rows"] >= 1
    assert all("training_data_hash" in model for model in registry["models"])
