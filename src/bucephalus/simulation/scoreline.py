from __future__ import annotations

import math


def poisson_pmf(k: int, lam: float) -> float:
    lam = max(0.05, float(lam))
    return math.exp(-lam) * lam**k / math.factorial(k)


def top_scorelines(home_goals: list[int], away_goals: list[int], limit: int = 5) -> list[dict]:
    counts = {}
    total = max(1, len(home_goals))
    for h, a in zip(home_goals, away_goals, strict=False):
        counts[(h, a)] = counts.get((h, a), 0) + 1
    rows = [{"scoreline": f"{h}-{a}", "probability": c / total} for (h, a), c in counts.items()]
    return sorted(rows, key=lambda row: row["probability"], reverse=True)[:limit]
