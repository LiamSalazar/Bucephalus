from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from bucephalus.config import settings
from bucephalus.tactics.matchup import evaluate_matchup
from bucephalus.tactics.schemas import TacticalState
from bucephalus.tactics.tactical_sliders import apply_tactical_sliders
from bucephalus.utils.paths import ProjectPaths


def load_team_state(team: str | None, paths: ProjectPaths | None = None, index: int = 0) -> TacticalState:
    paths = paths or settings.paths
    df = pl.read_parquet(paths.features / "tactical_engine_inputs.parquet")
    if team:
        filtered = df.filter(pl.col("team_name").str.to_lowercase().str.contains(team.lower()))
        if not filtered.is_empty():
            return TacticalState.from_team_baseline(filtered.row(0, named=True))
    return TacticalState.from_team_baseline(df.sort("team_name").row(index, named=True))


def auto_pick_teams(paths: ProjectPaths | None = None) -> tuple[TacticalState, TacticalState]:
    paths = paths or settings.paths
    df = pl.read_parquet(paths.features / "tactical_engine_inputs.parquet").sort(["sample_size_warning", "team_name"])
    if df.height < 2:
        raise ValueError("Need at least two tactical teams")
    return TacticalState.from_team_baseline(df.row(0, named=True)), TacticalState.from_team_baseline(df.row(1, named=True))


def run_tactical_scenario(home: TacticalState, away: TacticalState, home_deltas: dict | None = None, away_deltas: dict | None = None, output_path: Path | None = None) -> dict:
    home_adj, home_report = apply_tactical_sliders(home, **(home_deltas or {}))
    away_adj, away_report = apply_tactical_sliders(away, **(away_deltas or {}))
    matchup = evaluate_matchup(home_adj, away_adj)
    payload = {
        "home_team": home.team_name,
        "away_team": away.team_name,
        "home_adjustments": home_report.model_dump(mode="json"),
        "away_adjustments": away_report.model_dump(mode="json"),
        "matchup": matchup.model_dump(mode="json"),
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
