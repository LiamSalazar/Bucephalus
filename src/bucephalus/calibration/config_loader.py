from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


@lru_cache(maxsize=8)
def load_engine_config(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {"parameters": {}}
    return yaml.safe_load(file_path.read_text(encoding="utf-8")) or {"parameters": {}}


def parameter_value(config_path: str, name: str, default: Any) -> Any:
    return load_engine_config(config_path).get("parameters", {}).get(name, {}).get("value", default)
