from __future__ import annotations

from bucephalus.simulation.simulator import simulate_match


def test_calibrated_simulation_outputs_ci_and_anchor(tmp_path):
    from tests.test_scenario_simulation import test_scenario_simulates_from_tactical_inputs_and_sliders_change

    test_scenario_simulates_from_tactical_inputs_and_sliders_change(tmp_path)
    from bucephalus.utils.paths import ProjectPaths

    paths = ProjectPaths(data_root=tmp_path / "data")
    result = simulate_match(None, None, n_simulations=50, random_seed=1, paths=paths, simulation_mode="calibrated")
    assert result["simulation_mode"] == "calibrated"
    assert result["home_goals_ci"]["p5"] <= result["home_goals_ci"]["p50"] <= result["home_goals_ci"]["p95"]
    assert result["anchor_source"]
