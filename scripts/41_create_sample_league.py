from bucephalus.game.repository import GameRepository
from bucephalus.game.services import LeagueService, PlayerPoolService


if __name__ == "__main__":
    repo = GameRepository()
    league_service = LeagueService(repo)
    user1 = league_service.create_user("Liam Manager", ["league_creator", "manager"])
    user2 = league_service.create_user("Alex Analyst", ["manager", "analyst"])
    league = league_service.create_league("Bucephalus Friends League", user1["id"], "simulation_league")
    club1 = league_service.create_club(league["id"], "Bucephalus Royals", user1["id"])
    club2 = league_service.create_club(league["id"], "Alexandria Analysts", user2["id"])
    players = PlayerPoolService(repo).load_default_pool()
    print({"league": league, "clubs": [club1, club2], "player_pool": len(players)})
