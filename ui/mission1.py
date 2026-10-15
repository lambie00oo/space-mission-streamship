from pathlib import Path

import streamlit as st


ASSET_DIR = Path(__file__).resolve().parent.parent / "images"


def _complete_mission1() -> None:
    st.session_state.mission1_completed = True
    st.session_state.current_page = "MISSION2"


def _render_step1() -> None:
    with st.container(border=True):
        st.subheader("STEP1: 타원")
        st.image(str(ASSET_DIR / "eclipse.png"), width=300)
        st.markdown(
            """
            **타원**

            두 정점으로부터의 거리의 합이 장축으로 일정한 이차곡선.

            **타원의 구성 요소**
            - 긴 지름: 장축 (2a)
            - 작은 지름: 단축 (2b)
            - 꼭짓점 A, B, A', B'
            - 초점 F, F'
            """
        )


def _render_step2() -> None:
    with st.container(border=True):
        st.subheader("STEP2: 이심률")
        st.markdown(
            """
            **이심률**

            이차곡선에서 원뿔 곡선의 특성을 나타내는 값.
            원뿔 곡선이 원에서 벗어나는 정도를 나타낸다고 볼 수 있다.

            **이차곡선과 이심률**
            - e = 0: 원
            - 0 < e < 1: 타원
            - e = 1: 포물선
            - e > 1: 쌍곡선
            """
        )


def _render_step3() -> None:
    with st.container(border=True):
        st.subheader("STEP3: 케플러 법칙")
        st.image(str(ASSET_DIR / "kepler.png"), width=400)
        st.markdown(
            """
            **케플러 법칙**
            1. **제1법칙: 타원 궤도의 법칙**
               모든 행성은 태양을 한쪽 초점으로 하는 타원 궤도를 그리며 공전한다.
            2. **제2법칙: 면적속도 일정의 법칙**
               태양과 행성을 연결하는 선분이 같은 시간 동안 쓸고 지나가는 면적은 항상 일정하다.
            3. **제3법칙: 조화의 법칙**
               행성의 공전 주기의 제곱은 궤도의 긴반지름의 세제곱에 비례한다.
            """
        )


def _render_step4() -> None:
    with st.container(border=True):
        st.subheader("STEP4: 호만 전이 궤도")
        st.image(str(ASSET_DIR / "homann.png"), width=500)
        st.markdown(
            """
            **호만 전이 궤도**

            두 원형 궤도 사이를 최소한의 추진제로 이동할 수 있는 효율적인 타원형 전이 궤도.
            근일점은 지구 궤도의 거리에 위치하며, 원일점은 화성 궤도 거리에 위치함.

            **지구-화성까지 호만 전이 궤도 메커니즘**

            - 🚀 우주선이 발사대에 놓여 있음(근일점)
            - 🔥 로켓을 통해 가속
            - 원일점이 화성 궤도 거리에 위치하게 됨
            - 🪐 지구 대기권을 벗어나 호만 전이 궤도로 진입
            - ✨ 관성을 통해서 궤도를 따라 이동
            - 🔴 화성에 도착(원일점)
            """
        )


def render_mission1() -> None:
    st.header("MISSION 1. 우주의 비밀을 밝혀라!")
    st.write(
        "우주를 향한 탐험은 원리를 이해하는 것에서 시작된다. 타원의 모양과 초점, 행성의 공전 원리를 탐구하고 호만 전이 궤도의 기본 개념을 익혀, 미지의 우주로 나아가기 위한 첫걸음을 내디뎌라!"
    )
    _render_step1()
    _render_step1()
    _render_step2()
    _render_step3()
    _render_step4()

    st.divider()
    st.caption("이론 교육을 마쳤습니다. 이제 계산을 통해 전이 궤도를 설계합니다.")
    st.button(
        "교육 완료 · MISSION2 시작",
        key="mission1_complete",
        on_click=_complete_mission1,
    )
