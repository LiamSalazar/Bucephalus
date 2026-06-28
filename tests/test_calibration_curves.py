from __future__ import annotations

from bucephalus.models.calibration_curves import calibration_summary


def test_calibration_summary_probabilities_are_bounded() -> None:
    df = calibration_summary([0, 1, 1], [0.1, 0.6, 0.8], bins=3)
    assert not df.is_empty()
    assert df["mean_prediction"].min() >= 0
    assert df["mean_prediction"].max() <= 1
