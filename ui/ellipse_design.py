from __future__ import annotations

import math
from collections.abc import Mapping

import plotly.graph_objects as go
import streamlit as st

from logic.orbit_calculations import semi_minor_axis_from_focus


def expected_ellipse_points(
    semi_major_axis_au: float,
    semi_minor_axis_au: float,
    focus_distance_au: float,
) -> dict[str, tuple[float, float]]:
    return {
        "F′": (-2 * focus_distance_au, 0.0),
        "A": (-focus_distance_au + semi_major_axis_au, 0.0),
        "A′": (-focus_distance_au - semi_major_axis_au, 0.0),
        "B": (-focus_distance_au, semi_minor_axis_au),
        "B′": (-focus_distance_au, -semi_minor_axis_au),
    }


def create_ellipse_figure(
    semi_major_axis_au: float,
    semi_minor_axis_au: float,
    focus_distance_au: float,
) -> go.Figure:
    center_x = -focus_distance_au
    angles = [2 * math.pi * index / 360 for index in range(361)]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=[center_x + semi_major_axis_au * math.cos(angle) for angle in angles],
            y=[semi_minor_axis_au * math.sin(angle) for angle in angles],
            mode="lines",
            line={"color": "#50c8ff", "width": 3},
            name="타원 궤도",
            hoverinfo="skip",
        )
    )

    landmarks = {
        "태양 · 초점 F": (0.0, 0.0, "#ffcc33"),
        "중심 C": (center_x, 0.0, "#ffffff"),
        "다른 초점 F′": (-2 * focus_distance_au, 0.0, "#ff7b72"),
        "장축 끝점 A": (
            -focus_distance_au + semi_major_axis_au,
            0.0,
            "#bd93f9",
        ),
        "장축 끝점 A′": (
            -focus_distance_au - semi_major_axis_au,
            0.0,
            "#bd93f9",
        ),
        "단축 끝점 B": (
            -focus_distance_au,
            semi_minor_axis_au,
            "#bd93f9",
        ),
        "단축 끝점 B′": (
            -focus_distance_au,
            -semi_minor_axis_au,
            "#bd93f9",
        ),
    }
    for name, (x, y, color) in landmarks.items():
        figure.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text",
                marker={"color": color, "size": 11},
                text=[name],
                textposition="top right",
                name=name,
                hovertemplate=f"{name}<br>(%{{x:.4f}}, %{{y:.4f}}) AU<extra></extra>",
            )
        )

    extent_x = semi_major_axis_au + focus_distance_au
    extent_y = semi_minor_axis_au
    padding = max(extent_x, extent_y) * 0.15
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0b1b33",
        plot_bgcolor="#0b1b33",
        font={"color": "#f2f7ff"},
        xaxis={
            "title": "x (AU)",
            "range": [-extent_x - padding, semi_major_axis_au + padding],
            "gridcolor": "#66809b",
            "zerolinecolor": "#9bb4cb",
            "scaleanchor": "y",
            "scaleratio": 1,
        },
        yaxis={
            "title": "y (AU)",
            "range": [-extent_y - padding, extent_y + padding],
            "gridcolor": "#66809b",
            "zerolinecolor": "#9bb4cb",
        },
        height=520,
        margin={"l": 20, "r": 20, "t": 30, "b": 20},
        showlegend=True,
    )
    return figure


def _mission_orbit_values() -> tuple[float, float] | None:
    mission2_result = st.session_state.get("m2_result")
    if isinstance(mission2_result, Mapping):
        semi_major_axis = mission2_result.get("semi_major_axis_au")
        focus_distance = mission2_result.get("focus_distance_au")
        if semi_major_axis is not None and focus_distance is not None:
            return float(semi_major_axis), float(focus_distance)

    semi_major_axis = st.session_state.get("m2_a")
    focus_distance = st.session_state.get("m2_c")
    if semi_major_axis is None or focus_distance is None:
        return None
    return float(semi_major_axis), float(focus_distance)


def render_ellipse_design(
    semi_major_axis_au: float | None = None,
    focus_distance_au: float | None = None,
) -> None:
    for key in (
        "m2_ellipse_formula_input",
        "m2_ellipse_result",
        "m2_ellipse_config",
        "m2_ellipse_check",
        "m2_ellipse_reset",
    ):
        st.session_state.pop(key, None)

    if semi_major_axis_au is None or focus_distance_au is None:
        mission_values = _mission_orbit_values()
        if mission_values is None:
            st.info("MISSION 2에서 계산한 장반경 a와 초점 거리 c를 먼저 확인해 주세요.")
            return
        semi_major_axis_au, focus_distance_au = mission_values

    try:
        semi_minor_axis_au = semi_minor_axis_from_focus(
            semi_major_axis_au,
            focus_distance_au,
        )
    except ValueError as error:
        st.error(f"타원 단반경 b를 계산할 수 없습니다: {error}")
        return

    st.subheader("타원 궤도")
    columns = st.columns(3)
    columns[0].metric("장반경 a", f"{semi_major_axis_au:.4f} AU")
    columns[1].metric("단반경 b", f"{semi_minor_axis_au:.4f} AU")
    columns[2].metric("초점 거리 c", f"{focus_distance_au:.4f} AU")
    st.latex(r"b = \sqrt{a^2 - c^2}")
    st.markdown(
        f"b = √({semi_major_axis_au:.4f}² − {focus_distance_au:.4f}²)"
    )
    st.markdown(f"b = **{semi_minor_axis_au:.4f} AU**")
    st.plotly_chart(
        create_ellipse_figure(
            semi_major_axis_au,
            semi_minor_axis_au,
            focus_distance_au,
        ),
        key="mission2_ellipse_plot",
        alt="계산된 태양 중심 전이 타원의 중심, 두 초점, 장축 및 단축 끝점",
    )
