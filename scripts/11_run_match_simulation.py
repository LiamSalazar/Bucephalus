from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.simulation.scenario import auto_pick_teams
from bucephalus.simulation.simulator import simulate_match
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home-team")
    parser.add_argument("--away-team")
    parser.add_argument("--auto-pick-teams", action="store_true")
    parser.add_argument("--n-simulations", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    home_team, away_team = args.home_team, args.away_team
    if args.auto_pick_teams:
        home, away = auto_pick_teams(paths)
        home_team, away_team = home.team_name, away.team_name
    result = simulate_match(home_team, away_team, n_simulations=args.n_simulations, random_seed=args.seed, paths=paths)
    print(result)


if __name__ == "__main__":
    main()
