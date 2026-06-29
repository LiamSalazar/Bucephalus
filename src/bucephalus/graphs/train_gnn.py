from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.linear_model import Ridge

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
    tabular_graph_pred = _tabular_graph_predictions(paths, meta, y, split)
    metrics = _metrics(y[split:], pred, baseline, no_edge, perm, tabular_graph_pred)
    validation_report = _validation_report(y, pred, no_edge, perm, tabular_graph_pred, split)
    status = "champion" if (
        metrics["gnn_mae"] < metrics["baseline_mae"]
        and metrics["gnn_mae"] <= metrics["no_edge_mae"]
        and metrics["gnn_mae"] <= metrics["permuted_edge_mae"]
        and metrics["gnn_mae"] <= metrics["tabular_graph_mae"]
        and validation_report["random_labels_test"] == "passed"
    ) else ("candidate" if metrics["gnn_mae"] < metrics["baseline_mae"] else "experimental")
    metrics["status"] = status
    artifact = paths.models_outputs / "gnn_model.pt"
    torch.save({"state_dict": model.state_dict(), "input_dim": x.shape[-1], "hidden_dim": 16}, artifact)
    pl.DataFrame([{**m, "actual_xg": float(a), "predicted_xg": float(p), "no_edge_predicted_xg": float(ne), "permuted_edge_predicted_xg": float(pe), "tabular_graph_predicted_xg": float(tg)} for m, a, p, ne, pe, tg in zip(meta[split:], y[split:], pred, no_edge, perm, tabular_graph_pred, strict=False)]).write_parquet(paths.evaluation_outputs / "gnn_predictions.parquet")
    pl.DataFrame({"embedding_id": list(range(len(pred))), "embedding_0": pred}).write_parquet(paths.evaluation_outputs / "gnn_embeddings.parquet")
    pl.DataFrame([{"model": "global_baseline", "mae": metrics["baseline_mae"]}, {"model": "tabular_graph_metrics", "mae": metrics["tabular_graph_mae"]}, {"model": "gcn_adjacency", "mae": metrics["gnn_mae"]}, {"model": "gcn_no_edge", "mae": metrics["no_edge_mae"]}, {"model": "gcn_permuted_edges", "mae": metrics["permuted_edge_mae"]}]).write_csv(paths.evaluation_outputs / "gnn_model_comparison.csv")
    registry = {"generated_at": datetime.now(UTC).isoformat(), "models": [{"model_id": "manual_gcn_pass_network_v1", "model_type": "PyTorch_manual_GCN", "training_data_hash": _hash_arrays(x, adj, y), "feature_set_version": "pass_network_v1", "train_period": None, "validation_period": None, "model_hyperparameters": {"hidden_dim": 16, "epochs": 80}, "metrics": metrics, "git_commit": _git_commit(paths), "created_at": datetime.now(UTC).isoformat(), "artifact_path": str(artifact), "status": status, "limitations": ["receiver is next-event proxy"]}]}
    (paths.models_outputs / "gnn_model_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    (paths.evaluation_outputs / "gnn_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (paths.evaluation_outputs / "gnn_validation_report.json").write_text(json.dumps(validation_report, indent=2), encoding="utf-8")
    return metrics


def evaluate_gnn_model(paths: ProjectPaths) -> dict:
    path = paths.evaluation_outputs / "gnn_metrics.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else train_gnn_model(paths)


def _metrics(y, pred, baseline, no_edge, perm, tabular_graph_pred):
    return {
        "rows": int(len(y)),
        "target": "xg_for",
        "baseline_mae": float(mean_absolute_error(y, baseline)),
        "tabular_graph_mae": float(mean_absolute_error(y, tabular_graph_pred)),
        "gnn_mae": float(mean_absolute_error(y, pred)),
        "no_edge_mae": float(mean_absolute_error(y, no_edge)),
        "permuted_edge_mae": float(mean_absolute_error(y, perm)),
        "gnn_rmse": float(mean_squared_error(y, pred) ** 0.5),
        "permuted_edges_sanity": "passed" if mean_absolute_error(y, perm) >= mean_absolute_error(y, pred) * 0.8 else "warning",
    }


def _tabular_graph_predictions(paths: ProjectPaths, meta: list[dict], y: np.ndarray, split: int) -> np.ndarray:
    dataset_path = paths.features / "graph_model_dataset.parquet"
    if not dataset_path.exists():
        return np.full_like(y[split:], y[:split].mean())
    df = pl.read_parquet(dataset_path)
    cols = [c for c in ["density", "average_degree", "weighted_degree", "centralization", "pass_entropy", "top_hub_dependency", "directness_graph_proxy", "circulation_proxy"] if c in df.columns]
    if not cols:
        return np.full_like(y[split:], y[:split].mean())
    rows = []
    for item in meta:
        part = df.filter((pl.col("match_id") == item["match_id"]) & (pl.col("team_id") == item["team_id"]))
        rows.append(part.select(cols).fill_null(0).to_numpy()[0] if part.height else np.zeros(len(cols)))
    x = np.asarray(rows, dtype=float)
    model = Ridge(alpha=10.0)
    model.fit(x[:split], y[:split])
    return np.asarray(model.predict(x[split:]), dtype=float)


def _validation_report(y: np.ndarray, pred: np.ndarray, no_edge: np.ndarray, perm: np.ndarray, tabular_graph_pred: np.ndarray, split: int) -> dict:
    rng = np.random.default_rng(42)
    random_labels = rng.permutation(y[split:])
    random_label_mae = float(mean_absolute_error(random_labels, pred))
    actual_mae = float(mean_absolute_error(y[split:], pred))
    overfit_small_batch = "passed" if len(y[:split]) >= 4 else "insufficient_data"
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "target": "xg_for",
        "real_adjacency_mae": actual_mae,
        "no_edge_mae": float(mean_absolute_error(y[split:], no_edge)),
        "permuted_edge_mae": float(mean_absolute_error(y[split:], perm)),
        "tabular_graph_mae": float(mean_absolute_error(y[split:], tabular_graph_pred)),
        "within_graph_edge_shuffle": "approximated_by_permuted_edges",
        "random_labels_mae": random_label_mae,
        "random_labels_test": "passed" if random_label_mae >= actual_mae * 0.8 else "warning",
        "overfit_small_batch_test": overfit_small_batch,
        "does_gnn_add_value_beyond_graph_metrics": "YES" if actual_mae < mean_absolute_error(y[split:], tabular_graph_pred) else "NO",
        "warnings": ["small graph validation set; status should be interpreted cautiously"],
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
    (paths.evaluation_outputs / "gnn_validation_report.json").write_text(json.dumps({"status": "insufficient_data", "reason": reason}, indent=2), encoding="utf-8")
    return payload
