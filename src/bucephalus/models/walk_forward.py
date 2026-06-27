from __future__ import annotations

import json

import polars as pl


def temporal_split(df: pl.DataFrame, date_col: str = "match_date") -> dict[str, list[int]]:
    ordered = df.with_row_index("row_id").sort(date_col)
    n = ordered.height
    if n == 0:
        return {"train": [], "validation": [], "test": []}
    train_end = max(1, int(n * 0.6))
    val_end = max(train_end + 1, int(n * 0.8)) if n >= 3 else train_end
    val_end = min(val_end, n)
    return {
        "train": ordered[:train_end]["row_id"].to_list(),
        "validation": ordered[train_end:val_end]["row_id"].to_list(),
        "test": ordered[val_end:]["row_id"].to_list() if val_end < n else ordered[train_end:]["row_id"].to_list(),
    }


def split_summary(df: pl.DataFrame, splits: dict[str, list[int]], date_col: str = "match_date") -> dict:
    rows = []
    indexed = df.with_row_index("row_id")
    for name, ids in splits.items():
        part = indexed.filter(pl.col("row_id").is_in(ids))
        rows.append(
            {
                "split": name,
                "rows": part.height,
                "min_date": part[date_col].min() if part.height else None,
                "max_date": part[date_col].max() if part.height else None,
            }
        )
    return {"splits": rows, "no_overlap": len(set().union(*[set(v) for v in splits.values()])) == sum(len(v) for v in splits.values())}


def write_split_summary(path, df: pl.DataFrame, splits: dict[str, list[int]]) -> None:
    path.write_text(json.dumps(split_summary(df, splits), indent=2), encoding="utf-8")
