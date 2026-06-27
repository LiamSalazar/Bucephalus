from __future__ import annotations

from bucephalus.tactics.schemas import TacticalState
from bucephalus.tactics.tactical_sliders import apply_tactical_sliders


def _state() -> TacticalState:
    return TacticalState(
        team_name="A", possession=0.5, pressing=0.5, directness=0.5, transition=0.5,
        width=0.5, centrality=0.5, set_piece_dependency=0.2, defensive_exposure=0.4,
        second_half_intensity=0.5, late_goal_threat=0.3, fatigue_resistance=0.5,
        defensive_compactness=0.6, line_height=0.5, tempo=0.5, risk_tolerance=0.5,
    )


def test_sliders_do_not_mutate_and_respect_limits() -> None:
    baseline = _state()
    adjusted, report = apply_tactical_sliders(baseline, pressing_delta=0.8)
    assert baseline.pressing == 0.5
    assert adjusted.pressing == 1.0
    assert report.warnings
