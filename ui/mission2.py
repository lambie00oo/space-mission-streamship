from pathlib import Path

import streamlit as st

from data.planets import EARTH_ORBIT_RADIUS_AU, PLANETS
from logic.answer_checker import check_numeric_answer
from logic.orbit_calculations import (
    focus_distance,
    semi_minor_axis,
    transfer_eccentricity,
    transfer_semi_major_axis,
)
from ui.orbit_plot import mission2_orbit_plot


ASSET_DIR = Path(__file__).resolve().parent.parent / "images"

HINTS = {
    "m2_a": (
        "두 궤도 반지름을 더한 뒤 2로 나눕니다.",
        "r₁ + r₂를 계산한 다음 그 결과를 2로 나눠 보세요.",
        "장반경 공식은 a = (r₁ + r₂) / 2 입니다.",
    ),
    "m2_e": (
        "이심률은 두 반지름의 차이를 이용합니다.",
        "분자는 r₂ - r₁, 분모는 r₂ + r₁ 입니다.",
        "e = (r₂ - r₁) / (r₂ + r₁) 공식을 적용하세요.",
    ),
    "m2_c": (
        "초점 거리는 장반경과 이심률을 이용합니다.",
        "저장된 a와 e를 곱하면 됩니다.",
        "c = a × e 입니다.",
    ),
}


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
        "mission3_time_years_input",
        "mission3_time_days_input",
        "mission3_omega_input",
        "mission3_theta_input",
        "mission3_phase_input",
    ):
        st.session_state.pop(key, None)
    st.session_state.hint_counts = {}
    st.session_state.selected_planet = st.session_state.planet_select


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


def render_mission2() -> None:
    st.header("MISSION 2: 호만 전이 궤도 설계")
    st.caption("이론 교육 완료. 이제 실제 발사 임무를 시작한다.")
    st.write(
        "부개연구소에서의 사전 교육을 무사히 마친 여러분은 드디어 우주 탐사선에 탑승할 준비를 마쳤습니다. "
        "하지만 행성으로 향하는 여정은 단순히 로켓을 발사한다고 성공하는 것이 아닙니다. "
        "지구와 행성은 태양 주위를 계속 공전하고 있으며, 우주선이 도착할 때 행성이 어디에 있을지 예측해야 합니다.  \n"
        "호만 전이 궤도의 원리를 활용해 두 행성의 위치와 이동 시간을 고려하고, 성공적인 발사 조건을 찾아보세요."
    )
    st.write(
        "지구와 목적 행성의 궤도 반지름을 이용해 전이 타원의 크기와 모양을 계산합니다. "
        "이 화면은 태양 중심의 2차원 원형 행성 궤도를 가정하는 교육용 모델입니다."
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

    with st.expander("타원 구성 요소 복습"):
        st.image(str(ASSET_DIR / "eclipse.png"), width=420)
        st.caption("태양은 전이 타원의 중심이 아니라 초점에 위치합니다.")

    st.subheader("STEP 1 · 전이 궤도 장반경")
    st.latex(r"a = \frac{r_E + r_P}{2}")
    st.markdown(
        """
        - **a**: 전이 타원의 긴반지름 (**AU**)
        - **r_E**: 태양에서 지구까지의 평균 거리 (**AU**)
        - **r_P**: 태양에서 선택한 행성까지의 평균 거리 (**AU**)
        """
    )
    with st.form("mission2_step1"):
        answer_a = st.number_input(
            "장반경 a (AU)",
            min_value=0.0,
            step=0.01,
            format="%.4f",
            key="mission2_semi_major_input",
        )
        submit_a = st.form_submit_button("장반경 확인", key="mission2_step1_submit")
    if submit_a:
        _submit_answer(
            "m2_a",
            answer_a,
            transfer_semi_major_axis(planet),
            0.01,
            "정답입니다. 장반경을 다음 단계에 사용합니다.",
        )

    if "m2_a" not in st.session_state:
        return

    st.subheader("STEP 2-1 · 전이 궤도 이심률")
    st.latex(r"e = \frac{r_P - r_E}{r_P + r_E}")
    st.markdown(
        """
        - **e**: 전이 타원의 이심률 (**단위 없음**)
        - **r_P**: 태양에서 선택한 행성까지의 평균 거리 (**AU**)
        - **r_E**: 태양에서 지구까지의 평균 거리 (**AU**)
        """
    )
    with st.form("mission2_step2"):
        answer_e = st.number_input(
            "이심률 e",
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            format="%.5f",
            key="mission2_eccentricity_input",
        )
        submit_e = st.form_submit_button("이심률 확인", key="mission2_step2_submit")
    if submit_e:
        _submit_answer(
            "m2_e",
            answer_e,
            transfer_eccentricity(planet),
            0.01,
            "정답입니다. 전이 타원의 이심률을 저장했습니다.",
        )

    if "m2_e" not in st.session_state:
        return

    st.subheader("STEP 2-2 · 초점 거리")
    st.latex(r"c = a \times e")
    st.markdown(
        """
        - **c**: 타원의 중심에서 초점까지의 거리 (**AU**)
        - **a**: 전이 타원의 긴반지름 (**AU**)
        - **e**: 전이 타원의 이심률 (**단위 없음**)
        """
    )
    with st.form("mission2_step3"):
        answer_c = st.number_input(
            "초점 거리 c (AU)",
            min_value=0.0,
            step=0.01,
            format="%.4f",
            key="mission2_focus_input",
        )
        submit_c = st.form_submit_button("초점 거리 확인", key="mission2_step3_submit")
    if submit_c:
        _submit_answer(
            "m2_c",
            answer_c,
            focus_distance(st.session_state.m2_a, st.session_state.m2_e),
            0.01,
            "정답입니다. 타원 궤도를 확인할 수 있습니다.",
        )

    if "m2_c" not in st.session_state:
        return

    st.subheader("STEP 2-3 · 전이 타원 확인")
    semi_minor = semi_minor_axis(st.session_state.m2_a, st.session_state.m2_e)
    st.write(
        f"반단축 b = {semi_minor:.4f} AU · 초점 거리 c = "
        f"{st.session_state.m2_c:.4f} AU"
    )
    st.pyplot(mission2_orbit_plot(planet))

    st.button(
        "MISSION 2 궤도 확인 완료",
        key="mission2_complete_button",
        on_click=_complete_mission2,
    )
