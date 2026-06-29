from bucephalus.game.repository import GameRepository
from bucephalus.lab import LabScenarioService


if __name__ == "__main__":
    repo = GameRepository()
    clubs = repo.list("clubs")[:2]
    payload = LabScenarioService(repo).run_scenario(clubs[0]["id"], clubs[1]["id"], "Mbappe_Haaland_vs_Vinicius_Haaland_proxy")
    print({"scenario": payload["label"], "report": "outputs/lab/scenario_report.json"})
