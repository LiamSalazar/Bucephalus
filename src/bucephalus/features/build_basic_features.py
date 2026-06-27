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
    teams_path = paths.processed / "master_teams.parquet"
    if not events_path.exists():
        LOGGER.warning("No events.parquet found; skipping basic features.")
        return
    events = pl.read_parquet(events_path)
    matches = pl.read_parquet(matches_path) if matches_path.exists() else pl.DataFrame()
    master_teams = pl.read_parquet(teams_path) if teams_path.exists() else pl.DataFrame()
    team_profiles = build_team_profiles_baseline(events, matches, master_teams)
    player_match = build_player_match_basic(events)
    team_profiles.write_parquet(paths.features / "team_profiles_baseline.parquet")
    # Compatibility alias for early notebooks/scripts.
    team_profiles.write_parquet(paths.features / "team_profiles.parquet")
    player_match.write_parquet(paths.features / "player_match_basic.parquet")
    LOGGER.info("Feature tables written to %s.", paths.features)


def build_team_profiles(events: pl.DataFrame, matches: pl.DataFrame | None = None) -> pl.DataFrame:
    return build_team_profiles_baseline(events, matches or pl.DataFrame(), pl.DataFrame())


def build_team_profiles_baseline(
    events: pl.DataFrame, matches: pl.DataFrame | None = None, master_teams: pl.DataFrame | None = None
) -> pl.DataFrame:
    if events.is_empty():
        return pl.DataFrame()
    events = _ensure_event_columns(events)
    matches = matches if matches is not None else pl.DataFrame()
    master_teams = master_teams if master_teams is not None else pl.DataFrame()

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
            ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome") == "Goal") & (pl.col("minute") >= 70)).sum().alias(
                "late_goals_for"
            ),
            (pl.col("period") == 2).sum().alias("second_half_events"),
            ((pl.col("event_type") == "Carry") & (pl.col("carry_end_x") > pl.col("location_x"))).sum().alias(
                "progressive_carries_proxy"
            ),
        )
        .with_columns(
            (pl.col("passes") / pl.max_horizontal(pl.col("events"), pl.lit(1))).alias("possession_proxy"),
            (pl.col("pressures") / pl.max_horizontal(pl.col("events"), pl.lit(1))).alias("pressing_proxy"),
            (pl.col("second_half_events") / pl.max_horizontal(pl.col("events"), pl.lit(1))).alias("second_half_event_share"),
            (pl.col("set_piece_shots") / pl.max_horizontal(pl.col("shots"), pl.lit(1))).alias("set_piece_shot_share"),
            (pl.col("left_side_events") / pl.max_horizontal(pl.col("events"), pl.lit(1))).alias("left_side_event_share"),
            (pl.col("right_side_events") / pl.max_horizontal(pl.col("events"), pl.lit(1))).alias("right_side_event_share"),
            (pl.col("central_events") / pl.max_horizontal(pl.col("events"), pl.lit(1))).alias("central_event_share"),
            (pl.col("progressive_carries_proxy") / pl.max_horizontal(pl.col("events"), pl.lit(1))).alias("transition_proxy"),
        )
    )
    against = _against_metrics(team_match)
    goals = _goals_for_against(matches)
    profile = (
        team_match.join(against, on=["match_id", "team_id"], how="left")
        .join(goals, on=["match_id", "team_id"], how="left")
        .group_by(["team_id", "team_name"])
        .agg(
            pl.col("match_id").n_unique().alias("matches_count"),
            pl.col("goals_for").mean().alias("avg_goals_for"),
            pl.col("goals_against").mean().alias("avg_goals_against"),
            pl.col("shots").mean().alias("avg_shots"),
            pl.col("shots_against").mean().alias("avg_shots_against"),
            pl.col("xg").mean().alias("avg_xg"),
            pl.col("xg_against").mean().alias("avg_xg_against"),
            pl.col("passes").mean().alias("avg_passes"),
            pl.col("pressures").mean().alias("avg_pressures"),
            pl.col("possession_proxy").mean().alias("possession_proxy"),
            pl.col("avg_pass_progression_x").mean().alias("directness_proxy"),
            pl.col("set_piece_shot_share").mean().alias("set_piece_shot_share"),
            pl.col("left_side_event_share").mean().alias("left_side_event_share"),
            pl.col("right_side_event_share").mean().alias("right_side_event_share"),
            pl.col("central_event_share").mean().alias("central_event_share"),
            pl.col("late_goals_for").mean().alias("late_goal_for_rate"),
            pl.col("late_goals_against").mean().alias("late_goal_against_rate"),
            pl.col("second_half_event_share").mean().alias("second_half_event_share"),
            pl.col("pressing_proxy").mean().alias("pressing_proxy"),
            pl.col("transition_proxy").mean().alias("transition_proxy"),
        )
        .with_columns(_coverage_expr().alias("data_coverage_score"))
    )
    if not master_teams.is_empty() and {"statsbomb_team_id", "bucephalus_team_id"}.issubset(master_teams.columns):
        profile = profile.join(
            master_teams.select(pl.col("statsbomb_team_id").alias("team_id"), "bucephalus_team_id"),
            on="team_id",
            how="left",
        )
    else:
        profile = profile.with_columns(pl.lit(None, dtype=pl.Utf8).alias("bucephalus_team_id"))
    return profile.select(
        "bucephalus_team_id",
        "team_id",
        "team_name",
        "matches_count",
        "avg_goals_for",
        "avg_goals_against",
        "avg_shots",
        "avg_shots_against",
        "avg_xg",
        "avg_xg_against",
        "avg_passes",
        "avg_pressures",
        "possession_proxy",
        "directness_proxy",
        "set_piece_shot_share",
        "left_side_event_share",
        "right_side_event_share",
        "central_event_share",
        "late_goal_for_rate",
        "late_goal_against_rate",
        "second_half_event_share",
        "pressing_proxy",
        "transition_proxy",
        "data_coverage_score",
    )


def build_player_match_basic(events: pl.DataFrame) -> pl.DataFrame:
    if events.is_empty():
        return pl.DataFrame()
    events = _ensure_event_columns(events)
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


def _against_metrics(team_match: pl.DataFrame) -> pl.DataFrame:
    return team_match.join(team_match, on="match_id", how="inner", suffix="_opponent").filter(
        pl.col("team_id") != pl.col("team_id_opponent")
    ).select(
        "match_id",
        "team_id",
        pl.col("shots_opponent").alias("shots_against"),
        pl.col("xg_opponent").alias("xg_against"),
        pl.col("late_goals_for_opponent").alias("late_goals_against"),
    )


def _goals_for_against(matches: pl.DataFrame) -> pl.DataFrame:
    schema = {
        "match_id": pl.Int64,
        "team_id": pl.Int64,
        "goals_for": pl.Int64,
        "goals_against": pl.Int64,
    }
    if matches is None or matches.is_empty():
        return pl.DataFrame(schema=schema)
    home = matches.select(
        "match_id",
        pl.col("home_team_id").alias("team_id"),
        pl.col("home_score").alias("goals_for"),
        pl.col("away_score").alias("goals_against"),
    )
    away = matches.select(
        "match_id",
        pl.col("away_team_id").alias("team_id"),
        pl.col("away_score").alias("goals_for"),
        pl.col("home_score").alias("goals_against"),
    )
    return pl.concat([home, away], how="vertical_relaxed")


def _coverage_expr() -> pl.Expr:
    cols = ["avg_goals_for", "avg_shots", "avg_xg", "avg_passes", "avg_pressures", "directness_proxy"]
    return pl.sum_horizontal([pl.col(col).is_not_null().cast(pl.Float64) for col in cols]) / len(cols)


def _ensure_event_columns(events: pl.DataFrame) -> pl.DataFrame:
    defaults = {
        "event_type": pl.lit(None, dtype=pl.Utf8),
        "shot_xg": pl.lit(None, dtype=pl.Float64),
        "shot_type": pl.lit(None, dtype=pl.Utf8),
        "shot_outcome": pl.lit(None, dtype=pl.Utf8),
        "location_x": pl.lit(None, dtype=pl.Float64),
        "location_y": pl.lit(None, dtype=pl.Float64),
        "pass_end_x": pl.lit(None, dtype=pl.Float64),
        "carry_end_x": pl.lit(None, dtype=pl.Float64),
        "minute": pl.lit(None, dtype=pl.Int64),
        "period": pl.lit(None, dtype=pl.Int64),
        "position_name": pl.lit(None, dtype=pl.Utf8),
    }
    expressions = [expr.alias(column) for column, expr in defaults.items() if column not in events.columns]
    return events.with_columns(expressions) if expressions else events
