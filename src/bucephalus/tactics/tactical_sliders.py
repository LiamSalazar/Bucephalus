from __future__ import annotations

from bucephalus.tactics.schemas import TacticalAdjustmentReport, TacticalState

SLIDER_MAP = {
    "pressing_delta": "pressing",
    "possession_delta": "possession",
    "directness_delta": "directness",
    "transition_delta": "transition",
    "width_delta": "width",
    "centrality_delta": "centrality",
    "line_height_delta": "line_height",
    "tempo_delta": "tempo",
    "risk_tolerance_delta": "risk_tolerance",
    "defensive_compactness_delta": "defensive_compactness",
}


def apply_tactical_sliders(state: TacticalState, **deltas: float) -> tuple[TacticalState, TacticalAdjustmentReport]:
    data = state.model_dump()
    warnings = []
    applied = {}
    for slider, attr in SLIDER_MAP.items():
        delta = float(deltas.get(slider) or 0.0)
        if delta == 0:
            continue
        if abs(delta) >= 0.25:
            warnings.append(f"Extreme tactical slider change for {attr}: {delta:+.2f}")
        data[attr] = _clamp(data[attr] + delta)
        applied[attr] = delta
    after = TacticalState(**data)
    return after, TacticalAdjustmentReport(warnings=warnings, applied_deltas=applied, before=state, after=after)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
