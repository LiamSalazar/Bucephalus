from __future__ import annotations

from enum import StrEnum


class MatchState(StrEnum):
    OWN_THIRD = "OWN_THIRD"
    BUILD_UP = "BUILD_UP"
    MIDDLE_THIRD = "MIDDLE_THIRD"
    FINAL_THIRD = "FINAL_THIRD"
    BOX = "BOX"
    SHOT = "SHOT"
    GOAL = "GOAL"
    TURNOVER = "TURNOVER"
    COUNTER_ATTACK = "COUNTER_ATTACK"
    SET_PIECE = "SET_PIECE"
    END_POSSESSION = "END_POSSESSION"


TERMINAL_STATES = {MatchState.GOAL, MatchState.END_POSSESSION}
