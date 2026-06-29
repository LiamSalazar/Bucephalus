from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl
import torch
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from torch import nn

from bucephalus.deep.sequence_dataset import build_padded_sequence_dataset
from bucephalus.deep.sequence_encoder import GRUSequenceModel
from bucephalus.utils.paths import ProjectPaths


def train_sequence_model(paths: ProjectPaths) -> dict:
    paths.ensure()
    events_path = paths.processed / "events.parquet"
    if not events_path.exists():
        return _write_skipped(paths, "events.parquet missing")
    x, y, mask, meta = build_padded_sequence_dataset(pl.read_parquet(events_path), max_events=12)
    if len(y) < 100 or len(set(y.tolist())) < 2:
        return _write_skipped(paths, f"insufficient sequence rows/classes: rows={len(y)}")
    torch.manual_seed(42)
    split = int(len(y) * 0.75)
    model = GRUSequenceModel(input_dim=x.shape[-1], hidden_dim=24, dropout=0.25)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([(len(y[:split]) - y[:split].sum()) / max(1.0, y[:split].sum())], dtype=torch.float32))
    tx = torch.tensor(x[:split], dtype=torch.float32)
    ty = torch.tensor(y[:split], dtype=torch.float32)
    tm = torch.tensor(mask[:split], dtype=torch.float32)
    model.train()
    for _ in range(12):
        optimizer.zero_grad()
        loss = criterion(model(tx, tm), ty)
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        prob = torch.sigmoid(model(torch.tensor(x[split:], dtype=torch.float32), torch.tensor(mask[split:], dtype=torch.float32))).numpy()
    y_val = y[split:]
    metrics = {
        "status": "trained",
        "model_type": "pytorch_gru_sequence_model",
        "rows": int(len(y)),
        "log_loss": float(log_loss(y_val, prob, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y_val, prob)),
        "roc_auc": float(roc_auc_score(y_val, prob)) if len(set(y_val.tolist())) > 1 else None,
        "pr_auc": float(average_precision_score(y_val, prob)),
        "positive_rate": float(y.mean()),
        "survival_bias_guard": True,
        "target_type": "shot_probability_sequence",
        "horizon_type": "possession_suffix_proxy",
    }
    artifact = paths.models_outputs / "sequence_model.pt"
    torch.save({"state_dict": model.state_dict(), "input_dim": int(x.shape[-1]), "hidden_dim": 24, "dropout": 0.25}, artifact)
    registry = {
        "generated_at": datetime.now(UTC).isoformat(),
        "models": [{
            "model_id": "sequence_gru_v1",
            "model_type": "PyTorch_GRU",
            "training_data_hash": _hash_array(x, y),
            "feature_set_version": "sequence_events_padded_v1",
            "train_period": None,
            "validation_period": None,
            "model_hyperparameters": {"hidden_dim": 24, "dropout": 0.25, "epochs": 12, "lr": 0.01},
            "metrics": metrics,
            "git_commit": _git_commit(paths),
            "created_at": datetime.now(UTC).isoformat(),
            "artifact_path": str(artifact),
            "status": "candidate",
            "limitations": ["small event dataset for deep sequence learning"],
        }],
    }
    (paths.models_outputs / "sequence_model_registry.json").write_text(json.dumps(registry, indent=2), encoding="utf-8")
    pl.DataFrame(
        [
            {
                **meta_row,
                "shot_probability": float(p),
                "conditional_xg": float(p * 0.12),
                "expected_possession_value": float(p * 0.12 - (1 - p) * 0.015),
                "survival_bias_guard": True,
                "target_type": "shot_probability_sequence",
                "horizon_type": "possession_suffix_proxy",
            }
            for meta_row, p in zip(meta[split:], prob, strict=False)
        ]
    ).write_parquet(paths.evaluation_outputs / "sequence_predictions.parquet")
    (paths.evaluation_outputs / "sequence_model_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def evaluate_sequence_model(paths: ProjectPaths) -> dict:
    path = paths.evaluation_outputs / "sequence_model_metrics.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else train_sequence_model(paths)


def _hash_array(x: np.ndarray, y: np.ndarray) -> str:
    import hashlib
    digest = hashlib.sha256()
    digest.update(x.tobytes())
    digest.update(y.tobytes())
    return digest.hexdigest()


def _git_commit(paths: ProjectPaths) -> str | None:
    import subprocess
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=paths.root, text=True).strip()
    except Exception:
        return None


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "skipped", "reason": reason, "survival_bias_guard": True}
    (paths.evaluation_outputs / "sequence_model_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (paths.models_outputs / "sequence_model_registry.json").write_text(json.dumps({"models": [{"status": "insufficient_data", "reason": reason, "training_data_hash": None}]}, indent=2), encoding="utf-8")
    pl.DataFrame(schema={"shot_probability": pl.Float64, "conditional_xg": pl.Float64, "expected_possession_value": pl.Float64, "survival_bias_guard": pl.Boolean}).write_parquet(paths.evaluation_outputs / "sequence_predictions.parquet")
    return payload
