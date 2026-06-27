from __future__ import annotations

from bucephalus.tactics.schemas import TacticalState


def tactical_compatibility_proxy(a: TacticalState, b: TacticalState) -> float:
    return max(0.0, min(1.0, 1 - abs(a.tempo - b.tempo) * 0.25 - abs(a.risk_tolerance - b.risk_tolerance) * 0.25))
