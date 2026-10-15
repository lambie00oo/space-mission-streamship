import base64
import logging
import math
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import plotly.graph_objects as go
from matplotlib.font_manager import FontProperties
from matplotlib.figure import Figure
from matplotlib.ticker import StrMethodFormatter

from data.planets import DAYS_PER_YEAR, EARTH_ORBIT_RADIUS_AU, Planet
from logic.mission4_calculations import FlybyResult
from logic.orbit_calculations import (
    focus_distance,
    semi_minor_axis,
    transfer_eccentricity,
    transfer_semi_major_axis,
    transfer_time_years,
)


KOREAN_FONT = FontProperties(family="Malgun Gothic")
PLOT_BACKGROUND = "#0b1b33"
PLOT_FOREGROUND = "#f2f7ff"
PLOT_GRID = "#66809b"
SIMULATION_ORBIT_RADII_AU = {
    "지구": 1.00,
    "화성": 1.52,
    "목성": 5.20,
    "토성": 9.58,
}
SIMULATION_ORBITAL_PERIOD_DAYS = {
    "지구": DAYS_PER_YEAR,
    "화성": 686.98,
    "목성": 4332.59,
    "토성": 10759.22,
}
SIMULATION_REFERENCE_PHASE_RADIANS = {
    "지구": 0.0,
    "화성": 1.2,
    "목성": 2.4,
    "토성": 4.2,
}
SIMULATION_BODY_COLORS = {
    "태양": "#ffcc33",
    "지구": "#4ea5d9",
    "화성": "#d65353",
    "목성": "#e0aa59",
    "토성": "#d6c27a",
}
SIMULATION_BODY_IMAGES = {
    "태양": "sun",
    "지구": "earth",
    "화성": "mars",
    "목성": "jupiter",
    "토성": "saturn",
}
SIMULATION_BODY_IMAGE_SIZES_AU = {
    "태양": (0.76, 0.76),
    "지구": (0.50, 0.50),
    "화성": (0.54, 0.54),
    "목성": (0.62, 0.62),
    "토성": (0.80, 0.66),
}


def _apply_dark_theme(fig: Figure) -> None:
    fig.set_facecolor(PLOT_BACKGROUND)
    for ax in fig.axes:
        ax.set_facecolor(PLOT_BACKGROUND)
        ax.tick_params(colors=PLOT_FOREGROUND)
        ax.xaxis.label.set_color(PLOT_FOREGROUND)
        ax.yaxis.label.set_color(PLOT_FOREGROUND)
        ax.title.set_color(PLOT_FOREGROUND)
        for spine in ax.spines.values():
            spine.set_color(PLOT_GRID)
        legend = ax.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(PLOT_BACKGROUND)
            legend.get_frame().set_edgecolor(PLOT_GRID)
            for label in legend.get_texts():
                label.set_color(PLOT_FOREGROUND)


def _format_axis_ticks(ax: plt.Axes) -> None:
    formatter = StrMethodFormatter("{x:,.6g}")
    ax.xaxis.set_major_formatter(formatter)
    ax.yaxis.set_major_formatter(formatter)


def _draw_orbits(ax: plt.Axes, planet: Planet) -> tuple[float, float]:
    semi_major = transfer_semi_major_axis(planet)
    eccentricity = transfer_eccentricity(planet)
    focus = focus_distance(semi_major, eccentricity)
    semi_minor = semi_minor_axis(semi_major, eccentricity)
    center_x = -focus

    theta = [2 * math.pi * i / 361 for i in range(361)]
    transfer_x = [center_x + semi_major * math.cos(t) for t in theta]
    transfer_y = [semi_minor * math.sin(t) for t in theta]
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
    return semi_major, semi_minor


def _set_orbit_axes(ax: plt.Axes, planet: Planet) -> None:
    limit = planet.orbit_radius_au * 1.15
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    _format_axis_ticks(ax)


def mission2_orbit_plot(planet: Planet) -> Figure:
    fig, ax = plt.subplots(figsize=(9, 6))
    _draw_orbits(ax, planet)
    _set_orbit_axes(ax, planet)
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
    _apply_dark_theme(fig)
    fig.tight_layout(rect=(0, 0, 0.74, 0.96))
    return fig


def _solve_eccentric_anomaly(mean_anomaly: float, eccentricity: float) -> float:
    eccentric_anomaly = mean_anomaly if eccentricity < 0.8 else math.pi
    for _ in range(20):
        residual = (
            eccentric_anomaly
            - eccentricity * math.sin(eccentric_anomaly)
            - mean_anomaly
        )
        correction = residual / (
            1 - eccentricity * math.cos(eccentric_anomaly)
        )
        eccentric_anomaly -= correction
        if abs(correction) < 1e-12:
            return eccentric_anomaly
    raise ArithmeticError("케플러 방정식의 궤도 위치 계산이 수렴하지 않았습니다.")


@lru_cache(maxsize=None)
def _planet_image_data_uri(body_name: str) -> str | None:
    image_name = SIMULATION_BODY_IMAGES[body_name]
    image_path = (
        Path(__file__).resolve().parents[1]
        / "assets"
        / "planets"
        / f"{image_name}.png"
    )
    try:
        image_data = image_path.read_bytes()
    except OSError as error:
        logging.warning("Planet image unavailable at %s: %s", image_path, error)
        return None
    return f"data:image/png;base64,{base64.b64encode(image_data).decode('ascii')}"


def _simulation_image_layout(
    positions: dict[str, tuple[float, float]],
) -> list[dict[str, object]]:
    images: list[dict[str, object]] = []
    for body_name in SIMULATION_BODY_IMAGES:
        source = _planet_image_data_uri(body_name)
        if source is None:
            continue
        x, y = positions.get(body_name, (0.0, 0.0))
        width, height = SIMULATION_BODY_IMAGE_SIZES_AU[body_name]
        images.append(
            {
                "source": source,
                "xref": "x",
                "yref": "y",
                "x": x,
                "y": y,
                "xanchor": "center",
                "yanchor": "middle",
                "sizex": width,
                "sizey": height,
                "sizing": "contain",
                "layer": "above",
            }
        )
    return images


def mission2_orbit_simulation(
    planet: Planet,
    semi_major_axis_au: float,
    eccentricity: float,
    focus_distance_au: float,
    semi_minor_axis_au: float,
) -> go.Figure:
    """Build a time-stepped Plotly animation from the calculated transfer orbit."""
    values = (
        semi_major_axis_au,
        eccentricity,
        focus_distance_au,
        semi_minor_axis_au,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("궤도 계산 결과는 유한한 숫자여야 합니다.")
    if semi_major_axis_au <= 0 or semi_minor_axis_au <= 0:
        raise ValueError("궤도 장반경과 단반경은 0보다 커야 합니다.")
    if not 0 <= eccentricity < 1 or focus_distance_au < 0:
        raise ValueError("호만 전이 궤도에는 0 이상 1 미만의 이심률이 필요합니다.")
    if planet.name not in SIMULATION_ORBIT_RADII_AU:
        raise ValueError(f"시뮬레이션에 등록되지 않은 행성입니다: {planet.name}")

    frame_count = 61
    circle_angles = [2 * math.pi * index / 360 for index in range(361)]
    transfer_x = [
        semi_major_axis_au * math.cos(angle) - focus_distance_au
        for angle in circle_angles
    ]
    transfer_y = [
        semi_minor_axis_au * math.sin(angle)
        for angle in circle_angles
    ]
    spacecraft_positions = []
    for index in range(frame_count):
        mean_anomaly = math.pi * index / (frame_count - 1)
        eccentric_anomaly = _solve_eccentric_anomaly(
            mean_anomaly,
            eccentricity,
        )
        spacecraft_positions.append(
            (
                semi_major_axis_au * math.cos(eccentric_anomaly)
                - focus_distance_au,
                semi_minor_axis_au * math.sin(eccentric_anomaly),
            )
        )

    transfer_duration_years = transfer_time_years(semi_major_axis_au)
    destination_period_years = (
        SIMULATION_ORBITAL_PERIOD_DAYS[planet.name] / DAYS_PER_YEAR
    )
    initial_phases = SIMULATION_REFERENCE_PHASE_RADIANS.copy()
    initial_phases[planet.name] = (
        math.pi
        - 2 * math.pi * transfer_duration_years / destination_period_years
    )
    planet_positions_by_frame: list[dict[str, tuple[float, float]]] = []
    for index in range(frame_count):
        elapsed_years = transfer_duration_years * index / (frame_count - 1)
        frame_positions: dict[str, tuple[float, float]] = {}
        for body_name, radius_au in SIMULATION_ORBIT_RADII_AU.items():
            period_years = (
                SIMULATION_ORBITAL_PERIOD_DAYS[body_name] / DAYS_PER_YEAR
            )
            angle = (
                initial_phases[body_name]
                + 2 * math.pi * elapsed_years / period_years
            )
            frame_positions[body_name] = (
                radius_au * math.cos(angle),
                radius_au * math.sin(angle),
            )
        planet_positions_by_frame.append(frame_positions)

    limit = SIMULATION_ORBIT_RADII_AU["토성"] * 1.12
    frames: list[go.Frame] = []
    for index, planet_positions in enumerate(planet_positions_by_frame):
        spacecraft_x, spacecraft_y = spacecraft_positions[index]
        progress = index / (frame_count - 1)
        frame_data: list[go.Scatter] = [
            go.Scatter(
                x=[
                    position[0]
                    for position in spacecraft_positions[: index + 1]
                ],
                y=[
                    position[1]
                    for position in spacecraft_positions[: index + 1]
                ],
                mode="lines",
                line={"color": "#50c8ff", "width": 3},
                name="우주선 이동 경로",
            ),
            go.Scatter(
                x=[spacecraft_x],
                y=[spacecraft_y],
                mode="markers",
                marker={
                    "color": "#ffffff",
                    "size": 12,
                    "line": {"color": "#ff8c42", "width": 3},
                },
                customdata=[progress],
                hovertemplate=(
                    "우주선<br>x: %{x:.4f} AU"
                    "<br>y: %{y:.4f} AU"
                    "<br>전이 진행률: %{customdata:.0%}<extra></extra>"
                ),
                name="우주선 현재 위치",
            ),
        ]
        frame_trace_indexes = [6, 7]
        for body_index, (body_name, (body_x, body_y)) in enumerate(
            planet_positions.items()
        ):
            color = SIMULATION_BODY_COLORS[body_name]
            frame_data.extend(
                [
                    go.Scatter(
                        x=[body_x],
                        y=[body_y],
                        mode="markers",
                        marker={
                            "color": color,
                            "size": 15,
                            "line": {"color": PLOT_FOREGROUND, "width": 1},
                        },
                        hovertemplate=(
                            f"{body_name}<br>x: %{{x:.2f}} AU"
                            "<br>y: %{y:.2f} AU<extra></extra>"
                        ),
                        name=f"{body_name} 현재 위치",
                    ),
                    go.Scatter(
                        x=[
                            body_x
                            + SIMULATION_BODY_IMAGE_SIZES_AU[body_name][0] / 2
                            + 0.06
                        ],
                        y=[body_y + 0.06],
                        mode="text",
                        text=[body_name],
                        textposition="middle center",
                        textfont={"color": PLOT_FOREGROUND, "size": 11},
                        hoverinfo="skip",
                        showlegend=False,
                    ),
                ]
            )
            frame_trace_indexes.extend([8 + body_index, 12 + body_index])
        frames.append(
            go.Frame(
                name=f"frame-{index}",
                data=frame_data,
                traces=frame_trace_indexes,
                layout={
                    "images": _simulation_image_layout(
                        {"태양": (0.0, 0.0), **planet_positions}
                    )
                },
            )
        )

    initial_positions = planet_positions_by_frame[0]
    figure = go.Figure(
        data=[
            *[
                go.Scatter(
                    x=[
                        SIMULATION_ORBIT_RADII_AU[body_name] * math.cos(angle)
                        for angle in circle_angles
                    ],
                    y=[
                        SIMULATION_ORBIT_RADII_AU[body_name] * math.sin(angle)
                        for angle in circle_angles
                    ],
                    mode="lines",
                    line={
                        "color": SIMULATION_BODY_COLORS[body_name],
                        "width": 2.2 if body_name == planet.name else 1.2,
                        "dash": "solid" if body_name == planet.name else "dot",
                    },
                    name=f"{body_name} 공전 궤도"
                    if body_name != "지구"
                    else "지구 공전 궤도",
                )
                for body_name in SIMULATION_ORBIT_RADII_AU
            ],
            go.Scatter(
                x=transfer_x,
                y=transfer_y,
                mode="lines",
                line={"color": "#ff8c42", "width": 2.5},
                name="호만 전이 궤도",
            ),
            go.Scatter(
                x=[0],
                y=[0],
                mode="markers",
                marker={
                    "color": "#ffcc33",
                    "size": 20,
                    "line": {"color": "#e08a00", "width": 2},
                },
                name="태양 이미지 대체 표시",
                showlegend=False,
            ),
            go.Scatter(
                x=[EARTH_ORBIT_RADIUS_AU],
                y=[0],
                mode="lines",
                line={"color": "#50c8ff", "width": 3},
                name="우주선 이동 경로",
            ),
            go.Scatter(
                x=[EARTH_ORBIT_RADIUS_AU],
                y=[0],
                mode="markers",
                marker={
                    "color": "#ffffff",
                    "size": 12,
                    "line": {"color": "#ff8c42", "width": 3},
                },
                name="우주선 현재 위치",
            ),
            *[
                go.Scatter(
                    x=[initial_positions[body_name][0]],
                    y=[initial_positions[body_name][1]],
                    mode="markers",
                    marker={
                        "color": SIMULATION_BODY_COLORS[body_name],
                        "size": 15,
                        "line": {"color": PLOT_FOREGROUND, "width": 1},
                    },
                    hovertemplate=(
                        f"{body_name}<br>x: %{{x:.2f}} AU"
                        "<br>y: %{y:.2f} AU<extra></extra>"
                    ),
                    name=f"{body_name} 현재 위치",
                )
                for body_name in SIMULATION_ORBIT_RADII_AU
            ],
            *[
                go.Scatter(
                    x=[
                        initial_positions[body_name][0]
                        + SIMULATION_BODY_IMAGE_SIZES_AU[body_name][0] / 2
                        + 0.06
                    ],
                    y=[initial_positions[body_name][1] + 0.06],
                    mode="text",
                    text=[body_name],
                    textposition="middle center",
                    textfont={"color": PLOT_FOREGROUND, "size": 11},
                    hoverinfo="skip",
                    showlegend=False,
                )
                for body_name in SIMULATION_ORBIT_RADII_AU
            ],
        ],
        frames=frames,
    )
    figure.update_layout(
        title=f"지구에서 {planet.name}으로의 호만 전이 궤도 시뮬레이션",
        template="plotly_dark",
        paper_bgcolor=PLOT_BACKGROUND,
        plot_bgcolor=PLOT_BACKGROUND,
        font={"color": PLOT_FOREGROUND},
        xaxis={
            "title": "태양 기준 x 거리 (AU)",
            "range": [-limit, limit],
            "gridcolor": PLOT_GRID,
            "zerolinecolor": PLOT_GRID,
            "scaleanchor": "y",
            "scaleratio": 1,
        },
        yaxis={
            "title": "태양 기준 y 거리 (AU)",
            "range": [-limit, limit],
            "gridcolor": PLOT_GRID,
            "zerolinecolor": PLOT_GRID,
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        height=620,
        margin={"l": 20, "r": 20, "t": 105, "b": 20},
        images=_simulation_image_layout(
            {"태양": (0.0, 0.0), **initial_positions}
        ),
        updatemenus=[
            {
                "type": "buttons",
                "direction": "right",
                "showactive": False,
                "x": 0,
                "y": -0.12,
                "buttons": [
                    {
                        "label": "재생",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 60, "redraw": True},
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "일시 정지",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "mode": "immediate",
                                "frame": {"duration": 0, "redraw": False},
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "처음부터 재생",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": 60, "redraw": True},
                                "fromcurrent": False,
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
            }
        ],
    )
    return figure


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
        label=f"행성 이동 {travel_angle_degrees:.6g}°",
    )

    phase_angles = [phase_angle * i / 60 for i in range(61)]
    phase_radius = EARTH_ORBIT_RADIUS_AU * 0.45
    ax.plot(
        [phase_radius * math.cos(t) for t in phase_angles],
        [phase_radius * math.sin(t) for t in phase_angles],
        linestyle=":",
        color="#7f5aa2",
        linewidth=2.2,
        label=f"위상각 {phase_angle_degrees:.6g}°",
    )

    _set_orbit_axes(ax, planet)
    ax.set_title(f"전이 시간 동안 {planet.name}의 위치 변화")
    ax.legend(loc="upper right", fontsize=8)
    _apply_dark_theme(fig)
    fig.tight_layout()
    return fig


def mission4_flyby_plot(
    planet: Planet,
    results: tuple[FlybyResult, FlybyResult],
) -> Figure:
    fig, ax = plt.subplots(figsize=(8, 5.5))
    colors = ("#ff8c42", "#4ea5d9")
    max_distance = max(result.closest_distance_km for result in results) * 4
    for index, (result, color) in enumerate(zip(results, colors)):
        periapsis = result.closest_distance_km
        eccentricity = result.eccentricity
        semi_latus_rectum = periapsis * (1 + eccentricity)
        asymptote = math.acos(-1 / eccentricity)
        anomalies = [
            -asymptote + 0.002 + (2 * asymptote - 0.004) * step / 1200
            for step in range(1201)
        ]
        points = []
        for anomaly in anomalies:
            denominator = 1 + eccentricity * math.cos(anomaly)
            if denominator <= 0:
                continue
            radius = semi_latus_rectum / denominator
            if radius <= max_distance:
                points.append((radius * math.cos(anomaly), radius * math.sin(anomaly)))
        if not points:
            continue

        label = (
            f"선택 {'A' if index == 0 else 'B'} · 고도 "
            f"{result.altitude_km:,.6g} km · δ={result.deflection_angle_degrees:.6g}°"
        )
        x_values, y_values = zip(*points)
        ax.plot(x_values, y_values, color=color, linewidth=2, label=label)
        ax.scatter([periapsis], [0], color=color, s=36, zorder=5)
        arrow_index = max(1, len(points) // 4)
        arrow_start = points[arrow_index - 1]
        arrow_end = points[arrow_index]
        ax.annotate(
            "",
            xy=arrow_end,
            xytext=arrow_start,
            arrowprops={"arrowstyle": "->", "color": color, "lw": 1.5},
        )
        exit_index = max(1, 3 * len(points) // 4)
        ax.annotate(
            "",
            xy=points[exit_index],
            xytext=points[exit_index - 1],
            arrowprops={"arrowstyle": "->", "color": color, "lw": 1.5},
        )
        if index == 0:
            ax.text(
                *arrow_end,
                "접근",
                color=color,
                fontsize=8,
                fontproperties=KOREAN_FONT,
            )
            ax.text(
                *points[exit_index],
                "이탈",
                color=color,
                fontsize=8,
                fontproperties=KOREAN_FONT,
            )

    ax.add_patch(
        plt.Circle(
            (0, 0),
            planet.reference_radius_km,
            fill=False,
            linestyle="--",
            color="#777777",
            label=f"기준 반지름 ({planet.reference_surface})",
        )
    )
    ax.scatter([0], [0], color="#f2f7ff", s=24, zorder=6, label=f"{planet.name} 중심")
    ax.text(
        max(result.closest_distance_km for result in results),
        0,
        "근접점",
        ha="left",
        fontsize=9,
        color=PLOT_FOREGROUND,
        fontproperties=KOREAN_FONT,
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-max_distance, max_distance)
    ax.set_ylim(-max_distance * 0.65, max_distance * 0.65)
    ax.set_xlabel("행성 중심 기준 거리 (km)", fontproperties=KOREAN_FONT)
    ax.set_ylabel("행성 중심 기준 거리 (km)", fontproperties=KOREAN_FONT)
    _format_axis_ticks(ax)
    ax.set_title(f"{planet.name} 근접 통과 쌍곡선 궤도 비교", fontproperties=KOREAN_FONT)
    ax.grid(alpha=0.2)
    ax.legend(loc="upper right", fontsize=8, prop=KOREAN_FONT)
    _apply_dark_theme(fig)

    velocity_ax = ax.inset_axes([0.04, 0.64, 0.34, 0.32])
    max_speed = max(result.excess_speed_km_s for result in results)
    for index, (result, color) in enumerate(zip(results, colors)):
        speed = result.excess_speed_km_s
        eccentricity = result.eccentricity
        vx = speed / eccentricity
        vy = speed * math.sqrt(eccentricity**2 - 1) / eccentricity
        label = f"선택 {'A' if index == 0 else 'B'}"
        velocity_ax.quiver(
            0,
            0,
            vx,
            vy,
            angles="xy",
            scale_units="xy",
            scale=1,
            color=color,
            label=f"{label} 접근",
        )
        velocity_ax.quiver(
            0,
            0,
            -vx,
            vy,
            angles="xy",
            scale_units="xy",
            scale=1,
            color=color,
            linestyle="--",
            label=f"{label} 이탈",
        )
        velocity_ax.text(
            0.02,
            0.02 + index * 0.13,
            f"{label} 방향 전환각 δ = {result.deflection_angle_degrees:.6g}°",
            transform=velocity_ax.transAxes,
            fontsize=7,
            color=color,
            fontproperties=KOREAN_FONT,
        )

    velocity_ax.set_xlim(-max_speed * 1.2, max_speed * 1.2)
    velocity_ax.set_ylim(-max_speed * 0.1, max_speed * 1.2)
    velocity_ax.set_aspect("equal", adjustable="box")
    velocity_ax.set_title("행성 기준 속도 벡터 (km/s)", fontsize=8, fontproperties=KOREAN_FONT)
    velocity_ax.set_xlabel("vₓ (km/s)", fontsize=7)
    velocity_ax.set_ylabel("vᵧ (km/s)", fontsize=7)
    _format_axis_ticks(velocity_ax)
    velocity_ax.tick_params(labelsize=6)
    velocity_ax.legend(fontsize=6, loc="upper right", prop=KOREAN_FONT)
    fig.tight_layout()
    return fig
