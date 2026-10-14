from pathlib import Path

import streamlit as st


ASSET_DIR = Path(__file__).resolve().parent.parent / "images"


def _start_mission1() -> None:
    st.session_state.current_page = "MISSION1"


def render_intro() -> None:
    st.image(str(ASSET_DIR / "hero.jpg"), use_container_width=True)
    st.header("인류의 새로운 우주 탐사를 시작할 시간이다! 🚀")
    st.write(
        "여러분은 우주 탐사선의 궤도를 설계하는 임무를 맡았다.  \n"
        "목표는 지구를 출발해 행성에 안전하게 도착하는 것!  \n"
        "이번 미션에서는 원과 타원의 기하학적 특징을 알아보고, 지구와 화성을 연결하는 "
        "호만 전이 궤도와 적절한 발사 시기를 설계하는 방법을 배운다. 더 나아가 행성 주변의 "
        "쌍곡선 궤도를 살펴보며 실제 우주 비행을 근사하는 패치드 코닉 모델도 만나게 된다.  \n"
        "이제 우주를 향한 여정을 시작하라. 여러분의 설계가 화성 탐사의 운명을 결정한다!"
    )
    st.divider()
    st.button(
        "교육 시작 · MISSION1",
        key="start_mission1",
        on_click=_start_mission1,
    )
