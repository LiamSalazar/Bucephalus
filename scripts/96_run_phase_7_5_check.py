from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from bucephalus.calibration.parameter_registry import build_parameter_registry
from bucephalus.models.xg_model import evaluate_xg_model
from bucephalus.simulation.ablation import run_ablation_study
from bucephalus.simulation.markov_calibration import calibrate_markov_matrix
from bucephalus.simulation.simulation_validation import validate_simulation_backtest
from bucephalus.simulation.simulator import simulate_match
from bucephalus.utils.paths import ProjectPaths
from bucephalus.validation.leakage_audit import run_leakage_audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    paths.ensure()
    failures = []
    try:
        build_parameter_registry(paths)
        leakage = run_leakage_audit(paths)
        if not leakage["passed"]:
            failures.append("leakage audit failed")
        evaluate_xg_model(paths)
        calibrate_markov_matrix(paths)
        validate_simulation_backtest(paths)
        run_ablation_study(paths)
        sim = simulate_match(None, None, n_simulations=100, random_seed=42, paths=paths, simulation_mode="calibrated")
        if sim.get("simulation_mode") != "calibrated":
            failures.append("calibrated simulation did not run")
        if "home_goals_ci" not in sim or "result_probability_standard_error" not in sim:
            failures.append("simulation uncertainty intervals missing")
        required = [
            paths.calibration_outputs / "parameter_registry.json",
            paths.evaluation_outputs / "leakage_audit.json",
            paths.evaluation_outputs / "xg_metrics.json",
            paths.features / "markov_transition_matrix_global.parquet",
            paths.calibration_outputs / "markov_calibration_report.json",
            paths.evaluation_outputs / "simulation_backtest_metrics.json",
            paths.evaluation_outputs / "ablation_study.csv",
        ]
        for path in required:
            if not path.exists():
                failures.append(f"missing artifact: {path}")
    except Exception as exc:
        failures.append(str(exc))
    if not args.skip_tests:
        result = subprocess.run([sys.executable, "-m", "pytest"], cwd=paths.root, check=False)
        if result.returncode != 0:
            failures.append("pytest failed")
    payload = {"passed": not failures, "failures": failures}
    (paths.calibration_outputs / "phase_7_5_check.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures:
        print("PHASE 7.5 CHECK: FAIL")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("PHASE 7.5 CHECK: PASS")


if __name__ == "__main__":
    main()
