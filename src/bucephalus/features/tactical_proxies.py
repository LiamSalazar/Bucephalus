from __future__ import annotations

import polars as pl


def build_tactical_team_profiles(team_match_features: pl.DataFrame) -> pl.DataFrame:
    if team_match_features.is_empty():
        return pl.DataFrame()
    return team_match_features.group_by(["bucephalus_team_id", "team_name"]).agg(
        pl.len().alias("matches_count"),
        pl.col("possession_proxy").mean().alias("possession_baseline"),
        pl.col("pressing_proxy").mean().alias("pressing_baseline"),
        pl.col("directness_proxy").mean().alias("directness_baseline"),
        pl.col("transition_proxy").mean().alias("transition_baseline"),
        pl.col("width_proxy").mean().alias("width_baseline"),
        pl.col("centrality_proxy").mean().alias("centrality_baseline"),
        pl.col("set_piece_dependency_proxy").mean().alias("set_piece_dependency_baseline"),
        pl.col("goals_after_70_for").mean().alias("late_goal_for_baseline"),
        pl.col("goals_after_70_against").mean().alias("late_goal_against_baseline"),
        pl.col("second_half_event_share").mean().alias("second_half_intensity_baseline"),
        (pl.col("shots_against") + pl.col("xg_against")).mean().alias("defensive_exposure_baseline"),
        pl.col("xg_for").mean().alias("xg_for_baseline"),
        pl.col("xg_against").mean().alias("xg_against_baseline"),
        pl.col("data_coverage_score").mean().alias("data_coverage_score"),
    )
