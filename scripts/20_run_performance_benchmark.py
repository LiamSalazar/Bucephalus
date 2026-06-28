from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from bucephalus.calibration.bootstrap import bootstrap_tactical_parameters
from bucephalus.models.team_strength import build_team_strength_timeseries
from bucephalus.simulation.markov_calibration import calibrate_markov_matrix
from bucephalus.simulation.simulation_validation import validate_simulation_backtest
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    paths.ensure()
    timings = []
    for name, fn in [
        ("markov_calibration", lambda: calibrate_markov_matrix(paths)),
        ("team_strength", lambda: build_team_strength_timeseries(paths)),
        ("bootstrap_tactical", lambda: bootstrap_tactical_parameters(paths, n_bootstraps=30)),
        ("simulation_backtest", lambda: validate_simulation_backtest(paths, n_simulations=40)),
    ]:
        start = time.perf_counter()
        fn()
        timings.append({"step": name, "seconds": round(time.perf_counter() - start, 4)})
    row_counts = {}
    for table in ["events", "team_match_features", "model_dataset_matches"]:
        candidate = paths.processed / f"{table}.parquet"
        if not candidate.exists():
            candidate = paths.features / f"{table}.parquet"
        if candidate.exists():
            row_counts[table] = pl.scan_parquet(candidate).select(pl.len()).collect().item()
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "timings": timings,
        "row_counts": row_counts,
        "memory_note": "memory is not sampled in this lightweight benchmark",
    }
    (paths.quality_outputs / "performance_benchmark.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
