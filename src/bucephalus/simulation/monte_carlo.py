from __future__ import annotations

import random

import numpy as np

from bucephalus.simulation.markov_engine import simulate_possession
from bucephalus.simulation.schemas import SimulationResult
from bucephalus.simulation.scoreline import top_scorelines
from bucephalus.tactics.fatigue import evaluate_fatigue
from bucephalus.tactics.matchup import evaluate_matchup
from bucephalus.tactics.schemas import TacticalState


def simulate_states(home: TacticalState, away: TacticalState, n_simulations: int, seed: int) -> SimulationResult:
    matchup = evaluate_matchup(home, away)
    hf, af = evaluate_fatigue(home), evaluate_fatigue(away)
    base_home_xg = max(0.2, 0.9 + home.late_goal_threat + home.transition * 0.5)
    base_away_xg = max(0.2, 0.9 + away.late_goal_threat + away.transition * 0.5)
    lam_home = max(0.05, base_home_xg * matchup.home_xg_modifier * matchup.away_defense_modifier)
    lam_away = max(0.05, base_away_xg * matchup.away_xg_modifier * matchup.home_defense_modifier)
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    home_goals, away_goals = [], []
    home_xg_proxy, away_xg_proxy = [], []
    home_late_goal, away_late_goal = 0, 0
    possessions = max(20, int(55 + 20 * (home.tempo + away.tempo) / 2))
    for _ in range(n_simulations):
        hxg = axg = 0.0
        for _ in range(possessions // 2):
            hxg += simulate_possession(home, away, rng)["xg_proxy"]
            axg += simulate_possession(away, home, rng)["xg_proxy"]
        h_lam = (lam_home + hxg / max(1, possessions // 2)) / 2
        a_lam = (lam_away + axg / max(1, possessions // 2)) / 2
        hg = int(np_rng.poisson(h_lam))
        ag = int(np_rng.poisson(a_lam))
        home_goals.append(hg)
        away_goals.append(ag)
        home_xg_proxy.append(h_lam)
        away_xg_proxy.append(a_lam)
        home_late_goal += int(rng.random() < _late_goal_probability(home, hf))
        away_late_goal += int(rng.random() < _late_goal_probability(away, af))
    n = max(1, n_simulations)
    return SimulationResult(
        home_team=home.team_name,
        away_team=away.team_name,
        home_win_probability=sum(h > a for h, a in zip(home_goals, away_goals, strict=False)) / n,
        draw_probability=sum(h == a for h, a in zip(home_goals, away_goals, strict=False)) / n,
        away_win_probability=sum(h < a for h, a in zip(home_goals, away_goals, strict=False)) / n,
        expected_home_goals=float(np.mean(home_goals)),
        expected_away_goals=float(np.mean(away_goals)),
        expected_home_xg_proxy=float(np.mean(home_xg_proxy)),
        expected_away_xg_proxy=float(np.mean(away_xg_proxy)),
        top_scorelines=top_scorelines(home_goals, away_goals),
        home_after_70_goal_probability=home_late_goal / n,
        away_after_70_goal_probability=away_late_goal / n,
        home_fatigue_risk=hf["after_70_defensive_risk"],
        away_fatigue_risk=af["after_70_defensive_risk"],
        key_tactical_drivers=matchup.explanation_bullets,
        warnings=[] if min(home.reliability_score, away.reliability_score) >= 0.35 else ["low tactical baseline reliability; outputs are proxy-driven"],
    )


def _late_goal_probability(state: TacticalState, fatigue: dict) -> float:
    return max(0.02, min(0.55, 0.08 + 0.25 * state.late_goal_threat - 0.12 * fatigue["after_70_attacking_drop"]))
