from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from bucephalus.calibration.config_loader import load_engine_config
from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths

CONFIGS = ["configs/tactical_engine_v0.yaml", "configs/simulation_engine_v0.yaml"]


def build_parameter_registry(paths: ProjectPaths | None = None) -> dict[str, Any]:
    paths = paths or settings.paths
    paths.ensure()
    parameters = []
    warnings = []
    for config_path in CONFIGS:
        cfg = load_engine_config(config_path)
        for name, meta in cfg.get("parameters", {}).items():
            row = {"name": name, "config": config_path, **meta}
            parameters.append(row)
            if meta.get("source") == "heuristic_fallback":
                warnings.append(f"{name} remains heuristic_fallback")
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "parameters_count": len(parameters),
        "parameters": parameters,
        "warnings": warnings,
    }
    output = paths.calibration_outputs / "parameter_registry.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def get_parameter(name: str, default: Any, config: str | None = None) -> Any:
    configs = [config] if config else CONFIGS
    for config_path in configs:
        if config_path is None:
            continue
        value = load_engine_config(config_path).get("parameters", {}).get(name, {}).get("value")
        if value is not None:
            return value
    return default
