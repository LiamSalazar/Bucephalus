from __future__ import annotations

import json

from bucephalus.game.live_data.mock_provider import write_provider_health_report
from bucephalus.game.lineups import LineupService
from bucephalus.game.simulation_service import SimulationService
from bucephalus.lab.scenarios import LabScenarioService

from tests.game_helpers import TEAM_A, TEAM_B, seed_game


def test_phase9_smoke_flow(monkeypatch, tmp_path):
    repo, league, club_a, club_b = seed_game(tmp_path)
    LineupService(repo).create_lineup(club_a["id"], "4-3-3", TEAM_A)
    LineupService(repo).create_lineup(club_b["id"], "4-3-3", TEAM_B)
    write_provider_health_report(repo.paths)

    def fake_simulate_match(**kwargs):
        return {
            "home_win_probability": 0.4,
            "draw_probability": 0.3,
            "away_win_probability": 0.3,
            "expected_home_goals": 1.4,
            "expected_away_goals": 1.2,
            "expected_home_xg_proxy": 1.3,
            "expected_away_xg_proxy": 1.1,
            "top_scorelines": [],
            "reliability_score": 0.55,
            "warnings": [],
        }

    monkeypatch.setattr("bucephalus.game.simulation_service.simulate_match", fake_simulate_match)
    service = SimulationService(repo)
    fixture = service.create_fixture(league["id"], club_a["id"], club_b["id"])
    result = service.simulate_fixture(fixture["id"], n_simulations=10)
    lab = LabScenarioService(repo).run_scenario(club_a["id"], club_b["id"])

    state = json.loads(repo.path.read_text(encoding="utf-8"))
    assert result["resolution_source"] == "simulated"
    assert lab["mode"] == "lab"
    assert len(state["simulation_runs"]) >= 2
