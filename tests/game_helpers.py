from __future__ import annotations

from bucephalus.game.repository import GameRepository
from bucephalus.game.services import LeagueService, PlayerPoolService, TransferMarketService
from bucephalus.utils.paths import ProjectPaths

TEAM_A = [
    "courtois",
    "carvajal",
    "dias",
    "saliba",
    "grimaldo",
    "rodri",
    "valverde",
    "bellingham",
    "vinicius",
    "haaland",
    "saka",
]

TEAM_B = [
    "alisson",
    "hakimi",
    "ake",
    "gvardiol",
    "tchouameni",
    "camavinga",
    "pedri",
    "vitinha",
    "odegaard",
    "mbappe",
    "kane",
]


def make_repo(tmp_path):
    paths = ProjectPaths(data_root=tmp_path / "data")
    paths.ensure()
    repo = GameRepository(paths)
    repo.reset()
    return repo


def seed_game(tmp_path):
    repo = make_repo(tmp_path)
    league_service = LeagueService(repo)
    market = TransferMarketService(repo)
    user_a = league_service.create_user("Alice")
    user_b = league_service.create_user("Bob")
    league = league_service.create_league("Test League", user_a["id"])
    club_a = league_service.create_club(league["id"], "Bucephalus A", user_a["id"])
    club_b = league_service.create_club(league["id"], "Bucephalus B", user_b["id"])
    PlayerPoolService(repo).load_default_pool()
    for player_id in TEAM_A:
        market.sign_player(club_a["id"], player_id, amount=5_000_000)
    for player_id in TEAM_B:
        market.sign_player(club_b["id"], player_id, amount=5_000_000)
    return repo, league, club_a, club_b
