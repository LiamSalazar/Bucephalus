from __future__ import annotations

from bucephalus.tactics.schemas import TacticalState


def tactical_bullets(home: TacticalState, away: TacticalState, home_fatigue: dict, away_fatigue: dict) -> list[str]:
    bullets = []
    if home.pressing > 0.7:
        bullets.append("La presión alta local proyecta más recuperaciones, con costo estimado de fatiga después del minuto 70.")
    if away.transition > 0.65 and home.line_height > 0.6:
        bullets.append("La transición/directness visitante eleva el riesgo proxy contra una línea local alta.")
    if away_fatigue["after_70_defensive_risk"] > 0.5:
        bullets.append("El visitante muestra riesgo estimado de caída tardía bajo la cobertura actual.")
    if home.possession > 0.65 and home.directness < 0.35:
        bullets.append("La posesión local puede estabilizar control, pero con riesgo proxy de baja progresión.")
    if min(home.reliability_score, away.reliability_score) < 0.35:
        bullets.append("El resultado depende de proxies tácticos con cobertura limitada.")
    return bullets or ["El matchup proyecta un escenario equilibrado según los proxies disponibles."]
