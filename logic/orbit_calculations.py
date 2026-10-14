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
