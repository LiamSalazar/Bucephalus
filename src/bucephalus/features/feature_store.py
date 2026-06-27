from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus import __version__
from bucephalus.config import settings
from bucephalus.features.match_features import build_match_features
from bucephalus.features.player_features import build_player_match_features
from bucephalus.features.rolling import rolling_prior_features
from bucephalus.features.schemas import MODEL_EXCLUDED_COLUMNS
from bucephalus.features.tactical_proxies import build_tactical_team_profiles
from bucephalus.features.team_features import build_team_match_features
from bucephalus.utils.paths import ProjectPaths


def build_feature_store(paths: ProjectPaths | None = None) -> dict:
    paths = paths or settings.paths
    paths.ensure()
    matches = _read(paths.processed / "matches.parquet")
    events = _read(paths.processed / "events.parquet")
    three_sixty = _read(paths.processed / "three_sixty.parquet")
    master_matches = _read(paths.processed / "master_matches.parquet")
    master_teams = _read(paths.processed / "master_teams.parquet")
    master_players = _read(paths.processed / "master_players.parquet")

    match_features = build_match_features(matches, events, three_sixty, master_matches)
    team_match = build_team_match_features(matches, events, master_matches, master_teams)
    player_match = build_player_match_features(events, matches, master_matches, master_players, master_teams)
    team_rolling = rolling_prior_features(
        team_match, "bucephalus_team_id", "match_date",
        ["goals_for", "goals_against", "xg_for", "xg_against", "shots_for", "shots_against", "possession_proxy", "pressing_proxy", "directness_proxy", "transition_proxy", "goals_after_70_for", "goals_after_70_against"],
        [3, 5, 10], "team",
    )
    player_rolling = rolling_prior_features(
        player_match, "bucephalus_player_id", "match_date",
        ["shots", "xg", "passes", "pressures", "events_count"], [3, 5, 10], "player",
    )
    tactical = build_tactical_team_profiles(team_match)
    model_matches = _model_dataset_matches(match_features, team_rolling, team_match)
    model_team = _model_dataset_team_matches(team_match, team_rolling)

    tables = {
        "match_features": match_features,
        "team_match_features": team_match,
        "player_match_features": player_match,
        "team_rolling_features": team_rolling,
        "player_rolling_features": player_rolling,
        "tactical_team_profiles": tactical,
        "model_dataset_matches": model_matches,
        "model_dataset_team_matches": model_team,
    }
    for name, df in tables.items():
        df.write_parquet(paths.features / f"{name}.parquet")
    manifest = _write_manifest(paths, tables)
    return manifest


def _model_dataset_matches(match_features: pl.DataFrame, team_rolling: pl.DataFrame, team_match: pl.DataFrame) -> pl.DataFrame:
    if match_features.is_empty() or team_rolling.is_empty():
        return pl.DataFrame()
    ids = team_match.select("statsbomb_match_id", "team_id", "bucephalus_team_id", "is_home")
    rolling = team_rolling.join(ids, on=["statsbomb_match_id", "bucephalus_team_id"], how="left")
    home = rolling.filter(pl.col("is_home")).drop(["is_home", "team_id"]).rename({c: f"home_{c}" for c in rolling.columns if c.startswith("rolling_") or c == "historical_matches_available"})
    away = rolling.filter(~pl.col("is_home")).drop(["is_home", "team_id"]).rename({c: f"away_{c}" for c in rolling.columns if c.startswith("rolling_") or c == "historical_matches_available"})
    out = match_features.join(home, on="statsbomb_match_id", how="left").join(away, on="statsbomb_match_id", how="left", suffix="_awayrow")
    for col in list(out.columns):
        if col.startswith("home_rolling_") and col.replace("home_", "away_") in out.columns:
            out = out.with_columns((pl.col(col) - pl.col(col.replace("home_", "away_"))).alias(col.replace("home_", "diff_")))
    return out.sort("match_date")


def _model_dataset_team_matches(team_match: pl.DataFrame, team_rolling: pl.DataFrame) -> pl.DataFrame:
    if team_match.is_empty():
        return pl.DataFrame()
    return team_match.join(team_rolling, on=["statsbomb_match_id", "bucephalus_team_id"], how="left").sort("match_date")


def _write_manifest(paths: ProjectPaths, tables: dict[str, pl.DataFrame]) -> dict:
    warnings = []
    if tables["match_features"].height < 50:
        warnings.append("small dataset: baseline models may be skipped or unstable")
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "rows_by_table": {name: df.height for name, df in tables.items()},
        "feature_tables": sorted(tables),
        "feature_groups": ["match", "team_match", "player_match", "rolling_prior", "tactical_proxy", "model_dataset"],
        "leakage_policy": "model datasets use rolling features generated before the current match only",
        "warnings": warnings,
        "data_coverage": {
            "matches": tables["match_features"].height,
            "team_matches": tables["team_match_features"].height,
            "player_matches": tables["player_match_features"].height,
        },
        "target_columns": ["home_score", "away_score", "result_home_win", "result_draw", "result_away_win", "goals_for", "xg_for"],
        "excluded_from_training_columns": MODEL_EXCLUDED_COLUMNS,
        "version": __version__,
    }
    (paths.features / "feature_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _read(path) -> pl.DataFrame:
    return pl.read_parquet(path) if path.exists() else pl.DataFrame()
