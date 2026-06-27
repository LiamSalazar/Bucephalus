from __future__ import annotations

import csv
import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths

MINIMUMS = {"matches": 100, "events": 250_000, "shots": 2_000, "passes": 60_000}
TABLES = [
    "matches",
    "events",
    "players",
    "teams",
    "shots",
    "passes",
    "carries",
    "pressures",
    "duels",
    "goalkeeper_actions",
    "three_sixty",
]


def write_research_dataset_summary(paths: ProjectPaths | None = None) -> dict:
    paths = paths or settings.paths
    paths.ensure()
    counts = {}
    for table in TABLES:
        path = paths.processed / f"{table}.parquet"
        counts[table] = int(pl.scan_parquet(path).select(pl.len()).collect().item()) if path.exists() else 0
    warnings = [
        f"{table} below target: {counts.get(table, 0)} < {minimum}"
        for table, minimum in MINIMUMS.items()
        if counts.get(table, 0) < minimum
    ]
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "counts": counts,
        "minimum_targets": MINIMUMS,
        "targets_met": not warnings,
        "warnings": warnings,
    }
    json_path = paths.quality_outputs / "research_dataset_summary.json"
    csv_path = paths.quality_outputs / "research_dataset_summary.csv"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["table", "rows"])
        writer.writeheader()
        for table, rows in counts.items():
            writer.writerow({"table": table, "rows": rows})
    return summary
