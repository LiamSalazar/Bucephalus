from __future__ import annotations

import polars as pl


def majority_result_baseline(train: pl.DataFrame) -> int:
    if train.is_empty():
        return 0
    result = train.with_columns(
        pl.when(pl.col("home_score") > pl.col("away_score")).then(0).when(pl.col("home_score") == pl.col("away_score")).then(1).otherwise(2).alias("result")
    ).group_by("result").agg(pl.len().alias("rows")).sort("rows", descending=True)["result"][0]
    return int(result)
