from __future__ import annotations

import json
from datetime import UTC, datetime

import polars as pl
import torch

from bucephalus.deep.sequence_dataset import build_padded_sequence_dataset
from bucephalus.deep.sequence_encoder import GRUSequenceModel
from bucephalus.utils.paths import ProjectPaths


def build_sequence_explanation(paths: ProjectPaths) -> dict:
    model_path = paths.models_outputs / "sequence_model.pt"
    events_path = paths.processed / "events.parquet"
    out_dir = paths.outputs / "explainability"
    out_dir.mkdir(parents=True, exist_ok=True)
    if not model_path.exists() or not events_path.exists():
        payload = {"status": "skipped", "reason": "sequence model or events missing"}
    else:
        payload = _sequence_occlusion(paths, model_path, events_path)
    (out_dir / "sequence_event_attribution_sample.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out_dir / "prediction_explanation_sample.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _sequence_occlusion(paths: ProjectPaths, model_path, events_path) -> dict:
    ckpt = torch.load(model_path, map_location="cpu")
    model = GRUSequenceModel(input_dim=int(ckpt["input_dim"]), hidden_dim=int(ckpt["hidden_dim"]), dropout=float(ckpt.get("dropout", 0.25)))
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    events = pl.read_parquet(events_path)
    x, _, mask, meta = build_padded_sequence_dataset(events, max_events=12)
    if len(meta) == 0:
        return {"status": "skipped", "reason": "sequence dataset empty"}
    sample_x = torch.tensor(x[:1], dtype=torch.float32)
    sample_mask = torch.tensor(mask[:1], dtype=torch.float32)
    with torch.no_grad():
        base = float(torch.sigmoid(model(sample_x, sample_mask))[0])
        rows = []
        valid = int(sample_mask[0].sum().item())
        for idx in range(valid):
            occluded = sample_x.clone()
            occluded[0, idx, :] = 0.0
            prob = float(torch.sigmoid(model(occluded, sample_mask))[0])
            rows.append({"event_rank": idx + 1, "contribution": abs(base - prob), "occluded_probability": prob, "method": "event_occlusion"})
    rows = sorted(rows, key=lambda row: row["contribution"], reverse=True)[:3]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "model": "sequence_gru_v1",
        "prediction": base,
        "match_id": meta[0].get("match_id"),
        "possession": meta[0].get("possession"),
        "top_events": rows,
        "warning": "Event occlusion is local to one sample; no attention weights are claimed.",
    }
