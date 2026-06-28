from __future__ import annotations

from bucephalus.simulation.vectorized_monte_carlo import run_vectorized_simulation_benchmark
from bucephalus.utils.paths import ProjectPaths


def test_vectorized_monte_carlo_probabilities(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    result = run_vectorized_simulation_benchmark(paths, n_simulations=1000)
    total = result["home_win_probability"] + result["draw_probability"] + result["away_win_probability"]
    assert abs(total - 1) < 1e-9
