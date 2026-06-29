from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error

from bucephalus.graphs.graph_dataset import build_graph_arrays
from bucephalus.graphs.gnn_model import ManualGCN
from bucephalus.utils.paths import ProjectPaths


def train_gnn_model(paths: ProjectPaths) -> dict:
    paths.ensure()
    x, adj, mask, y, meta = build_graph_arrays(paths)
    if len(y) < 12:
        return _write_skipped(paths, f"insufficient graphs: {len(y)}")
    split = int(len(y) * 0.75)
    torch.manual_seed(42)
    model = ManualGCN(input_dim=x.shape[-1], hidden_dim=16, dropout=0.2)
    opt = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = torch.nn.MSELoss()
    tx, ta, tm, ty = map(lambda z: torch.tensor(z, dtype=torch.float32), [x[:split], adj[:split], mask[:split], y[:split]])
    model.train()
    for _ in range(80):
        opt.zero_grad()
        loss = loss_fn(model(tx, ta, tm), ty)
        loss.backward()
        opt.step()
    model.eval()
    with torch.no_grad():
        pred = model(torch.tensor(x[split:], dtype=torch.float32), torch.tensor(adj[split:], dtype=torch.float32), torch.tensor(mask[split:], dtype=torch.float32)).numpy()
        no_edge = model(torch.tensor(x[split:], dtype=torch.float32), torch.eye(adj.shape[-1]).repeat(len(y)-split,1,1), torch.tensor(mask[split:], dtype=torch.float32)).numpy()
        perm_adj = torch.tensor(adj[split:].copy(), dtype=torch.float32)
        perm_adj = perm_adj[torch.randperm(perm_adj.shape[0])]
        perm = model(torch.tensor(x[split:], dtype=torch.float32), perm_adj, torch.tensor(mask[split:], dtype=torch.float32)).numpy()
    baseline = np.full_like(y[split:], y[:split].mean())
    metrics = _metrics(y[split:], pred, baseline, no_edge, perm)
    status = "champion" if (
        metrics["gnn_mae"] < metrics["baseline_mae"]
        and metrics["gnn_mae"] <= metrics["no_edge_mae"]
        and metrics["gnn_mae"] <= metrics["permuted_edge_mae"]
    ) else ("candidate" if metrics["gnn_mae"] < metrics["baseline_mae"] else "experimental")
    metrics["status"] = status
    artifact = paths.models_outputs / "gnn_model.pt"
    torch.save({"state_dict": model.state_dict(), "input_dim": x.shape[-1], "hidden_dim": 16}, artifact)
    pl.DataFrame([{**m, "actual_xg": float(a), "predicted_xg": float(p), "no_edge_predicted_xg": float(ne), "permuted_edge_predicted_xg": float(pe)} for m, a, p, ne, pe in zip(meta[split:], y[split:], pred, no_edge, perm, strict=False)]).write_parquet(paths.evaluation_outputs / "gnn_predictions.parquet")
    pl.DataFrame({"embedding_id": list(range(len(pred))), "embedding_0": pred}).write_parquet(paths.evaluation_outputs / "gnn_embeddings.parquet")
    pl.DataFrame([{"model": "global_baseline", "mae": metrics["baseline_mae"]}, {"model": "gcn_adjacency", "mae": metrics["gnn_mae"]}, {"model": "gcn_no_edge", "mae": metrics["no_edge_mae"]}, {"model": "gcn_permuted_edges", "mae": metrics["permuted_edge_mae"]}]).write_csv(paths.evaluation_outputs / "gnn_model_comparison.csv")
    registry = {"generated_at": datetime.now(UTC).isoformat(), "models": [{"model_id": "manual_gcn_pass_network_v1", "model_type": "PyTorch_manual_GCN", "training_data_hash": _hash_arrays(x, adj, y), "feature_set_version": "pass_network_v1", "train_period": None, "validation_period": None, "model_hyperparameters": {"hidden_dim": 16, "epochs": 80}, "metrics": metrics, "git_commit": _git_commit(paths), "created_at": datetime.now(UTC).isoformat(), "artifact_path": str(artifact), "status": status, "limitations": ["receiver is next-event proxy"]}]}
    (paths.models_outputs / "gnn_model_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    (paths.evaluation_outputs / "gnn_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def evaluate_gnn_model(paths: ProjectPaths) -> dict:
    path = paths.evaluation_outputs / "gnn_metrics.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else train_gnn_model(paths)


def _metrics(y, pred, baseline, no_edge, perm):
    return {
        "rows": int(len(y)),
        "target": "xg_for",
        "baseline_mae": float(mean_absolute_error(y, baseline)),
        "gnn_mae": float(mean_absolute_error(y, pred)),
        "no_edge_mae": float(mean_absolute_error(y, no_edge)),
        "permuted_edge_mae": float(mean_absolute_error(y, perm)),
        "gnn_rmse": float(mean_squared_error(y, pred) ** 0.5),
        "permuted_edges_sanity": "passed" if mean_absolute_error(y, perm) >= mean_absolute_error(y, pred) * 0.8 else "warning",
    }


def _hash_arrays(*arrays) -> str:
    import hashlib
    digest = hashlib.sha256()
    for arr in arrays:
        digest.update(arr.tobytes())
    return digest.hexdigest()


def _git_commit(paths: ProjectPaths) -> str | None:
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=paths.root, text=True).strip()
    except Exception:
        return None


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "insufficient_data", "reason": reason, "training_data_hash": None}
    (paths.evaluation_outputs / "gnn_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (paths.models_outputs / "gnn_model_registry.json").write_text(json.dumps({"models": [payload]}, indent=2), encoding="utf-8")
    pl.DataFrame().write_parquet(paths.evaluation_outputs / "gnn_predictions.parquet")
    pl.DataFrame().write_parquet(paths.evaluation_outputs / "gnn_embeddings.parquet")
    pl.DataFrame([{"model": "skipped", "mae": None}]).write_csv(paths.evaluation_outputs / "gnn_model_comparison.csv")
    return payload
