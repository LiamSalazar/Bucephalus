from __future__ import annotations

import json
import time
from datetime import UTC, datetime

import numpy as np

from bucephalus.utils.paths import ProjectPaths


def run_vectorized_simulation_benchmark(paths: ProjectPaths, n_simulations: int = 10000, seed: int = 42) -> dict:
    paths.ensure()
    rng = np.random.default_rng(seed)
    start = time.perf_counter()
    home = rng.poisson(1.35, size=n_simulations)
    away = rng.poisson(1.10, size=n_simulations)
    seconds = time.perf_counter() - start
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "n_simulations": n_simulations,
        "seconds": seconds,
        "simulations_per_second": n_simulations / max(seconds, 1e-9),
        "home_win_probability": float(np.mean(home > away)),
        "draw_probability": float(np.mean(home == away)),
        "away_win_probability": float(np.mean(home < away)),
        "mode": "numpy_vectorized_poisson",
    }
    (paths.quality_outputs / "vectorized_simulation_benchmark.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
