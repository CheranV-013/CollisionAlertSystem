from dataclasses import dataclass
from .models.domain import RiskLevel

@dataclass(frozen=True)
class RiskConfig:
    caution_distance_m: float = 45
    warning_distance_m: float = 22
    critical_distance_m: float = 8
    caution_ttc_s: float = 6
    warning_ttc_s: float = 3.5
    critical_ttc_s: float = 1.5

def risk_score(distance_m: float, closing_speed_mps: float, ttc_s: float | None, relative_bearing_deg: float, config: RiskConfig = RiskConfig()) -> tuple[float, RiskLevel]:
    proximity = max(0.0, min(1.0, 1 - distance_m / config.caution_distance_m))
    closing = max(0.0, min(1.0, closing_speed_mps / 15))
    ttc = 0.0 if ttc_s is None else max(0.0, min(1.0, 1 - ttc_s / 8))
    lane_factor = max(0.0, 1 - abs(relative_bearing_deg) / 100)
    score = max(0.0, min(1.0, 0.35 * proximity + 0.3 * closing + 0.25 * ttc + 0.1 * lane_factor))
    if distance_m <= config.critical_distance_m or (ttc_s is not None and ttc_s <= config.critical_ttc_s):
        return max(score, .9), RiskLevel.CRITICAL
    if distance_m <= config.warning_distance_m or (ttc_s is not None and ttc_s <= config.warning_ttc_s):
        return max(score, .65), RiskLevel.WARNING
    if distance_m <= config.caution_distance_m or closing_speed_mps > 1 or (ttc_s is not None and ttc_s <= config.caution_ttc_s):
        return max(score, .35), RiskLevel.CAUTION
    return score, RiskLevel.SAFE

def time_to_collision(distance_m: float, closing_speed_mps: float) -> float | None:
    return distance_m / closing_speed_mps if closing_speed_mps > 0.05 else None

