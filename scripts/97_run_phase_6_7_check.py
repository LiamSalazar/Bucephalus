from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import polars as pl

from bucephalus.simulation.markov_engine import base_transition_matrix, validate_transition_matrix
from bucephalus.simulation.scenario import auto_pick_teams, run_tactical_scenario
from bucephalus.simulation.sensitivity import run_sensitivity
from bucephalus.simulation.simulator import simulate_match
from bucephalus.tactics.style_profiles import build_tactical_engine_inputs
from bucephalus.tactics.tactical_sliders import apply_tactical_sliders
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    paths.ensure()
    failures = []
    try:
        if not (paths.features / "tactical_engine_inputs.parquet").exists():
            build_tactical_engine_inputs(paths)
        df = pl.read_parquet(paths.features / "tactical_engine_inputs.parquet")
        if df.is_empty():
            failures.append("tactical_engine_inputs is empty")
        home, away = auto_pick_teams(paths)
        _, slider_report = apply_tactical_sliders(home, pressing_delta=0.2)
        if slider_report.after.pressing == slider_report.before.pressing:
            failures.append("sliders did not change pressing")
        scenario = run_tactical_scenario(home, away, {"pressing_delta": 0.1}, {}, paths.simulations_outputs / "tactical_scenario_report.json")
        if not scenario["matchup"]["explanation_bullets"]:
            failures.append("missing tactical explanations")
        if not validate_transition_matrix(base_transition_matrix()):
            failures.append("base Markov transition matrix invalid")
        sim = simulate_match(home.team_name, away.team_name, n_simulations=200, random_seed=42, paths=paths)
        prob_sum = sim["home_win_probability"] + sim["draw_probability"] + sim["away_win_probability"]
        if abs(prob_sum - 1) > 1e-9:
            failures.append("Monte Carlo probabilities do not sum to 1")
        run_sensitivity(home.team_name, away.team_name, "pressing", [-0.2, 0.0, 0.2], 100, 42, paths)
        for file in [
            paths.features / "tactical_engine_inputs.parquet",
            paths.features / "tactical_engine_manifest.json",
            paths.simulations_outputs / "latest_match_simulation.json",
            paths.simulations_outputs / "sensitivity_analysis.csv",
        ]:
            if not file.exists():
                failures.append(f"missing artifact: {file}")
    except Exception as exc:
        failures.append(str(exc))
    if not args.skip_tests:
        result = subprocess.run([sys.executable, "-m", "pytest"], cwd=paths.root, check=False)
        if result.returncode != 0:
            failures.append("pytest failed")
    payload = {"passed": not failures, "failures": failures}
    (paths.simulations_outputs / "phase_6_7_check.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures:
        print("PHASE 6-7 CHECK: FAIL")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("PHASE 6-7 CHECK: PASS")


if __name__ == "__main__":
    main()
