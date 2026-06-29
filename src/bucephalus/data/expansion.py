from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from bucephalus.data.provider_adapters import (
    APIFootballAdapter,
    FootballDataAdapter,
    ManualCSVAdapter,
    SportmonksAdapter,
    StatsBombOpenAdapter,
)
from bucephalus.utils.paths import ProjectPaths


TARGETS = {
    "shots": 5_000,
    "events": 300_000,
    "pass_network_graphs": 500,
    "matches": 300,
}


def write_data_expansion_report(paths: ProjectPaths | None = None) -> dict:
    paths = paths or ProjectPaths()
    paths.ensure()
    counts = {
        "matches": _count(paths.processed / "matches.parquet"),
        "events": _count(paths.processed / "events.parquet"),
        "shots": _count(paths.processed / "shots.parquet"),
        "passes": _count(paths.processed / "passes.parquet"),
        "pressures": _count(paths.processed / "pressures.parquet"),
        "teams": _count(paths.processed / "teams.parquet"),
        "players": _count(paths.processed / "players.parquet"),
        "pass_network_graphs": _count(paths.features / "pass_network_graphs.parquet"),
        "competitions": _count(paths.processed / "competitions.parquet"),
        "three_sixty": _count(paths.processed / "three_sixty.parquet"),
    }
    adapters = [
        StatsBombOpenAdapter(paths),
        ManualCSVAdapter(paths=paths),
        APIFootballAdapter(),
        SportmonksAdapter(),
        FootballDataAdapter(),
    ]
    adapter_status = []
    for adapter in adapters:
        fixtures = adapter.fetch_fixtures()
        adapter_status.append(
            {
                "provider": adapter.provider_name,
                "fixtures_status": fixtures.status,
                "fixtures_rows": len(fixtures.rows),
                "warnings": fixtures.warnings,
            }
        )
    distance = {
        key: {
            "current": counts.get(key, 0),
            "target": target,
            "remaining": max(0, target - int(counts.get(key) or 0)),
            "target_met": int(counts.get(key) or 0) >= target,
        }
        for key, target in TARGETS.items()
    }
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "completed",
        "dataset_source": "StatsBomb Open Data + optional adapters",
        "counts": counts,
        "targets": distance,
        "provider_status": adapter_status,
        "coverage_360": bool((counts.get("three_sixty") or 0) > 0),
        "limitations": _limitations(distance, adapter_status),
    }
    paths.quality_outputs.mkdir(parents=True, exist_ok=True)
    (paths.quality_outputs / "data_expansion_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (paths.quality_outputs / "data_expansion_report.md").write_text(_markdown(payload), encoding="utf-8")
    _write_research_summary(paths, payload)
    return payload


def _count(path: Path) -> int:
    return pl.read_parquet(path).height if path.exists() else 0


def _limitations(distance: dict, adapter_status: list[dict]) -> list[str]:
    rows = []
    for key, value in distance.items():
        if not value["target_met"]:
            rows.append(f"{key} below recommended target: {value['current']}/{value['target']}")
    for adapter in adapter_status:
        if adapter["fixtures_status"] == "provider_unavailable":
            rows.extend(adapter["warnings"])
    return rows


def _markdown(payload: dict) -> str:
    lines = [
        "# Data Expansion Report",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        "## Counts",
    ]
    for key, value in payload["counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Target Distance"])
    for key, value in payload["targets"].items():
        lines.append(f"- {key}: {value['current']}/{value['target']} target_met={value['target_met']}")
    lines.extend(["", "## Providers"])
    for adapter in payload["provider_status"]:
        lines.append(f"- {adapter['provider']}: {adapter['fixtures_status']} rows={adapter['fixtures_rows']}")
    lines.extend(["", "## Limitations"])
    lines.extend(f"- {item}" for item in payload["limitations"])
    return "\n".join(lines) + "\n"


def _write_research_summary(paths: ProjectPaths, payload: dict) -> None:
    summary = {
        "generated_at": payload["generated_at"],
        "matches": payload["counts"]["matches"],
        "events": payload["counts"]["events"],
        "players": payload["counts"]["players"],
        "teams": payload["counts"]["teams"],
        "shots": payload["counts"]["shots"],
        "passes": payload["counts"]["passes"],
        "pressures": payload["counts"]["pressures"],
        "pass_network_graphs": payload["counts"]["pass_network_graphs"],
        "source": payload["dataset_source"],
        "limitations": payload["limitations"],
    }
    (paths.quality_outputs / "research_dataset_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
