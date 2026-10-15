from pathlib import Path

import streamlit as st

from data.planets import EARTH_ORBIT_RADIUS_AU, PLANETS
from logic.orbit_calculations import (
    focus_distance,
    semi_minor_axis_from_focus,
    transfer_eccentricity,
    transfer_semi_major_axis,
)
from ui.formula_problems import (
    FormulaInput,
    render_formula_problem,
)
from ui.ellipse_design import render_ellipse_design


ASSET_DIR = Path(__file__).resolve().parent.parent / "images"

def _complete_mission2() -> None:
    planet = PLANETS[st.session_state.selected_planet]
    st.session_state.m2_complete = True
    st.session_state.m2_result = {
        "planet_key": st.session_state.selected_planet,
        "planet_name": planet.name,
        "semi_major_axis_au": st.session_state.m2_a,
        "eccentricity": st.session_state.m2_e,
        "focus_distance_au": st.session_state.m2_c,
    }
    st.session_state.current_page = "MISSION3"


def _eccentricity_from_radii(values: dict[str, float]) -> float:
    if values["r_p"] <= values["r_e"]:
        raise ValueError("목적 행성의 궤도 반지름은 지구 궤도 반지름보다 커야 합니다.")
    return (values["r_p"] - values["r_e"]) / (
        values["r_p"] + values["r_e"]
    )


def _on_planet_change() -> None:
    for key in (
        "m2_a",
        "m2_e",
        "m2_c",
        "m2_complete",
        "m2_result",
        "m3_time_years",
        "m3_time_days",
        "m3_omega",
        "m3_travel_angle",
        "m3_phase_angle",
        "m3_complete",
        "mission2_semi_major_input",
        "mission2_eccentricity_input",
        "mission2_focus_input",
        "m2_a_r_e_input",
        "m2_a_r_p_input",
        "m2_a_formula_input",
        "m2_e_r_p_input",
        "m2_e_r_e_input",
        "m2_e_formula_input",
        "m2_c_a_input",
        "m2_c_e_input",
        "m2_c_formula_input",
        "mission3_time_years_input",
        "mission3_time_days_input",
        "mission3_omega_input",
        "mission3_theta_input",
        "mission3_phase_input",
        "mission3_time_years_saved",
        "mission3_time_days_saved",
        "mission3_omega_saved",
        "mission3_theta_saved",
        "mission3_phase_saved",
        "m3_time_years_a_input",
        "m3_time_days_years_input",
        "m3_time_days_days_per_year_input",
        "m3_omega_period_input",
        "m3_travel_angle_omega_input",
        "m3_travel_angle_days_input",
        "m3_phase_angle_travel_angle_input",
        "m3_time_years_formula_input",
        "m3_time_days_formula_input",
        "m3_omega_formula_input",
        "m3_travel_angle_formula_input",
        "m3_phase_angle_formula_input",
        "m4_arrival_speed",
        "m4_arrival_speed_saved",
        "m4_arrival_speed_input",
        "m4_arrival_speed_submit",
        "m4_arrival_speed_mu_input",
        "m4_arrival_speed_radius_input",
        "m4_arrival_speed_axis_input",
        "m4_arrival_speed_formula_input",
        "m4_planet_speed",
        "m4_planet_speed_saved",
        "m4_planet_speed_input",
        "m4_planet_speed_submit",
        "m4_planet_speed_mu_input",
        "m4_planet_speed_radius_input",
        "m4_planet_speed_formula_input",
        "m4_excess_speed",
        "m4_excess_speed_saved",
        "m4_excess_speed_input",
        "m4_excess_speed_submit",
        "m4_excess_speed_spacecraft_input",
        "m4_excess_speed_planet_input",
        "m4_excess_speed_formula_input",
        "m4_altitude_selection",
        "m4_confirm_altitude",
        "m4_confirm_altitude_disabled",
        "m4_selected_altitude_km",
        "m4_closest_distance_km",
        "m4_step2_complete",
        "m4_eccentricity",
        "m4_eccentricity_saved",
        "m4_eccentricity_input",
        "m4_eccentricity_submit",
        "m4_eccentricity_distance_input",
        "m4_eccentricity_speed_input",
        "m4_eccentricity_mu_input",
        "m4_eccentricity_formula_input",
        "m4_deflection_angle",
        "m4_deflection_angle_saved",
        "m4_deflection_angle_input",
        "m4_deflection_angle_submit",
        "m4_deflection_angle_eccentricity_input",
        "m4_deflection_angle_formula_input",
        "m4_final_approach_input_context",
        "m4_final_approach_soi",
        "m4_final_approach_soi_formula_input",
        "m4_final_approach_angular_momentum",
        "m4_final_approach_angular_momentum_formula_input",
        "m4_final_approach_energy",
        "m4_final_approach_energy_formula_input",
        "m4_final_approach_eccentricity",
        "m4_final_approach_eccentricity_formula_input",
        "m4_complete",
    ):
        st.session_state.pop(key, None)
    st.session_state.pop("mission2_saved_answers", None)
    st.session_state.hint_counts = {}
    st.session_state.selected_planet = st.session_state.planet_select


def render_mission2() -> None:
    st.header("MISSION 2. 미지의 항로를 개척하라!")
    st.write(
        "미지의 행성을 향한 첫 여정이 시작된다. 타원의 성질을 탐구하고 우주선의 전이 궤도를 설계해, 미지의 세계로 나아갈 항로를 개척하라!"
    )

    planet_key = st.selectbox(
        "목적 행성",
        options=list(PLANETS),
        format_func=lambda key: PLANETS[key].name,
        key="planet_select",
        on_change=_on_planet_change,
    )

    planet = PLANETS[planet_key]
    st.subheader("행성 기본 데이터 · 제공값")
    earth_column, planet_column = st.columns(2)
    with earth_column:
        st.metric("지구 평균 태양 거리", f"{EARTH_ORBIT_RADIUS_AU:.3f} AU")
    with planet_column:
        st.metric("목적 행성", planet.name)
        st.write(f"평균 태양 거리: **{planet.orbit_radius_au:.3f} AU**")
        st.write(
            f"공전 주기: **{planet.orbital_period_days:,.2f}일** "
            f"({planet.orbital_period_years:.4f}년)"
        )
    st.caption(planet.description)
    st.subheader("직접 계산할 값")
    st.caption(
        "아래 단계에서는 위에 제공된 행성 데이터를 이용해 각 값을 직접 계산합니다."
    )

    with st.container(key="mission2-conditions", border=True):
        st.subheader("조건")
        st.markdown(
            """
            행성의 궤도 역학을 고려하여 우주선을 발사하는 것은 매우 복잡한 수학적 작업이므로. 이 작업을 단순화하기 위해 세 가지 가정을 세워야 합니다.

            ⓵ 지구와 행성의 궤도는 원형이며 태양을 중심으로 한다.

            ⓶ 지구와 행성은 일정한 속도로 움직인다.

            ⓷ 지구와 행성의 궤도는 동일 평면상에 있다.
            """
        )

    with st.expander("타원 구성 요소 복습"):
        st.image(str(ASSET_DIR / "eclipse.png"), width=420)
        st.caption("태양은 전이 타원의 중심이 아니라 초점에 위치합니다.")

    st.subheader("STEP 1 · 전이 궤도 장반경")
    if not render_formula_problem(
        key="m2_a",
        title="전이 타원의 장반경 계산",
        formula=r"a = \frac{r_E + r_P}{2}",
        formula_layout="""
            <span>a = </span>
            <span class="formula-fraction">
                <span class="formula-numerator">
                    <span data-formula-slot="r_e"></span> +
                    <span data-formula-slot="r_p"></span>
                </span>
                <span class="formula-denominator">2</span>
            </span>
        """,
        inputs=(
            FormulaInput(
                "r_e", "지구 궤도 반지름 r_E", EARTH_ORBIT_RADIUS_AU,
                "AU", "%.4f", strictly_positive=True,
            ),
            FormulaInput(
                "r_p", "행성 궤도 반지름 r_P", planet.orbit_radius_au,
                "AU", "%.4f", strictly_positive=True,
            ),
        ),
        calculate=lambda values: (values["r_e"] + values["r_p"]) / 2,
        expected=transfer_semi_major_axis(planet),
        tolerance=0.01,
        result_label="계산 결과 a",
        result_unit="AU",
        success_message="정답입니다. 장반경을 다음 단계에 사용합니다.",
        hints=(
            "두 입력 반지름을 더한 다음 2로 나누세요.",
            "a = (r_E + r_P) / 2 입니다.",
        ),
    ):
        return

    st.success(f"전이 궤도 장반경 a: {st.session_state.m2_a:.4f} AU")
    st.subheader("STEP 2-1 · 전이 궤도 이심률")
    if not render_formula_problem(
        key="m2_e",
        title="전이 타원의 이심률 계산",
        formula=r"e = \frac{r_P - r_E}{r_P + r_E}",
        formula_layout="""
            <span>e = </span>
            <span class="formula-fraction">
                <span class="formula-numerator">
                    <span data-formula-slot="r_p"></span> −
                    <span data-formula-slot="r_e"></span>
                </span>
                <span class="formula-denominator">
                    <span data-formula-slot="r_p"></span> +
                    <span data-formula-slot="r_e"></span>
                </span>
            </span>
        """,
        inputs=(
            FormulaInput(
                "r_p", "행성 궤도 반지름 r_P", planet.orbit_radius_au,
                "AU", "%.4f", strictly_positive=True,
            ),
            FormulaInput(
                "r_e", "지구 궤도 반지름 r_E", EARTH_ORBIT_RADIUS_AU,
                "AU", "%.4f", strictly_positive=True,
            ),
        ),
        calculate=_eccentricity_from_radii,
        expected=transfer_eccentricity(planet),
        tolerance=0.01,
        result_label="계산 결과 e",
        result_unit="",
        success_message="정답입니다. 전이 타원의 이심률을 저장했습니다.",
        hints=(
            "분자는 r_P - r_E, 분모는 r_P + r_E 입니다.",
            "e = (r_P - r_E) / (r_P + r_E) 입니다.",
        ),
    ):
        return

    st.success(f"전이 궤도 이심률 e: {st.session_state.m2_e:.5f}")
    st.subheader("STEP 2-2 · 초점 거리")
    expected_focus = focus_distance(
        st.session_state.m2_a,
        st.session_state.m2_e,
    )
    if not render_formula_problem(
        key="m2_c",
        title="타원 중심에서 초점까지의 거리 계산",
        formula=r"c = a \times e",
        formula_layout="""
            <span>c = </span>
            <span data-formula-slot="a"></span>
            <span>×</span>
            <span data-formula-slot="e"></span>
        """,
        inputs=(
            FormulaInput("a", "장반경 a", st.session_state.m2_a, "AU", "%.4f", strictly_positive=True),
            FormulaInput("e", "이심률 e", st.session_state.m2_e, "", "%.5f", strictly_positive=True),
        ),
        calculate=lambda values: focus_distance(values["a"], values["e"]),
        expected=expected_focus,
        tolerance=0.01,
        result_label="계산 결과 c",
        result_unit="AU",
        success_message="정답입니다. 타원 궤도를 확인할 수 있습니다.",
        hints=(
            "장반경 a와 이심률 e를 곱하세요.",
            "c = a × e 입니다.",
        ),
    ):
        return

    st.success(f"초점 거리 c: {st.session_state.m2_c:.4f} AU")
    st.subheader("STEP 2-3 · 전이 타원의 단반경 b")
    st.latex(r"b = \sqrt{a^2 - c^2}")
    try:
        semi_minor = semi_minor_axis_from_focus(
            st.session_state.m2_a,
            st.session_state.m2_c,
        )
    except ValueError as error:
        st.error(f"단반경을 계산할 수 없습니다: {error}")
        return
    st.write(
        f"검증: a² > c² · "
        f"{st.session_state.m2_a:.4f}² > {st.session_state.m2_c:.4f}²"
    )
    result_columns = st.columns(3)
    result_columns[0].metric("장반경 a", f"{st.session_state.m2_a:.4f} AU")
    result_columns[1].metric("단반경 b", f"{semi_minor:.4f} AU")
    result_columns[2].metric("초점 거리 c", f"{st.session_state.m2_c:.4f} AU")

    st.subheader("STEP 2-4 · 타원 궤도 시각화")
    render_ellipse_design()

    st.button(
        "MISSION 2 궤도 확인 완료",
        key="mission2_complete_button",
        on_click=_complete_mission2,
    )
