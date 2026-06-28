from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def build_ingestion_manifest(paths: ProjectPaths) -> dict:
    paths.ensure()
    matches_path = paths.processed / "matches.parquet"
    events_path = paths.processed / "events.parquet"
    if not matches_path.exists():
        return _write_empty(paths, "matches.parquet missing")
    matches = pl.read_parquet(matches_path)
    events = pl.read_parquet(events_path) if events_path.exists() else pl.DataFrame()
    event_counts = {}
    if not events.is_empty() and "match_id" in events.columns:
        event_counts = {
            str(row["match_id"]): int(row["events_count"])
            for row in events.group_by("match_id").agg(pl.len().alias("events_count")).to_dicts()
        }
    rows = []
    now = datetime.now(UTC).isoformat()
    for row in matches.to_dicts():
        provider_match_id = str(row.get("match_id") or row.get("statsbomb_match_id"))
        raw_file = _find_raw_match_file(paths.raw, provider_match_id)
        processed_file = str(matches_path)
        rows.append(
            {
                "provider": "statsbomb",
                "provider_match_id": provider_match_id,
                "bucephalus_match_id": row.get("bucephalus_match_id") or f"statsbomb_match_{provider_match_id}",
                "raw_file_path": str(raw_file) if raw_file else None,
                "processed_file_path": processed_file,
                "checksum": _checksum(raw_file) if raw_file else _checksum(matches_path),
                "last_processed_at": now,
                "processing_status": "processed",
                "events_count": event_counts.get(provider_match_id, 0),
                "warnings": json.dumps([] if raw_file else ["raw per-match file not found; checksum uses matches parquet"]),
            }
        )
    manifest = pl.DataFrame(rows)
    manifest.write_parquet(paths.processed / "ingestion_manifest.parquet")
    payload = {
        "generated_at": now,
        "rows": manifest.height,
        "matches_with_events": sum(1 for row in rows if row["events_count"] > 0),
        "status": "completed",
    }
    return payload


def _find_raw_match_file(raw_dir: Path, match_id: str) -> Path | None:
    candidates = list(raw_dir.rglob(f"{match_id}.json"))
    return candidates[0] if candidates else None


def _checksum(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_empty(paths: ProjectPaths, reason: str) -> dict:
    schema = {
        "provider": pl.Utf8,
        "provider_match_id": pl.Utf8,
        "bucephalus_match_id": pl.Utf8,
        "raw_file_path": pl.Utf8,
        "processed_file_path": pl.Utf8,
        "checksum": pl.Utf8,
        "last_processed_at": pl.Utf8,
        "processing_status": pl.Utf8,
        "events_count": pl.Int64,
        "warnings": pl.Utf8,
    }
    pl.DataFrame(schema=schema).write_parquet(paths.processed / "ingestion_manifest.parquet")
    return {"generated_at": datetime.now(UTC).isoformat(), "status": "skipped", "reason": reason}
