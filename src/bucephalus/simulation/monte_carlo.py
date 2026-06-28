from __future__ import annotations

import random

import numpy as np
import polars as pl

from bucephalus.calibration.parameter_registry import get_parameter
from bucephalus.simulation.markov_engine import simulate_possession
from bucephalus.simulation.markov_states import MatchState
from bucephalus.simulation.schemas import SimulationResult
from bucephalus.simulation.scoreline import top_scorelines
from bucephalus.tactics.fatigue import evaluate_fatigue
from bucephalus.tactics.matchup import evaluate_matchup
from bucephalus.tactics.schemas import TacticalState
from bucephalus.utils.paths import ProjectPaths


def simulate_states(
    home: TacticalState,
    away: TacticalState,
    n_simulations: int,
    seed: int,
    anchor: dict | None = None,
    paths: ProjectPaths | None = None,
    simulation_mode: str = "heuristic",
) -> SimulationResult:
    matchup = evaluate_matchup(home, away)
    hf, af = evaluate_fatigue(home), evaluate_fatigue(away)
    anchor = anchor or {}
    base_home_xg = max(0.2, float(anchor.get("base_home_xg", 0.9 + home.late_goal_threat + home.transition * 0.5)))
    base_away_xg = max(0.2, float(anchor.get("base_away_xg", 0.9 + away.late_goal_threat + away.transition * 0.5)))
    lam_home = max(0.05, base_home_xg * matchup.home_xg_modifier * matchup.away_defense_modifier)
    lam_away = max(0.05, base_away_xg * matchup.away_xg_modifier * matchup.home_defense_modifier)
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    markov_matrix, markov_source, transition_coverage = _load_markov_matrix(paths, simulation_mode)
    home_goals, away_goals = [], []
    home_xg_proxy, away_xg_proxy = [], []
    home_late_goal, away_late_goal = 0, 0
    possessions_base = int(get_parameter("monte_carlo_default_possessions", 55))
    possessions = max(20, int(possessions_base + 20 * (home.tempo + away.tempo) / 2))
    for _ in range(n_simulations):
        hxg = axg = 0.0
        for _ in range(possessions // 2):
            hxg += simulate_possession(home, away, rng, base_matrix=markov_matrix)["xg_proxy"]
            axg += simulate_possession(away, home, rng, base_matrix=markov_matrix)["xg_proxy"]
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
    hw = sum(h > a for h, a in zip(home_goals, away_goals, strict=False)) / n
    dr = sum(h == a for h, a in zip(home_goals, away_goals, strict=False)) / n
    aw = sum(h < a for h, a in zip(home_goals, away_goals, strict=False)) / n
    return SimulationResult(
        home_team=home.team_name,
        away_team=away.team_name,
        home_win_probability=hw,
        draw_probability=dr,
        away_win_probability=aw,
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
        n_simulations=n_simulations,
        random_seed=seed,
        home_goals_ci=_ci(home_goals),
        away_goals_ci=_ci(away_goals),
        home_xg_ci=_ci_float(home_xg_proxy),
        away_xg_ci=_ci_float(away_xg_proxy),
        result_probability_standard_error={
            "home_win": float((hw * (1 - hw) / n) ** 0.5),
            "draw": float((dr * (1 - dr) / n) ** 0.5),
            "away_win": float((aw * (1 - aw) / n) ** 0.5),
        },
        simulation_mode=simulation_mode,
        markov_source=markov_source,
        markov_reliability_score=1.0 if markov_source == "global_calibrated" else 0.35,
        transition_coverage=transition_coverage,
    )


def _late_goal_probability(state: TacticalState, fatigue: dict) -> float:
    return max(0.02, min(0.55, 0.08 + 0.25 * state.late_goal_threat - 0.12 * fatigue["after_70_attacking_drop"]))


def _ci(values: list[int]) -> dict:
    return {
        "p5": float(np.percentile(values, 5)),
        "p50": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
    }


def _ci_float(values: list[float]) -> dict:
    return {
        "p5": float(np.percentile(values, 5)),
        "p50": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
    }


def _load_markov_matrix(
    paths: ProjectPaths | None,
    simulation_mode: str,
) -> tuple[dict[MatchState, dict[MatchState, float]] | None, str, dict]:
    if simulation_mode != "calibrated" or paths is None:
        return None, "heuristic_fallback", {"rows": 0}
    matrix_path = paths.features / "markov_transition_matrix_global.parquet"
    if not matrix_path.exists():
        return None, "heuristic_fallback", {"rows": 0}
    matrix_df = pl.read_parquet(matrix_path)
    rows: dict[MatchState, dict[MatchState, float]] = {}
    for row in matrix_df.to_dicts():
        try:
            from_state = MatchState(row["from_state"])
            to_state = MatchState(row["to_state"])
        except ValueError:
            continue
        rows.setdefault(from_state, {})[to_state] = float(row["probability"])
    if not rows:
        return None, "heuristic_fallback", {"rows": 0}
    return rows, "global_calibrated", {"rows": matrix_df.height, "states": len(rows)}
