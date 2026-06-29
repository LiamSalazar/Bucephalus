from __future__ import annotations

from bucephalus.models.survival_model import train_hazard_model


def test_survival_model_interface_exists():
    assert callable(train_hazard_model)
