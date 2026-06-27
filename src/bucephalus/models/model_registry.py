from __future__ import annotations

import json
from datetime import UTC, datetime

from bucephalus import __version__


def write_registry(path, models: list[dict]) -> dict:
    payload = {"generated_at": datetime.now(UTC).isoformat(), "version": __version__, "models": models}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
