from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from bucephalus.game.chemistry import calculate_chemistry
from bucephalus.game.lineups import validate_lineup
from bucephalus.game.models import Fixture, SimulationRun
from bucephalus.game.repository import GameRepository
from bucephalus.game.tactics import infer_tactical_baseline_from_lineup
from bucephalus.simulation.simulator import simulate_match
from bucephalus.utils.paths import ProjectPaths


class SimulationService:
    def __init__(self, repo: GameRepository, paths: ProjectPaths | None = None) -> None:
        self.repo = repo
        self.paths = paths or repo.paths

    def simulate_fixture(self, fixture_id: str, n_simulations: int = 1000, seed: int = 42, resolution_mode: str = "simulated") -> dict:
        fixture = self.repo.get("fixtures", fixture_id)
        if fixture is None:
            raise ValueError("fixture not found")
        return self.simulate_match(fixture["home_club_id"], fixture["away_club_id"], fixture_id, n_simulations, seed, resolution_mode)

    def simulate_match(self, home_club_id: str, away_club_id: str, fixture_id: str | None = None, n_simulations: int = 1000, seed: int = 42, resolution_mode: str = "simulated") -> dict:
        home_players = self._club_players(home_club_id)
        away_players = self._club_players(away_club_id)
        home_lineup = validate_lineup(home_players[:11], "4-3-3")
        away_lineup = validate_lineup(away_players[:11], "4-3-3")
        home_tactics = infer_tactical_baseline_from_lineup(home_players[:11], "4-3-3")
        away_tactics = infer_tactical_baseline_from_lineup(away_players[:11], "4-3-3")
        home_chem = calculate_chemistry(home_players[:11], "4-3-3")
        away_chem = calculate_chemistry(away_players[:11], "4-3-3")
        sim = simulate_match(n_simulations=n_simulations, random_seed=seed, paths=self.paths, simulation_mode="calibrated")
        confidence = "medium" if sim.get("reliability_score", 0) >= 0.5 else "low"
        payload = {
            "fixture_id": fixture_id,
            "resolution_source": resolution_mode,
            "model_confidence": confidence,
            "win_draw_loss_probabilities": {
                "home": sim["home_win_probability"],
                "draw": sim["draw_probability"],
                "away": sim["away_win_probability"],
            },
            "expected_goals": {"home": sim["expected_home_goals"], "away": sim["expected_away_goals"]},
            "expected_xg": {"home": sim.get("expected_home_xg_proxy"), "away": sim.get("expected_away_xg_proxy")},
            "top_scorelines": sim.get("top_scorelines", []),
            "lineups": {"home": home_lineup, "away": away_lineup},
            "chemistry": {"home": home_chem, "away": away_chem},
            "tactical_drivers": {"home": home_tactics, "away": away_tactics},
            "chemistry_drivers": {"home": home_chem["warnings"], "away": away_chem["warnings"]},
            "lineup_warnings": home_lineup["warnings"] + away_lineup["warnings"],
            "model_status_used": _model_status(self.paths),
            "warnings": sim.get("warnings", []) + home_tactics["warnings"] + away_tactics["warnings"],
        }
        report_id = fixture_id or str(uuid4())
        json_path = self.paths.outputs / "game" / f"match_report_{report_id}.json"
        md_path = self.paths.outputs / "game" / f"match_report_{report_id}.md"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        md_path.write_text(_match_markdown(payload), encoding="utf-8")
        payload["report_json"] = str(json_path)
        payload["report_markdown"] = str(md_path)
        self.repo.add("simulation_runs", SimulationRun(id=str(uuid4()), fixture_id=fixture_id, payload=payload))
        self.repo.audit("simulate_match", {"fixture_id": fixture_id, "report": str(json_path)})
        return payload

    def create_fixture(self, league_id: str, home_club_id: str, away_club_id: str) -> dict:
        payload = self.repo.add("fixtures", Fixture(id=str(uuid4()), league_id=league_id, home_club_id=home_club_id, away_club_id=away_club_id))
        self.repo.audit("create_fixture", payload)
        return payload

    def _club_players(self, club_id: str) -> list[dict]:
        player_ids = [row["player_id"] for row in self.repo.list("squad_players") if row["club_id"] == club_id]
        return [p for pid in player_ids if (p := self.repo.get("players", pid))]


def _model_status(paths: ProjectPaths) -> dict:
    path = paths.evaluation_outputs / "phase8_model_scorecard.json"
    if not path.exists():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8")).get("rows", [])
    return {row["component"]: row["status"] for row in rows}


def _match_markdown(payload: dict) -> str:
    probs = payload["win_draw_loss_probabilities"]
    xg = payload["expected_goals"]
    return (
        "# Bucephalus Match Report\n\n"
        f"resolution_source: {payload['resolution_source']}\n\n"
        f"model_confidence: {payload['model_confidence']}\n\n"
        f"Expected goals: home {xg['home']:.2f} - away {xg['away']:.2f}\n\n"
        f"Probabilities: home {probs['home']:.3f}, draw {probs['draw']:.3f}, away {probs['away']:.3f}\n\n"
        f"Warnings: {payload['warnings']}\n"
    )
