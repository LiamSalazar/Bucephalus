from __future__ import annotations

from bucephalus.explainability.sequence_explain import build_sequence_explanation
from bucephalus.utils.paths import ProjectPaths


def explain_prediction(match_id: int | None = None, minute: int | None = None, paths: ProjectPaths | None = None) -> dict:
    _ = (match_id, minute)
    return build_sequence_explanation(paths or ProjectPaths())
