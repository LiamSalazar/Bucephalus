from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl

from bucephalus.utils.paths import ProjectPaths


PARAMETER_COLUMNS = {
    "possession_baseline": "possession_proxy",
    "pressing_baseline": "pressing_proxy",
    "directness_baseline": "directness_proxy",
    "transition_baseline": "transition_proxy",
}


def bootstrap_tactical_parameters(
    paths: ProjectPaths,
    n_bootstraps: int = 200,
    random_seed: int = 42,
) -> dict:
    paths.ensure()
    source_path = paths.features / "team_match_features.parquet"
    if not source_path.exists():
        return _write_insufficient(paths, "team_match_features.parquet missing")
    df = pl.read_parquet(source_path)
    usable = [col for col in PARAMETER_COLUMNS.values() if col in df.columns]
    if df.height < 6 or not usable:
        return _write_insufficient(paths, f"insufficient rows={df.height} usable_columns={usable}")

    rng = np.random.default_rng(random_seed)
    df = _normalize_columns(df, usable)
    samples: list[dict] = []
    for iteration in range(n_bootstraps):
        idx = rng.integers(0, df.height, size=df.height)
        sampled = df[idx.tolist()]
        row = {"bootstrap_iteration": iteration}
        for parameter, column in PARAMETER_COLUMNS.items():
            if column in sampled.columns:
                row["parameter"] = parameter
                row["value"] = float(sampled[column].mean() or 0.0)
                samples.append(dict(row))

    boot = pl.DataFrame(samples)
    boot.write_parquet(paths.calibration_outputs / "tactical_parameter_bootstrap.parquet")
    summary_rows = []
    for parameter in sorted(set(boot["parameter"].to_list())):
        values = boot.filter(pl.col("parameter") == parameter)["value"].to_numpy()
        p5, p50, p95 = np.percentile(values, [5, 50, 95])
        summary_rows.append(
            {
                "parameter": parameter,
                "p5": float(p5),
                "p50": float(p50),
                "p95": float(p95),
                "std": float(np.std(values)),
                "stability": "unstable" if float(p95 - p5) > 0.35 else "stable",
            }
        )
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "completed",
        "rows": df.height,
        "n_bootstraps": n_bootstraps,
        "parameters": summary_rows,
        "warnings": [],
    }
    (paths.calibration_outputs / "tactical_parameter_uncertainty.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    return payload


def _write_insufficient(paths: ProjectPaths, reason: str) -> dict:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "insufficient_data",
        "reason": reason,
        "parameters": [],
        "warnings": [reason],
    }
    pl.DataFrame(
        schema={
            "bootstrap_iteration": pl.Int64,
            "parameter": pl.Utf8,
            "value": pl.Float64,
        }
    ).write_parquet(paths.calibration_outputs / "tactical_parameter_bootstrap.parquet")
    (paths.calibration_outputs / "tactical_parameter_uncertainty.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    return payload


def _normalize_columns(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    output = df
    for column in columns:
        values = output[column].drop_nulls()
        if values.is_empty():
            continue
        min_value = float(values.min())
        max_value = float(values.max())
        if min_value >= 0 and max_value <= 1:
            continue
        span = max(max_value - min_value, 1e-9)
        output = output.with_columns(((pl.col(column) - min_value) / span).clip(0, 1).alias(column))
    return output
