from bucephalus.game.repository import GameRepository
from bucephalus.game.services import TransferMarketService


TEAM_A = ["courtois", "carvajal", "dias", "saliba", "grimaldo", "rodri", "valverde", "bellingham", "vinicius", "haaland", "saka"]
TEAM_B = ["alisson", "hakimi", "ake", "gvardiol", "tchouameni", "camavinga", "pedri", "vitinha", "odegaard", "mbappe", "kane"]


if __name__ == "__main__":
    repo = GameRepository()
    clubs = repo.list("clubs")
    market = TransferMarketService(repo)
    signed = []
    for club, player_ids in zip(clubs[:2], [TEAM_A, TEAM_B], strict=False):
        for player_id in player_ids:
            player = repo.get("players", player_id)
            signed.append(market.sign_player(club["id"], player_id, amount=min(player["value"], 5_000_000)))
    print({"signed": len(signed), "club_budgets": {club["name"]: repo.get("clubs", club["id"])["budget"] for club in clubs[:2]}})
