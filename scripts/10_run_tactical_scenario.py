from __future__ import annotations

import argparse
from pathlib import Path

from bucephalus.simulation.scenario import auto_pick_teams, load_team_state, run_tactical_scenario
from bucephalus.utils.paths import ProjectPaths


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home-team")
    parser.add_argument("--away-team")
    parser.add_argument("--auto-pick-teams", action="store_true")
    parser.add_argument("--home-pressing-delta", type=float, default=0.0)
    parser.add_argument("--home-line-height-delta", type=float, default=0.0)
    parser.add_argument("--home-tempo-delta", type=float, default=0.0)
    parser.add_argument("--away-transition-delta", type=float, default=0.0)
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    paths = ProjectPaths(data_root=args.data_root)
    if args.auto_pick_teams:
        home, away = auto_pick_teams(paths)
    else:
        home = load_team_state(args.home_team, paths, 0)
        away = load_team_state(args.away_team, paths, 1)
    payload = run_tactical_scenario(
        home,
        away,
        home_deltas={
            "pressing_delta": args.home_pressing_delta,
            "line_height_delta": args.home_line_height_delta,
            "tempo_delta": args.home_tempo_delta,
        },
        away_deltas={"transition_delta": args.away_transition_delta},
        output_path=paths.simulations_outputs / "tactical_scenario_report.json",
    )
    print(payload["matchup"]["explanation_bullets"])


if __name__ == "__main__":
    main()
