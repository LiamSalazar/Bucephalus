from __future__ import annotations

LEAKAGE_TARGET_COLUMNS = {
    "home_score",
    "away_score",
    "total_goals",
    "result_home_win",
    "result_draw",
    "result_away_win",
    "goals_for",
    "goals_against",
    "goal_difference",
    "win",
    "draw",
    "loss",
    "xg_for",
    "shots_for",
    "shots_on_target_for",
}

ID_COLUMNS = {
    "bucephalus_match_id",
    "statsbomb_match_id",
    "bucephalus_team_id",
    "bucephalus_player_id",
    "team_name",
    "player_name",
    "opponent_team_name",
    "match_date",
}

MODEL_EXCLUDED_COLUMNS = sorted(LEAKAGE_TARGET_COLUMNS | ID_COLUMNS)
