from __future__ import annotations

import json
import time
from datetime import UTC, datetime

import numpy as np

from bucephalus.simulation.simulator import simulate_match
from bucephalus.simulation.uncertainty_propagation import combine_uncertainty
from bucephalus.utils.paths import ProjectPaths


def run_vectorized_simulation_benchmark(paths: ProjectPaths, n_simulations: int = 10000, seed: int = 42, home_team: str | None = None, away_team: str | None = None) -> dict:
    paths.ensure()
    if (paths.features / "tactical_engine_inputs.parquet").exists():
        loop = simulate_match(home_team, away_team, n_simulations=500, random_seed=seed, paths=paths, simulation_mode="calibrated")
    else:
        loop = {
            "expected_home_goals": 1.35,
            "expected_away_goals": 1.10,
            "home_win_probability": 0.42,
            "draw_probability": 0.27,
            "away_win_probability": 0.31,
            "model_uncertainty_std": 0.05,
            "uncertainty_sources": ["heuristic_minimal_test_fallback"],
        }
    home_lambda = max(0.05, float(loop["expected_home_goals"]))
    away_lambda = max(0.05, float(loop["expected_away_goals"]))
    rng = np.random.default_rng(seed)
    start = time.perf_counter()
    model_noise = rng.normal(0, float(loop.get("model_uncertainty_std") or 0.05), size=n_simulations)
    home = rng.poisson(np.clip(home_lambda + model_noise, 0.05, 6.0))
    away = rng.poisson(np.clip(away_lambda - model_noise, 0.05, 6.0))
    seconds = time.perf_counter() - start
    model_uncertainty_std = float(loop.get("model_uncertainty_std") or 0.05)
    parameter_uncertainty_std = float(loop.get("parameter_uncertainty_std") or 0.03)
    simulation_uncertainty_std = float(np.std(home - away) / max(n_simulations ** 0.5, 1.0))
    combined_std = combine_uncertainty(model_uncertainty_std, parameter_uncertainty_std, simulation_uncertainty_std)
    total_goals = home + away
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "n_simulations": n_simulations,
        "seconds": seconds,
        "simulations_per_second": n_simulations / max(seconds, 1e-9),
        "home_win_probability": float(np.mean(home > away)),
        "draw_probability": float(np.mean(home == away)),
        "away_win_probability": float(np.mean(home < away)),
        "expected_home_goals": float(home.mean()),
        "expected_away_goals": float(away.mean()),
        "loop_expected_home_goals": loop["expected_home_goals"],
        "loop_expected_away_goals": loop["expected_away_goals"],
        "expected_goals_difference": float(abs(home.mean() - loop["expected_home_goals"]) + abs(away.mean() - loop["expected_away_goals"])),
        "home_probability_difference": float(abs(np.mean(home > away) - loop["home_win_probability"])),
        "draw_probability_difference": float(abs(np.mean(home == away) - loop["draw_probability"])),
        "away_probability_difference": float(abs(np.mean(home < away) - loop["away_win_probability"])),
        "speedup_proxy_vs_loop_500": float((n_simulations / max(seconds, 1e-9)) / 500),
        "memory_estimate_mb": float((home.nbytes + away.nbytes + model_noise.nbytes) / 1_000_000),
        "uncertainty_sources": sorted(set([*loop.get("uncertainty_sources", []), "model_uncertainty", "parameter_uncertainty", "simulation_uncertainty", "data_uncertainty"])),
        "model_uncertainty_std": model_uncertainty_std,
        "parameter_uncertainty_std": parameter_uncertainty_std,
        "simulation_uncertainty_std": simulation_uncertainty_std,
        "data_uncertainty_flag": bool(loop.get("data_uncertainty_flag", True)),
        "combined_interval": {
            "p5": float(np.percentile(total_goals, 5) - combined_std),
            "p50": float(np.percentile(total_goals, 50)),
            "p95": float(np.percentile(total_goals, 95) + combined_std),
        },
        "mode": "numpy_vectorized_empirical_anchor_poisson",
    }
    (paths.quality_outputs / "vectorized_simulation_benchmark.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (paths.simulations_outputs / "vectorized_match_simulation.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
