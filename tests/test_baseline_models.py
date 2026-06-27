from __future__ import annotations

import polars as pl

from bucephalus.models.baseline_goals import poisson_rolling_predictions, result_probabilities


def test_poisson_probabilities_are_valid() -> None:
    probs = result_probabilities(1.4, 1.1)
    assert all(0 <= p <= 1 for p in probs)
    assert abs(sum(probs) - 1) < 1e-6


def test_poisson_predictions_no_critical_nan() -> None:
    train = pl.DataFrame({"home_score": [1, 2], "away_score": [0, 1]})
    test = pl.DataFrame({"statsbomb_match_id": [1], "match_date": ["2024-01-01"], "home_score": [1], "away_score": [1]})
    preds = poisson_rolling_predictions(train, test)
    assert preds["expected_home_goals"].null_count() == 0
    assert preds["prob_home_win"].null_count() == 0
