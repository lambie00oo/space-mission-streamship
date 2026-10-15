import math
from pathlib import Path

import streamlit as st

from data.planets import DAYS_PER_YEAR, PLANETS
from logic.orbit_calculations import (
    EARTH_ORBIT_RADIUS_AU,
    phase_angle_degrees,
    planet_angular_velocity_degrees_per_day,
    planet_travel_angle_degrees,
    semi_minor_axis,
    transfer_time_days,
    transfer_time_years,
)
from ui.formula_problems import (
    FormulaInput,
    render_formula_problem,
)
from ui.mission3_rendezvous import COMPONENT_KEY, render_rendezvous_simulation


ASSET_DIR = Path(__file__).resolve().parent.parent / "images"

HINTS = {
    "m3_time_years": (
        "케플러 제3법칙에서 전이 타원의 전체 주기를 먼저 구합니다.",
        "T = √(a³)을 구한 뒤, 호만 전이는 그 절반입니다.",
        "전이 시간(년)은 √(a³) / 2 입니다.",
    ),
    "m3_time_days": (
        "년 단위 결과를 일 단위로 바꾸어야 합니다.",
        f"1년은 {DAYS_PER_YEAR:g}일로 환산합니다.",
        f"전이 시간(일) = 전이 시간(년) × {DAYS_PER_YEAR:g} 입니다.",
    ),
    "m3_omega": (
        "한 바퀴의 각도는 360°입니다.",
        "공전 각속도는 360°를 공전 주기(일)로 나눕니다.",
        "ω = 360° / T_P 입니다. T_P는 일 단위로 사용합니다.",
    ),
    "m3_travel_angle": (
        "행성 이동 각도는 각속도와 전이 시간을 함께 사용합니다.",
        "각속도(°/day)에 전이 시간(day)을 곱합니다.",
        "Δθ = ω × t_일 입니다.",
    ),
    "m3_phase_angle": (
        "전이 타원의 반 바퀴는 180°입니다.",
        "180°에서 행성의 이동 각도를 뺀 다음 360° 기준으로 조정합니다.",
        "φ = (180° - Δθ) mod 360° 입니다.",
    ),
}


def _complete_mission3() -> None:
    required_results = (
        "m3_time_years",
        "m3_time_days",
        "m3_omega",
        "m3_travel_angle",
        "m3_phase_angle",
    )
    if not all(key in st.session_state for key in required_results):
        st.error("MISSION 3의 필수 계산과 검증을 모두 완료해 주세요.")
        return

    component_state = st.session_state.get(COMPONENT_KEY, {})
    component_snapshot = (
        component_state.get("snapshot")
        if isinstance(component_state, dict)
        else getattr(component_state, "snapshot", None)
    )
    if not isinstance(component_snapshot, dict):
        component_snapshot = st.session_state.get("m3_rendezvous_snapshot")
    if not isinstance(component_snapshot, dict):
        component_snapshot = {}

    try:
        angle_degrees = float(
            component_snapshot.get(
                "angle",
                st.session_state.m3_rendezvous_angle_degrees
                if "m3_rendezvous_angle_degrees" in st.session_state
                else st.session_state.m3_phase_angle,
            )
        )
        progress = float(
            component_snapshot.get(
                "progress",
                st.session_state.get("m3_rendezvous_progress", 0.0),
            )
        )
    except (TypeError, ValueError):
        st.error("MISSION 3의 최종 시뮬레이션 상태가 올바르지 않습니다.")
        return
    if (
        not math.isfinite(angle_degrees)
        or not math.isfinite(progress)
        or not 0 <= progress <= 1
    ):
        st.error("MISSION 3의 최종 시뮬레이션 상태가 올바르지 않습니다.")
        return

    st.session_state.m3_final_approach_snapshot = {
        "angle_degrees": angle_degrees % 360,
        "progress": progress,
        "status": str(
            component_snapshot.get(
                "status",
                st.session_state.get("m3_rendezvous_status", "ready"),
            )
        ),
    }
    st.session_state.m3_complete = True
    st.session_state.current_page = "MISSION4"


def _prepare_input_state(planet_name: str, semi_major_axis: float) -> None:
    context = (planet_name, semi_major_axis)
    previous_context = st.session_state.get("mission3_input_context")
    if previous_context is not None and previous_context != context:
        for key in (
            "m3_time_years",
            "m3_time_days",
            "m3_omega",
            "m3_travel_angle",
            "m3_phase_angle",
            "m3_complete",
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
            "m3_rendezvous_angle_degrees",
            "m3_rendezvous_status",
            "m3_rendezvous_progress",
            "m3_rendezvous_revision",
            "m3_rendezvous_component",
            "m3_rendezvous_snapshot",
            "m3_final_approach_snapshot",
            "m4_final_approach_input_context",
            "m4_final_approach_soi",
            "m4_final_approach_soi_formula_input",
            "m4_final_approach_angular_momentum",
            "m4_final_approach_angular_momentum_formula_input",
            "m4_final_approach_energy",
            "m4_final_approach_energy_formula_input",
            "m4_final_approach_eccentricity",
            "m4_final_approach_eccentricity_formula_input",
        ):
            st.session_state.pop(key, None)
    st.session_state.mission3_input_context = context


def _render_mission3_calculation(planet, semi_major_axis: float) -> None:
    _prepare_input_state(planet.name, semi_major_axis)
    st.header("MISSION 3. 운명의 조우를 찾아라!")
    st.write(
        "광활한 우주에서 목적 행성과 만나는 순간을 찾아야 한다. 우주선과 행성의 움직임을 추적하고 이동 시간과 위치를 분석해, 성공적인 만남을 위한 항해 계획을 완성하라!"
    )
    st.image(str(ASSET_DIR / "kepler.png"), width=460)
    st.subheader("계산에 사용할 데이터")
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

    expected_years = transfer_time_years(semi_major_axis)
    expected_days = transfer_time_days(semi_major_axis)
    st.subheader("STEP 1 · 호만 전이 시간")
    st.markdown(
        """
        - **t_year**: 전이 궤도 이동 시간 (**년**)
        - **a**: MISSION2에서 구한 전이 타원의 긴반지름 (**AU**)

        이 식은 케플러 제3법칙을 이용한 이상적인 호만 전이 궤도 이동 시간의
        **교육용 근삿값**입니다.
        """
    )
    st.caption(f"MISSION 2 장반경: {semi_major_axis:.4f} AU")

    if "m3_time_years" not in st.session_state:
        if not render_formula_problem(
            key="m3_time_years",
            title="호만 전이 시간 계산",
            formula=r"t_{\text{year}} = \frac{1}{2}\sqrt{a^3}",
            formula_layout="""
                <span>t<sub>year</sub> = ½</span>
                <span class="formula-radical">
                    <span>√</span>
                    <span class="formula-radicand">
                        <span data-formula-slot="a"></span><sup>3</sup>
                    </span>
                </span>
            """,
            inputs=(
                FormulaInput(
                    "a", "전이 타원 장반경 a", semi_major_axis,
                    "AU", "%.4f", strictly_positive=True,
                ),
            ),
            calculate=lambda values: transfer_time_years(values["a"]),
            expected=expected_years,
            tolerance=0.01,
            result_label="계산 결과 t_year",
            result_unit="년",
            success_message="정답입니다. 이제 일 단위로 변환합니다.",
            hints=HINTS["m3_time_years"],
        ):
            return

    if "m3_time_days" not in st.session_state:
        st.markdown(
            f"""
            - **t_days**: 전이 궤도 이동 시간 (**일**)
            - **t_year**: 전이 궤도 이동 시간 (**년**)
            - **{DAYS_PER_YEAR:g}**: 1년을 일 단위로 환산할 때 사용하는 값 (**일/년**)
            """
        )
        if not render_formula_problem(
            key="m3_time_days",
            title="전이 시간을 일 단위로 변환",
            formula=rf"t_{{\text{{days}}}} = t_{{\text{{year}}}} \times {DAYS_PER_YEAR:g}",
            formula_layout=f"""
                <span>t<sub>days</sub> = </span>
                <span data-formula-slot="years"></span>
                <span>×</span>
                <span data-formula-slot="days_per_year"></span>
            """,
            inputs=(
                FormulaInput(
                    "years", "전이 시간 t_year", st.session_state.m3_time_years,
                    "년", "%.5f", strictly_positive=True,
                ),
                FormulaInput(
                    "days_per_year", "일수 환산값", DAYS_PER_YEAR,
                    "일/년", "%.2f", strictly_positive=True,
                ),
            ),
            calculate=lambda values: values["years"] * values["days_per_year"],
            expected=expected_days,
            tolerance=2.0,
            result_label="계산 결과 t_days",
            result_unit="일",
            success_message="정답입니다. 전이 시간을 일 단위로 저장했습니다.",
            hints=HINTS["m3_time_days"],
        ):
            return

    st.success(
        f"전이 시간: {st.session_state.m3_time_years:.4f}년 · "
        f"{st.session_state.m3_time_days:.2f}일"
    )

    expected_omega = planet_angular_velocity_degrees_per_day(planet)
    st.subheader("STEP 2-1 · 행성의 공전 각속도")
    st.markdown(
        """
        - **ω**: 목적 행성의 공전 각속도 (**°/일**)
        - **T_P**: 목적 행성의 공전 주기 (**일**)
        - **360°**: 행성이 한 바퀴 공전할 때 이동하는 각도
        """
    )
    if "m3_omega" not in st.session_state:
        if not render_formula_problem(
            key="m3_omega",
            title="행성의 공전 각속도 계산",
            formula=r"\omega = \frac{360^\circ}{T_P}",
            formula_layout="""
                <span>ω = </span>
                <span class="formula-fraction">
                    <span class="formula-numerator">360°</span>
                    <span class="formula-denominator">
                        <span data-formula-slot="period"></span>
                    </span>
                </span>
            """,
            inputs=(
                FormulaInput(
                    "period", "공전 주기 T_P", planet.orbital_period_days,
                    "일", "%.2f", strictly_positive=True,
                ),
            ),
            calculate=lambda values: 360 / values["period"],
            expected=expected_omega,
            tolerance=0.0001,
            result_label="계산 결과 ω",
            result_unit="°/일",
            success_message="정답입니다. 행성의 이동 각도를 계산할 수 있습니다.",
            hints=HINTS["m3_omega"],
        ):
            return

    st.success(
        f"행성 공전 각속도: {st.session_state.m3_omega:.6f}°/일"
    )
    expected_theta = planet_travel_angle_degrees(planet, st.session_state.m3_time_days)
    st.subheader("STEP 2-2 · 전이 시간 동안 행성이 이동한 각도")
    st.markdown(
        """
        - **Δθ**: 우주선이 이동하는 동안 선택한 행성이 공전하는 각도 (**°**)
        - **ω**: 선택한 행성의 평균 공전 각속도 (**°/일**)
        - **t_days**: 전이 궤도 이동 시간 (**일**)
        """
    )
    if "m3_travel_angle" not in st.session_state:
        if not render_formula_problem(
            key="m3_travel_angle",
            title="전이 시간 동안 행성이 이동한 각도 계산",
            formula=r"\Delta\theta = \omega \times t_{\text{days}}",
            formula_layout="""
                <span>Δθ = </span>
                <span data-formula-slot="omega"></span>
                <span>×</span>
                <span data-formula-slot="days"></span>
            """,
            inputs=(
                FormulaInput(
                    "omega", "공전 각속도 ω", st.session_state.m3_omega,
                    "°/일", "%.6f", strictly_positive=True,
                ),
                FormulaInput(
                    "days", "전이 시간 t_days", st.session_state.m3_time_days,
                    "일", "%.3f", strictly_positive=True,
                ),
            ),
            calculate=lambda values: values["omega"] * values["days"],
            expected=expected_theta,
            tolerance=0.1,
            result_label="계산 결과 Δθ",
            result_unit="°",
            success_message="정답입니다. 위상각을 계산할 수 있습니다.",
            hints=HINTS["m3_travel_angle"],
        ):
            return

    st.success(
        f"행성 이동 각도: {st.session_state.m3_travel_angle:.4f}°"
    )
    expected_phase = phase_angle_degrees(st.session_state.m3_travel_angle)
    st.subheader("STEP 2-3 · 출발 시 필요한 위상각")
    st.markdown(
        """
        - **φ**: 지구 출발 시점에서 목적 행성의 초기 위치를 나타내는 위상각 (**°**)
        - **Δθ**: 전이 시간 동안 목적 행성이 이동한 각도 (**°**)
        - **180°**: 이상적인 호만 전이 궤도에서 목적 행성의 도착 위치를 나타내는 각도
        - **mod 360°**: 결과를 **0° 이상 360° 미만**의 각도로 바꾸는 연산
        """
    )
    if "m3_phase_angle" not in st.session_state:
        if not render_formula_problem(
            key="m3_phase_angle",
            title="출발 시 필요한 위상각 계산",
            formula=r"\phi = (180^\circ - \Delta\theta) \bmod 360^\circ",
            formula_layout="""
                <span>φ = (180° − </span>
                <span data-formula-slot="travel_angle"></span>
                <span>) mod 360°</span>
            """,
            inputs=(
                FormulaInput(
                    "travel_angle", "행성 이동 각도 Δθ",
                    st.session_state.m3_travel_angle, "°", "%.4f",
                ),
            ),
            calculate=lambda values: phase_angle_degrees(values["travel_angle"]),
            expected=expected_phase,
            tolerance=0.1,
            result_label="계산 결과 φ",
            result_unit="°",
            success_message="정답입니다. 궤도에 각도를 표시합니다.",
            hints=HINTS["m3_phase_angle"],
        ):
            return

    with st.container(border=True):
        st.subheader("STEP 3 · 궤도에서 각도 확인")
        st.write(
            f"행성 이동 각도: {st.session_state.m3_travel_angle:.4f}° · "
            f"위상각: {st.session_state.m3_phase_angle:.4f}°"
        )
        st.caption(
            "Mission 2에서 계산한 전이 타원과 Mission 3에서 계산한 위상각으로 "
            "행성 도착 시점을 확인합니다."
        )
        mission2_result = st.session_state.m2_result
        render_rendezvous_simulation(
            planet=planet,
            semi_major_axis_au=float(mission2_result["semi_major_axis_au"]),
            eccentricity=float(mission2_result["eccentricity"]),
            focus_distance_au=float(mission2_result["focus_distance_au"]),
            semi_minor_axis_au=semi_minor_axis(
                float(mission2_result["semi_major_axis_au"]),
                float(mission2_result["eccentricity"]),
            ),
            transfer_days=float(st.session_state.m3_time_days),
            target_angle_degrees=float(st.session_state.m3_phase_angle),
        )
        st.button(
            "학습 완료",
            key="mission3_complete_button",
            on_click=_complete_mission3,
        )


def render_mission3() -> None:
    result = st.session_state.get("m2_result")
    if (
        not st.session_state.get("m2_complete", False)
        or not isinstance(result, dict)
    ):
        st.header("MISSION 3. 운명의 조우를 찾아라!")
        st.info("MISSION2의 궤도 설계를 완료하면 다음 단계가 열립니다.")
        st.button(
            "MISSION2로 이동",
            key="mission3_locked_back",
            on_click=lambda: st.session_state.update(
                current_page="MISSION2"
            )
        )
        return

    planet = PLANETS[result["planet_key"]]
    _render_mission3_calculation(
        planet,
        float(result["semi_major_axis_au"]),
    )
