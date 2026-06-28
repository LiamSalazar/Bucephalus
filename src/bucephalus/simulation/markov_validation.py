from __future__ import annotations

import polars as pl


def validate_markov_matrix(matrix: pl.DataFrame) -> dict:
    row_sums = matrix.group_by("from_state").agg(pl.col("probability").sum().alias("row_sum"))
    return {
        "rows_sum_to_one": bool(row_sums.select((pl.col("row_sum") - 1).abs().max()).item() < 1e-9),
        "no_negative_probabilities": bool(matrix.filter(pl.col("probability") < 0).is_empty()),
        "states_count": row_sums.height,
    }
