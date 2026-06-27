from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from bucephalus import __version__
from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths


def write_download_metadata(
    paths: ProjectPaths,
    mode: str,
    competitions: list[int] | None,
    seasons: list[int] | None,
    max_matches: int,
    actual_matches_downloaded: int,
    skip_360: bool,
    warnings: list[str] | None = None,
) -> None:
    paths.ensure()
    payload = {
        "generated_at": _now(),
        "source_name": "StatsBomb Open Data",
        "source_url": settings.statsbomb_base_url,
        "mode": mode,
        "competitions": competitions or [],
        "seasons": seasons or [],
        "max_matches": max_matches,
        "actual_matches_downloaded": actual_matches_downloaded,
        "skip_360": skip_360,
        "warnings": warnings or [],
    }
    (paths.raw / "_download_metadata.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_data_manifest(paths: ProjectPaths | None = None, errors: list[str] | None = None) -> dict[str, Any]:
    paths = paths or settings.paths
    paths.ensure()
    metadata = _read_json(paths.raw / "_download_metadata.json")
    processed_tables = sorted(path.stem for path in paths.processed.glob("*.parquet"))
    rows_by_table = {}
    for table in processed_tables:
        rows_by_table[table] = pl.scan_parquet(paths.processed / f"{table}.parquet").select(pl.len()).collect().item()
    raw_files = sorted(path for path in paths.raw.rglob("*") if path.is_file())
    manifest = {
        "generated_at": _now(),
        "source_name": metadata.get("source_name", "StatsBomb Open Data"),
        "source_url": metadata.get("source_url", settings.statsbomb_base_url),
        "mode": metadata.get("mode", "unknown"),
        "competitions": metadata.get("competitions", []),
        "seasons": metadata.get("seasons", []),
        "max_matches": metadata.get("max_matches"),
        "actual_matches_downloaded": metadata.get("actual_matches_downloaded"),
        "has_events": (paths.raw / "events").exists() and any((paths.raw / "events").glob("*.json")),
        "has_lineups": (paths.raw / "lineups").exists() and any((paths.raw / "lineups").glob("*.json")),
        "has_360": (paths.raw / "three-sixty").exists() and any((paths.raw / "three-sixty").glob("*.json")),
        "raw_files_count": len(raw_files),
        "processed_tables": processed_tables,
        "rows_by_table": rows_by_table,
        "pipeline_version": __version__,
        "git_commit": _git_commit(paths.root),
        "warnings": metadata.get("warnings", []),
        "errors": errors or [],
        "checksums": {_relative_path(path, paths): _sha256(path) for path in raw_files[:200]},
    }
    json_path = paths.processed / "data_manifest.json"
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    pl.DataFrame([_json_safe(manifest)]).write_parquet(paths.processed / "data_manifest.parquet")
    return manifest


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(path: Path, paths: ProjectPaths) -> str:
    for base in [paths.root, paths.data]:
        try:
            return str(path.relative_to(base))
        except ValueError:
            continue
    return str(path)


def _json_safe(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value
        for key, value in payload.items()
    }
