from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from bucephalus.models.calibration import calibration_table
from bucephalus.models.evaluation import evaluate_predictions
from bucephalus.utils.logging import configure_logging
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    configure_logging("DEBUG" if args.verbose else "INFO")
    paths = ProjectPaths(data_root=args.data_root)
    preds = pl.read_parquet(paths.evaluation_outputs / "predictions_baseline.parquet")
    metrics = evaluate_predictions(preds)
    (paths.evaluation_outputs / "baseline_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    pl.DataFrame(metrics["models"]).write_csv(paths.evaluation_outputs / "model_comparison.csv")
    calibration_table(preds).write_csv(paths.evaluation_outputs / "calibration_summary.csv")
    print("Evaluation metrics:", metrics)


if __name__ == "__main__":
    main()
