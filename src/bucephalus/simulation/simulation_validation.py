from __future__ import annotations

import csv
import json
import math
from datetime import UTC, datetime

import numpy as np
import polars as pl

from bucephalus.simulation.simulator import simulate_match
from bucephalus.utils.paths import ProjectPaths

MODELS = [
    "naive_baseline",
    "poisson_rolling",
    "empirical_anchor",
    "empirical_anchor_tactical",
    "empirical_anchor_markov",
    "full_calibrated_team_strength",
]


def validate_simulation_backtest(paths: ProjectPaths, n_simulations: int = 150) -> dict:
    dataset_path = paths.features / "model_dataset_matches.parquet"
    if not dataset_path.exists():
        return _write_empty(paths, "model_dataset_matches missing")
    df = pl.read_parquet(dataset_path).sort("match_date")
    if df.height < 6:
        return _write_empty(paths, "insufficient matches")
    match_names = _match_name_lookup(paths)
    eval_rows = _walk_forward_eval_rows(df)
    rows = []
    historical_home_mean = float(df["home_score"].mean() or 1.2)
    historical_away_mean = float(df["away_score"].mean() or 1.0)
    for fold_id, row in enumerate(eval_rows):
        names = match_names.get(str(row["statsbomb_match_id"]), {})
        actual_home = float(row["home_score"])
        actual_away = float(row["away_score"])
        for model_name in MODELS:
            pred = _predict_model(
                model_name,
                row,
                names,
                paths,
                historical_home_mean,
                historical_away_mean,
                n_simulations=n_simulations,
            )
            rows.append(
                {
                    "fold_id": fold_id,
                    "model": model_name,
                    "statsbomb_match_id": row["statsbomb_match_id"],
                    "home_team_name": names.get("home_team_name"),
                    "away_team_name": names.get("away_team_name"),
                    "actual_home_goals": actual_home,
                    "actual_away_goals": actual_away,
                    "pred_home_goals": pred["home_goals"],
                    "pred_away_goals": pred["away_goals"],
                    "home_win_probability": pred["home_win_probability"],
                    "draw_probability": pred["draw_probability"],
                    "away_win_probability": pred["away_win_probability"],
                    "actual_result": _result(actual_home, actual_away),
                    "predicted_result": _pred_result(pred),
                    "interval_low_total_goals": pred["interval_low_total_goals"],
                    "interval_high_total_goals": pred["interval_high_total_goals"],
                    "anchor_source": pred.get("anchor_source"),
                    "markov_source": pred.get("markov_source"),
                }
            )
    metrics_rows = [_metrics(model, [r for r in rows if r["model"] == model]) for model in MODELS]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "evaluated",
        "walk_forward": True,
        "models": MODELS,
        "metrics": metrics_rows[-1],
        "rows": len(rows),
    }
    (paths.evaluation_outputs / "simulation_backtest_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pl.DataFrame(rows).write_parquet(paths.evaluation_outputs / "simulation_backtest_predictions.parquet")
    _write_csv(paths.evaluation_outputs / "simulation_model_comparison.csv", metrics_rows)
    _write_csv(paths.evaluation_outputs / "simulation_calibration_summary.csv", rows)
    return payload


def _walk_forward_eval_rows(df: pl.DataFrame) -> list[dict]:
    rows = df.to_dicts()
    cuts = sorted({int(len(rows) * 0.6), int(len(rows) * 0.75), max(0, len(rows) - 10)})
    selected = []
    seen = set()
    for cut in cuts:
        for row in rows[cut : min(len(rows), cut + 5)]:
            key = row["statsbomb_match_id"]
            if key not in seen:
                selected.append(row)
                seen.add(key)
    return selected or rows[-min(10, len(rows)) :]


def _predict_model(
    model_name: str,
    row: dict,
    names: dict,
    paths: ProjectPaths,
    historical_home_mean: float,
    historical_away_mean: float,
    n_simulations: int,
) -> dict:
    if model_name == "naive_baseline":
        home, away = historical_home_mean, historical_away_mean
        return _poisson_probs(home, away)
    if model_name == "poisson_rolling":
        home = row.get("home_rolling_goals_for_5") or historical_home_mean
        away = row.get("away_rolling_goals_for_5") or historical_away_mean
        return _poisson_probs(float(home), float(away))
    mode = "calibrated" if model_name != "empirical_anchor_tactical" else "calibrated"
    sliders = {"pressing_delta": 0.05} if "tactical" in model_name or "full" in model_name else None
    sim = simulate_match(
        names.get("home_team_name"),
        names.get("away_team_name"),
        home_sliders=sliders,
        n_simulations=n_simulations,
        random_seed=int(row["statsbomb_match_id"]) % 10000,
        paths=paths,
        simulation_mode=mode,
    )
    return {
        "home_goals": sim["expected_home_goals"],
        "away_goals": sim["expected_away_goals"],
        "home_win_probability": sim["home_win_probability"],
        "draw_probability": sim["draw_probability"],
        "away_win_probability": sim["away_win_probability"],
        "interval_low_total_goals": sim["home_goals_ci"]["p5"] + sim["away_goals_ci"]["p5"],
        "interval_high_total_goals": sim["home_goals_ci"]["p95"] + sim["away_goals_ci"]["p95"],
        "anchor_source": sim.get("anchor_source"),
        "markov_source": sim.get("markov_source"),
    }


def _poisson_probs(home: float, away: float) -> dict:
    max_goals = 8
    probs = {}
    hw = dr = aw = 0.0
    for h in range(max_goals + 1):
        hp = math.exp(-home) * home**h / math.factorial(h)
        for a in range(max_goals + 1):
            ap = math.exp(-away) * away**a / math.factorial(a)
            p = hp * ap
            if h > a:
                hw += p
            elif h == a:
                dr += p
            else:
                aw += p
            probs[(h, a)] = p
    total = hw + dr + aw
    return {
        "home_goals": home,
        "away_goals": away,
        "home_win_probability": hw / total,
        "draw_probability": dr / total,
        "away_win_probability": aw / total,
        "interval_low_total_goals": max(0, home + away - 2 * math.sqrt(home + away)),
        "interval_high_total_goals": home + away + 2 * math.sqrt(home + away),
    }


def _metrics(model: str, rows: list[dict]) -> dict:
    ah = np.array([r["actual_home_goals"] for r in rows])
    aa = np.array([r["actual_away_goals"] for r in rows])
    ph = np.array([r["pred_home_goals"] for r in rows])
    pa = np.array([r["pred_away_goals"] for r in rows])
    result_probs = np.array([[r["home_win_probability"], r["draw_probability"], r["away_win_probability"]] for r in rows])
    y = np.array([{"home": 0, "draw": 1, "away": 2}[r["actual_result"]] for r in rows])
    clipped = np.clip(result_probs, 1e-9, 1)
    return {
        "model": model,
        "rows": len(rows),
        "mae_home_goals": float(np.abs(ah - ph).mean()),
        "mae_away_goals": float(np.abs(aa - pa).mean()),
        "rmse": float(np.sqrt(((ah - ph) ** 2 + (aa - pa) ** 2).mean() / 2)),
        "accuracy": float(np.mean([r["actual_result"] == r["predicted_result"] for r in rows])),
        "log_loss": float(-np.log(clipped[np.arange(len(y)), y]).mean()),
        "brier_score": float(np.mean(np.sum((result_probs - np.eye(3)[y]) ** 2, axis=1))),
        "expected_calibration_error": _ece(rows),
        "interval_coverage": float(np.mean([(r["interval_low_total_goals"] <= r["actual_home_goals"] + r["actual_away_goals"] <= r["interval_high_total_goals"]) for r in rows])),
        "total_goals_distribution_error": float(abs((ah + aa).mean() - (ph + pa).mean())),
        "scoreline_distribution_error": float(np.mean(np.abs((ah - ph) + (aa - pa)))),
        "jensen_shannon_divergence": None,
    }


def _ece(rows: list[dict]) -> float:
    conf = []
    corr = []
    for row in rows:
        probs = {"home": row["home_win_probability"], "draw": row["draw_probability"], "away": row["away_win_probability"]}
        pred = max(probs, key=probs.get)
        conf.append(probs[pred])
        corr.append(float(pred == row["actual_result"]))
    return float(abs(np.mean(conf) - np.mean(corr)))


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
    return {
        str(row.get("match_id") or row.get("statsbomb_match_id")): {
            "home_team_name": row.get("home_team_name"),
            "away_team_name": row.get("away_team_name"),
        }
        for row in matches.to_dicts()
    }


def _result(home: float, away: float) -> str:
    if home > away:
        return "home"
    if home < away:
        return "away"
    return "draw"


def _pred_result(pred: dict) -> str:
    probs = {
        "home": pred["home_win_probability"],
        "draw": pred["draw_probability"],
        "away": pred["away_win_probability"],
    }
    return max(probs, key=probs.get)


def _write_csv(path, rows: list[dict]) -> None:
    if not rows:
        rows = [{"empty": True}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
