from __future__ import annotations

import polars as pl


def rolling_prior_features(df: pl.DataFrame, group_col: str, date_col: str, value_cols: list[str], windows: list[int], prefix: str) -> pl.DataFrame:
    if df.is_empty():
        return pl.DataFrame()
    rows = []
    for _, group in df.sort([group_col, date_col, "statsbomb_match_id"]).group_by(group_col, maintain_order=True):
        history: list[dict] = []
        for row in group.to_dicts():
            out = {
                group_col: row[group_col],
                "statsbomb_match_id": row["statsbomb_match_id"],
                "feature_cutoff_date": history[-1].get(date_col) if history else None,
                "historical_matches_available": len(history),
            }
            for col in value_cols:
                vals = [h.get(col) for h in history if h.get(col) is not None]
                for window in windows:
                    window_vals = vals[-window:]
                    out[f"rolling_{col}_{window}"] = sum(window_vals) / len(window_vals) if window_vals else None
                if len(vals) >= 3:
                    mean = sum(vals) / len(vals)
                    out[f"{prefix}_{col}_volatility"] = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
            rows.append(out)
            history.append(row)
    return pl.DataFrame(rows) if rows else pl.DataFrame()
