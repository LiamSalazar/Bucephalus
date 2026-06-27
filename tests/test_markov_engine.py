from __future__ import annotations

import random

from tests.test_tactical_sliders import _state
from bucephalus.simulation.markov_engine import base_transition_matrix, simulate_possession, validate_transition_matrix


def test_markov_matrix_valid_and_possession_terminates() -> None:
    assert validate_transition_matrix(base_transition_matrix())
    result = simulate_possession(_state(), _state(), random.Random(42))
    assert result["sequence"]
    assert "terminal_state" in result
    assert isinstance(result["shot_generated"], bool)
