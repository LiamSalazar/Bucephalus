from __future__ import annotations

from tests.game_helpers import TEAM_A, seed_game


def test_default_pool_and_squad_assignment(tmp_path):
    repo, _, club_a, _ = seed_game(tmp_path)
    squad = [row for row in repo.list("squad_players") if row["club_id"] == club_a["id"]]

    assert len(squad) == len(TEAM_A)
    assert {row["player_id"] for row in squad} == set(TEAM_A)
