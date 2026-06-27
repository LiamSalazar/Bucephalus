from __future__ import annotations

import json

from bucephalus.config import settings
from bucephalus.simulation.monte_carlo import simulate_states
from bucephalus.simulation.scenario import load_team_state
from bucephalus.tactics.tactical_sliders import apply_tactical_sliders
from bucephalus.utils.paths import ProjectPaths


def simulate_match(home_team: str | None = None, away_team: str | None = None, home_sliders: dict | None = None, away_sliders: dict | None = None, n_simulations: int = 1000, random_seed: int = 42, paths: ProjectPaths | None = None) -> dict:
    paths = paths or settings.paths
    home = load_team_state(home_team, paths, index=0)
    away = load_team_state(away_team, paths, index=1)
    home, home_report = apply_tactical_sliders(home, **(home_sliders or {}))
    away, away_report = apply_tactical_sliders(away, **(away_sliders or {}))
    result = simulate_states(home, away, n_simulations=n_simulations, seed=random_seed)
    payload = result.model_dump(mode="json")
    payload["home_slider_warnings"] = home_report.warnings
    payload["away_slider_warnings"] = away_report.warnings
    output = paths.simulations_outputs / "latest_match_simulation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
