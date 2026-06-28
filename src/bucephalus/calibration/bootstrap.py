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


EFFECT_SPECS = [
    ("pressing_to_shots_for", ["pressing_proxy"], "shots_for"),
    ("pressing_to_xg_for", ["pressing_proxy"], "xg_for"),
    ("pressing_tempo_to_goals_against_after_70", ["pressing_proxy", "directness_proxy"], "goals_after_70_against"),
    ("transition_to_shots_for", ["transition_proxy"], "shots_for"),
    ("transition_to_xg_for", ["transition_proxy"], "xg_for"),
    ("defensive_exposure_to_xg_against", ["late_pressure_or_fatigue_proxy"], "xg_against"),
    ("defensive_exposure_to_shots_against", ["late_pressure_or_fatigue_proxy"], "shots_against"),
    ("directness_to_final_third_entries", ["directness_proxy"], "final_third_entries_proxy"),
    ("directness_to_shots_for", ["directness_proxy"], "shots_for"),
    ("set_piece_dependency_to_set_piece_shots", ["set_piece_dependency_proxy"], "set_piece_shots_for"),
    ("set_piece_dependency_to_set_piece_xg", ["set_piece_dependency_proxy"], "set_piece_xg_for"),
]


def bootstrap_tactical_effects(
    paths: ProjectPaths,
    n_bootstraps: int = 200,
    random_seed: int = 42,
) -> dict:
    paths.ensure()
    source_path = paths.features / "team_match_features.parquet"
    if not source_path.exists():
        return _write_effect_insufficient(paths, "team_match_features.parquet missing")
    df = pl.read_parquet(source_path)
    rng = np.random.default_rng(random_seed)
    rows = []
    summary = []
    for effect_name, feature_cols, target_col in EFFECT_SPECS:
        missing = [c for c in [*feature_cols, target_col] if c not in df.columns]
        clean = df.drop_nulls([c for c in [*feature_cols, target_col] if c in df.columns]) if not missing else pl.DataFrame()
        if missing or clean.height < 12:
            summary.append(
                {
                    "effect": effect_name,
                    "status": "insufficient_data",
                    "sample_size": clean.height,
                    "warning": f"missing={missing} rows={clean.height}",
                }
            )
            continue
        x = clean.select(feature_cols).to_numpy().astype(float)
        y = clean[target_col].to_numpy().astype(float)
        x = _standardize_matrix(x)
        coefs = []
        for iteration in range(n_bootstraps):
            idx = rng.integers(0, clean.height, clean.height)
            coef = _ols_coef(x[idx], y[idx])
            coefs.append(coef)
            rows.append(
                {
                    "effect": effect_name,
                    "bootstrap_iteration": iteration,
                    "coefficient": float(coef),
                    "sample_size": clean.height,
                }
            )
        p5, p50, p95 = np.percentile(coefs, [5, 50, 95])
        summary.append(
            {
                "effect": effect_name,
                "status": "estimated",
                "coefficient_mean": float(np.mean(coefs)),
                "p5": float(p5),
                "p50": float(p50),
                "p95": float(p95),
                "sample_size": clean.height,
                "stability": "unstable" if float(p95 - p5) > max(1.0, abs(float(p50))) else "stable",
                "warning": None,
            }
        )
    pl.DataFrame(rows or [], schema={"effect": pl.Utf8, "bootstrap_iteration": pl.Int64, "coefficient": pl.Float64, "sample_size": pl.Int64}).write_parquet(
        paths.calibration_outputs / "tactical_effect_bootstrap.parquet"
    )
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "completed",
        "n_bootstraps": n_bootstraps,
        "effects": summary,
        "warnings": [s["warning"] for s in summary if s.get("warning")],
    }
    (paths.calibration_outputs / "tactical_effect_uncertainty.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
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


def _write_effect_insufficient(paths: ProjectPaths, reason: str) -> dict:
    pl.DataFrame(schema={"effect": pl.Utf8, "bootstrap_iteration": pl.Int64, "coefficient": pl.Float64, "sample_size": pl.Int64}).write_parquet(
        paths.calibration_outputs / "tactical_effect_bootstrap.parquet"
    )
    payload = {"generated_at": datetime.now(UTC).isoformat(), "status": "insufficient_data", "effects": [], "warnings": [reason]}
    (paths.calibration_outputs / "tactical_effect_uncertainty.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
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


def _standardize_matrix(x: np.ndarray) -> np.ndarray:
    std = x.std(axis=0)
    std[std == 0] = 1.0
    return (x - x.mean(axis=0)) / std


def _ols_coef(x: np.ndarray, y: np.ndarray) -> float:
    design = np.column_stack([np.ones(len(x)), x])
    try:
        beta = np.linalg.lstsq(design, y, rcond=None)[0]
    except np.linalg.LinAlgError:
        return 0.0
    return float(np.mean(beta[1:]))
