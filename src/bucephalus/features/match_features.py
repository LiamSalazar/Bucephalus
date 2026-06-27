from __future__ import annotations

import polars as pl


def build_match_features(matches: pl.DataFrame, events: pl.DataFrame, three_sixty: pl.DataFrame, master_matches: pl.DataFrame) -> pl.DataFrame:
    if matches.is_empty():
        return pl.DataFrame()
    event_counts = events.group_by("match_id").agg(
        pl.len().alias("available_event_rows"),
        pl.col("shot_xg").is_not_null().any().alias("has_xg"),
        (pl.col("event_type") == "Pressure").any().alias("has_pressure"),
        (pl.col("event_type") == "Duel").any().alias("has_duels"),
    ) if not events.is_empty() else pl.DataFrame(schema={"match_id": pl.Int64})
    has_360 = three_sixty.group_by("match_id").agg(pl.len().gt(0).alias("has_360")) if not three_sixty.is_empty() else pl.DataFrame(schema={"match_id": pl.Int64, "has_360": pl.Boolean})
    out = matches.join(event_counts, on="match_id", how="left").join(has_360, on="match_id", how="left")
    if not master_matches.is_empty():
        out = out.join(
            master_matches.select(pl.col("statsbomb_match_id").alias("match_id"), "bucephalus_match_id"),
            on="match_id",
            how="left",
        )
    else:
        out = out.with_columns(pl.lit(None, dtype=pl.Utf8).alias("bucephalus_match_id"))
    return out.with_columns(
        (pl.col("home_score") + pl.col("away_score")).alias("total_goals"),
        (pl.col("home_score") > pl.col("away_score")).cast(pl.Int8).alias("result_home_win"),
        (pl.col("home_score") == pl.col("away_score")).cast(pl.Int8).alias("result_draw"),
        (pl.col("home_score") < pl.col("away_score")).cast(pl.Int8).alias("result_away_win"),
        (pl.col("home_score") - pl.col("away_score")).alias("goal_difference"),
        pl.col("available_event_rows").fill_null(0),
        pl.col("has_xg").fill_null(False),
        pl.col("has_pressure").fill_null(False),
        pl.col("has_duels").fill_null(False),
        pl.col("has_360").fill_null(False),
    ).select(
        "bucephalus_match_id",
        pl.col("match_id").alias("statsbomb_match_id"),
        "competition_id",
        "season_id",
        "match_date",
        "home_team_id",
        "away_team_id",
        "home_score",
        "away_score",
        "total_goals",
        "result_home_win",
        "result_draw",
        "result_away_win",
        "goal_difference",
        "available_event_rows",
        "has_xg",
        "has_pressure",
        "has_duels",
        "has_360",
    )
