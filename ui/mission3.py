from html import escape
from pathlib import Path

import streamlit as st

from data.planets import DAYS_PER_YEAR, PLANETS
from logic.answer_checker import check_numeric_answer
from logic.orbit_calculations import (
    EARTH_ORBIT_RADIUS_AU,
    phase_angle_degrees,
    planet_angular_velocity_degrees_per_day,
    planet_travel_angle_degrees,
    transfer_time_days,
    transfer_time_years,
)
from ui.orbit_plot import mission3_orbit_plot


ASSET_DIR = Path(__file__).resolve().parent.parent / "images"

HINTS = {
    "m3_years": (
        "케플러 제3법칙에서 전이 타원의 전체 주기를 먼저 구합니다.",
        "T = √(a³)을 구한 뒤, 호만 전이는 그 절반입니다.",
        "전이 시간(년)은 √(a³) / 2 입니다.",
    ),
    "m3_days": (
        "년 단위 결과를 일 단위로 바꾸어야 합니다.",
        f"1년은 {DAYS_PER_YEAR:g}일로 환산합니다.",
        f"전이 시간(일) = 전이 시간(년) × {DAYS_PER_YEAR:g} 입니다.",
    ),
    "m3_omega": (
        "한 바퀴의 각도는 360°입니다.",
        "공전 각속도는 360°를 공전 주기(일)로 나눕니다.",
        "ω = 360° / T_P 입니다. T_P는 일 단위로 사용합니다.",
    ),
    "m3_theta": (
        "행성 이동 각도는 각속도와 전이 시간을 함께 사용합니다.",
        "각속도(°/day)에 전이 시간(day)을 곱합니다.",
        "Δθ = ω × t_일 입니다.",
    ),
    "m3_phase": (
        "전이 타원의 반 바퀴는 180°입니다.",
        "180°에서 행성의 이동 각도를 뺀 다음 360° 기준으로 조정합니다.",
        "φ = (180° - Δθ) mod 360° 입니다.",
    ),
}


def _submit_answer(
    key: str,
    answer: float,
    expected: float,
    tolerance: float,
    success_message: str,
) -> None:
    if check_numeric_answer(answer, expected, tolerance):
        st.session_state[key] = expected
        st.session_state.hint_counts.pop(key, None)
        st.success(success_message)
        st.rerun()

    hint_counts = st.session_state.setdefault("hint_counts", {})
    attempts = hint_counts.get(key, 0) + 1
    hint_counts[key] = attempts
    st.error("계산값을 다시 확인해 주세요.")
    st.info(HINTS[key][min(attempts - 1, len(HINTS[key]) - 1)])


def _render_mission3_calculation(planet, semi_major_axis: float) -> None:
    st.header("MISSION 3: 전이 시간 및 도착 위치 예측")
    st.write(
        "MISSION 2에서 설계한 타원을 따라 이동하는 시간을 구하고, "
        "도착 시점의 행성 위치와 출발 위상각을 예측합니다."
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
    st.latex(r"t_{\text{year}} = \frac{1}{2}\sqrt{a^3}")
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
        with st.form("mission3_time_years"):
            answer_years = st.number_input(
                "전이 시간 (년)",
                min_value=0.0,
                step=0.01,
                format="%.5f",
                key="mission3_time_years_input",
            )
            submit_years = st.form_submit_button(
                "년 단위 결과 확인",
                key="mission3_time_years_submit",
            )
        if submit_years:
            _submit_answer(
                "m3_time_years",
                answer_years,
                expected_years,
                0.01,
                "정답입니다. 이제 일 단위로 변환합니다.",
            )
        return

    if "m3_time_days" not in st.session_state:
        st.latex(
            rf"t_{{\text{{days}}}} = t_{{\text{{year}}}} \times {DAYS_PER_YEAR:g}"
        )
        st.markdown(
            f"""
            - **t_days**: 전이 궤도 이동 시간 (**일**)
            - **t_year**: 전이 궤도 이동 시간 (**년**)
            - **{DAYS_PER_YEAR:g}**: 1년을 일 단위로 환산할 때 사용하는 값 (**일/년**)
            """
        )
        with st.form("mission3_time_days"):
            answer_days = st.number_input(
                "전이 시간 (일)",
                min_value=0.0,
                step=1.0,
                format="%.3f",
                key="mission3_time_days_input",
            )
            submit_days = st.form_submit_button(
                "일 단위 결과 확인",
                key="mission3_time_days_submit",
            )
        if submit_days:
            _submit_answer(
                "m3_time_days",
                answer_days,
                expected_days,
                2.0,
                "정답입니다. 전이 시간을 일 단위로 저장했습니다.",
            )
        return

    st.success(
        f"전이 시간: {st.session_state.m3_time_years:.4f}년 · "
        f"{st.session_state.m3_time_days:.2f}일"
    )

    expected_omega = planet_angular_velocity_degrees_per_day(planet)
    st.subheader("STEP 2-1 · 행성의 공전 각속도")
    st.latex(r"\omega = \frac{360^\circ}{T_P}")
    st.markdown(
        """
        - **ω**: 목적 행성의 공전 각속도 (**°/일**)
        - **T_P**: 목적 행성의 공전 주기 (**일**)
        - **360°**: 행성이 한 바퀴 공전할 때 이동하는 각도
        """
    )
    if "m3_omega" not in st.session_state:
        with st.form("mission3_angular_velocity"):
            answer_omega = st.number_input(
                "공전 각속도 ω (°/일)",
                min_value=0.0,
                step=0.001,
                format="%.6f",
                key="mission3_omega_input",
            )
            submit_omega = st.form_submit_button(
                "각속도 확인",
                key="mission3_omega_submit",
            )
        if submit_omega:
            _submit_answer(
                "m3_omega",
                answer_omega,
                expected_omega,
                0.0001,
                "정답입니다. 행성의 이동 각도를 계산할 수 있습니다.",
            )
        return

    expected_theta = planet_travel_angle_degrees(planet, st.session_state.m3_time_days)
    st.subheader("STEP 2-2 · 전이 시간 동안 행성이 이동한 각도")
    st.latex(r"\Delta\theta = \omega \times t_{\text{days}}")
    st.markdown(
        """
        - **Δθ**: 우주선이 이동하는 동안 선택한 행성이 공전하는 각도 (**°**)
        - **ω**: 선택한 행성의 평균 공전 각속도 (**°/일**)
        - **t_days**: 전이 궤도 이동 시간 (**일**)
        """
    )
    if "m3_travel_angle" not in st.session_state:
        with st.form("mission3_travel_angle"):
            answer_theta = st.number_input(
                "이동 각도 Δθ (°)",
                min_value=0.0,
                step=1.0,
                format="%.4f",
                key="mission3_theta_input",
            )
            submit_theta = st.form_submit_button(
                "이동 각도 확인",
                key="mission3_theta_submit",
            )
        if submit_theta:
            _submit_answer(
                "m3_travel_angle",
                answer_theta,
                expected_theta,
                0.1,
                "정답입니다. 위상각을 계산할 수 있습니다.",
            )
        return

    expected_phase = phase_angle_degrees(st.session_state.m3_travel_angle)
    st.subheader("STEP 2-3 · 출발 시 필요한 위상각")
    st.latex(r"\phi = (180^\circ - \Delta\theta) \bmod 360^\circ")
    st.markdown(
        """
        - **φ**: 지구 출발 시점에서 목적 행성의 초기 위치를 나타내는 위상각 (**°**)
        - **Δθ**: 전이 시간 동안 목적 행성이 이동한 각도 (**°**)
        - **180°**: 이상적인 호만 전이 궤도에서 목적 행성의 도착 위치를 나타내는 각도
        - **mod 360°**: 결과를 **0° 이상 360° 미만**의 각도로 바꾸는 연산
        """
    )
    if "m3_phase_angle" not in st.session_state:
        with st.form("mission3_phase_angle"):
            answer_phase = st.number_input(
                "위상각 φ (°)",
                min_value=0.0,
                max_value=360.0,
                step=0.01,
                format="%.4f",
                key="mission3_phase_input",
            )
            submit_phase = st.form_submit_button(
                "위상각 확인",
                key="mission3_phase_submit",
            )
        if submit_phase:
            _submit_answer(
                "m3_phase_angle",
                answer_phase,
                expected_phase,
                0.1,
                "정답입니다. 궤도에 각도를 표시합니다.",
            )
        return

    st.subheader("STEP 2-4 · 궤도에서 각도 확인")
    st.write(
        f"행성 이동 각도: {st.session_state.m3_travel_angle:.4f}° · "
        f"위상각: {st.session_state.m3_phase_angle:.4f}°"
    )
    st.pyplot(
        mission3_orbit_plot(
            planet,
            st.session_state.m3_phase_angle,
            st.session_state.m3_travel_angle,
        )
    )
    st.caption("각도는 도(degree), 반시계 방향을 양의 회전 방향으로 표시합니다.")
    if st.button("MISSION 3 완료 확인", key="mission3_complete_button"):
        st.session_state.m3_complete = True
        st.success("MISSION 3 완료!")


def _render_mission2_results(result: dict | None) -> None:
    card_style = (
        "background-color: #f0f5fa; border: 1px solid #c7d6e5; "
        "border-radius: 0.5rem; padding: 0.9rem;"
    )
    if result is None:
        st.markdown(
            f"""
            <div style="{card_style}">
              <strong>MISSION2 계산 결과</strong>
              <p>MISSION2를 완료하면 계산 결과가 여기에 표시됩니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    planet_name = escape(str(result["planet_name"]))
    semi_major_axis = float(result["semi_major_axis_au"])
    eccentricity = float(result["eccentricity"])
    focus_distance = float(result["focus_distance_au"])
    st.markdown(
        f"""
        <div style="{card_style}">
          <strong>MISSION2 계산 결과</strong><hr>
          <strong>목적 행성</strong><br>{planet_name}
          <hr>
          <strong>장반경 a</strong> · 전이 타원의 긴반지름 (AU)<br>
          {semi_major_axis:.4f} AU
          <br><br>
          <strong>이심률 e</strong> · 타원의 찌그러진 정도 (단위 없음)<br>
          {eccentricity:.4f}
          <br><br>
          <strong>초점 거리 c</strong> · 타원 중심에서 초점까지의 거리 (AU)<br>
          {focus_distance:.4f} AU
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mission3() -> None:
    result = st.session_state.get("m2_result")
    if (
        not st.session_state.get("m2_complete", False)
        or not isinstance(result, dict)
    ):
        result = None

    calculation_column, result_column = st.columns([3, 1], gap="large")
    with calculation_column:
        if result is None:
            st.header("MISSION 3: 전이 시간 및 도착 위치 예측")
            st.info("MISSION2의 궤도 설계를 완료하면 다음 단계가 열립니다.")
            st.button(
                "MISSION2로 이동",
                key="mission3_locked_back",
                on_click=lambda: st.session_state.update(
                    current_page="MISSION2"
                ),
            )
        else:
            planet = PLANETS[result["planet_key"]]
            _render_mission3_calculation(
                planet,
                float(result["semi_major_axis_au"]),
            )
    with result_column:
        _render_mission2_results(result)
