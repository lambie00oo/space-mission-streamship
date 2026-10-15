import math

import plotly.graph_objects as go
import streamlit as st

from data.constants import AU_TO_KM
from data.planets import PLANETS, Planet
from logic.final_approach import (
    FINAL_APPROACH_PLANET_DATA,
    GRAVITATIONAL_CONSTANT_KM3_PER_KG_S2,
    HyperbolicOrbit,
    RendezvousPosition,
    SUN_MASS_KG,
    find_sphere_of_influence_entry,
    hyperbolic_orbit_from_entry,
    rendezvous_positions_at,
    sphere_of_influence_radius_km,
)
from logic.orbit_calculations import semi_minor_axis
from ui.formula_problems import FormulaInput, render_formula_problem
from ui.mission3_rendezvous import _extract_simulation_data


PLOT_BACKGROUND = "#071426"
PLOT_GRID = "#24415f"
PLOT_FOREGROUND = "#f2f7ff"
_FINAL_APPROACH_FORMULA_STATE_KEYS = (
    "m4_final_approach_soi",
    "m4_final_approach_soi_formula_input",
    "m4_final_approach_angular_momentum",
    "m4_final_approach_angular_momentum_formula_input",
    "m4_final_approach_energy",
    "m4_final_approach_energy_formula_input",
    "m4_final_approach_eccentricity",
    "m4_final_approach_eccentricity_formula_input",
    "m4_final_approach_entry_days",
    "m4_final_approach_entered",
    "m4_final_approach_hyperbolic",
)


def _eccentricity_from_energy_and_angular_momentum(
    values: dict[str, float],
) -> float:
    radicand = (
        1
        + 2
        * values["energy"]
        * values["angular_momentum"] ** 2
        / values["mu"] ** 2
    )
    if radicand < 0:
        raise ValueError("이심률 제곱근 안의 값이 0보다 작습니다.")
    return math.sqrt(radicand)


def _solar_system_figure(
    planet: Planet,
    transfer_path_au: list[list[float]],
    position: RendezvousPosition,
    influence_radius_km: float,
    *,
    is_entry: bool,
) -> go.Figure:
    angles = [2 * math.pi * index / 360 for index in range(361)]
    figure = go.Figure()
    for radius, name, color in (
        (1.0, "지구 공전 궤도", "#4ea5d9"),
        (planet.orbit_radius_au, f"{planet.name} 공전 궤도", "#d6c27a"),
    ):
        figure.add_trace(
            go.Scatter(
                x=[radius * math.cos(angle) for angle in angles],
                y=[radius * math.sin(angle) for angle in angles],
                mode="lines",
                line={"color": color, "dash": "dot", "width": 1.5},
                name=name,
            )
        )
    figure.add_trace(
        go.Scatter(
            x=[point[0] for point in transfer_path_au],
            y=[point[1] for point in transfer_path_au],
            mode="lines",
            line={"color": "#ff8c42", "width": 2},
            name="MISSION 2·3 호만 전이 타원",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[0, position.planet_au[0]],
            y=[0, position.planet_au[1]],
            mode="markers",
            marker={"color": ["#ffcc33", "#d6c27a"], "size": [15, 12]},
            text=["태양", planet.name],
            name="태양과 행성",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[position.spacecraft_au[0]],
            y=[position.spacecraft_au[1]],
            mode="markers+text",
            marker={
                "color": "#50c8ff",
                "size": 14,
                "symbol": "star",
                "line": {"color": "#ffffff", "width": 1},
            },
            text=["영향권 진입점" if is_entry else "전이 종료 위치"],
            textposition="top right",
            name="우주선",
        )
    )
    influence_radius_au = influence_radius_km / AU_TO_KM
    figure.add_shape(
        type="circle",
        x0=position.planet_au[0] - influence_radius_au,
        y0=position.planet_au[1] - influence_radius_au,
        x1=position.planet_au[0] + influence_radius_au,
        y1=position.planet_au[1] + influence_radius_au,
        line={"color": "#fff2a8", "width": 2},
        name="영향권 경계",
    )
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor=PLOT_BACKGROUND,
        plot_bgcolor=PLOT_BACKGROUND,
        font={"color": PLOT_FOREGROUND},
        xaxis={
            "title": "태양 기준 x 거리 (AU)",
            "range": [-planet.orbit_radius_au * 1.12, planet.orbit_radius_au * 1.12],
            "gridcolor": PLOT_GRID,
            "scaleanchor": "y",
            "scaleratio": 1,
        },
        yaxis={
            "title": "태양 기준 y 거리 (AU)",
            "range": [-planet.orbit_radius_au * 1.12, planet.orbit_radius_au * 1.12],
            "gridcolor": PLOT_GRID,
        },
        height=450,
        margin={"l": 20, "r": 20, "t": 25, "b": 20},
        legend={"orientation": "h", "y": -0.2},
    )
    return figure


def _planet_center_figure(
    planet: Planet,
    position: RendezvousPosition,
    influence_radius_km: float,
    planet_radius_km: float,
    hyperbola: HyperbolicOrbit | None,
) -> go.Figure:
    relative_x_km, relative_y_km = position.relative_position_km
    relative_vx, relative_vy = position.relative_velocity_km_s
    relative_speed = math.hypot(relative_vx, relative_vy)
    limit_km = max(
        influence_radius_km * 1.12,
        math.hypot(relative_x_km, relative_y_km) * 1.12,
        1.0,
    )
    figure = go.Figure()
    figure.add_shape(
        type="circle",
        x0=-influence_radius_km,
        y0=-influence_radius_km,
        x1=influence_radius_km,
        y1=influence_radius_km,
        line={"color": "#fff2a8", "width": 2, "dash": "dash"},
        fillcolor="rgba(255, 242, 168, 0.10)",
        name="영향권 경계",
    )
    figure.add_shape(
        type="circle",
        x0=-planet_radius_km,
        y0=-planet_radius_km,
        x1=planet_radius_km,
        y1=planet_radius_km,
        line={"color": "#d6c27a", "width": 1},
        fillcolor="#d6c27a",
        name="행성 표면",
    )
    if hyperbola is not None:
        figure.add_trace(
            go.Scatter(
                x=[point[0] for point in hyperbola.orbit_path_km],
                y=[point[1] for point in hyperbola.orbit_path_km],
                mode="lines",
                line={"color": "#ff8c42", "width": 2.5},
                name="행성 중심 쌍곡선 구간",
            )
        )
    figure.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            mode="markers+text",
            marker={"color": "#d6c27a", "size": 13},
            text=[planet.name],
            textposition="top center",
            name="행성 중심",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[relative_x_km],
            y=[relative_y_km],
            mode="markers+text",
            marker={"color": "#50c8ff", "size": 14, "symbol": "star"},
            text=["경계 진입점" if hyperbola is not None else "상대 위치"],
            textposition="top right",
            name="우주선",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[0, relative_x_km],
            y=[0, relative_y_km],
            mode="lines",
            line={"color": "#50c8ff", "dash": "dot", "width": 1.5},
            name="상대 위치 벡터",
        )
    )
    velocity_display_length = limit_km * 0.18
    if relative_speed > 0:
        velocity_dx = relative_vx / relative_speed * velocity_display_length
        velocity_dy = relative_vy / relative_speed * velocity_display_length
        figure.add_annotation(
            x=relative_x_km + velocity_dx,
            y=relative_y_km + velocity_dy,
            ax=relative_x_km,
            ay=relative_y_km,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=3,
            arrowwidth=2,
            arrowcolor="#ff6680",
            text="v_rel 방향 (길이 시각화용)",
            font={"color": "#ffb3c0"},
        )
    if hyperbola is not None:
        figure.add_trace(
            go.Scatter(
                x=[hyperbola.periapsis_position_km[0]],
                y=[hyperbola.periapsis_position_km[1]],
                mode="markers+text",
                marker={"color": "#ff6680", "size": 11, "symbol": "diamond"},
                text=[
                    "근점 (행성 내부)"
                    if hyperbola.impact_position_km is not None
                    else "근점"
                ],
                textposition="bottom center",
                name="근점",
            )
        )
        if hyperbola.exit_position_km is not None:
            figure.add_trace(
                go.Scatter(
                    x=[hyperbola.exit_position_km[0]],
                    y=[hyperbola.exit_position_km[1]],
                    mode="markers",
                    marker={"color": "#b9efff", "size": 10, "symbol": "circle-open"},
                    name="영향권 이탈점",
                )
            )
        if hyperbola.impact_position_km is not None:
            figure.add_trace(
                go.Scatter(
                    x=[hyperbola.impact_position_km[0]],
                    y=[hyperbola.impact_position_km[1]],
                    mode="markers+text",
                    marker={"color": "#ff6680", "size": 10, "symbol": "x"},
                    text=["행성 표면 도달"],
                    textposition="top right",
                    name="표면 도달점",
                )
            )
    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor=PLOT_BACKGROUND,
        plot_bgcolor=PLOT_BACKGROUND,
        font={"color": PLOT_FOREGROUND},
        xaxis={
            "title": "행성 중심 x 거리 (km)",
            "range": [-limit_km, limit_km],
            "gridcolor": PLOT_GRID,
            "scaleanchor": "y",
            "scaleratio": 1,
        },
        yaxis={
            "title": "행성 중심 y 거리 (km)",
            "range": [-limit_km, limit_km],
            "gridcolor": PLOT_GRID,
        },
        height=450,
        margin={"l": 20, "r": 20, "t": 25, "b": 20},
        legend={"orientation": "h", "y": -0.2},
    )
    return figure


def _render_entry_position(
    position: RendezvousPosition,
    influence_radius_km: float,
) -> None:
    spacecraft_x_km = position.spacecraft_au[0] * AU_TO_KM
    spacecraft_y_km = position.spacecraft_au[1] * AU_TO_KM
    planet_x_km = position.planet_au[0] * AU_TO_KM
    planet_y_km = position.planet_au[1] * AU_TO_KM
    relative_x_km, relative_y_km = position.relative_position_km
    distance_km = math.hypot(relative_x_km, relative_y_km)

    st.write(f"진입 시각: **{position.elapsed_days:.6f}일**")
    st.write(
        f"우주선 태양중심 위치: "
        f"({spacecraft_x_km:,.3f}, {spacecraft_y_km:,.3f}) km"
    )
    st.write(
        f"행성 태양중심 위치: ({planet_x_km:,.3f}, {planet_y_km:,.3f}) km"
    )
    st.write(
        f"상대 위치 r_rel: ({relative_x_km:,.3f}, {relative_y_km:,.3f}) km · "
        f"|r_rel| = {distance_km:,.3f} km · "
        f"r_SOI = {influence_radius_km:,.3f} km"
    )


def render_mission4() -> None:
    st.header("MISSION 4. 새로운 세계의 경계를 넘어라!")
    st.write(
        "목적 행성의 영향권에 도달한 지금, 새로운 탐험이 기다리고 있다. 행성을 기준으로 우주선의 위치와 속도를 다시 분석하고 쌍곡선 궤도의 조건을 확인하라. 미지의 영역을 향한 마지막 항로를 완성하고 탐험의 다음 장을 열어라!"
    )

    result = st.session_state.get("m2_result")
    if (
        not st.session_state.get("m2_complete", False)
        or not isinstance(result, dict)
        or result.get("planet_key") not in PLANETS
    ):
        st.info("MISSION 2의 궤도 설계를 완료하면 FINAL APPROACH를 진행할 수 있습니다.")
        st.button(
            "MISSION2로 이동",
            key="mission4_locked_back",
            on_click=lambda: st.session_state.update(current_page="MISSION2"),
        )
        return
    if not st.session_state.get("m3_complete", False):
        st.info("MISSION 3 계산을 완료한 후 FINAL APPROACH를 시작할 수 있습니다.")
        st.button(
            "MISSION3으로 이동",
            key="mission4_mission3_back",
            on_click=lambda: st.session_state.update(current_page="MISSION3"),
        )
        return

    planet_key = result["planet_key"]
    if planet_key != st.session_state.selected_planet:
        st.warning("목적 행성 선택과 MISSION 2 결과가 다릅니다. MISSION 2를 다시 진행해 주세요.")
        return
    snapshot = st.session_state.get("m3_final_approach_snapshot")
    if not isinstance(snapshot, dict):
        st.error(
            "MISSION 3의 저장된 행성 초기각을 찾을 수 없습니다. "
            "MISSION 3에서 다시 완료해 주세요."
        )
        st.button(
            "MISSION3으로 이동",
            key="mission4_missing_snapshot_back",
            on_click=lambda: st.session_state.update(current_page="MISSION3"),
        )
        return

    planet = PLANETS[planet_key]
    if planet_key not in FINAL_APPROACH_PLANET_DATA:
        st.error(f"{planet.name}의 영향권 자료가 없습니다.")
        return
    try:
        semi_major_axis_au = float(result["semi_major_axis_au"])
        eccentricity = float(result["eccentricity"])
        focus_distance_au = float(result["focus_distance_au"])
        transfer_days = float(st.session_state.m3_time_days)
        initial_angle_degrees = float(snapshot["angle_degrees"])
        input_context = (
            planet_key,
            semi_major_axis_au,
            eccentricity,
            focus_distance_au,
            transfer_days,
            initial_angle_degrees,
        )
        if st.session_state.get("m4_final_approach_input_context") != input_context:
            for state_key in _FINAL_APPROACH_FORMULA_STATE_KEYS:
                st.session_state.pop(state_key, None)
            st.session_state.m4_final_approach_input_context = input_context
        transfer_path_au, spacecraft_path_au = _extract_simulation_data(
            planet,
            semi_major_axis_au,
            eccentricity,
            focus_distance_au,
            semi_minor_axis(semi_major_axis_au, eccentricity),
        )
        (
            planet_orbit_radius_km,
            planet_mass_kg,
            planet_radius_km,
        ) = FINAL_APPROACH_PLANET_DATA[planet_key]
        influence_radius_km = sphere_of_influence_radius_km(
            planet_orbit_radius_km,
            planet_mass_kg,
        )
        entry = find_sphere_of_influence_entry(
            spacecraft_path_au,
            planet,
            initial_angle_degrees,
            transfer_days,
            influence_radius_km,
        )
    except (KeyError, TypeError, ValueError) as error:
        st.error(f"FINAL APPROACH 데이터를 계산할 수 없습니다: {error}")
        return

    st.subheader("STEP 1 · 도착 행성의 영향권")
    if not render_formula_problem(
        key="m4_final_approach_soi",
        title="도착 행성의 영향권 반지름 계산",
        formula=(
            r"r_{\mathrm{SOI}}=a_{\mathrm{planet}}"
            r"\left(\frac{m_{\mathrm{planet}}}{M_{\mathrm{sun}}}\right)^{2/5}"
        ),
        formula_layout="""
            <span>r<sub>SOI</sub> = </span>
            <span data-formula-slot="planet_axis"></span>
            <span>× (</span>
            <span data-formula-slot="planet_mass"></span>
            <span> / </span>
            <span data-formula-slot="sun_mass"></span>
            <span>)<sup>2/5</sup></span>
        """,
        inputs=(
            FormulaInput(
                "planet_axis",
                "행성 공전 궤도 반지름 a_planet",
                planet_orbit_radius_km,
                "km",
                "%.0f",
                strictly_positive=True,
            ),
            FormulaInput(
                "planet_mass",
                "행성 질량 m_planet",
                planet_mass_kg,
                "kg",
                "%.4e",
                strictly_positive=True,
            ),
            FormulaInput(
                "sun_mass",
                "태양 질량 M_sun",
                SUN_MASS_KG,
                "kg",
                "%.4e",
                strictly_positive=True,
            ),
        ),
        calculate=lambda values: sphere_of_influence_radius_km(
            values["planet_axis"],
            values["planet_mass"],
            values["sun_mass"],
        ),
        expected=influence_radius_km,
        tolerance=max(0.1, influence_radius_km * 1e-8),
        result_label="계산 결과 r_SOI",
        result_unit="km",
        success_message="정답입니다. 계산된 영향권 반지름을 다음 단계에 사용합니다.",
        hints=(
            "행성 공전 반지름에 (행성 질량 / 태양 질량)의 2/5제곱을 곱합니다.",
            "질량은 같은 단위(kg), 거리는 km로 입력하세요.",
        ),
    ):
        return
    st.metric("계산된 영향권 반지름", f"{influence_radius_km:,.3f} km")
    st.write(f"목적 행성 반지름: **{planet_radius_km:,.1f} km**")
    st.caption(
        "영향권은 중력이 갑자기 시작되는 물리적 벽이 아니라, "
        "패치드 코닉 근사 모델에서 태양 중심 계산을 행성 중심 계산으로 "
        "전환할 때 사용하는 경계입니다."
    )

    with st.container(border=True):
        st.subheader("STEP 2 · 전이 구간에서 최초 영향권 진입 탐색")
        st.write(
            f"MISSION 3의 전이 시간 **{transfer_days:.6f}일**을 "
            "20,000개 구간으로 탐색하고 경계 통과 시각을 이분법으로 정밀화합니다."
        )
        if entry is None:
            st.warning(
                "전이 구간에서 우주선이 영향권 경계를 바깥에서 안쪽으로 통과하지 않았습니다. "
                "진입 시각이나 진입점을 임의로 만들지 않았습니다."
            )
            display_position = rendezvous_positions_at(
                spacecraft_path_au,
                1.0,
                initial_angle_degrees,
                transfer_days,
                planet,
            )
        else:
            st.success("영향권 경계를 통과하는 최초 진입 시각을 찾았습니다.")
            _render_entry_position(entry, influence_radius_km)
            display_position = entry

    with st.container(border=True):
        st.subheader("STEP 3 · 동일 시각의 행성 중심 상대 상태")
        if entry is None:
            st.info("진입 시각이 없어 행성 중심 진입 상태를 구성할 수 없습니다.")
            velocity_position = display_position
        else:
            velocity_position = entry
            st.write(
                f"진입 진행률: **{entry.progress:.8f}** · "
                f"진입 시각: **{entry.elapsed_days:.6f}일**"
            )
        sc_vx, sc_vy = velocity_position.spacecraft_velocity_km_s
        planet_vx, planet_vy = velocity_position.planet_velocity_km_s
        rel_x, rel_y = velocity_position.relative_position_km
        rel_vx, rel_vy = velocity_position.relative_velocity_km_s
        st.write(
            f"태양중심 우주선 속도: ({sc_vx:.8f}, {sc_vy:.8f}) km/s · "
            f"태양중심 행성 속도: ({planet_vx:.8f}, {planet_vy:.8f}) km/s"
        )
        st.write(
            f"행성중심 r_rel: ({rel_x:,.3f}, {rel_y:,.3f}) km · "
            f"v_rel: ({rel_vx:.8f}, {rel_vy:.8f}) km/s"
        )
        st.caption(
            "위치와 속도는 같은 시각·같은 방향의 x-y 축에서 계산했습니다. "
            "행성을 원점으로 바꾸는 것은 좌표 기준의 변경이며 우주선의 실제 "
            "위치나 속도가 순간적으로 바뀌는 현상이 아닙니다."
        )

    with st.container(border=True):
        st.subheader("STEP 4 · 행성 중심 궤도의 쌍곡선 판정")
        mu = GRAVITATIONAL_CONSTANT_KM3_PER_KG_S2 * planet_mass_kg
        hyperbola: HyperbolicOrbit | None = None
        hyperbola_error: str | None = None
        if entry is None:
            st.info("영향권 진입이 없어 쌍곡선 조건을 판정하지 않습니다.")
        else:
            relative_x, relative_y = entry.relative_position_km
            velocity_x, velocity_y = entry.relative_velocity_km_s
            relative_radius = math.hypot(relative_x, relative_y)
            angular_momentum_z = (
                relative_x * velocity_y - relative_y * velocity_x
            )
            specific_energy = (
                (velocity_x**2 + velocity_y**2) / 2 - mu / relative_radius
            )
            st.write(f"μ = Gm = **{mu:.8g} km³/s²**")
            if not render_formula_problem(
                key="m4_final_approach_angular_momentum",
                title="진입 상태의 각운동량 계산",
                formula=r"h_z = r_x v_y - r_y v_x",
                formula_layout="""
                    <span>h<sub>z</sub> = </span>
                    <span data-formula-slot="rx"></span>
                    <span>×</span>
                    <span data-formula-slot="vy"></span>
                    <span>−</span>
                    <span data-formula-slot="ry"></span>
                    <span>×</span>
                    <span data-formula-slot="vx"></span>
                """,
                inputs=(
                    FormulaInput("rx", "r_x", relative_x, "km", "%.3f"),
                    FormulaInput("vy", "v_y", velocity_y, "km/s", "%.10f"),
                    FormulaInput("ry", "r_y", relative_y, "km", "%.3f"),
                    FormulaInput("vx", "v_x", velocity_x, "km/s", "%.10f"),
                ),
                calculate=lambda values: (
                    values["rx"] * values["vy"] - values["ry"] * values["vx"]
                ),
                expected=angular_momentum_z,
                tolerance=max(1e-2, abs(angular_momentum_z) * 1e-8),
                result_label="계산 결과 h_z",
                result_unit="km²/s",
                success_message="정답입니다. 각운동량을 저장했습니다.",
                hints=(
                    "r_rel × v_rel의 z 성분을 계산합니다.",
                    "h_z = r_x v_y - r_y v_x 입니다.",
                ),
            ):
                return
            if not render_formula_problem(
                key="m4_final_approach_energy",
                title="행성 중심 특정 에너지 계산",
                formula=r"\varepsilon = \frac{v_x^2+v_y^2}{2} - \frac{\mu}{r}",
                formula_layout="""
                    <span>ε = (</span>
                    <span data-formula-slot="vx"></span><sup>2</sup>
                    <span> + </span>
                    <span data-formula-slot="vy"></span><sup>2</sup>
                    <span>) / 2 − </span>
                    <span data-formula-slot="mu"></span>
                    <span> / </span>
                    <span data-formula-slot="radius"></span>
                """,
                inputs=(
                    FormulaInput("vx", "상대 속도 v_x", velocity_x, "km/s", "%.10f"),
                    FormulaInput("vy", "상대 속도 v_y", velocity_y, "km/s", "%.10f"),
                    FormulaInput("mu", "중력 상수 μ", mu, "km³/s²", "%.10g", strictly_positive=True),
                    FormulaInput("radius", "상대 거리 r", relative_radius, "km", "%.3f", strictly_positive=True),
                ),
                calculate=lambda values: (
                    (values["vx"] ** 2 + values["vy"] ** 2) / 2
                    - values["mu"] / values["radius"]
                ),
                expected=specific_energy,
                tolerance=max(1e-8, abs(specific_energy) * 1e-6),
                result_label="계산 결과 ε",
                result_unit="km²/s²",
                success_message="정답입니다. 특정 에너지를 저장했습니다.",
                hints=(
                    "먼저 상대 속력의 제곱을 2로 나눈 뒤 μ/r을 빼세요.",
                    "쌍곡선이 되려면 특정 에너지 ε가 0보다 커야 합니다.",
                ),
            ):
                return
            if not render_formula_problem(
                key="m4_final_approach_eccentricity",
                title="행성 중심 궤도 이심률 계산",
                formula=r"e = \sqrt{1 + \frac{2\varepsilon h_z^2}{\mu^2}}",
                formula_layout="""
                    <span>e = √(1 + 2 × </span>
                    <span data-formula-slot="energy"></span>
                    <span> × </span>
                    <span data-formula-slot="angular_momentum"></span><sup>2</sup>
                    <span> / </span>
                    <span data-formula-slot="mu"></span><sup>2</sup>
                    <span>)</span>
                """,
                inputs=(
                    FormulaInput("energy", "특정 에너지 ε", specific_energy, "km²/s²", "%.10g"),
                    FormulaInput(
                        "angular_momentum",
                        "각운동량 h_z",
                        angular_momentum_z,
                        "km²/s",
                        "%.10g",
                    ),
                    FormulaInput("mu", "중력 상수 μ", mu, "km³/s²", "%.10g", strictly_positive=True),
                ),
                calculate=_eccentricity_from_energy_and_angular_momentum,
                expected=math.sqrt(
                    1
                    + 2
                    * specific_energy
                    * angular_momentum_z**2
                    / mu**2
                ),
                tolerance=1e-6,
                result_label="계산 결과 e",
                result_unit="",
                success_message="정답입니다. 이제 쌍곡선 조건을 확인합니다.",
                hints=(
                    "특정 에너지 ε, 각운동량 h_z, 중력 상수 μ를 공식에 대입하세요.",
                    "쌍곡선이 되려면 이심률 e도 1보다 커야 합니다.",
                ),
            ):
                return
            st.write(f"μ = Gm = **{mu:.8g} km³/s²**")
            try:
                hyperbola = hyperbolic_orbit_from_entry(
                    entry,
                    planet_mass_kg,
                    influence_radius_km,
                    planet_radius_km=planet_radius_km,
                )
            except ValueError as error:
                hyperbola_error = str(error)
                st.metric("특정 에너지 ε", f"{specific_energy:.8g} km²/s²")
                st.error(
                    f"이 진입 상태에서 쌍곡선 조건이 성립하지 않습니다: {error}"
                )
            else:
                st.metric(
                    "특정 에너지 ε",
                    f"{specific_energy:.8g} km²/s²",
                )
                st.metric(
                    "이심률 e",
                    f"{math.sqrt(1 + 2 * specific_energy * angular_momentum_z**2 / mu**2):.10g}",
                )
                st.success("ε > 0 및 e > 1 조건을 모두 만족합니다.")
                st.write(
                    f"이심률 벡터: ({hyperbola.eccentricity_vector[0]:.10g}, "
                    f"{hyperbola.eccentricity_vector[1]:.10g})"
                )
        st.session_state.m4_final_approach_entry_days = (
            entry.elapsed_days if entry is not None else None
        )
        st.session_state.m4_final_approach_entered = entry is not None
        st.session_state.m4_final_approach_hyperbolic = hyperbola is not None

    with st.container(border=True):
        st.subheader("STEP 5 · 태양중심 전이와 행성중심 접근 궤도")
        left_column, right_column = st.columns(2)
        with left_column:
            st.markdown("**태양중심 · 전이 구간 및 SOI**")
            st.plotly_chart(
                _solar_system_figure(
                    planet,
                    transfer_path_au,
                    display_position,
                    influence_radius_km,
                    is_entry=entry is not None,
                ),
                width="stretch",
                key="mission4_solar_system_plot",
            )
        with right_column:
            st.markdown(f"**{planet.name} 중심 · 영향권 내부**")
            st.plotly_chart(
                _planet_center_figure(
                    planet,
                    display_position,
                    influence_radius_km,
                    planet_radius_km,
                    hyperbola if entry is not None else None,
                ),
                width="stretch",
                key="mission4_influence_zone_plot",
            )
        if hyperbola is not None:
            st.write(
                f"쌍곡선 반장축 a_h = **{hyperbola.semi_major_axis_km:,.3f} km** "
                f"(부호 포함) · 반통경 p = **{hyperbola.semi_latus_rectum_km:,.3f} km** · "
                f"근점 거리 = **{hyperbola.periapsis_km:,.3f} km**"
            )
            st.write(
                f"진입 위치 잔차: {hyperbola.position_residual_km:.6g} km · "
                f"진입 속도 잔차: {hyperbola.velocity_residual_km_s:.6g} km/s"
            )
            if hyperbola.impact_position_km is not None:
                st.warning(
                    f"계산된 근점({hyperbola.periapsis_km:,.3f} km)이 "
                    f"{planet.name} 반지름({planet_radius_km:,.1f} km)보다 작아 "
                    "행성 표면과 교차합니다. 충돌 이후의 이탈 궤도는 표시하지 않았습니다."
                )
        elif hyperbola_error is not None:
            st.info("물리적으로 유효한 쌍곡선 구간이 없어 쌍곡선은 표시하지 않았습니다.")
        else:
            st.info("영향권 진입 상태가 없어 쌍곡선은 표시하지 않았습니다.")
        st.caption(
            "속도 화살표의 길이만 방향을 읽기 쉽도록 시각화용으로 정규화했습니다. "
            "거리·속도 계산에는 화면 픽셀 좌표를 사용하지 않습니다."
        )
