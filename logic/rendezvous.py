import math

from data.planets import Planet


AU_TO_KM = 149_597_870.7
RENDEZVOUS_TOLERANCE_KM = 10_000.0


def normalize_angle_degrees(angle_degrees: float) -> float:
    if not math.isfinite(angle_degrees):
        raise ValueError("각도는 유한한 숫자여야 합니다.")
    return angle_degrees % 360


def shortest_angle_difference_degrees(
    target_angle_degrees: float,
    current_angle_degrees: float,
) -> float:
    difference = (
        normalize_angle_degrees(target_angle_degrees)
        - normalize_angle_degrees(current_angle_degrees)
        + 180
    ) % 360 - 180
    return difference


def fine_tune_angle_degrees(
    current_angle_degrees: float,
    target_angle_degrees: float,
    max_step_degrees: float = 5.0,
) -> float:
    if not math.isfinite(max_step_degrees) or max_step_degrees <= 0:
        raise ValueError("미세 조정 폭은 양수여야 합니다.")
    difference = shortest_angle_difference_degrees(
        target_angle_degrees,
        current_angle_degrees,
    )
    step = min(abs(difference), max_step_degrees)
    return normalize_angle_degrees(
        current_angle_degrees + math.copysign(step, difference)
    )


def planet_position_au(
    planet: Planet,
    initial_angle_degrees: float,
    elapsed_days: float,
) -> tuple[float, float]:
    if not math.isfinite(elapsed_days) or elapsed_days < 0:
        raise ValueError("경과 시간은 0 이상인 유한한 값이어야 합니다.")
    angle = math.radians(
        normalize_angle_degrees(initial_angle_degrees)
        + 360 * elapsed_days / planet.orbital_period_days
    )
    return (
        planet.orbit_radius_au * math.cos(angle),
        planet.orbit_radius_au * math.sin(angle),
    )


def arrival_distance_km(
    spacecraft_position_au: tuple[float, float],
    planet: Planet,
    initial_angle_degrees: float,
    transfer_days: float,
) -> float:
    planet_x, planet_y = planet_position_au(
        planet,
        initial_angle_degrees,
        transfer_days,
    )
    spacecraft_x, spacecraft_y = spacecraft_position_au
    distance_au = math.hypot(
        spacecraft_x - planet_x,
        spacecraft_y - planet_y,
    )
    return distance_au * AU_TO_KM
