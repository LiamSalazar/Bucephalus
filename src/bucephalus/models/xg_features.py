from __future__ import annotations

import math

import polars as pl

GOAL_X = 120.0
GOAL_Y = 40.0
GOAL_WIDTH = 7.32 / 68 * 80


def build_xg_training_frame(shots: pl.DataFrame) -> pl.DataFrame:
    if shots.is_empty():
        return pl.DataFrame()
    if "play_pattern_name" not in shots.columns and "play_pattern" not in shots.columns:
        shots = shots.with_columns(pl.lit("unknown").alias("play_pattern_name"))
    elif "play_pattern_name" not in shots.columns:
        shots = shots.with_columns(pl.col("play_pattern").alias("play_pattern_name"))
    df = shots.with_columns(
        (pl.col("shot_outcome") == "Goal").cast(pl.Int8).alias("is_goal"),
        (GOAL_X - pl.col("location_x").fill_null(90)).alias("dx_to_goal"),
        (GOAL_Y - pl.col("location_y").fill_null(40)).alias("dy_to_goal"),
    ).with_columns(
        ((pl.col("dx_to_goal") ** 2 + pl.col("dy_to_goal") ** 2).sqrt()).alias("distance_to_goal"),
        pl.struct(["location_x", "location_y"]).map_elements(_angle, return_dtype=pl.Float64).alias("angle_to_goal"),
        pl.col("under_pressure").fill_null(False).cast(pl.Int8).alias("under_pressure_int"),
        pl.col("shot_type").fill_null("unknown").alias("shot_type_name"),
        pl.col("play_pattern_name").fill_null("unknown").alias("play_pattern_name_clean"),
    )
    return df


def feature_columns(df: pl.DataFrame) -> list[str]:
    cols = ["location_x", "location_y", "distance_to_goal", "angle_to_goal", "under_pressure_int"]
    return [c for c in cols if c in df.columns]


def _angle(row: dict) -> float:
    x = row.get("location_x") if row.get("location_x") is not None else 90.0
    y = row.get("location_y") if row.get("location_y") is not None else 40.0
    left = math.atan2(GOAL_Y - GOAL_WIDTH / 2 - y, GOAL_X - x)
    right = math.atan2(GOAL_Y + GOAL_WIDTH / 2 - y, GOAL_X - x)
    return abs(right - left)
