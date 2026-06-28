from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import polars as pl

from bucephalus.simulation.simulator import simulate_match
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    paths.ensure()
    failures = []
    required = [
        paths.quality_outputs / "pre_phase_8_gap_audit.json",
        paths.calibration_outputs / "parameter_registry.json",
        paths.evaluation_outputs / "leakage_audit.json",
        paths.evaluation_outputs / "xg_metrics.json",
        paths.features / "markov_transition_matrix_global.parquet",
        paths.features / "markov_transition_counts.parquet",
        paths.evaluation_outputs / "simulation_backtest_metrics.json",
        paths.evaluation_outputs / "simulation_backtest_predictions.parquet",
        paths.evaluation_outputs / "ablation_study.csv",
        paths.calibration_outputs / "tactical_parameter_uncertainty.json",
        paths.features / "team_strength_timeseries.parquet",
        paths.processed / "ingestion_manifest.parquet",
        paths.quality_outputs / "incremental_feature_update_report.json",
        paths.quality_outputs / "performance_benchmark.json",
        paths.models_outputs / "model_registry.json",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    try:
        sim = simulate_match(None, None, n_simulations=80, random_seed=42, paths=paths, simulation_mode="calibrated")
        if sim.get("simulation_mode") != "calibrated":
            failures.append("calibrated simulation did not run")
        if sim.get("anchor_source") in {None, "heuristic_state_formula"}:
            failures.append("empirical anchor not reported")
        if sim.get("markov_source") not in {"global_calibrated", "heuristic_fallback"}:
            failures.append("markov source missing")
        if "home_goals_ci" not in sim or "home_xg_ci" not in sim:
            failures.append("simulation uncertainty intervals missing")
    except Exception as exc:
        failures.append(f"calibrated simulation error: {exc}")
    matrix_path = paths.features / "markov_transition_matrix_global.parquet"
    if matrix_path.exists():
        matrix = pl.read_parquet(matrix_path)
        row_sums = matrix.group_by("from_state").agg(pl.col("probability").sum().alias("row_sum"))
        if row_sums.select((pl.col("row_sum") - 1).abs().max()).item() > 1e-6:
            failures.append("markov matrix rows do not sum to 1")
    if not args.skip_tests:
        result = subprocess.run([sys.executable, "-m", "pytest"], cwd=paths.root, check=False)
        if result.returncode != 0:
            failures.append("pytest failed")
    payload = {"passed": not failures, "failures": failures}
    (paths.quality_outputs / "pre_phase_8_check.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures:
        print("PRE-PHASE 8 CHECK: FAIL")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("PRE-PHASE 8 CHECK: PASS")


if __name__ == "__main__":
    main()
