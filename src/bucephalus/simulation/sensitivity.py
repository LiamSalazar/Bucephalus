from __future__ import annotations

import csv

from bucephalus.config import settings
from bucephalus.simulation.simulator import simulate_match
from bucephalus.utils.paths import ProjectPaths


def run_sensitivity(home_team: str | None, away_team: str | None, slider: str, values: list[float], n_simulations: int, seed: int = 42, paths: ProjectPaths | None = None) -> list[dict]:
    paths = paths or settings.paths
    rows = []
    delta_key = f"{slider}_delta"
    for value in values:
        result = simulate_match(home_team, away_team, home_sliders={delta_key: value}, n_simulations=n_simulations, random_seed=seed, paths=paths)
        rows.append({
            "slider": slider,
            "value": value,
            "home_win_probability": result["home_win_probability"],
            "draw_probability": result["draw_probability"],
            "away_win_probability": result["away_win_probability"],
            "expected_home_goals": result["expected_home_goals"],
            "expected_away_goals": result["expected_away_goals"],
            "home_fatigue_risk": result["home_fatigue_risk"],
            "away_fatigue_risk": result["away_fatigue_risk"],
            "home_after_70_goal_probability": result["home_after_70_goal_probability"],
            "away_after_70_goal_probability": result["away_after_70_goal_probability"],
        })
    path = paths.simulations_outputs / "sensitivity_analysis.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows
