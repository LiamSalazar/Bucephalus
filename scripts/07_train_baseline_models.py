from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from bucephalus.features.schemas import MODEL_EXCLUDED_COLUMNS
from bucephalus.models.baseline_goals import naive_predictions, poisson_rolling_predictions, top_scorelines
from bucephalus.models.calibration import calibration_table
from bucephalus.models.evaluation import evaluate_predictions
from bucephalus.models.model_registry import write_registry
from bucephalus.models.walk_forward import temporal_split, write_split_summary
from bucephalus.utils.logging import configure_logging
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    configure_logging("DEBUG" if args.verbose else "INFO")
    paths = ProjectPaths(data_root=args.data_root)
    paths.ensure()
    dataset_path = paths.features / "model_dataset_matches.parquet"
    if not dataset_path.exists():
        raise FileNotFoundError(dataset_path)
    df = pl.read_parquet(dataset_path).sort("match_date")
    splits = temporal_split(df)
    indexed = df.with_row_index("row_id")
    train = indexed.filter(pl.col("row_id").is_in(splits["train"])).drop("row_id")
    test_ids = splits["test"] or splits["validation"]
    test = indexed.filter(pl.col("row_id").is_in(test_ids)).drop("row_id")
    predictions = pl.concat([naive_predictions(train, test), poisson_rolling_predictions(train, test)], how="vertical_relaxed")
    predictions.write_parquet(paths.evaluation_outputs / "predictions_baseline.parquet")
    metrics = evaluate_predictions(predictions)
    (paths.evaluation_outputs / "baseline_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    calibration_table(predictions).write_csv(paths.evaluation_outputs / "calibration_summary.csv")
    pl.DataFrame(metrics["models"]).write_csv(paths.evaluation_outputs / "model_comparison.csv")
    write_split_summary(paths.evaluation_outputs / "walk_forward_splits.json", df, splits)
    registry = [
        {"model_name": "naive_prior", "status": "trained", "description": "global train-set home/away goal means"},
        {"model_name": "poisson_rolling", "status": "trained", "description": "Poisson probabilities from prior rolling goals"},
        {
            "model_name": "regularized_regression",
            "status": "skipped" if df.height < 60 else "deferred",
            "reason": "insufficient rows for stable out-of-sample regression" if df.height < 60 else "kept out of current lightweight baseline run",
        },
        {
            "model_name": "simple_tree",
            "status": "skipped" if df.height < 100 else "deferred",
            "reason": "insufficient rows for tree baseline" if df.height < 100 else "kept for later comparison",
        },
    ]
    write_registry(paths.models_outputs / "baseline_registry.json", registry)
    leakage = {
        "excluded_columns": MODEL_EXCLUDED_COLUMNS,
        "used_columns": [c for c in df.columns if c not in MODEL_EXCLUDED_COLUMNS],
        "targets": ["home_score", "away_score", "result_home_win", "result_draw", "result_away_win"],
        "rolling_features_previous_only": True,
        "validation": "temporal walk-forward split",
        "warnings": [] if df.height >= 20 else ["very small dataset; metrics are smoke-test only"],
    }
    (paths.evaluation_outputs / "leakage_check.json").write_text(json.dumps(leakage, indent=2), encoding="utf-8")
    sample_scorelines = []
    for row in predictions.head(5).to_dicts():
        sample_scorelines.append(
            {
                "statsbomb_match_id": row["statsbomb_match_id"],
                "model_name": row["model_name"],
                "top_scorelines": top_scorelines(row["expected_home_goals"], row["expected_away_goals"]),
            }
        )
    (paths.evaluation_outputs / "scoreline_samples.json").write_text(json.dumps(sample_scorelines, indent=2), encoding="utf-8")
    print("Baseline metrics:", metrics)


if __name__ == "__main__":
    main()
