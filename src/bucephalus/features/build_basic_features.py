from __future__ import annotations

import logging

import polars as pl

from bucephalus.config import settings
from bucephalus.utils.paths import ProjectPaths

LOGGER = logging.getLogger(__name__)


def build_basic_features(paths: ProjectPaths | None = None) -> None:
    paths = paths or settings.paths
    paths.ensure()
    events_path = paths.processed / "events.parquet"
    matches_path = paths.processed / "matches.parquet"
    if not events_path.exists():
        LOGGER.warning("No events.parquet found; skipping basic features.")
        return
    events = pl.read_parquet(events_path)
    matches = pl.read_parquet(matches_path) if matches_path.exists() else pl.DataFrame()
    team_profiles = build_team_profiles(events, matches)
    player_match = build_player_match_basic(events)
    team_profiles.write_parquet(paths.features / "team_profiles.parquet")
    player_match.write_parquet(paths.features / "player_match_basic.parquet")
    LOGGER.info("Feature tables written to %s.", paths.features)


def build_team_profiles(events: pl.DataFrame, matches: pl.DataFrame | None = None) -> pl.DataFrame:
    if events.is_empty():
        return pl.DataFrame()
    team_match = (
        events.group_by(["team_id", "team_name", "match_id"])
        .agg(
            pl.len().alias("events"),
            (pl.col("event_type") == "Shot").sum().alias("shots"),
            (pl.col("event_type") == "Pass").sum().alias("passes"),
            (pl.col("event_type") == "Pressure").sum().alias("pressures"),
            pl.col("shot_xg").sum().alias("xg"),
            ((pl.col("event_type") == "Shot") & (pl.col("shot_type") == "Free Kick")).sum().alias("set_piece_shots"),
            (pl.col("location_y") < 26.6667).sum().alias("left_side_events"),
            ((pl.col("location_y") >= 26.6667) & (pl.col("location_y") <= 53.3333)).sum().alias("central_events"),
            (pl.col("location_y") > 53.3333).sum().alias("right_side_events"),
            (pl.col("pass_end_x") - pl.col("location_x")).mean().alias("avg_pass_progression_x"),
        )
        .with_columns((pl.col("passes") / pl.col("events")).alias("possession_proxy"))
    )
    return team_match.group_by(["team_id", "team_name"]).agg(
        pl.col("match_id").n_unique().alias("matches_count"),
        pl.col("possession_proxy").mean().alias("avg_possession_proxy"),
        pl.col("shots").mean().alias("avg_shots"),
        pl.col("xg").mean().alias("avg_xg"),
        pl.col("passes").mean().alias("avg_passes"),
        pl.col("pressures").mean().alias("avg_pressures"),
        pl.col("avg_pass_progression_x").mean().alias("avg_directness_proxy"),
        pl.col("set_piece_shots").mean().alias("avg_set_piece_shots"),
        pl.col("left_side_events").mean().alias("avg_left_side_events"),
        pl.col("right_side_events").mean().alias("avg_right_side_events"),
        pl.col("central_events").mean().alias("avg_central_events"),
    )


def build_player_match_basic(events: pl.DataFrame) -> pl.DataFrame:
    if events.is_empty():
        return pl.DataFrame()
    return events.drop_nulls("player_id").group_by(
        ["match_id", "team_id", "team_name", "player_id", "player_name", "position_name"]
    ).agg(
        pl.len().alias("events"),
        (pl.col("event_type") == "Shot").sum().alias("shots"),
        pl.col("shot_xg").sum().alias("xg"),
        (pl.col("event_type") == "Pass").sum().alias("passes"),
        (pl.col("event_type") == "Pressure").sum().alias("pressures"),
        (pl.col("event_type") == "Duel").sum().alias("duels"),
        (pl.col("event_type") == "Goal Keeper").sum().alias("goalkeeper_actions"),
    )
