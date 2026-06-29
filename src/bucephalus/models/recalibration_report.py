from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def write_recalibration_report(paths: ProjectPaths | None = None) -> dict:
    paths = paths or ProjectPaths()
    rows = []
    for name, path in [
        ("xg", paths.evaluation_outputs / "xg_metrics.json"),
        ("hazard", paths.evaluation_outputs / "hazard_metrics.json"),
        ("sequence", paths.evaluation_outputs / "sequence_model_metrics.json"),
        ("simulation", paths.evaluation_outputs / "simulation_backtest_metrics.json"),
        ("team_strength", paths.models_outputs / "team_strength_registry.json"),
    ]:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            metrics = data.get("metrics", data)
            rows.append(
                {
                    "component": name,
                    "status": metrics.get("status", data.get("status", "available")),
                    "brier_score": metrics.get("brier_score"),
                    "log_loss": metrics.get("log_loss"),
                    "roc_auc": metrics.get("roc_auc"),
                    "calibration_error": metrics.get("calibration_error") or metrics.get("expected_calibration_error"),
                    "rows": metrics.get("rows", data.get("rows")),
                }
            )
        else:
            rows.append({"component": name, "status": "missing"})
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "completed",
        "calibration_improved": None,
        "summary": "Current run records post-expansion calibration metrics; comparison baseline is retained in component-specific reports when available.",
        "components": rows,
    }
    paths.evaluation_outputs.mkdir(parents=True, exist_ok=True)
    (paths.evaluation_outputs / "calibration_recalibration_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pl.DataFrame(rows).write_csv(paths.evaluation_outputs / "model_calibration_comparison.csv")
    return payload
