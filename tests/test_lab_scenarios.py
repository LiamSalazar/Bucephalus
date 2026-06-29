from __future__ import annotations

from bucephalus.lab.scenarios import LabScenarioService

from tests.game_helpers import seed_game


def test_lab_scenario_writes_outputs(monkeypatch, tmp_path):
    repo, _, club_a, club_b = seed_game(tmp_path)

    def fake_simulate_match(self, home_club_id, away_club_id, **kwargs):
        return {
            "win_draw_loss_probabilities": {"home": 0.5, "draw": 0.25, "away": 0.25},
            "expected_goals": {"home": 1.8, "away": 1.1},
            "warnings": [],
        }

    monkeypatch.setattr("bucephalus.lab.scenarios.SimulationService.simulate_match", fake_simulate_match)
    payload = LabScenarioService(repo).run_scenario(club_a["id"], club_b["id"])

    assert payload["mode"] == "lab"
    assert repo.paths.outputs.joinpath("lab", "scenario_report.json").exists()
    assert repo.paths.outputs.joinpath("lab", "scenario_comparison.csv").exists()
