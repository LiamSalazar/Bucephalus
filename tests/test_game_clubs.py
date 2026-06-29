from __future__ import annotations

from bucephalus.game.services import LeagueService

from tests.game_helpers import make_repo


def test_create_club_uses_league_budget(tmp_path):
    repo = make_repo(tmp_path)
    service = LeagueService(repo)
    user = service.create_user("Manager")
    league = service.create_league("Budget League", user["id"])
    club = service.create_club(league["id"], "Club A", user["id"])

    assert club["league_id"] == league["id"]
    assert club["budget"] == league["settings"]["initial_budget"]
