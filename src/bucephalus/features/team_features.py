from __future__ import annotations

import polars as pl


def build_team_match_features(matches: pl.DataFrame, events: pl.DataFrame, master_matches: pl.DataFrame, master_teams: pl.DataFrame) -> pl.DataFrame:
    if matches.is_empty():
        return pl.DataFrame()
    base = _team_match_base(matches, master_matches, master_teams)
    if events.is_empty():
        return base
    ev = _ensure_events(events)
    agg = ev.group_by(["match_id", "team_id"]).agg(
        pl.len().alias("events_for"),
        (pl.col("event_type") == "Shot").sum().alias("shots_for"),
        ((pl.col("event_type") == "Shot") & pl.col("shot_outcome").is_in(["Goal", "Saved"])).sum().alias("shots_on_target_for"),
        pl.col("shot_xg").sum().alias("xg_for"),
        ((pl.col("event_type") == "Shot") & (pl.col("location_x") >= 102) & (pl.col("location_y").is_between(18, 62))).sum().alias("box_shots_for"),
        ((pl.col("event_type") == "Shot") & (pl.col("shot_type") != "Open Play")).sum().alias("set_piece_shots_for"),
        pl.when(pl.col("shot_type") != "Open Play").then(pl.col("shot_xg")).otherwise(0).sum().alias("set_piece_xg_for"),
        (pl.col("event_type") == "Pass").sum().alias("passes_for"),
        ((pl.col("event_type") == "Pass") & pl.col("pass_end_x").is_not_null()).sum().alias("completed_passes_for"),
        ((pl.col("event_type") == "Pass") & ((pl.col("pass_end_x") - pl.col("location_x")) >= 15)).sum().alias("progressive_passes_proxy"),
        ((pl.col("event_type") == "Pass") & (pl.col("pass_end_x") >= 80) & (pl.col("location_x") < 80)).sum().alias("final_third_entries_proxy"),
        (pl.col("event_type") == "Carry").sum().alias("carries_for"),
        ((pl.col("event_type") == "Carry") & ((pl.col("carry_end_x") - pl.col("location_x")) >= 10)).sum().alias("progressive_carries_proxy"),
        (pl.col("event_type") == "Pressure").sum().alias("pressures_for"),
        (pl.col("event_type") == "Duel").sum().alias("duels_for"),
        pl.col("duel_outcome").str.contains("Won", literal=False).fill_null(False).sum().alias("duels_won_for"),
        pl.col("duel_type").str.contains("Aerial", literal=False).fill_null(False).sum().alias("aerial_duels_for"),
        (pl.col("duel_type").str.contains("Aerial", literal=False).fill_null(False) & pl.col("duel_outcome").str.contains("Won", literal=False).fill_null(False)).sum().alias("aerial_duels_won_for"),
        (pl.col("event_type") == "Interception").sum().alias("interceptions_for"),
        (pl.col("event_type") == "Tackle").sum().alias("tackles_for"),
        (pl.col("event_type") == "Goal Keeper").sum().alias("goalkeeper_actions_for"),
        (pl.col("location_y") < 26.6667).sum().alias("left_side_events"),
        (pl.col("location_y") > 53.3333).sum().alias("right_side_events"),
        (pl.col("location_y").is_between(26.6667, 53.3333)).sum().alias("central_events"),
        (pl.col("location_x") < 40).sum().alias("own_third_events"),
        (pl.col("location_x").is_between(40, 80)).sum().alias("middle_third_events"),
        (pl.col("location_x") > 80).sum().alias("final_third_events"),
        ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome") == "Goal") & (pl.col("period") == 1)).sum().alias("first_half_goals_for"),
        ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome") == "Goal") & (pl.col("period") == 2)).sum().alias("second_half_goals_for"),
        pl.when(pl.col("period") == 1).then(pl.col("shot_xg")).otherwise(0).sum().alias("first_half_xg_for"),
        pl.when(pl.col("period") == 2).then(pl.col("shot_xg")).otherwise(0).sum().alias("second_half_xg_for"),
        ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome") == "Goal") & (pl.col("minute") >= 70)).sum().alias("goals_after_70_for"),
        ((pl.col("event_type") == "Shot") & (pl.col("minute") >= 70)).sum().alias("shots_after_70_for"),
        (pl.col("minute") >= 70).sum().alias("events_after_70"),
        (pl.col("period") == 2).sum().alias("second_half_events"),
        (pl.col("pass_end_x") - pl.col("location_x")).mean().alias("directness_proxy"),
    )
    out = base.join(agg, left_on=["statsbomb_match_id", "team_id"], right_on=["match_id", "team_id"], how="left")
    against = out.select(
        "statsbomb_match_id",
        pl.col("team_id").alias("opponent_team_id"),
        pl.col("shots_for").alias("shots_against"),
        pl.col("shots_on_target_for").alias("shots_on_target_against"),
        pl.col("xg_for").alias("xg_against"),
        pl.col("passes_for").alias("passes_against"),
        pl.col("pressures_for").alias("pressures_against"),
        pl.col("goals_after_70_for").alias("goals_after_70_against"),
        pl.col("shots_after_70_for").alias("shots_after_70_against"),
    )
    out = out.join(against, on=["statsbomb_match_id", "opponent_team_id"], how="left")
    numeric_defaults = [c for c in out.columns if c.endswith("_for") or c.endswith("_against") or c.endswith("_events")]
    out = out.with_columns(
        [pl.col(c).fill_null(0) for c in numeric_defaults]
        + [
            (pl.col("goals_for") - pl.col("goals_against")).alias("goal_difference"),
            (pl.col("goals_for") > pl.col("goals_against")).cast(pl.Int8).alias("win"),
            (pl.col("goals_for") == pl.col("goals_against")).cast(pl.Int8).alias("draw"),
            (pl.col("goals_for") < pl.col("goals_against")).cast(pl.Int8).alias("loss"),
            (pl.col("xg_for") / pl.max_horizontal(pl.col("shots_for"), pl.lit(1))).alias("avg_shot_xg"),
            (pl.col("completed_passes_for") / pl.max_horizontal(pl.col("passes_for"), pl.lit(1))).alias("pass_completion_rate"),
            (pl.col("left_side_events") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("left_side_event_share"),
            (pl.col("right_side_events") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("right_side_event_share"),
            (pl.col("central_events") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("central_event_share"),
            (pl.col("own_third_events") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("own_third_event_share"),
            (pl.col("middle_third_events") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("middle_third_event_share"),
            (pl.col("final_third_events") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("final_third_event_share"),
            (pl.col("events_after_70") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("event_share_after_70"),
            (pl.col("second_half_events") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("second_half_event_share"),
            (pl.col("passes_for") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("possession_proxy"),
            (pl.col("pressures_for") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("pressing_proxy"),
            (pl.col("progressive_carries_proxy") / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("transition_proxy"),
            (pl.col("set_piece_shots_for") / pl.max_horizontal(pl.col("shots_for"), pl.lit(1))).alias("set_piece_dependency_proxy"),
            ((pl.col("pressures_for") - pl.col("pressures_against")) / pl.max_horizontal(pl.col("events_for"), pl.lit(1))).alias("late_pressure_or_fatigue_proxy"),
            pl.col("xg_for").is_null().cast(pl.Int8).alias("missing_xg_flag"),
            (pl.col("pressures_for") == 0).cast(pl.Int8).alias("missing_pressure_flag"),
            (pl.col("duels_for") == 0).cast(pl.Int8).alias("missing_duels_flag"),
        ]
    )
    return out.with_columns(
        ((pl.col("left_side_event_share") + pl.col("right_side_event_share")) / 2).alias("width_proxy"),
        pl.col("central_event_share").alias("centrality_proxy"),
        (((1 - pl.col("missing_xg_flag")) + (1 - pl.col("missing_pressure_flag")) + (1 - pl.col("missing_duels_flag"))) / 3).alias("data_coverage_score"),
    )


def _team_match_base(matches: pl.DataFrame, master_matches: pl.DataFrame, master_teams: pl.DataFrame) -> pl.DataFrame:
    home = matches.select(
        pl.col("match_id").alias("statsbomb_match_id"), "match_date", "competition_id", "season_id",
        pl.col("home_team_id").alias("team_id"), pl.col("home_team_name").alias("team_name"),
        pl.col("away_team_id").alias("opponent_team_id"), pl.col("away_team_name").alias("opponent_team_name"),
        pl.lit(True).alias("is_home"), pl.col("home_score").alias("goals_for"), pl.col("away_score").alias("goals_against"),
    )
    away = matches.select(
        pl.col("match_id").alias("statsbomb_match_id"), "match_date", "competition_id", "season_id",
        pl.col("away_team_id").alias("team_id"), pl.col("away_team_name").alias("team_name"),
        pl.col("home_team_id").alias("opponent_team_id"), pl.col("home_team_name").alias("opponent_team_name"),
        pl.lit(False).alias("is_home"), pl.col("away_score").alias("goals_for"), pl.col("home_score").alias("goals_against"),
    )
    base = pl.concat([home, away], how="vertical_relaxed")
    if not master_matches.is_empty():
        base = base.join(master_matches.select(pl.col("statsbomb_match_id"), "bucephalus_match_id"), on="statsbomb_match_id", how="left")
    if not master_teams.is_empty():
        base = base.join(master_teams.select(pl.col("statsbomb_team_id").alias("team_id"), "bucephalus_team_id"), on="team_id", how="left")
    return base


def _ensure_events(events: pl.DataFrame) -> pl.DataFrame:
    defaults = {
        "shot_xg": pl.lit(None, dtype=pl.Float64), "shot_outcome": pl.lit(None, dtype=pl.Utf8), "shot_type": pl.lit(None, dtype=pl.Utf8),
        "pass_end_x": pl.lit(None, dtype=pl.Float64), "carry_end_x": pl.lit(None, dtype=pl.Float64), "location_x": pl.lit(None, dtype=pl.Float64),
        "location_y": pl.lit(None, dtype=pl.Float64), "duel_type": pl.lit(None, dtype=pl.Utf8), "duel_outcome": pl.lit(None, dtype=pl.Utf8),
    }
    missing = [expr.alias(col) for col, expr in defaults.items() if col not in events.columns]
    return events.with_columns(missing) if missing else events
