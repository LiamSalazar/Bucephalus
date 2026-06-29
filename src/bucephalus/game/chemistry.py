from __future__ import annotations


def calculate_chemistry(players: list[dict], formation: str = "4-3-3") -> dict:
    attrs = [p.get("attributes", {}) for p in players]
    names = {p["id"] for p in players}
    attack = _avg(attrs, ["finishing", "creation", "dribbling"])
    midfield = _avg(attrs, ["control", "association", "press_resistance", "progression"])
    defense = _avg(attrs, ["defense", "compactness", "goalkeeping"])
    pressing = _avg(attrs, ["pressing", "coverage", "fatigue"])
    progression = _avg(attrs, ["progression", "creation", "transition"])
    overlap_penalty = 0.0
    warnings: list[str] = []
    if {"haaland", "mbappe"}.issubset(names):
        overlap_penalty += 0.12
        warnings.append("Haaland + Mbappe creates elite transition/finishing but can reduce association and collective pressing.")
    if {"haaland", "vinicius"}.issubset(names):
        progression += 0.08
        warnings.append("Vinicius + Haaland projects strong creator-finisher complementarity.")
    if {"rodri", "pedri", "vitinha"}.intersection(names):
        midfield += 0.06
    zone_coverage = _formation_balance(players, formation)
    score = _clip((attack + midfield + defense + pressing + progression + zone_coverage) / 6 - overlap_penalty)
    return {
        "chemistry_score": score,
        "attack_chemistry": _clip(attack),
        "midfield_control": _clip(midfield),
        "defensive_balance": _clip(defense),
        "pressing_cohesion": _clip(pressing - overlap_penalty / 2),
        "progression_synergy": _clip(progression),
        "role_overlap_penalty": _clip(overlap_penalty),
        "zone_coverage_score": _clip(zone_coverage),
        "warnings": warnings,
    }


def _avg(attrs: list[dict], keys: list[str]) -> float:
    vals = [float(a.get(k, 0.55)) for a in attrs for k in keys if k in a]
    return sum(vals) / len(vals) if vals else 0.55


def _formation_balance(players: list[dict], formation: str) -> float:
    positions = [p.get("canonical_position", "") for p in players]
    has_gk = "GK" in positions
    defenders = sum(p in {"CB", "LB", "RB", "WB"} for p in positions)
    mids = sum(p in {"DM", "CM", "AM"} for p in positions)
    forwards = sum(p in {"LW", "RW", "CF", "ST"} for p in positions)
    base = 0.25 * has_gk + min(defenders, 4) / 4 * 0.3 + min(mids, 3) / 3 * 0.3 + min(forwards, 3) / 3 * 0.15
    if formation.startswith("3") and defenders >= 3:
        base += 0.03
    return _clip(base)


def _clip(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
