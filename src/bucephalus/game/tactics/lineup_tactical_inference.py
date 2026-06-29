from __future__ import annotations

from bucephalus.game.chemistry import calculate_chemistry


def infer_tactical_baseline_from_lineup(players: list[dict], formation: str = "4-3-3", manual_overrides: dict[str, float] | None = None) -> dict:
    attrs = [p.get("attributes", {}) for p in players]
    names = {p["id"] for p in players}
    chemistry = calculate_chemistry(players, formation)
    pressing = _avg(attrs, ["pressing", "coverage", "fatigue"])
    possession = _avg(attrs, ["control", "association", "press_resistance"])
    directness = _avg(attrs, ["pace", "transition", "finishing"])
    transition = _avg(attrs, ["transition", "pace", "progression"])
    width = _avg(attrs, ["width", "dribbling", "creation"])
    centrality = _avg(attrs, ["control", "centrality", "association"])
    compactness = _avg(attrs, ["compactness", "defense", "coverage"])
    fatigue = _avg(attrs, ["fatigue", "coverage"])
    defensive_exposure = _clip(0.65 + directness * 0.25 - compactness * 0.35 - _avg(attrs, ["defense"]) * 0.15)
    warnings = list(chemistry["warnings"])
    if {"haaland", "mbappe"}.issubset(names):
        pressing = min(pressing, 0.58)
        possession = min(possession, 0.66)
        transition = max(transition, 0.82)
        defensive_exposure = max(defensive_exposure, 0.62)
        warnings.append("High attacking power but lower collective pressing and association.")
    if {"rodri", "pedri", "vitinha"}.intersection(names):
        possession = max(possession, 0.78)
        centrality = max(centrality, 0.76)
    result = {
        "pressing_predicted": _clip(pressing),
        "possession_predicted": _clip(possession),
        "directness_predicted": _clip(directness),
        "transition_predicted": _clip(transition),
        "width_predicted": _clip(width),
        "centrality_predicted": _clip(centrality),
        "compactness_predicted": _clip(compactness),
        "fatigue_resistance_predicted": _clip(fatigue),
        "defensive_exposure_predicted": _clip(defensive_exposure),
        "chemistry_score": chemistry["chemistry_score"],
        "role_balance_score": _role_balance(players),
        "tactical_feasibility_score": _clip((chemistry["chemistry_score"] + compactness + fatigue) / 3),
        "chemistry": chemistry,
        "manual_override": bool(manual_overrides),
        "realism_warning": False,
        "warnings": warnings,
    }
    if manual_overrides:
        _apply_overrides(result, manual_overrides)
    return result


def _apply_overrides(result: dict, overrides: dict[str, float]) -> None:
    for key, value in overrides.items():
        target = key if key.endswith("_predicted") else f"{key}_predicted"
        if target in result:
            if target == "pressing_predicted" and (value > result[target] + 0.18 or value >= 0.9):
                result["realism_warning"] = True
                result["warnings"].append("Requested high press is unlikely with selected lineup. Simulation will increase fatigue and transition exposure.")
                result["fatigue_resistance_predicted"] = _clip(result["fatigue_resistance_predicted"] - 0.12)
                result["defensive_exposure_predicted"] = _clip(result["defensive_exposure_predicted"] + 0.15)
            result[target] = _clip(value)


def _avg(attrs: list[dict], keys: list[str]) -> float:
    vals = [float(a.get(k, 0.55)) for a in attrs for k in keys if k in a]
    return sum(vals) / len(vals) if vals else 0.55


def _role_balance(players: list[dict]) -> float:
    positions = [p.get("canonical_position") for p in players]
    return _clip(0.25 * ("GK" in positions) + 0.25 * (sum(p in {"CB", "LB", "RB"} for p in positions) >= 3) + 0.25 * (sum(p in {"DM", "CM", "AM"} for p in positions) >= 2) + 0.25 * (sum(p in {"LW", "RW", "CF", "ST"} for p in positions) <= 4))


def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
