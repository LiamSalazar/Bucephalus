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
    match_names = _match_name_lookup(paths)
    if df.height < 2:
        return _write_empty(paths, "insufficient matches")
    rows = []
    for row in df.tail(min(10, df.height)).to_dicts():
        names = match_names.get(str(row["statsbomb_match_id"]), {})
        sim = simulate_match(
            names.get("home_team_name"),
            names.get("away_team_name"),
            n_simulations=n_simulations,
            random_seed=int(row["statsbomb_match_id"]) % 10000,
            paths=paths,
            simulation_mode="calibrated",
        )
        actual_result = _result(row["home_score"], row["away_score"])
        rows.append({
            "model": "calibrated_anchor_tactical_markov",
            "statsbomb_match_id": row["statsbomb_match_id"],
            "home_team_name": names.get("home_team_name"),
            "away_team_name": names.get("away_team_name"),
            "actual_home_goals": row["home_score"],
            "actual_away_goals": row["away_score"],
            "pred_home_goals": sim["expected_home_goals"],
            "pred_away_goals": sim["expected_away_goals"],
            "home_win_probability": sim["home_win_probability"],
            "draw_probability": sim["draw_probability"],
            "away_win_probability": sim["away_win_probability"],
            "actual_result": actual_result,
            "predicted_result": _pred_result(sim),
            "anchor_source": sim.get("anchor_source"),
            "markov_source": sim.get("markov_source"),
        })
    metrics = _metrics(rows)
    payload = {"generated_at": datetime.now(UTC).isoformat(), "status": "evaluated", "metrics": metrics, "rows": len(rows)}
    (paths.evaluation_outputs / "simulation_backtest_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pl.DataFrame(rows).write_parquet(paths.evaluation_outputs / "simulation_backtest_predictions.parquet")
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
        "result_accuracy": float(np.mean([r["actual_result"] == r["predicted_result"] for r in rows])),
        "total_goals_distribution_error": float(abs((ah + aa).mean() - (ph + pa).mean())),
    }


def _write_empty(paths: ProjectPaths, reason: str) -> dict:
    payload = {"generated_at": datetime.now(UTC).isoformat(), "status": "skipped", "reason": reason, "metrics": {}}
    (paths.evaluation_outputs / "simulation_backtest_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_csv(paths.evaluation_outputs / "simulation_model_comparison.csv", [{"model": "skipped", "reason": reason}])
    _write_csv(paths.evaluation_outputs / "simulation_calibration_summary.csv", [{"reason": reason}])
    return payload


def _match_name_lookup(paths: ProjectPaths) -> dict[str, dict]:
    matches_path = paths.processed / "matches.parquet"
    if not matches_path.exists():
        return {}
    matches = pl.read_parquet(matches_path)
    lookup = {}
    for row in matches.to_dicts():
        match_id = str(row.get("match_id") or row.get("statsbomb_match_id"))
        lookup[match_id] = {
            "home_team_name": row.get("home_team_name"),
            "away_team_name": row.get("away_team_name"),
        }
    return lookup


def _result(home: float, away: float) -> str:
    if home > away:
        return "home"
    if home < away:
        return "away"
    return "draw"


def _pred_result(sim: dict) -> str:
    probs = {
        "home": sim["home_win_probability"],
        "draw": sim["draw_probability"],
        "away": sim["away_win_probability"],
    }
    return max(probs, key=probs.get)


def _write_csv(path, rows: list[dict]) -> None:
    if not rows:
        rows = [{"empty": True}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
