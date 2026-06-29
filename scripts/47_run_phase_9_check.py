from __future__ import annotations

import json
import sys
from pathlib import Path

from bucephalus.game.repository import GameRepository


def main() -> None:
    repo = GameRepository()
    failures = []
    data = repo.read()
    checks = {
        "users": len(data.get("users", [])) >= 2,
        "leagues": len(data.get("leagues", [])) >= 1,
        "clubs": len(data.get("clubs", [])) >= 2,
        "players": len(data.get("players", [])) >= 22,
        "squads": len(data.get("squad_players", [])) >= 22,
        "lineups": len(data.get("lineups", [])) >= 2,
        "fixtures": len(data.get("fixtures", [])) >= 1,
        "simulations": len(data.get("simulation_runs", [])) >= 2,
        "transfers": len(data.get("transfer_bids", [])) >= 22,
        "match_report": bool(list((repo.paths.outputs / "game").glob("match_report_*.json"))),
        "lab_report": (repo.paths.outputs / "lab" / "scenario_report.json").exists(),
        "provider_health": (repo.paths.outputs / "live" / "provider_health_report.json").exists(),
    }
    failures.extend(key for key, ok in checks.items() if not ok)
    report = _write_report(repo, checks, failures)
    payload = {"passed": not failures, "checks": checks, "failures": failures, "report": report}
    out = repo.paths.quality_outputs / "phase_9_check.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if failures:
        print("PHASE 9 CHECK: FAIL")
        print(payload)
        sys.exit(1)
    print("PHASE 9 CHECK: PASS")


def _write_report(repo: GameRepository, checks: dict, failures: list[str]) -> str:
    lines = [
        "# Phase 9 Game System Report",
        "",
        "## Implemented",
        "- Local game repository for users, leagues, clubs, squads, lineups, fixtures, transfers, simulations and audit logs.",
        "- Game Mode flow: create league -> clubs -> player pool -> draft -> lineup -> tactical inference -> simulation -> report.",
        "- Lab Mode scenario and comparison outputs.",
        "- Mock live provider and provider health report.",
        "- Transfer market budget/duplicate validation.",
        "",
        "## Checks",
    ]
    lines.extend(f"- {key}: {value}" for key, value in checks.items())
    lines.extend(
        [
            "",
            "## Limitations",
            "- Local JSON persistence is used for Phase 9 smoke flow; production DB/API can be added in Fases 10-12.",
            "- External live providers require API keys and are disabled by default.",
            "- Pass recipients may use proxy when provider data lacks explicit recipient.",
            "- No frontend, chatbot or deployment is included.",
            "",
            "## Next Steps",
            "- Add production auth/API and PostgreSQL migrations.",
            "- Expand provider coverage and richer league settings UI.",
            "- Promote only candidate/champion models into default match resolution.",
        ]
    )
    if failures:
        lines.extend(["", "## Failures", *[f"- {failure}" for failure in failures]])
    path = repo.paths.outputs / "reports" / "phase9_game_system_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)


if __name__ == "__main__":
    main()
