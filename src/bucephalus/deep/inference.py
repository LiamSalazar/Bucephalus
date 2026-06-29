from __future__ import annotations

import json
from datetime import UTC, datetime

import numpy as np
import polars as pl
import torch

from bucephalus.deep.sequence_dataset import build_padded_sequence_dataset
from bucephalus.deep.sequence_encoder import GRUSequenceModel
from bucephalus.utils.paths import ProjectPaths


def run_mc_dropout(paths: ProjectPaths, n_mc_samples: int = 50, dropout_rate: float = 0.25) -> dict:
    artifact_path = paths.models_outputs / "sequence_model.pt"
    events_path = paths.processed / "events.parquet"
    if not artifact_path.exists() or not events_path.exists():
        return _write_skipped(paths, "sequence model checkpoint or events missing")
    checkpoint = torch.load(artifact_path, map_location="cpu", weights_only=False)
    model = GRUSequenceModel(checkpoint["input_dim"], checkpoint["hidden_dim"], dropout_rate)
    model.load_state_dict(checkpoint["state_dict"], strict=False)
    x, _, mask, meta = build_padded_sequence_dataset(pl.read_parquet(events_path), max_events=12)
    if len(x) == 0:
        return _write_skipped(paths, "sequence dataset empty")
    x_t = torch.tensor(x[:200], dtype=torch.float32)
    m_t = torch.tensor(mask[:200], dtype=torch.float32)
    samples = []
    model.train()
    with torch.no_grad():
        for _ in range(n_mc_samples):
            samples.append(torch.sigmoid(model(x_t, m_t)).numpy())
    arr = np.vstack(samples)
    out = pl.DataFrame(
        [
            {
                **meta_row,
                "prediction_mean": float(mean),
                "prediction_std": float(std),
                "p5": float(p5),
                "p50": float(p50),
                "p95": float(p95),
                "epistemic_uncertainty": float(std),
                "n_mc_samples": n_mc_samples,
                "dropout_rate": dropout_rate,
                "model_id": "sequence_gru_v1",
            }
            for meta_row, mean, std, p5, p50, p95 in zip(
                meta[:200],
                arr.mean(axis=0),
                arr.std(axis=0),
                np.percentile(arr, 5, axis=0),
                np.percentile(arr, 50, axis=0),
                np.percentile(arr, 95, axis=0),
                strict=False,
            )
        ]
    )
    out.write_parquet(paths.evaluation_outputs / "mc_dropout_uncertainty.parquet")
    summary = {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "completed",
        "rows": out.height,
        "n_mc_samples": n_mc_samples,
        "dropout_rate": dropout_rate,
        "model_id": "sequence_gru_v1",
        "mean_epistemic_uncertainty": float(out["epistemic_uncertainty"].mean()),
    }
    (paths.evaluation_outputs / "mc_dropout_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _write_skipped(paths: ProjectPaths, reason: str) -> dict:
    payload = {"status": "skipped", "reason": reason}
    (paths.evaluation_outputs / "mc_dropout_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    pl.DataFrame(schema={"prediction_mean": pl.Float64, "prediction_std": pl.Float64, "p5": pl.Float64, "p50": pl.Float64, "p95": pl.Float64}).write_parquet(paths.evaluation_outputs / "mc_dropout_uncertainty.parquet")
    return payload
