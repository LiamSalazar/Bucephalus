from bucephalus.game.lineups import LineupService
from bucephalus.game.repository import GameRepository
from bucephalus.game.tactics import infer_tactical_baseline_from_lineup


if __name__ == "__main__":
    repo = GameRepository()
    service = LineupService(repo)
    outputs = []
    for club in repo.list("clubs")[:2]:
        player_ids = [row["player_id"] for row in repo.list("squad_players") if row["club_id"] == club["id"]][:11]
        lineup = service.create_lineup(club["id"], "4-3-3", player_ids)
        players = [repo.get("players", pid) for pid in player_ids]
        tactics = infer_tactical_baseline_from_lineup(players, "4-3-3")
        outputs.append({"club": club["name"], "lineup_validity": lineup["validation"]["lineup_validity"], "tactics": tactics})
    print(outputs)
