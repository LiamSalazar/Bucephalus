from __future__ import annotations

from bucephalus.game.tactics.lineup_tactical_inference import infer_tactical_baseline_from_lineup

from tests.game_helpers import TEAM_A, TEAM_B, seed_game


def test_tactics_change_with_players_and_override_warns(tmp_path):
    repo, _, _, _ = seed_game(tmp_path)
    team_a = [repo.get("players", player_id) for player_id in TEAM_A]
    team_b = [repo.get("players", player_id) for player_id in TEAM_B]
    inferred_a = infer_tactical_baseline_from_lineup(team_a, "4-3-3")
    inferred_b = infer_tactical_baseline_from_lineup(team_b, "4-3-3")
    forced = infer_tactical_baseline_from_lineup(
        team_a,
        "4-3-3",
        manual_overrides={"pressing_predicted": 0.95},
    )

    assert inferred_a["transition_predicted"] != inferred_b["transition_predicted"]
    assert forced["manual_override"] is True
    assert forced["realism_warning"] is True
