from __future__ import annotations


def combine_uncertainty(*values: float | None) -> float:
    clean = [float(v) for v in values if v is not None]
    return sum(v * v for v in clean) ** 0.5
