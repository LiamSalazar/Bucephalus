from __future__ import annotations

import numpy as np
import polars as pl

from bucephalus.utils.paths import ProjectPaths


NODE_FEATURES = ["touches", "passes_attempted", "pressures_received", "average_x", "average_y", "centrality_degree", "centrality_weighted_degree"]


def build_graph_arrays(paths: ProjectPaths, max_players: int = 18) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    nodes_path = paths.features / "pass_network_nodes.parquet"
    edges_path = paths.features / "pass_network_edges.parquet"
    dataset_path = paths.features / "graph_model_dataset.parquet"
    if not nodes_path.exists() or not edges_path.exists() or not dataset_path.exists():
        return np.empty((0, max_players, len(NODE_FEATURES))), np.empty((0, max_players, max_players)), np.empty((0, max_players)), np.empty((0,)), []
    nodes, edges, targets = pl.read_parquet(nodes_path), pl.read_parquet(edges_path), pl.read_parquet(dataset_path)
    xs, adjs, masks, ys, meta = [], [], [], [], []
    for row in targets.drop_nulls(["xg_for"]).to_dicts():
        g_nodes = nodes.filter((pl.col("match_id") == row["match_id"]) & (pl.col("team_id") == row["team_id"])).head(max_players)
        if g_nodes.is_empty():
            continue
        player_ids = g_nodes["player_id"].to_list()
        index = {pid: i for i, pid in enumerate(player_ids)}
        x = np.zeros((max_players, len(NODE_FEATURES)), dtype=np.float32)
        for i, nrow in enumerate(g_nodes.to_dicts()):
            vals = [float(nrow.get(f) or 0.0) for f in NODE_FEATURES]
            vals[3] /= 120.0
            vals[4] /= 80.0
            x[i] = vals
        adj = np.eye(max_players, dtype=np.float32)
        g_edges = edges.filter((pl.col("match_id") == row["match_id"]) & (pl.col("team_id") == row["team_id"]))
        for erow in g_edges.to_dicts():
            if erow["passer_id"] in index and erow["receiver_id"] in index:
                adj[index[erow["passer_id"]], index[erow["receiver_id"]]] += float(erow.get("pass_count") or 1.0)
        mask = np.zeros(max_players, dtype=np.float32)
        mask[: len(player_ids)] = 1.0
        xs.append(x)
        adjs.append(_normalize_adj(adj))
        masks.append(mask)
        ys.append(float(row["xg_for"]))
        meta.append({"match_id": row["match_id"], "team_id": row["team_id"], "team_name": row.get("team_name")})
    return np.asarray(xs), np.asarray(adjs), np.asarray(masks), np.asarray(ys, dtype=np.float32), meta


def _normalize_adj(adj: np.ndarray) -> np.ndarray:
    degree = adj.sum(axis=1)
    inv = np.power(np.clip(degree, 1e-9, None), -0.5)
    return (adj * inv[:, None]) * inv[None, :]
