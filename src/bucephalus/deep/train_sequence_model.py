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
    events = _events_with_match_dates(paths, pl.read_parquet(events_path))
    x, y, mask, meta = build_padded_sequence_dataset(events, max_events=12)
    if len(y) < 100 or len(set(y.tolist())) < 2:
        return _write_skipped(paths, f"insufficient sequence rows/classes: rows={len(y)}")
    order = _temporal_order(meta)
    x, y, mask = x[order], y[order], mask[order]
    meta = [meta[i] for i in order]
    torch.manual_seed(42)
    train_idx, val_idx, test_idx, split_payload = _temporal_splits(meta)
    if len(train_idx) == 0 or len(test_idx) == 0:
        return _write_skipped(paths, "insufficient temporal split coverage")
    model = GRUSequenceModel(input_dim=x.shape[-1], hidden_dim=24, dropout=0.25)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([(len(y[train_idx]) - y[train_idx].sum()) / max(1.0, y[train_idx].sum())], dtype=torch.float32))
    tx = torch.tensor(x[train_idx], dtype=torch.float32)
    ty = torch.tensor(y[train_idx], dtype=torch.float32)
    tm = torch.tensor(mask[train_idx], dtype=torch.float32)
    model.train()
    for _ in range(12):
        optimizer.zero_grad()
        loss = criterion(model(tx, tm), ty)
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        prob = torch.sigmoid(model(torch.tensor(x[test_idx], dtype=torch.float32), torch.tensor(mask[test_idx], dtype=torch.float32))).numpy()
        val_prob = torch.sigmoid(model(torch.tensor(x[val_idx], dtype=torch.float32), torch.tensor(mask[val_idx], dtype=torch.float32))).numpy() if len(val_idx) else np.asarray([])
    y_val = y[test_idx]
    metrics = {
        "status": "trained",
        "model_type": "pytorch_gru_sequence_model",
        "rows": int(len(y)),
        "train_rows": int(len(train_idx)),
        "validation_rows": int(len(val_idx)),
        "test_rows": int(len(test_idx)),
        "log_loss": float(log_loss(y_val, prob, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y_val, prob)),
        "roc_auc": float(roc_auc_score(y_val, prob)) if len(set(y_val.tolist())) > 1 else None,
        "pr_auc": float(average_precision_score(y_val, prob)),
        "validation_brier_score": float(brier_score_loss(y[val_idx], val_prob)) if len(val_idx) else None,
        "positive_rate": float(y.mean()),
        "survival_bias_guard": True,
        "target_type": "shot_probability_sequence",
        "horizon_type": "event_horizon_proxy",
        "temporal_split": True,
    }
    (paths.evaluation_outputs / "sequence_temporal_split.json").write_text(json.dumps(split_payload, indent=2), encoding="utf-8")
    artifact = paths.models_outputs / "sequence_model.pt"
    torch.save({"state_dict": model.state_dict(), "input_dim": int(x.shape[-1]), "hidden_dim": 24, "dropout": 0.25}, artifact)
    registry = {
        "generated_at": datetime.now(UTC).isoformat(),
        "models": [{
            "model_id": "sequence_gru_v1",
            "model_type": "PyTorch_GRU",
            "training_data_hash": _hash_array(x, y),
            "feature_set_version": "sequence_events_padded_v1",
            "train_period": [split_payload.get("train_start_date"), split_payload.get("train_end_date")],
            "validation_period": [split_payload.get("validation_start_date"), split_payload.get("validation_end_date")],
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
    prediction_rows = [
            {
                **meta_row,
                "shot_probability": float(p),
                "conditional_xg": float(p * 0.12),
                "expected_possession_value": float(p * 0.12 - (1 - p) * 0.015),
                "survival_bias_guard": True,
                "target_type": "shot_probability_sequence",
                "horizon_type": "event_horizon_proxy",
            }
            for meta_row, p in zip([meta[i] for i in test_idx], prob, strict=False)
        ]
    pl.DataFrame(prediction_rows, infer_schema_length=None).write_parquet(paths.evaluation_outputs / "sequence_predictions.parquet")
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


def _events_with_match_dates(paths: ProjectPaths, events: pl.DataFrame) -> pl.DataFrame:
    matches_path = paths.processed / "matches.parquet"
    if "match_date" in events.columns or not matches_path.exists():
        return events
    matches = pl.read_parquet(matches_path)
    if "match_id" not in matches.columns or "match_date" not in matches.columns:
        return events
    return events.join(matches.select(["match_id", "match_date"]), on="match_id", how="left")


def _temporal_order(meta: list[dict]) -> np.ndarray:
    def key(idx: int) -> tuple[str, int, int]:
        row = meta[idx]
        date = str(row.get("target_match_date") or "9999-12-31")
        return date, int(row.get("match_id") or 0), int(row.get("event_index") or 0)

    return np.asarray(sorted(range(len(meta)), key=key), dtype=int)


def _temporal_splits(meta: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    dates = sorted({str(row.get("target_match_date") or "9999-12-31") for row in meta})
    if len(dates) >= 3:
        train_cut = max(1, int(len(dates) * 0.6))
        val_cut = max(train_cut + 1, int(len(dates) * 0.8))
        train_dates = set(dates[:train_cut])
        val_dates = set(dates[train_cut:val_cut])
        test_dates = set(dates[val_cut:])
    else:
        n = len(meta)
        train_dates = val_dates = test_dates = set()
        train_idx = np.arange(0, int(n * 0.6), dtype=int)
        val_idx = np.arange(int(n * 0.6), int(n * 0.8), dtype=int)
        test_idx = np.arange(int(n * 0.8), n, dtype=int)
        return train_idx, val_idx, test_idx, _split_payload(meta, train_idx, val_idx, test_idx, fallback=True)
    train_idx = np.asarray([i for i, row in enumerate(meta) if str(row.get("target_match_date") or "9999-12-31") in train_dates], dtype=int)
    val_idx = np.asarray([i for i, row in enumerate(meta) if str(row.get("target_match_date") or "9999-12-31") in val_dates], dtype=int)
    test_idx = np.asarray([i for i, row in enumerate(meta) if str(row.get("target_match_date") or "9999-12-31") in test_dates], dtype=int)
    return train_idx, val_idx, test_idx, _split_payload(meta, train_idx, val_idx, test_idx, fallback=False)


def _split_payload(meta: list[dict], train_idx: np.ndarray, val_idx: np.ndarray, test_idx: np.ndarray, fallback: bool) -> dict:
    def dates(indices: np.ndarray) -> list[str]:
        values = [str(meta[int(i)].get("target_match_date") or "9999-12-31") for i in indices]
        return sorted(set(values))

    train_dates, val_dates, test_dates = dates(train_idx), dates(val_idx), dates(test_idx)
    no_overlap = (
        (not train_dates or not val_dates or max(train_dates) < min(val_dates))
        and (not val_dates or not test_dates or max(val_dates) < min(test_dates))
        and not (set(train_dates) & set(val_dates) or set(train_dates) & set(test_dates) or set(val_dates) & set(test_dates))
    )
    return {
        "train_start_date": train_dates[0] if train_dates else None,
        "train_end_date": train_dates[-1] if train_dates else None,
        "validation_start_date": val_dates[0] if val_dates else None,
        "validation_end_date": val_dates[-1] if val_dates else None,
        "test_start_date": test_dates[0] if test_dates else None,
        "test_end_date": test_dates[-1] if test_dates else None,
        "train_rows": int(len(train_idx)),
        "validation_rows": int(len(val_idx)),
        "test_rows": int(len(test_idx)),
        "train_matches": len(train_dates),
        "validation_matches": len(val_dates),
        "test_matches": len(test_dates),
        "no_temporal_overlap": bool(no_overlap),
        "fallback_index_split": fallback,
    }


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "skipped", "reason": reason, "survival_bias_guard": True}
    (paths.evaluation_outputs / "sequence_model_metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (paths.evaluation_outputs / "sequence_model_insufficient_data.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (paths.evaluation_outputs / "sequence_temporal_split.json").write_text(json.dumps({"status": "skipped", "reason": reason}, indent=2), encoding="utf-8")
    (paths.models_outputs / "sequence_model_registry.json").write_text(json.dumps({"models": [{"status": "insufficient_data", "reason": reason, "training_data_hash": None}]}, indent=2), encoding="utf-8")
    pl.DataFrame(schema={"shot_probability": pl.Float64, "conditional_xg": pl.Float64, "expected_possession_value": pl.Float64, "survival_bias_guard": pl.Boolean}).write_parquet(paths.evaluation_outputs / "sequence_predictions.parquet")
    return payload
