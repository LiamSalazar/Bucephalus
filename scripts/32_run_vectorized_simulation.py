from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.simulation.vectorized_monte_carlo import run_vectorized_simulation_benchmark
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--n-simulations", type=int, default=10000)
    args = parser.parse_args()
    print(run_vectorized_simulation_benchmark(ProjectPaths(data_root=args.data_root), n_simulations=args.n_simulations))


if __name__ == "__main__":
    main()
