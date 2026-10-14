import math

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.figure import Figure

from data.planets import EARTH_ORBIT_RADIUS_AU, Planet


KOREAN_FONT = FontProperties(family="Malgun Gothic")


def _draw_orbits(ax: plt.Axes, planet: Planet) -> tuple[float, float]:
    semi_major_axis = (EARTH_ORBIT_RADIUS_AU + planet.orbit_radius_au) / 2
    eccentricity = (planet.orbit_radius_au - EARTH_ORBIT_RADIUS_AU) / (
        planet.orbit_radius_au + EARTH_ORBIT_RADIUS_AU
    )
    focus_distance = semi_major_axis * eccentricity
    semi_minor_axis = semi_major_axis * math.sqrt(1 - eccentricity**2)
    center_x = -focus_distance

    theta = [2 * math.pi * i / 361 for i in range(361)]
    transfer_x = [center_x + semi_major_axis * math.cos(t) for t in theta]
    transfer_y = [semi_minor_axis * math.sin(t) for t in theta]
    ax.plot(
        transfer_x,
        transfer_y,
        color="#ff8c42",
        linewidth=2.4,
        label="호만 전이 타원",
    )
    ax.add_patch(
        plt.Circle(
            (0, 0),
            EARTH_ORBIT_RADIUS_AU,
            fill=False,
            color="#4ea5d9",
            label="지구 공전 궤도",
        )
    )
    ax.add_patch(
        plt.Circle(
            (0, 0),
            planet.orbit_radius_au,
            fill=False,
            color="#b58bd4",
            label=f"{planet.name} 공전 궤도",
        )
    )
    ax.scatter(
        [0],
        [0],
        s=150,
        color="#ffcc33",
        edgecolors="#e08a00",
        zorder=5,
        label="태양 (전이 타원의 초점)",
    )
    ax.scatter(
        [EARTH_ORBIT_RADIUS_AU],
        [0],
        color="#4ea5d9",
        s=55,
        zorder=6,
        label="지구 출발 위치",
    )
    ax.scatter(
        [-planet.orbit_radius_au],
        [0],
        color="#d65353",
        s=65,
        zorder=6,
        label=f"{planet.name} 도착 위치",
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("태양 기준 x 거리 (AU)", fontproperties=KOREAN_FONT)
    ax.set_ylabel("태양 기준 y 거리 (AU)", fontproperties=KOREAN_FONT)
    ax.grid(alpha=0.18)
    ax.legend(loc="upper right", fontsize=8, prop=KOREAN_FONT)
    return semi_major_axis, semi_minor_axis


def mission2_orbit_plot(planet: Planet) -> Figure:
    fig, ax = plt.subplots(figsize=(9, 6))
    _draw_orbits(ax, planet)
    limit = planet.orbit_radius_au * 1.15
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_title(
        f"지구에서 {planet.name}으로의 호만 전이 궤도",
        fontproperties=KOREAN_FONT,
        pad=12,
    )
    ax.get_legend().remove()
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        borderaxespad=0,
        fontsize=8,
        prop=KOREAN_FONT,
    )
    fig.tight_layout(rect=(0, 0, 0.74, 0.96))
    return fig


def mission3_orbit_plot(
    planet: Planet,
    phase_angle_degrees: float,
    travel_angle_degrees: float,
) -> Figure:
    fig, ax = plt.subplots(figsize=(8, 6))
    _draw_orbits(ax, planet)

    phase_angle = math.radians(phase_angle_degrees)
    travel_angle = math.radians(travel_angle_degrees)
    initial_planet_angle = phase_angle
    initial_x = planet.orbit_radius_au * math.cos(initial_planet_angle)
    initial_y = planet.orbit_radius_au * math.sin(initial_planet_angle)
    ax.scatter([initial_x], [initial_y], color="#64a653", s=75, zorder=7, label=f"{planet.name} 출발 시")

    arc_steps = max(2, int(abs(travel_angle) * 40))
    arc_angles = [
        initial_planet_angle + travel_angle * i / arc_steps
        for i in range(arc_steps + 1)
    ]
    arc_radius = planet.orbit_radius_au * 0.9
    ax.plot(
        [arc_radius * math.cos(t) for t in arc_angles],
        [arc_radius * math.sin(t) for t in arc_angles],
        linestyle="--",
        color="#64a653",
        linewidth=2,
        label=f"행성 이동 {travel_angle_degrees:.1f}°",
    )

    phase_angles = [phase_angle * i / 60 for i in range(61)]
    phase_radius = EARTH_ORBIT_RADIUS_AU * 0.45
    ax.plot(
        [phase_radius * math.cos(t) for t in phase_angles],
        [phase_radius * math.sin(t) for t in phase_angles],
        linestyle=":",
        color="#7f5aa2",
        linewidth=2.2,
        label=f"위상각 {phase_angle_degrees:.1f}°",
    )

    limit = planet.orbit_radius_au * 1.15
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_title(f"전이 시간 동안 {planet.name}의 위치 변화")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    return fig
