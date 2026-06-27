from __future__ import annotations

from bucephalus.data.download_statsbomb import download_sample
from bucephalus.data.entity_resolution import build_master_entities
from bucephalus.data.process_statsbomb import process_raw_to_parquet
from bucephalus.features.feature_store import build_feature_store
from bucephalus.simulation.scenario import auto_pick_teams
from bucephalus.simulation.simulator import simulate_match
from bucephalus.tactics.style_profiles import build_tactical_engine_inputs
from bucephalus.utils.paths import ProjectPaths


def test_scenario_simulates_from_tactical_inputs_and_sliders_change(tmp_path) -> None:
    paths = ProjectPaths(data_root=tmp_path / "data")
    download_sample(paths=paths, max_matches=2, force_fallback=True)
    process_raw_to_parquet(paths)
    build_master_entities(paths)
    build_feature_store(paths)
    build_tactical_engine_inputs(paths)
    home, away = auto_pick_teams(paths)
    base = simulate_match(home.team_name, away.team_name, n_simulations=100, random_seed=7, paths=paths)
    changed = simulate_match(home.team_name, away.team_name, home_sliders={"pressing_delta": 0.3}, n_simulations=100, random_seed=7, paths=paths)
    assert base["key_tactical_drivers"]
    assert changed["home_fatigue_risk"] >= base["home_fatigue_risk"]
