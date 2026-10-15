import math

from data.planets import DAYS_PER_YEAR, EARTH_ORBIT_RADIUS_AU, Planet


def transfer_semi_major_axis(planet: Planet) -> float:
    return (EARTH_ORBIT_RADIUS_AU + planet.orbit_radius_au) / 2


def transfer_eccentricity(planet: Planet) -> float:
    return (planet.orbit_radius_au - EARTH_ORBIT_RADIUS_AU) / (
        planet.orbit_radius_au + EARTH_ORBIT_RADIUS_AU
    )


def focus_distance(semi_major_axis_au: float, eccentricity: float) -> float:
    return semi_major_axis_au * eccentricity


def semi_minor_axis(semi_major_axis_au: float, eccentricity: float) -> float:
    return semi_major_axis_au * math.sqrt(1 - eccentricity**2)


def semi_minor_axis_from_focus(
    semi_major_axis_au: float,
    focus_distance_au: float,
) -> float:
    if not math.isfinite(semi_major_axis_au) or not math.isfinite(focus_distance_au):
        raise ValueError("장반경 a와 초점 거리 c는 유한한 숫자여야 합니다.")
    if semi_major_axis_au <= 0 or semi_major_axis_au**2 <= focus_distance_au**2:
        raise ValueError("타원 조건 a² > c²를 만족해야 합니다.")
    return math.sqrt(semi_major_axis_au**2 - focus_distance_au**2)


def transfer_time_years(semi_major_axis_au: float) -> float:
    return math.sqrt(semi_major_axis_au**3) / 2


def transfer_time_days(semi_major_axis_au: float) -> float:
    return transfer_time_years(semi_major_axis_au) * DAYS_PER_YEAR


def planet_angular_velocity_degrees_per_day(planet: Planet) -> float:
    return 360 / planet.orbital_period_days


def planet_travel_angle_degrees(planet: Planet, transfer_days: float) -> float:
    return planet_angular_velocity_degrees_per_day(planet) * transfer_days


def phase_angle_degrees(planet_travel_angle: float) -> float:
    return (180 - planet_travel_angle) % 360
