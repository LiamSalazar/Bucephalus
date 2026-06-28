from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from bucephalus.simulation.simulator import simulate_match
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    paths.ensure()
    readme = (paths.root / "README.md").read_text(encoding="utf-8")
    checks = {
        "readme_mentions_7_5_to_7_7": "7.5" in readme and "7.7" in readme,
        "makefile_has_phase_7_5": "all-phase-7-5" in (paths.root / "Makefile").read_text(encoding="utf-8"),
        "pyyaml_dependency": "PyYAML" in (paths.root / "pyproject.toml").read_text(encoding="utf-8"),
        "parameter_registry_exists": (paths.calibration_outputs / "parameter_registry.json").exists(),
        "leakage_audit_exists": (paths.evaluation_outputs / "leakage_audit.json").exists(),
        "xg_metrics_exists": (paths.evaluation_outputs / "xg_metrics.json").exists(),
        "markov_matrix_exists": (paths.features / "markov_transition_matrix_global.parquet").exists(),
        "team_strength_exists": (paths.features / "team_strength_timeseries.parquet").exists(),
        "model_registry_exists": (paths.models_outputs / "model_registry.json").exists(),
    }
    try:
        sim = simulate_match(None, None, n_simulations=20, random_seed=7, paths=paths, simulation_mode="calibrated")
        checks["calibrated_simulation_runs"] = sim.get("simulation_mode") == "calibrated"
        checks["empirical_anchor_used"] = sim.get("anchor_source") != "heuristic_state_formula"
        checks["markov_source_reported"] = bool(sim.get("markov_source"))
    except Exception as exc:
        checks["calibrated_simulation_runs"] = False
        checks["simulation_error"] = str(exc)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "checks": checks,
        "passed": all(value is True for value in checks.values() if isinstance(value, bool)),
        "blockers": [name for name, passed in checks.items() if passed is False],
        "files_affected": [
            "configs/tactical_engine_v0.yaml",
            "configs/simulation_engine_v0.yaml",
            "src/bucephalus/calibration",
            "src/bucephalus/simulation",
            "src/bucephalus/models",
            "src/bucephalus/features",
            "scripts",
            "Makefile",
            "README.md",
        ],
        "risks": [
            "sample/fallback data can pass checks with low statistical power",
            "some tactical parameters remain heuristic_fallback until larger calibration datasets are used",
        ],
        "actions_taken": ["pre-phase-8 gap audit generated"],
    }
    (paths.quality_outputs / "pre_phase_8_gap_audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
