from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    paths.ensure()
    counts = {}
    for name, path in {"matches": paths.processed / "matches.parquet", "events": paths.processed / "events.parquet", "shots": paths.processed / "shots.parquet"}.items():
        counts[name] = pl.read_parquet(path).height if path.exists() else 0
    scorecard_path = paths.evaluation_outputs / "phase8_model_scorecard.json"
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8")) if scorecard_path.exists() else {"rows": []}
    report = paths.outputs / "reports" / "phase8_results_summary.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# Phase 8 Results Summary\n\n"
        f"Dataset: {counts['matches']} matches, {counts['events']} events, {counts['shots']} shots.\n\n"
        "Models trained: xG v2 tabular, hazard, EPV, PyTorch GRU sequence, pass network GCN, MC Dropout, vectorized Monte Carlo.\n\n"
        "Scorecard:\n"
        + "\n".join(f"- {r['component']}: {r['status']} ({r['primary_metric']}={r['advanced_score']})" for r in scorecard.get("rows", []))
        + "\n\nLimitations: small research dataset, pass receiver uses next-event proxy, no tracking-speed data, GNN remains experimental unless it improves baseline.\n\n"
        "Recommendation for Phase 9: integrate these artifacts into Lab/Game Mode as calibrated candidates, not final champions.\n",
        encoding="utf-8",
    )
    print({"report": str(report), "counts": counts})


if __name__ == "__main__":
    main()
