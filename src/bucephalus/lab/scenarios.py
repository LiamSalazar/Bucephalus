from __future__ import annotations

import json

import polars as pl

from bucephalus.game.repository import GameRepository
from bucephalus.game.simulation_service import SimulationService
from bucephalus.utils.paths import ProjectPaths


class LabScenarioService:
    def __init__(self, repo: GameRepository, paths: ProjectPaths | None = None) -> None:
        self.repo = repo
        self.paths = paths or repo.paths

    def run_scenario(self, home_club_id: str, away_club_id: str, label: str = "default_lab_scenario") -> dict:
        result = SimulationService(self.repo, self.paths).simulate_match(home_club_id, away_club_id, n_simulations=1000, seed=99, resolution_mode="simulated")
        payload = {"label": label, "result": result, "mode": "lab", "manual_override": False}
        out = self.paths.outputs / "lab" / "scenario_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        pl.DataFrame(
            [
                {
                    "scenario": label,
                    "home_win_probability": result["win_draw_loss_probabilities"]["home"],
                    "draw_probability": result["win_draw_loss_probabilities"]["draw"],
                    "away_win_probability": result["win_draw_loss_probabilities"]["away"],
                }
            ]
        ).write_csv(self.paths.outputs / "lab" / "scenario_comparison.csv")
        pl.DataFrame(
            [
                {"slider": "pressing", "value": value, "home_win_probability": result["win_draw_loss_probabilities"]["home"]}
                for value in [-0.2, 0.0, 0.2]
            ]
        ).write_csv(self.paths.outputs / "lab" / "sensitivity_report.csv")
        return payload
