from __future__ import annotations

from bucephalus.game.simulation_service import SimulationService

from tests.game_helpers import seed_game


def test_simulation_service_generates_report(monkeypatch, tmp_path):
    repo, league, club_a, club_b = seed_game(tmp_path)

    def fake_simulate_match(**kwargs):
        return {
            "home_win_probability": 0.45,
            "draw_probability": 0.25,
            "away_win_probability": 0.30,
            "expected_home_goals": 1.6,
            "expected_away_goals": 1.2,
            "expected_home_xg_proxy": 1.5,
            "expected_away_xg_proxy": 1.1,
            "top_scorelines": [{"scoreline": "1-1", "probability": 0.12}],
            "reliability_score": 0.6,
            "warnings": [],
        }

    monkeypatch.setattr("bucephalus.game.simulation_service.simulate_match", fake_simulate_match)
    service = SimulationService(repo)
    fixture = service.create_fixture(league["id"], club_a["id"], club_b["id"])
    result = service.simulate_fixture(fixture["id"], n_simulations=20)

    assert result["win_draw_loss_probabilities"]["home"] == 0.45
    assert repo.paths.outputs.joinpath("game", f"match_report_{fixture['id']}.json").exists()
