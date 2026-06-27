from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths


def read_json(path: Path) -> list[dict] | dict:
    return json.loads(path.read_text(encoding="utf-8"))


def raw_json_files(kind: str, paths: ProjectPaths | None = None) -> list[Path]:
    paths = paths or settings.paths
    base = paths.raw / kind
    if kind == "competitions":
        return [paths.raw / "competitions.json"] if (paths.raw / "competitions.json").exists() else []
    if not base.exists():
        return []
    return sorted(base.rglob("*.json"))


def iter_json_rows(files: Iterable[Path]) -> Iterable[tuple[Path, list[dict]]]:
    for path in files:
        data = read_json(path)
        if isinstance(data, list):
            yield path, data
