from __future__ import annotations

import math

import numpy as np
import polars as pl


def poisson_pmf(k: int, lam: float) -> float:
    lam = max(float(lam), 0.05)
    return math.exp(-lam) * lam**k / math.factorial(k)


def result_probabilities(lambda_home: float, lambda_away: float, max_goals: int = 8) -> tuple[float, float, float]:
    home = draw = away = 0.0
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_pmf(h, lambda_home) * poisson_pmf(a, lambda_away)
            if h > a:
                home += p
            elif h == a:
                draw += p
            else:
                away += p
    total = home + draw + away
    return home / total, draw / total, away / total


def top_scorelines(lambda_home: float, lambda_away: float, limit: int = 5) -> list[dict]:
    rows = []
    for h in range(8):
        for a in range(8):
            rows.append({"scoreline": f"{h}-{a}", "probability": poisson_pmf(h, lambda_home) * poisson_pmf(a, lambda_away)})
    return sorted(rows, key=lambda row: row["probability"], reverse=True)[:limit]


def naive_predictions(train: pl.DataFrame, test: pl.DataFrame) -> pl.DataFrame:
    home_mean = float(train["home_score"].mean() or 1.2)
    away_mean = float(train["away_score"].mean() or 1.0)
    return _prediction_frame(test, home_mean, away_mean, "naive_prior")


def poisson_rolling_predictions(train: pl.DataFrame, test: pl.DataFrame) -> pl.DataFrame:
    home_mean = float(train["home_score"].mean() or 1.2)
    away_mean = float(train["away_score"].mean() or 1.0)
    rows = []
    for row in test.to_dicts():
        lam_h = _first_number(row, ["home_rolling_goals_for_5", "home_rolling_goals_for_3", "diff_rolling_goals_for_5"], home_mean)
        lam_a = _first_number(row, ["away_rolling_goals_for_5", "away_rolling_goals_for_3"], away_mean)
        ph, pd, pa = result_probabilities(lam_h, lam_a)
        rows.append(_row_prediction(row, lam_h, lam_a, ph, pd, pa, "poisson_rolling"))
    return pl.DataFrame(rows)


def _prediction_frame(test: pl.DataFrame, lam_h: float, lam_a: float, model_name: str) -> pl.DataFrame:
    ph, pd, pa = result_probabilities(lam_h, lam_a)
    return pl.DataFrame([_row_prediction(row, lam_h, lam_a, ph, pd, pa, model_name) for row in test.to_dicts()])


def _row_prediction(row: dict, lam_h: float, lam_a: float, ph: float, pd: float, pa: float, model_name: str) -> dict:
    return {
        "model_name": model_name,
        "bucephalus_match_id": row.get("bucephalus_match_id"),
        "statsbomb_match_id": row.get("statsbomb_match_id"),
        "match_date": row.get("match_date"),
        "actual_home_goals": row.get("home_score"),
        "actual_away_goals": row.get("away_score"),
        "expected_home_goals": float(lam_h),
        "expected_away_goals": float(lam_a),
        "prob_home_win": float(ph),
        "prob_draw": float(pd),
        "prob_away_win": float(pa),
        "predicted_result": int(np.argmax([ph, pd, pa])),
        "actual_result": 0 if row.get("home_score", 0) > row.get("away_score", 0) else 1 if row.get("home_score") == row.get("away_score") else 2,
    }


def _first_number(row: dict, keys: list[str], default: float) -> float:
    for key in keys:
        value = row.get(key)
        if value is not None and not (isinstance(value, float) and math.isnan(value)):
            return max(float(value), 0.05)
    return default
