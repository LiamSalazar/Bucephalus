from __future__ import annotations

from bucephalus.explainability.gnn_explain import build_gnn_explanations
from bucephalus.explainability.sequence_explain import build_sequence_explanation
from bucephalus.explainability.tabular_explain import build_tabular_explanations
from bucephalus.utils.paths import ProjectPaths


def explain_prediction(match_id: int | None = None, possession_id: int | None = None, event_index: int | None = None, paths: ProjectPaths | None = None) -> dict:
    project_paths = paths or ProjectPaths()
    tabular = build_tabular_explanations(project_paths)
    sequence = build_sequence_explanation(project_paths)
    gnn = build_gnn_explanations(project_paths)
    return {
        "model_used": "tabular_sequence_gnn",
        "match_id": match_id,
        "possession_id": possession_id,
        "event_index": event_index,
        "prediction": sequence.get("prediction"),
        "top_factors": tabular.get("top_features", [])[:3],
        "top_events": sequence.get("top_events", [])[:3],
        "top_graph_components": {
            "edges": gnn.get("edge_rows"),
            "nodes": gnn.get("node_rows"),
        },
        "warnings": [value for value in [tabular.get("warning"), sequence.get("warning")] if value],
    }
