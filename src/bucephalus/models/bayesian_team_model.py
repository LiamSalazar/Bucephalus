from __future__ import annotations

from datetime import UTC, datetime


def bayesian_team_model_status() -> dict:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "not_enabled",
        "reason": "PyMC/Stan are intentionally not dependencies yet; use bootstrap and sequential team strength in this phase.",
    }
