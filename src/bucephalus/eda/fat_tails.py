from __future__ import annotations

import numpy as np
import polars as pl


def fat_tail_summary(metrics: dict[str, list[float | None]]) -> pl.DataFrame:
    rows = []
    for name, values in metrics.items():
        total = len(values)
        arr = np.array([v for v in values if v is not None and np.isfinite(v)], dtype=float)
        if arr.size == 0:
            continue
        std = float(arr.std(ddof=1)) if arr.size > 1 else 0.0
        centered = arr - float(arr.mean())
        skew = float((centered**3).mean() / (std**3)) if std > 0 else 0.0
        kurt = float((centered**4).mean() / (std**4) - 3) if std > 0 else 0.0
        rows.append(
            {
                "metric": name,
                "count": int(arr.size),
                "mean": float(arr.mean()),
                "std": std,
                "skewness": skew,
                "kurtosis": kurt,
                "p50": float(np.percentile(arr, 50)),
                "p75": float(np.percentile(arr, 75)),
                "p90": float(np.percentile(arr, 90)),
                "p95": float(np.percentile(arr, 95)),
                "p99": float(np.percentile(arr, 99)),
                "min": float(arr.min()),
                "max": float(arr.max()),
                "missing_rate": float((total - arr.size) / total) if total else 0.0,
            }
        )
    return pl.DataFrame(rows)
