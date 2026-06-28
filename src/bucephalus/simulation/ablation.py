from __future__ import annotations

import csv
import json
from datetime import UTC, datetime

from bucephalus.simulation.simulator import simulate_match
from bucephalus.utils.paths import ProjectPaths

ABLATIONS = [
    ("baseline_only", {}),
    ("baseline_pressure", {"pressing_delta": 0.2}),
    ("baseline_fatigue", {"tempo_delta": 0.2}),
    ("baseline_transition", {"transition_delta": 0.2}),
    ("baseline_full_tactical", {"pressing_delta": 0.2, "tempo_delta": 0.1, "transition_delta": 0.1}),
    ("baseline_markov", {}),
    ("full_calibrated_simulation", {"pressing_delta": 0.1}),
]


def run_ablation_study(paths: ProjectPaths, n_simulations: int = 150) -> dict:
    rows = []
    for name, sliders in ABLATIONS:
        mode = "calibrated" if "calibrated" in name or name != "baseline_only" else "heuristic"
        sim = simulate_match(None, None, home_sliders=sliders, n_simulations=n_simulations, random_seed=42, paths=paths, simulation_mode=mode)
        rows.append({
            "ablation": name,
            "simulation_mode": sim["simulation_mode"],
            "home_win_probability": sim["home_win_probability"],
            "draw_probability": sim["draw_probability"],
            "away_win_probability": sim["away_win_probability"],
            "expected_home_goals": sim["expected_home_goals"],
            "expected_away_goals": sim["expected_away_goals"],
            "reliability_score": sim["reliability_score"],
        })
    csv_path = paths.evaluation_outputs / "ablation_study.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    payload = {"generated_at": datetime.now(UTC).isoformat(), "ablations": [r["ablation"] for r in rows], "rows": len(rows)}
    (paths.evaluation_outputs / "ablation_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
