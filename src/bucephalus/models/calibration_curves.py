from __future__ import annotations

import numpy as np
import polars as pl


def calibration_summary(y_true: list[int], y_prob: list[float], bins: int = 10) -> pl.DataFrame:
    if not y_true:
        return pl.DataFrame()
    arr_y = np.array(y_true)
    arr_p = np.array(y_prob)
    rows = []
    edges = np.linspace(0, 1, bins + 1)
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (arr_p >= lo) & (arr_p < hi if i < bins - 1 else arr_p <= hi)
        if mask.sum() == 0:
            continue
        rows.append({
            "bin_lower": float(lo),
            "bin_upper": float(hi),
            "count": int(mask.sum()),
            "mean_prediction": float(arr_p[mask].mean()),
            "actual_rate": float(arr_y[mask].mean()),
        })
    return pl.DataFrame(rows)
