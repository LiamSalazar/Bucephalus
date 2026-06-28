from __future__ import annotations

import csv
import json
from datetime import UTC, datetime

import numpy as np
import polars as pl

from bucephalus.simulation.simulator import simulate_match
from bucephalus.utils.paths import ProjectPaths


def validate_simulation_backtest(paths: ProjectPaths, n_simulations: int = 150) -> dict:
    dataset_path = paths.features / "model_dataset_matches.parquet"
    if not dataset_path.exists():
        return _write_empty(paths, "model_dataset_matches missing")
    df = pl.read_parquet(dataset_path).sort("match_date")
    if df.height < 2:
        return _write_empty(paths, "insufficient matches")
    rows = []
    for row in df.tail(min(10, df.height)).to_dicts():
        sim = simulate_match(None, None, n_simulations=n_simulations, random_seed=int(row["statsbomb_match_id"]) % 10000, paths=paths, simulation_mode="calibrated")
        rows.append({
            "model": "calibrated_anchor_tactical_markov",
            "actual_home_goals": row["home_score"],
            "actual_away_goals": row["away_score"],
            "pred_home_goals": sim["expected_home_goals"],
            "pred_away_goals": sim["expected_away_goals"],
            "home_win_probability": sim["home_win_probability"],
            "draw_probability": sim["draw_probability"],
            "away_win_probability": sim["away_win_probability"],
        })
    metrics = _metrics(rows)
    payload = {"generated_at": datetime.now(UTC).isoformat(), "status": "evaluated", "metrics": metrics, "rows": len(rows)}
    (paths.evaluation_outputs / "simulation_backtest_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_csv(paths.evaluation_outputs / "simulation_model_comparison.csv", [metrics])
    _write_csv(paths.evaluation_outputs / "simulation_calibration_summary.csv", rows)
    return payload


def _metrics(rows: list[dict]) -> dict:
    ah = np.array([r["actual_home_goals"] for r in rows])
    aa = np.array([r["actual_away_goals"] for r in rows])
    ph = np.array([r["pred_home_goals"] for r in rows])
    pa = np.array([r["pred_away_goals"] for r in rows])
    return {
        "model": "calibrated_anchor_tactical_markov",
        "rows": len(rows),
        "mae_home_goals": float(np.abs(ah - ph).mean()),
        "mae_away_goals": float(np.abs(aa - pa).mean()),
        "rmse": float(np.sqrt(((ah - ph) ** 2 + (aa - pa) ** 2).mean() / 2)),
        "mean_total_goals_actual": float((ah + aa).mean()),
        "mean_total_goals_predicted": float((ph + pa).mean()),
    }


def _write_empty(paths: ProjectPaths, reason: str) -> dict:
    payload = {"generated_at": datetime.now(UTC).isoformat(), "status": "skipped", "reason": reason, "metrics": {}}
    (paths.evaluation_outputs / "simulation_backtest_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_csv(paths.evaluation_outputs / "simulation_model_comparison.csv", [{"model": "skipped", "reason": reason}])
    _write_csv(paths.evaluation_outputs / "simulation_calibration_summary.csv", [{"reason": reason}])
    return payload


def _write_csv(path, rows: list[dict]) -> None:
    if not rows:
        rows = [{"empty": True}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
