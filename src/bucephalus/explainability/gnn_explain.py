from __future__ import annotations

import json
from datetime import UTC, datetime

import torch

from bucephalus.graphs.graph_dataset import build_graph_arrays
from bucephalus.graphs.gnn_model import ManualGCN
from bucephalus.utils.paths import ProjectPaths


def build_gnn_explanations(paths: ProjectPaths) -> dict:
    edges_path = paths.features / "pass_network_edges.parquet"
    nodes_path = paths.features / "pass_network_nodes.parquet"
    out_dir = paths.outputs / "explainability"
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = paths.models_outputs / "gnn_model.pt"
    if not edges_path.exists() or not nodes_path.exists() or not model_path.exists():
        payload = {"status": "skipped", "reason": "pass network missing"}
    else:
        edge_payload, node_payload = _gnn_occlusion(paths, model_path, edges_path, nodes_path)
        (out_dir / "gnn_edge_importance_sample.json").write_text(json.dumps(edge_payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "gnn_node_importance_sample.json").write_text(json.dumps(node_payload, indent=2, default=str), encoding="utf-8")
        payload = {"status": "completed", "edge_rows": len(edge_payload.get("top_edges", [])), "node_rows": len(node_payload.get("top_nodes", []))}
    return payload


def _gnn_occlusion(paths: ProjectPaths, model_path, edges_path, nodes_path) -> tuple[dict, dict]:
    ckpt = torch.load(model_path, map_location="cpu")
    x, adj, mask, _, meta = build_graph_arrays(paths)
    if len(meta) == 0:
        skipped = {"status": "skipped", "reason": "graph arrays empty"}
        return skipped, skipped
    model = ManualGCN(input_dim=int(ckpt["input_dim"]), hidden_dim=int(ckpt["hidden_dim"]))
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    sample_x = torch.tensor(x[:1], dtype=torch.float32)
    sample_adj = torch.tensor(adj[:1], dtype=torch.float32)
    sample_mask = torch.tensor(mask[:1], dtype=torch.float32)
    with torch.no_grad():
        base = float(model(sample_x, sample_adj, sample_mask)[0])
        node_rows = []
        valid = int(sample_mask[0].sum().item())
        for idx in range(valid):
            occluded_x = sample_x.clone()
            occluded_x[0, idx, :] = 0.0
            pred = float(model(occluded_x, sample_adj, sample_mask)[0])
            node_rows.append({"node_index": idx, "contribution": abs(base - pred), "occluded_prediction": pred, "method": "node_occlusion"})
        edge_rows = []
        nz = torch.nonzero(sample_adj[0] > 0, as_tuple=False)
        for edge_idx, (i, j) in enumerate(nz[:50]):
            if i == j:
                continue
            occluded_adj = sample_adj.clone()
            occluded_adj[0, i, j] = 0.0
            pred = float(model(sample_x, occluded_adj, sample_mask)[0])
            edge_rows.append({"edge_index": edge_idx, "from_node": int(i), "to_node": int(j), "contribution": abs(base - pred), "occluded_prediction": pred, "method": "edge_occlusion"})
    edge_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "model": "manual_gcn_pass_network_v1",
        "prediction": base,
        "graph": meta[0],
        "top_edges": sorted(edge_rows, key=lambda row: row["contribution"], reverse=True)[:5],
        "warning": "Edge occlusion is local to one graph sample.",
    }
    node_payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "model": "manual_gcn_pass_network_v1",
        "prediction": base,
        "graph": meta[0],
        "top_nodes": sorted(node_rows, key=lambda row: row["contribution"], reverse=True)[:5],
        "warning": "Node occlusion is local to one graph sample.",
    }
    return edge_payload, node_payload
