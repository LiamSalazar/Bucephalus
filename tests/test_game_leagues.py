from __future__ import annotations

from bucephalus.game.services import LeagueService

from tests.game_helpers import make_repo


def test_create_league_and_roles(tmp_path):
    repo = make_repo(tmp_path)
    service = LeagueService(repo)
    user = service.create_user("Liam", roles=["league_creator", "manager"])
    league = service.create_league("Friends Champions", user["id"], "simulation_league")

    assert league["creator_user_id"] == user["id"]
    assert league["settings"]["initial_budget"] == 300_000_000
    assert "league_creator" in user["roles"]
