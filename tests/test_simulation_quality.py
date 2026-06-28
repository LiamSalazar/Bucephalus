from __future__ import annotations

from bucephalus.simulation.monte_carlo import simulate_states
from bucephalus.tactics.schemas import TacticalState


def _state(name: str) -> TacticalState:
    return TacticalState.from_team_baseline(
        {
            "bucephalus_team_id": name,
            "team_name": name,
            "possession_baseline": 0.5,
            "pressing_baseline": 0.5,
            "directness_baseline": 0.5,
            "transition_baseline": 0.5,
            "width_baseline": 0.5,
            "centrality_baseline": 0.5,
            "set_piece_dependency_baseline": 0.3,
            "defensive_exposure_baseline": 0.4,
            "second_half_intensity_baseline": 0.5,
            "late_goal_for_baseline": 0.4,
            "reliability_score": 0.8,
        }
    )


def test_monte_carlo_uncertainty_and_seed_reproducibility():
    home, away = _state("h"), _state("a")
    one = simulate_states(home, away, n_simulations=200, seed=123)
    two = simulate_states(home, away, n_simulations=200, seed=123)
    assert one.home_win_probability == two.home_win_probability
    assert abs(one.home_win_probability + one.draw_probability + one.away_win_probability - 1) < 1e-9
    assert one.home_goals_ci["p5"] <= one.home_goals_ci["p50"] <= one.home_goals_ci["p95"]
    assert one.home_xg_ci["p5"] <= one.home_xg_ci["p50"] <= one.home_xg_ci["p95"]
    assert one.result_probability_standard_error["home_win"] >= 0
