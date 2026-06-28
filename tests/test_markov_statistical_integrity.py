from __future__ import annotations

from bucephalus.simulation.markov_engine import adjusted_transition_matrix, validate_transition_matrix
from bucephalus.tactics.schemas import TacticalState


def test_adjusted_markov_rows_are_valid():
    matrix = adjusted_transition_matrix(_state("A"), _state("B"))
    assert validate_transition_matrix(matrix)
    assert all(all(probability >= 0 for probability in row.values()) for row in matrix.values())


def _state(name: str) -> TacticalState:
    return TacticalState.from_team_baseline(
        {
            "bucephalus_team_id": name,
            "team_name": name,
            "possession_baseline": 0.5,
            "pressing_baseline": 0.5,
            "directness_baseline": 0.5,
            "transition_baseline": 0.5,
            "width_baseline": 0.5,
            "centrality_baseline": 0.5,
            "set_piece_dependency_baseline": 0.3,
            "defensive_exposure_baseline": 0.4,
            "second_half_intensity_baseline": 0.5,
            "late_goal_for_baseline": 0.4,
            "reliability_score": 0.8,
        }
    )
