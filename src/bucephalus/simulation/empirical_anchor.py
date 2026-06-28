from __future__ import annotations

import polars as pl

from bucephalus.calibration.parameter_registry import get_parameter
from bucephalus.tactics.schemas import TacticalState
from bucephalus.utils.paths import ProjectPaths


def build_empirical_anchor(home: TacticalState, away: TacticalState, paths: ProjectPaths) -> dict:
    warnings = []
    source = "heuristic_fallback"
    reliability = min(home.reliability_score, away.reliability_score)
    base_home_xg = float(get_parameter("heuristic_base_home_xg", 1.15))
    base_away_xg = float(get_parameter("heuristic_base_away_xg", 1.0))
    base_home_goals = base_home_xg
    base_away_goals = base_away_xg
    team_features_path = paths.features / "team_match_features.parquet"
    if team_features_path.exists():
        tm = pl.read_parquet(team_features_path)
        home_rows = tm.filter(pl.col("bucephalus_team_id") == home.team_id)
        away_rows = tm.filter(pl.col("bucephalus_team_id") == away.team_id)
        if not home_rows.is_empty() and not away_rows.is_empty():
            base_home_xg = float(home_rows["xg_for"].mean() or base_home_xg)
            base_away_xg = float(away_rows["xg_for"].mean() or base_away_xg)
            base_home_goals = float(home_rows["goals_for"].mean() or base_home_goals)
            base_away_goals = float(away_rows["goals_for"].mean() or base_away_goals)
            source = "team_match_empirical_means"
            reliability = max(reliability, min(1.0, (home_rows.height + away_rows.height) / 20))
        else:
            warnings.append("team-specific empirical rows missing; using heuristic fallback")
    else:
        warnings.append("team_match_features missing; using heuristic fallback")
    return {
        "base_home_xg": max(0.05, base_home_xg),
        "base_away_xg": max(0.05, base_away_xg),
        "base_home_goals": max(0.05, base_home_goals),
        "base_away_goals": max(0.05, base_away_goals),
        "anchor_source": source,
        "reliability_score": float(reliability),
        "warnings": warnings,
    }
