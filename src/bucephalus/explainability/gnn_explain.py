from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl

from bucephalus.utils.paths import ProjectPaths


def build_gnn_explanations(paths: ProjectPaths) -> dict:
    edges_path = paths.features / "pass_network_edges.parquet"
    nodes_path = paths.features / "pass_network_nodes.parquet"
    out_dir = paths.outputs / "explainability"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not edges_path.exists() or not nodes_path.exists():
        payload = {"status": "skipped", "reason": "pass network missing"}
    else:
        edges = pl.read_parquet(edges_path).sort("pass_count", descending=True).head(5)
        nodes = pl.read_parquet(nodes_path).sort("centrality_weighted_degree", descending=True).head(5)
        edge_payload = {"generated_at": datetime.now(UTC).isoformat(), "method": "edge_occlusion_proxy", "top_edges": edges.to_dicts()}
        node_payload = {"generated_at": datetime.now(UTC).isoformat(), "method": "node_occlusion_proxy", "top_nodes": nodes.to_dicts()}
        (out_dir / "gnn_edge_importance_sample.json").write_text(json.dumps(edge_payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "gnn_node_importance_sample.json").write_text(json.dumps(node_payload, indent=2, default=str), encoding="utf-8")
        payload = {"status": "completed", "edge_rows": edges.height, "node_rows": nodes.height}
    return payload
