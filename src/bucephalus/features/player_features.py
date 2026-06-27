from __future__ import annotations

import polars as pl


def build_player_match_features(events: pl.DataFrame, matches: pl.DataFrame, master_matches: pl.DataFrame, master_players: pl.DataFrame, master_teams: pl.DataFrame) -> pl.DataFrame:
    if events.is_empty():
        return pl.DataFrame()
    ev = events
    agg = ev.drop_nulls("player_id").group_by(["match_id", "team_id", "team_name", "player_id", "player_name", "position_name"]).agg(
        (pl.col("minute").max() - pl.col("minute").min() + 1).clip(1, 90).alias("minutes_proxy"),
        pl.len().alias("events_count"),
        (pl.col("event_type") == "Shot").sum().alias("shots"),
        ((pl.col("event_type") == "Shot") & pl.col("shot_outcome").is_in(["Goal", "Saved"])).sum().alias("shots_on_target"),
        ((pl.col("event_type") == "Shot") & (pl.col("shot_outcome") == "Goal")).sum().alias("goals"),
        pl.col("shot_xg").sum().alias("xg"),
        (pl.col("event_type") == "Pass").sum().alias("passes"),
        ((pl.col("event_type") == "Pass") & pl.col("pass_end_x").is_not_null()).sum().alias("completed_passes"),
        (pl.col("event_type") == "Carry").sum().alias("carries"),
        (pl.col("event_type") == "Pressure").sum().alias("pressures"),
        (pl.col("event_type") == "Duel").sum().alias("duels"),
        pl.col("duel_type").str.contains("Aerial", literal=False).fill_null(False).sum().alias("aerial_duels"),
        (pl.col("event_type") == "Goal Keeper").sum().alias("goalkeeper_actions"),
        (pl.col("event_type") == "Foul Committed").sum().alias("fouls_committed"),
        (pl.col("event_type") == "Foul Won").sum().alias("fouls_won"),
        (pl.col("event_type") == "Bad Behaviour").sum().alias("cards"),
    )
    context = matches.select(pl.col("match_id"), "match_date", "competition_id", "season_id")
    out = agg.join(context, on="match_id", how="left")
    if not master_matches.is_empty():
        out = out.join(master_matches.select(pl.col("statsbomb_match_id").alias("match_id"), "bucephalus_match_id"), on="match_id", how="left")
    if not master_players.is_empty():
        out = out.join(master_players.select(pl.col("statsbomb_player_id").alias("player_id"), "bucephalus_player_id"), on="player_id", how="left")
    if not master_teams.is_empty():
        out = out.join(master_teams.select(pl.col("statsbomb_team_id").alias("team_id"), "bucephalus_team_id"), on="team_id", how="left")
    return out.with_columns(
        (pl.col("shots") * 90 / pl.max_horizontal(pl.col("minutes_proxy"), pl.lit(1))).alias("shots_per90_proxy"),
        (pl.col("xg") * 90 / pl.max_horizontal(pl.col("minutes_proxy"), pl.lit(1))).alias("xg_per90_proxy"),
        (pl.col("passes") * 90 / pl.max_horizontal(pl.col("minutes_proxy"), pl.lit(1))).alias("passes_per90_proxy"),
        (pl.col("pressures") * 90 / pl.max_horizontal(pl.col("minutes_proxy"), pl.lit(1))).alias("pressures_per90_proxy"),
        pl.lit(None, dtype=pl.Int64).alias("assists"),
    ).rename({"match_id": "statsbomb_match_id"}).select(
        "bucephalus_match_id", "statsbomb_match_id", "bucephalus_player_id", "player_name", "bucephalus_team_id",
        "team_name", "position_name", "match_date", "competition_id", "season_id", "minutes_proxy", "events_count",
        "shots", "shots_on_target", "goals", "xg", "assists", "passes", "completed_passes", "carries", "pressures",
        "duels", "aerial_duels", "goalkeeper_actions", "fouls_committed", "fouls_won", "cards", "shots_per90_proxy",
        "xg_per90_proxy", "passes_per90_proxy", "pressures_per90_proxy",
    )
