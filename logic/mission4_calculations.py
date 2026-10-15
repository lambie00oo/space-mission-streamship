import math
from typing import NamedTuple

from data.constants import AU_TO_KM, SUN_GRAVITATIONAL_PARAMETER_KM3_S2
from data.planets import Planet


class FlybyResult(NamedTuple):
    altitude_km: float
    closest_distance_km: float
    excess_speed_km_s: float
    eccentricity: float
    deflection_angle_degrees: float


def _positive_finite(value: float, label: str) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a positive finite number")
    return value


def spacecraft_arrival_speed_km_s(
    sun_mu_km3_s2: float,
    target_orbit_radius_km: float,
    semi_major_axis_km: float,
) -> float:
    mu = _positive_finite(sun_mu_km3_s2, "Solar gravitational parameter")
    radius = _positive_finite(target_orbit_radius_km, "Target orbit radius")
    semi_major_axis = _positive_finite(semi_major_axis_km, "Semi-major axis")
    speed_squared = mu * (2 / radius - 1 / semi_major_axis)
    if not math.isfinite(speed_squared) or speed_squared <= 0:
        raise ValueError("Transfer orbit does not have a real arrival speed")
    return math.sqrt(speed_squared)


def planet_orbital_speed_km_s(
    sun_mu_km3_s2: float,
    target_orbit_radius_km: float,
) -> float:
    mu = _positive_finite(sun_mu_km3_s2, "Solar gravitational parameter")
    radius = _positive_finite(target_orbit_radius_km, "Target orbit radius")
    return math.sqrt(mu / radius)


def educational_excess_speed_km_s(
    spacecraft_speed_km_s: float,
    planet_speed_km_s: float,
) -> float:
    if not math.isfinite(spacecraft_speed_km_s) or spacecraft_speed_km_s < 0:
        raise ValueError("Spacecraft speed must be finite and non-negative")
    if not math.isfinite(planet_speed_km_s) or planet_speed_km_s < 0:
        raise ValueError("Planet speed must be finite and non-negative")
    return abs(spacecraft_speed_km_s - planet_speed_km_s)


def closest_distance_km(
    reference_radius_km: float,
    closest_altitude_km: float,
) -> float:
    radius = _positive_finite(reference_radius_km, "Reference radius")
    if not math.isfinite(closest_altitude_km) or closest_altitude_km < 0:
        raise ValueError("Closest altitude must be finite and non-negative")
    return radius + closest_altitude_km


def hyperbolic_eccentricity(
    closest_distance_km: float,
    excess_speed_km_s: float,
    planet_mu_km3_s2: float,
) -> float:
    distance = _positive_finite(closest_distance_km, "Closest distance")
    speed = _positive_finite(excess_speed_km_s, "Excess speed")
    mu = _positive_finite(planet_mu_km3_s2, "Planetary gravitational parameter")
    eccentricity = 1 + distance * speed**2 / mu
    if not math.isfinite(eccentricity) or eccentricity <= 1:
        raise ValueError("Flyby trajectory must be hyperbolic (eccentricity > 1)")
    return eccentricity


def deflection_angle_degrees(eccentricity: float) -> float:
    if not math.isfinite(eccentricity) or eccentricity <= 1:
        raise ValueError("Hyperbolic eccentricity must be greater than 1")
    deflection_radians = 2 * math.asin(1 / eccentricity)
    return math.degrees(deflection_radians)


def compare_flyby_altitudes(
    planet: Planet,
    excess_speed_km_s: float,
    altitudes_km: tuple[float, float] | None = None,
) -> tuple[FlybyResult, FlybyResult]:
    speed = _positive_finite(excess_speed_km_s, "Excess speed")
    if (
        planet.reference_radius_km is None
        or planet.gravitational_parameter_km3_s2 is None
        or planet.flyby_altitudes_km is None
    ):
        raise ValueError(f"{planet.name} has no flyby data")
    altitudes = (
        planet.flyby_altitudes_km if altitudes_km is None else altitudes_km
    )
    if len(altitudes) != 2:
        raise ValueError("Exactly two flyby altitudes are required")

    results = []
    for altitude in altitudes:
        distance = closest_distance_km(planet.reference_radius_km, altitude)
        eccentricity = hyperbolic_eccentricity(
            distance,
            speed,
            planet.gravitational_parameter_km3_s2,
        )
        results.append(
            FlybyResult(
                altitude,
                distance,
                speed,
                eccentricity,
                deflection_angle_degrees(eccentricity),
            )
        )
    return results[0], results[1]


def mission4_solar_parameters(
    planet: Planet,
    semi_major_axis_au: float,
) -> tuple[float, float, float]:
    orbit_radius_km = planet.orbit_radius_au * AU_TO_KM
    semi_major_axis_km = (
        _positive_finite(semi_major_axis_au, "Semi-major axis") * AU_TO_KM
    )
    arrival_speed = spacecraft_arrival_speed_km_s(
        SUN_GRAVITATIONAL_PARAMETER_KM3_S2,
        orbit_radius_km,
        semi_major_axis_km,
    )
    planet_speed = planet_orbital_speed_km_s(
        SUN_GRAVITATIONAL_PARAMETER_KM3_S2,
        orbit_radius_km,
    )
    excess_speed = educational_excess_speed_km_s(arrival_speed, planet_speed)
    return arrival_speed, planet_speed, excess_speed
