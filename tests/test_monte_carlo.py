from __future__ import annotations

from tests.test_tactical_sliders import _state
from bucephalus.simulation.monte_carlo import simulate_states


def test_monte_carlo_probabilities_and_seed_reproducibility() -> None:
    a, b = _state(), _state().model_copy(update={"team_name": "B"})
    r1 = simulate_states(a, b, 100, 42)
    r2 = simulate_states(a, b, 100, 42)
    total = r1.home_win_probability + r1.draw_probability + r1.away_win_probability
    assert abs(total - 1) < 1e-9
    assert r1.expected_home_goals >= 0
    assert r1.top_scorelines
    assert r1 == r2
