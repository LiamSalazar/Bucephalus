from __future__ import annotations

from uuid import uuid4

from bucephalus.game.models import Lineup, LineupSlot
from bucephalus.game.repository import GameRepository


FORMATIONS = {
    "4-3-3": {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3},
    "4-2-3-1": {"GK": 1, "DEF": 4, "MID": 5, "FWD": 1},
    "4-4-2": {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2},
    "3-5-2": {"GK": 1, "DEF": 3, "MID": 5, "FWD": 2},
}

GROUPS = {"GK": {"GK"}, "DEF": {"CB", "LB", "RB", "WB"}, "MID": {"DM", "CM", "AM"}, "FWD": {"LW", "RW", "CF", "ST"}}


class LineupService:
    def __init__(self, repo: GameRepository) -> None:
        self.repo = repo

    def create_lineup(self, club_id: str, formation: str, player_ids: list[str]) -> dict:
        players = [_player for pid in player_ids if (_player := self.repo.get("players", pid))]
        validation = validate_lineup(players, formation)
        slots = [LineupSlot(player_id=p["id"], role=_role_for_position(p["canonical_position"]), position=p["canonical_position"]) for p in players]
        lineup = Lineup(id=str(uuid4()), club_id=club_id, formation=formation, slots=slots)
        payload = self.repo.add("lineups", lineup)
        payload["validation"] = validation
        self.repo.audit("create_lineup", payload)
        return payload


def validate_lineup(players: list[dict], formation: str) -> dict:
    warnings = []
    ids = [p["id"] for p in players]
    counts = _group_counts(players)
    valid = True
    if len(players) != 11:
        valid = False
        warnings.append("lineup must contain exactly 11 players")
    if len(set(ids)) != len(ids):
        valid = False
        warnings.append("duplicate players are not allowed")
    if counts["GK"] != 1:
        valid = False
        warnings.append("lineup must contain exactly one goalkeeper")
    if counts["DEF"] < 3:
        valid = False
        warnings.append("lineup needs at least three defensive players")
    if counts["MID"] < 2:
        valid = False
        warnings.append("lineup needs midfield coverage")
    if counts["FWD"] > 4:
        valid = False
        warnings.append("lineup has too many forwards")
    return {
        "lineup_validity": valid,
        "formation": formation,
        "counts": counts,
        "role_fit_scores": {p["id"]: role_fit_score(p, _role_for_position(p["canonical_position"])) for p in players},
        "formation_balance": _balance(counts),
        "coverage_map_proxy": counts,
        "warnings": warnings,
    }


def role_fit_score(player: dict, role: str) -> float:
    position = player.get("canonical_position", "")
    attrs = player.get("attributes", {})
    base = 0.85 if role == _role_for_position(position) else 0.55
    if player["id"] == "valverde" and role in {"MID", "FWD", "DEF"}:
        base = max(base, 0.72)
    if player["id"] == "bellingham" and role in {"MID", "FWD"}:
        base = max(base, 0.78)
    if player["id"] == "haaland" and role != "FWD":
        base = min(base, 0.35)
    if player["id"] == "mbappe" and role == "MID":
        base = min(base, 0.45)
    return max(0.0, min(1.0, base + float(attrs.get("association", 0.0)) * 0.05))


def _group_counts(players: list[dict]) -> dict[str, int]:
    return {group: sum(p.get("canonical_position") in positions for p in players) for group, positions in GROUPS.items()}


def _role_for_position(position: str) -> str:
    for group, positions in GROUPS.items():
        if position in positions:
            return group
    return "MID"


def _balance(counts: dict[str, int]) -> float:
    return max(0.0, min(1.0, 0.25 * (counts["GK"] == 1) + 0.3 * min(counts["DEF"], 4) / 4 + 0.3 * min(counts["MID"], 4) / 4 + 0.15 * min(counts["FWD"], 3) / 3))
