import math
from dataclasses import dataclass
from typing import Sequence

from data.constants import AU_TO_KM
from data.planets import Planet


SUN_MASS_KG: float = 1.989e30
GRAVITATIONAL_CONSTANT_KM3_PER_KG_S2: float = 6.67430e-20
SECONDS_PER_DAY: float = 86_400.0
FINAL_APPROACH_PLANET_DATA: dict[str, tuple[float, float, float]] = {
    "mars": (227_900_000, 6.417e23, 3389.5),
    "jupiter": (778_600_000, 1.898e27, 69911.0),
    "saturn": (1_434_000_000, 5.683e26, 58232.0),
}


@dataclass(frozen=True)
class RendezvousPosition:
    progress: float
    elapsed_days: float
    spacecraft_au: tuple[float, float]
    planet_au: tuple[float, float]
    spacecraft_velocity_km_s: tuple[float, float]
    planet_velocity_km_s: tuple[float, float]

    @property
    def relative_position_km(self) -> tuple[float, float]:
        return (
            (self.spacecraft_au[0] - self.planet_au[0]) * AU_TO_KM,
            (self.spacecraft_au[1] - self.planet_au[1]) * AU_TO_KM,
        )

    @property
    def relative_velocity_km_s(self) -> tuple[float, float]:
        return (
            self.spacecraft_velocity_km_s[0] - self.planet_velocity_km_s[0],
            self.spacecraft_velocity_km_s[1] - self.planet_velocity_km_s[1],
        )


@dataclass(frozen=True)
class SphereOfInfluenceStatus:
    distance_km: float
    radius_km: float
    remaining_km: float
    entered: bool


@dataclass(frozen=True)
class HyperbolicOrbit:
    gravitational_parameter_km3_s2: float
    specific_energy_km2_s2: float
    eccentricity: float
    eccentricity_vector: tuple[float, float]
    semi_major_axis_km: float
    semi_latus_rectum_km: float
    periapsis_km: float
    entry_true_anomaly_rad: float
    position_residual_km: float
    velocity_residual_km_s: float
    orbit_path_km: tuple[tuple[float, float], ...]
    periapsis_position_km: tuple[float, float]
    exit_position_km: tuple[float, float] | None
    impact_position_km: tuple[float, float] | None


def sphere_of_influence_radius_km(
    semi_major_axis_km: float,
    planet_mass_kg: float,
    sun_mass_kg: float = SUN_MASS_KG,
) -> float:
    values = (semi_major_axis_km, planet_mass_kg, sun_mass_kg)
    if not all(math.isfinite(value) and value > 0 for value in values):
        raise ValueError("거리와 질량은 유한한 양수여야 합니다.")
    return semi_major_axis_km * (planet_mass_kg / sun_mass_kg) ** (2 / 5)


def rendezvous_positions_at(
    spacecraft_path_au: Sequence[Sequence[float]],
    progress: float,
    initial_planet_angle_degrees: float,
    transfer_days: float,
    planet: Planet,
) -> RendezvousPosition:
    if len(spacecraft_path_au) < 2:
        raise ValueError("우주선 경로에는 서로 다른 시각의 좌표가 두 개 이상 필요합니다.")
    if any(len(point) != 2 for point in spacecraft_path_au):
        raise ValueError("우주선 궤도 좌표는 (x, y) 쌍이어야 합니다.")
    values = (
        progress,
        initial_planet_angle_degrees,
        transfer_days,
        planet.orbital_period_days,
        planet.orbit_radius_au,
        *(coordinate for point in spacecraft_path_au for coordinate in point),
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("좌표와 시뮬레이션 값은 유한한 숫자여야 합니다.")
    if not 0 <= progress <= 1:
        raise ValueError("시뮬레이션 진행률은 0 이상 1 이하여야 합니다.")
    if transfer_days <= 0 or planet.orbital_period_days <= 0 or planet.orbit_radius_au <= 0:
        raise ValueError("전이 시간과 행성 궤도 값이 올바르지 않습니다.")

    sample_count = len(spacecraft_path_au)
    scaled_index = progress * (sample_count - 1)
    index = min(math.floor(scaled_index), sample_count - 2)
    fraction = scaled_index - index
    start = spacecraft_path_au[index]
    end = spacecraft_path_au[index + 1]
    spacecraft_au = (
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    )
    elapsed_days = transfer_days * progress

    sample_interval_days = transfer_days / (sample_count - 1)
    au_per_day_to_km_per_second = AU_TO_KM / SECONDS_PER_DAY
    spacecraft_velocity = (
        (end[0] - start[0]) / sample_interval_days * au_per_day_to_km_per_second,
        (end[1] - start[1]) / sample_interval_days * au_per_day_to_km_per_second,
    )

    planet_angle = math.radians(
        initial_planet_angle_degrees
        + 360 * elapsed_days / planet.orbital_period_days
    )
    planet_au = (
        planet.orbit_radius_au * math.cos(planet_angle),
        planet.orbit_radius_au * math.sin(planet_angle),
    )
    planet_angular_velocity_rad_s = (
        2
        * math.pi
        / (planet.orbital_period_days * SECONDS_PER_DAY)
    )
    planet_velocity = (
        -planet.orbit_radius_au
        * AU_TO_KM
        * math.sin(planet_angle)
        * planet_angular_velocity_rad_s,
        planet.orbit_radius_au
        * AU_TO_KM
        * math.cos(planet_angle)
        * planet_angular_velocity_rad_s,
    )
    return RendezvousPosition(
        progress=progress,
        elapsed_days=elapsed_days,
        spacecraft_au=spacecraft_au,
        planet_au=planet_au,
        spacecraft_velocity_km_s=spacecraft_velocity,
        planet_velocity_km_s=planet_velocity,
    )


def find_sphere_of_influence_entry(
    spacecraft_path_au: Sequence[Sequence[float]],
    planet: Planet,
    initial_planet_angle_degrees: float,
    transfer_days: float,
    influence_radius_km: float,
    *,
    samples: int = 20_000,
) -> RendezvousPosition | None:
    if not math.isfinite(influence_radius_km) or influence_radius_km <= 0:
        raise ValueError("영향권 반지름은 유한한 양수여야 합니다.")
    if samples < 2:
        raise ValueError("영향권 탐색 샘플은 2개 이상이어야 합니다.")

    def state_and_distance(progress: float) -> tuple[RendezvousPosition, float]:
        state = rendezvous_positions_at(
            spacecraft_path_au,
            progress,
            initial_planet_angle_degrees,
            transfer_days,
            planet,
        )
        relative_x, relative_y = state.relative_position_km
        return state, math.hypot(relative_x, relative_y)

    previous_progress = 0.0
    _, previous_distance = state_and_distance(previous_progress)
    for sample_index in range(1, samples + 1):
        current_progress = sample_index / samples
        _, current_distance = state_and_distance(current_progress)
        if previous_distance > influence_radius_km and current_distance <= influence_radius_km:
            low = previous_progress
            high = current_progress
            for _ in range(60):
                middle = (low + high) / 2
                _, middle_distance = state_and_distance(middle)
                if middle_distance <= influence_radius_km:
                    high = middle
                else:
                    low = middle
            entry_state, _ = state_and_distance(high)
            return entry_state
        previous_progress = current_progress
        previous_distance = current_distance
    return None


def sphere_of_influence_status(
    spacecraft_au: Sequence[float],
    planet_au: Sequence[float],
    influence_radius_km: float,
    au_to_km: float = AU_TO_KM,
) -> SphereOfInfluenceStatus:
    if len(spacecraft_au) != 2 or len(planet_au) != 2:
        raise ValueError("우주선과 행성 좌표는 (x, y) 쌍이어야 합니다.")
    values = (*spacecraft_au, *planet_au, influence_radius_km, au_to_km)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("좌표와 거리는 유한한 숫자여야 합니다.")
    if influence_radius_km <= 0 or au_to_km <= 0:
        raise ValueError("영향권 반지름과 AU 환산값은 양수여야 합니다.")

    dx_km = (spacecraft_au[0] - planet_au[0]) * au_to_km
    dy_km = (spacecraft_au[1] - planet_au[1]) * au_to_km
    distance_km = math.hypot(dx_km, dy_km)
    return SphereOfInfluenceStatus(
        distance_km=distance_km,
        radius_km=influence_radius_km,
        remaining_km=distance_km - influence_radius_km,
        entered=distance_km <= influence_radius_km,
    )


def hyperbolic_orbit_from_entry(
    entry_state: RendezvousPosition,
    planet_mass_kg: float,
    influence_radius_km: float,
    *,
    planet_radius_km: float | None = None,
    samples: int = 361,
) -> HyperbolicOrbit:
    if samples < 3:
        raise ValueError("쌍곡선 궤도 표시에는 샘플이 3개 이상 필요합니다.")
    mu = GRAVITATIONAL_CONSTANT_KM3_PER_KG_S2 * planet_mass_kg
    rx, ry = entry_state.relative_position_km
    vx, vy = entry_state.relative_velocity_km_s
    radius = math.hypot(rx, ry)
    speed_squared = vx * vx + vy * vy
    energy = speed_squared / 2 - mu / radius
    angular_momentum_z = rx * vy - ry * vx
    eccentricity_vector = (
        vy * angular_momentum_z / mu - rx / radius,
        -vx * angular_momentum_z / mu - ry / radius,
    )
    eccentricity = math.hypot(*eccentricity_vector)

    energy_tolerance = max(speed_squared / 2, mu / radius) * 1e-12
    if energy <= energy_tolerance or eccentricity <= 1 + 1e-10:
        raise ValueError(
            f"진입 상태는 쌍곡선이 아닙니다 (특정 에너지 {energy:.8g} km²/s², "
            f"이심률 {eccentricity:.8g})."
        )
    angular_momentum = abs(angular_momentum_z)
    if angular_momentum == 0:
        raise ValueError("진입 상태의 각운동량이 0이어서 쌍곡선을 결정할 수 없습니다.")

    semi_major_axis = -mu / (2 * energy)
    semi_latus_rectum = angular_momentum**2 / mu
    periapsis = semi_latus_rectum / (1 + eccentricity)
    if periapsis >= influence_radius_km:
        raise ValueError(
            "계산된 쌍곡선 근점이 영향권 내부에 있지 않아 유효한 내부 구간이 없습니다."
        )
    if planet_radius_km is not None and (
        not math.isfinite(planet_radius_km)
        or planet_radius_km <= 0
    ):
        raise ValueError("행성 반지름은 유한한 양수여야 합니다.")
    radius_tolerance = max(1e-3, influence_radius_km * 1e-9)
    if abs(radius - influence_radius_km) > radius_tolerance:
        raise ValueError(
            "진입 위치의 반지름이 영향권 경계와 허용 오차 내에서 일치하지 않습니다."
        )

    ex, ey = eccentricity_vector
    e_hat = (ex / eccentricity, ey / eccentricity)
    rotation_sign = math.copysign(1.0, angular_momentum_z)
    q_hat = (-rotation_sign * e_hat[1], rotation_sign * e_hat[0])
    dot_er = ex * rx + ey * ry
    cross_er = ex * ry - ey * rx
    entry_true_anomaly = math.atan2(
        rotation_sign * cross_er,
        dot_er,
    )
    radial_velocity = rx * vx + ry * vy
    if radial_velocity >= 0:
        raise ValueError("영향권 진입점의 속도가 안쪽을 향하지 않습니다.")

    cos_boundary = (semi_latus_rectum / influence_radius_km - 1) / eccentricity
    if not -1 <= cos_boundary <= 1:
        raise ValueError("쌍곡선이 영향권 경계와 다시 만나는 해가 없습니다.")
    boundary_anomaly = math.acos(cos_boundary)
    if abs(entry_true_anomaly + boundary_anomaly) > 1e-5:
        raise ValueError("진입 진근점이각이 계산된 쌍곡선의 입사 경계와 일치하지 않습니다.")

    entry_orbit_radius = semi_latus_rectum / (
        1 + eccentricity * math.cos(entry_true_anomaly)
    )
    reconstructed_entry_position = (
        entry_orbit_radius
        * (
            e_hat[0] * math.cos(entry_true_anomaly)
            + q_hat[0] * math.sin(entry_true_anomaly)
        ),
        entry_orbit_radius
        * (
            e_hat[1] * math.cos(entry_true_anomaly)
            + q_hat[1] * math.sin(entry_true_anomaly)
        ),
    )
    speed_scale = math.sqrt(mu / semi_latus_rectum)
    reconstructed_entry_velocity = (
        speed_scale
        * (
            -e_hat[0] * math.sin(entry_true_anomaly)
            + q_hat[0] * (eccentricity + math.cos(entry_true_anomaly))
        ),
        speed_scale
        * (
            -e_hat[1] * math.sin(entry_true_anomaly)
            + q_hat[1] * (eccentricity + math.cos(entry_true_anomaly))
        ),
    )
    position_residual = math.hypot(
        reconstructed_entry_position[0] - rx,
        reconstructed_entry_position[1] - ry,
    )
    velocity_residual = math.hypot(
        reconstructed_entry_velocity[0] - vx,
        reconstructed_entry_velocity[1] - vy,
    )
    if position_residual > radius_tolerance or velocity_residual > max(
        1e-8,
        math.hypot(vx, vy) * 1e-8,
    ):
        raise ValueError("쌍곡선 궤도의 위치 또는 속도가 진입 상태와 일치하지 않습니다.")

    impact = planet_radius_km is not None and periapsis <= planet_radius_km
    impact_position: tuple[float, float] | None = None
    if impact:
        cos_surface = (semi_latus_rectum / planet_radius_km - 1) / eccentricity
        if not -1 <= cos_surface <= 1:
            raise ValueError("행성 표면과 만나는 쌍곡선 궤도를 찾을 수 없습니다.")
        end_anomaly = -math.acos(cos_surface)
        exit_anomaly = None
    else:
        end_anomaly = boundary_anomaly
        exit_anomaly = end_anomaly
    anomaly_values = [
        entry_true_anomaly
        + (end_anomaly - entry_true_anomaly) * index / (samples - 1)
        for index in range(samples)
    ]
    orbit_points: list[tuple[float, float]] = []
    for anomaly in anomaly_values:
        denominator = 1 + eccentricity * math.cos(anomaly)
        if denominator <= 0:
            continue
        orbit_radius = semi_latus_rectum / denominator
        orbit_points.append(
            (
                orbit_radius
                * (
                    e_hat[0] * math.cos(anomaly)
                    + q_hat[0] * math.sin(anomaly)
                ),
                orbit_radius
                * (
                    e_hat[1] * math.cos(anomaly)
                    + q_hat[1] * math.sin(anomaly)
                ),
            )
        )
    if len(orbit_points) != samples:
        raise ValueError("쌍곡선 표시 구간에 유효하지 않은 방정식 분모가 있습니다.")

    periapsis_position = (
        periapsis * e_hat[0],
        periapsis * e_hat[1],
    )
    if impact:
        impact_radius = semi_latus_rectum / (
            1 + eccentricity * math.cos(end_anomaly)
        )
        impact_position = (
            impact_radius
            * (e_hat[0] * math.cos(end_anomaly) + q_hat[0] * math.sin(end_anomaly)),
            impact_radius
            * (e_hat[1] * math.cos(end_anomaly) + q_hat[1] * math.sin(end_anomaly)),
        )
    return HyperbolicOrbit(
        gravitational_parameter_km3_s2=mu,
        specific_energy_km2_s2=energy,
        eccentricity=eccentricity,
        eccentricity_vector=eccentricity_vector,
        semi_major_axis_km=semi_major_axis,
        semi_latus_rectum_km=semi_latus_rectum,
        periapsis_km=periapsis,
        entry_true_anomaly_rad=entry_true_anomaly,
        position_residual_km=position_residual,
        velocity_residual_km_s=velocity_residual,
        orbit_path_km=tuple(orbit_points),
        periapsis_position_km=periapsis_position,
        exit_position_km=(
            orbit_points[-1] if exit_anomaly is not None else None
        ),
        impact_position_km=impact_position,
    )
