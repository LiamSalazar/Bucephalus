from __future__ import annotations

from pydantic import BaseModel


class SimulationResult(BaseModel):
    home_team: str
    away_team: str
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    expected_home_goals: float
    expected_away_goals: float
    expected_home_xg_proxy: float
    expected_away_xg_proxy: float
    top_scorelines: list[dict]
    home_after_70_goal_probability: float
    away_after_70_goal_probability: float
    home_fatigue_risk: float
    away_fatigue_risk: float
    key_tactical_drivers: list[str]
    warnings: list[str]
