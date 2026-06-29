from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from bucephalus.game.models import AuditLog, Club, Fixture, League, Lineup, Player, SimulationRun, SquadPlayer, TransferBid, User
from bucephalus.utils.paths import ProjectPaths


class GameRepository:
    tables = {
        "users": User,
        "leagues": League,
        "clubs": Club,
        "players": Player,
        "squad_players": SquadPlayer,
        "lineups": Lineup,
        "fixtures": Fixture,
        "transfer_bids": TransferBid,
        "simulation_runs": SimulationRun,
        "audit_logs": AuditLog,
    }

    def __init__(self, paths: ProjectPaths | None = None) -> None:
        self.paths = paths or ProjectPaths()
        self.path = self.paths.outputs / "game" / "game_state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.write({name: [] for name in self.tables})

    def read(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def reset(self) -> None:
        self.write({name: [] for name in self.tables})

    def add(self, table: str, obj) -> dict:
        data = self.read()
        payload = obj.model_dump(mode="json") if hasattr(obj, "model_dump") else dict(obj)
        data.setdefault(table, []).append(payload)
        self.write(data)
        return payload

    def list(self, table: str) -> list[dict]:
        return self.read().get(table, [])

    def get(self, table: str, object_id: str) -> dict | None:
        return next((row for row in self.list(table) if row.get("id") == object_id), None)

    def replace(self, table: str, object_id: str, payload: dict) -> None:
        data = self.read()
        rows = data.get(table, [])
        data[table] = [payload if row.get("id") == object_id else row for row in rows]
        self.write(data)

    def audit(self, action: str, payload: dict) -> None:
        self.add("audit_logs", AuditLog(id=str(uuid4()), action=action, payload=payload))


def db_path(paths: ProjectPaths | None = None) -> Path:
    repo = GameRepository(paths)
    return repo.path
