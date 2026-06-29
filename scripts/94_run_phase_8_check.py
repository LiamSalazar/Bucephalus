from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    failures = []
    pre = paths.quality_outputs / "pre_phase_8_check.json"
    if not pre.exists() or not json.loads(pre.read_text(encoding="utf-8")).get("passed"):
        failures.append("pre-phase-8 check has not passed")
    required = [
        paths.models_outputs / "tabular_model_registry.json",
        paths.evaluation_outputs / "tabular_model_metrics.json",
        paths.models_outputs / "hazard_model_registry.json",
        paths.evaluation_outputs / "hazard_metrics.json",
        paths.evaluation_outputs / "possession_value_metrics.json",
        paths.evaluation_outputs / "epv_metrics.json",
        paths.models_outputs / "sequence_model_registry.json",
        paths.evaluation_outputs / "sequence_model_metrics.json",
        paths.evaluation_outputs / "mc_dropout_summary.json",
        paths.quality_outputs / "vectorized_simulation_benchmark.json",
        paths.simulations_outputs / "vectorized_match_simulation.json",
        paths.features / "pass_network_nodes.parquet",
        paths.features / "pass_network_edges.parquet",
        paths.features / "pass_network_metrics.parquet",
        paths.models_outputs / "gnn_model_registry.json",
        paths.evaluation_outputs / "gnn_metrics.json",
        paths.outputs / "explainability" / "tabular_feature_importance.csv",
        paths.outputs / "explainability" / "sequence_event_attribution_sample.json",
        paths.outputs / "explainability" / "gnn_edge_importance_sample.json",
        paths.evaluation_outputs / "phase8_model_scorecard.json",
        paths.outputs / "reports" / "phase8_results_summary.md",
        paths.outputs / "explainability" / "prediction_explanation_sample.json",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    for registry in [
        paths.models_outputs / "tabular_model_registry.json",
        paths.models_outputs / "hazard_model_registry.json",
        paths.models_outputs / "sequence_model_registry.json",
    ]:
        if registry.exists() and "training_data_hash" not in registry.read_text(encoding="utf-8"):
            failures.append(f"metadata missing training_data_hash: {registry}")
    if not args.skip_tests:
        result = subprocess.run([sys.executable, "-m", "pytest"], cwd=paths.root, check=False)
        if result.returncode != 0:
            failures.append("pytest failed")
    payload = {"passed": not failures, "failures": failures}
    (paths.quality_outputs / "phase_8_check.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures:
        print("PHASE 8 CHECK: FAIL")
        for failure in failures:
            print(f"- {failure}")
        sys.exit(1)
    print("PHASE 8 CHECK: PASS")


if __name__ == "__main__":
    main()
