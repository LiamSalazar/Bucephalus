from __future__ import annotations

import polars as pl

from bucephalus.models.walk_forward import temporal_split


def test_walk_forward_split_has_no_overlap_and_temporal_order() -> None:
    df = pl.DataFrame({"match_date": [f"2024-01-{i:02d}" for i in range(1, 11)]})
    splits = temporal_split(df)
    assert not (set(splits["train"]) & set(splits["validation"]))
    assert not (set(splits["train"]) & set(splits["test"]))
    assert max(splits["train"]) < min(splits["validation"])
