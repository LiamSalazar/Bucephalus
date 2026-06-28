from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    paths.ensure()
    versions = paths.models_outputs / "model_versions"
    versions.mkdir(parents=True, exist_ok=True)
    entries = []
    for model_type, artifact in [
        ("baseline_models", paths.models_outputs / "baseline_registry.json"),
        ("xg_model", paths.models_outputs / "xg_model_registry.json"),
        ("team_strength", paths.models_outputs / "team_strength_registry.json"),
        ("markov_matrix", paths.features / "markov_transition_matrix_global.parquet"),
        ("calibrated_simulation_config", paths.calibration_outputs / "parameter_registry.json"),
    ]:
        if artifact.exists():
            model_id = f"{model_type}_v0"
            entries.append(
                {
                    "model_id": model_id,
                    "model_type": model_type,
                    "created_at": datetime.now(UTC).isoformat(),
                    "training_data_hash": _hash_file(artifact),
                    "feature_set_version": "feature_store_v0",
                    "train_period": None,
                    "validation_period": None,
                    "metrics": _metrics_for(paths, model_type),
                    "artifact_path": str(artifact),
                    "status": "candidate",
                    "rollback_from": None,
                    "notes": "local lightweight registry; no external tracking server",
                }
            )
            (versions / f"{model_id}.json").write_text(json.dumps(entries[-1], indent=2), encoding="utf-8")
    payload = {"generated_at": datetime.now(UTC).isoformat(), "models": entries, "rows": len(entries)}
    (paths.models_outputs / "model_registry.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(payload)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metrics_for(paths: ProjectPaths, model_type: str) -> dict:
    candidates = {
        "xg_model": paths.evaluation_outputs / "xg_metrics.json",
        "team_strength": paths.evaluation_outputs / "team_strength_backtest.json",
        "baseline_models": paths.evaluation_outputs / "baseline_metrics.json",
        "markov_matrix": paths.calibration_outputs / "markov_calibration_report.json",
        "calibrated_simulation_config": paths.evaluation_outputs / "simulation_backtest_metrics.json",
    }
    path = candidates.get(model_type)
    if path and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


if __name__ == "__main__":
    main()
