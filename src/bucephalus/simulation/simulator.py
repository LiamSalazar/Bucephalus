from __future__ import annotations

import json

from bucephalus.config import settings
from bucephalus.simulation.empirical_anchor import build_empirical_anchor
from bucephalus.simulation.monte_carlo import simulate_states
from bucephalus.simulation.scenario import load_team_state
from bucephalus.tactics.tactical_sliders import apply_tactical_sliders
from bucephalus.utils.paths import ProjectPaths


def simulate_match(home_team: str | None = None, away_team: str | None = None, home_sliders: dict | None = None, away_sliders: dict | None = None, n_simulations: int = 1000, random_seed: int = 42, paths: ProjectPaths | None = None, simulation_mode: str = "heuristic") -> dict:
    paths = paths or settings.paths
    home = load_team_state(home_team, paths, index=0)
    away = load_team_state(away_team, paths, index=1)
    home, home_report = apply_tactical_sliders(home, **(home_sliders or {}))
    away, away_report = apply_tactical_sliders(away, **(away_sliders or {}))
    anchor = build_empirical_anchor(home, away, paths) if simulation_mode == "calibrated" else None
    result = simulate_states(home, away, n_simulations=n_simulations, seed=random_seed, anchor=anchor)
    payload = result.model_dump(mode="json")
    payload["simulation_mode"] = simulation_mode
    payload["anchor_source"] = anchor["anchor_source"] if anchor else "heuristic_state_formula"
    payload["calibrated_parameters_used"] = ["team_match_empirical_means"] if anchor and anchor["anchor_source"] != "heuristic_fallback" else []
    payload["heuristic_parameters_used"] = [] if anchor and anchor["anchor_source"] != "heuristic_fallback" else ["heuristic_base_xg", "tactical_proxy_modifiers"]
    payload["reliability_score"] = anchor["reliability_score"] if anchor else min(home.reliability_score, away.reliability_score)
    if anchor:
        payload["warnings"].extend(anchor["warnings"])
    payload["home_slider_warnings"] = home_report.warnings
    payload["away_slider_warnings"] = away_report.warnings
    output = paths.simulations_outputs / "latest_match_simulation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
