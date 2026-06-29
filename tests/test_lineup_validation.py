from __future__ import annotations

from bucephalus.game.lineups import LineupService, validate_lineup

from tests.game_helpers import TEAM_A, seed_game


def test_valid_lineup_and_invalid_duplicate(tmp_path):
    repo, _, club_a, _ = seed_game(tmp_path)
    players = [repo.get("players", player_id) for player_id in TEAM_A]
    valid = validate_lineup(players, "4-3-3")
    invalid = validate_lineup(players[:-1] + [players[-2]], "4-3-3")
    lineup = LineupService(repo).create_lineup(club_a["id"], "4-3-3", TEAM_A)

    assert valid["lineup_validity"] is True
    assert invalid["lineup_validity"] is False
    assert lineup["validation"]["lineup_validity"] is True
