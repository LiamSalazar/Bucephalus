from __future__ import annotations

import math

import numpy as np
import polars as pl


def evaluate_predictions(predictions: pl.DataFrame) -> dict:
    rows = []
    for model in predictions["model_name"].unique().to_list():
        df = predictions.filter(pl.col("model_name") == model)
        if df.is_empty():
            continue
        home_err = np.array(df["expected_home_goals"].to_list()) - np.array(df["actual_home_goals"].to_list())
        away_err = np.array(df["expected_away_goals"].to_list()) - np.array(df["actual_away_goals"].to_list())
        probs = df.select("prob_home_win", "prob_draw", "prob_away_win").to_numpy()
        actual = np.array(df["actual_result"].to_list(), dtype=int)
        chosen = probs[np.arange(len(actual)), actual]
        rows.append(
            {
                "model_name": model,
                "rows": df.height,
                "mae_home_goals": float(np.abs(home_err).mean()),
                "mae_away_goals": float(np.abs(away_err).mean()),
                "rmse_goals": float(math.sqrt(((home_err**2 + away_err**2) / 2).mean())),
                "mean_predicted_home_goals": float(df["expected_home_goals"].mean()),
                "mean_actual_home_goals": float(df["actual_home_goals"].mean()),
                "mean_predicted_away_goals": float(df["expected_away_goals"].mean()),
                "mean_actual_away_goals": float(df["actual_away_goals"].mean()),
                "accuracy": float((np.argmax(probs, axis=1) == actual).mean()),
                "log_loss": float((-np.log(np.clip(chosen, 1e-9, 1))).mean()),
                "brier_score": float(np.mean(np.sum((probs - np.eye(3)[actual]) ** 2, axis=1))),
            }
        )
    return {"models": rows}


def calibration_table(predictions: pl.DataFrame) -> pl.DataFrame:
    if predictions.is_empty():
        return pl.DataFrame()
    out = predictions.with_columns(
        pl.max_horizontal("prob_home_win", "prob_draw", "prob_away_win").alias("confidence"),
        (pl.col("predicted_result") == pl.col("actual_result")).cast(pl.Int8).alias("correct"),
    )
    return out.with_columns(
        ((pl.col("confidence") * 5).floor() / 5).clip(0, 0.8).alias("confidence_bucket"),
    ).group_by(["model_name", "confidence_bucket"]).agg(
        pl.len().alias("rows"),
        pl.col("confidence").mean().alias("mean_confidence"),
        pl.col("correct").mean().alias("empirical_accuracy"),
    ).sort(["model_name", "confidence_bucket"])
