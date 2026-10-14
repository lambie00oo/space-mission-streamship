import streamlit as st

from ui.intro import render_intro
from ui.mission1 import render_mission1
from ui.mission2 import render_mission2
from ui.mission3 import render_mission3
from ui.calculator import render_calculator


def _return_to_mission1() -> None:
    st.session_state.current_page = "MISSION1"


st.set_page_config(
    page_title="SPACE ODYSSEY",
    page_icon="🚀",
    layout="wide",
)

if "selected_planet" not in st.session_state:
    st.session_state.selected_planet = "mars"
if "planet_select" not in st.session_state:
    st.session_state.planet_select = st.session_state.selected_planet
if "current_page" not in st.session_state:
    st.session_state.current_page = "도입부"
if "hint_counts" not in st.session_state:
    st.session_state.hint_counts = {}

st.title("SPACE ODYSSEY")
st.caption("우주 궤도 설계 교육 게임")
st.markdown(
    """
    <style>
    .st-key-calculator-sticky-panel {
      position: fixed;
      top: 4rem;
      right: max(2rem, calc((100vw - 1200px) / 2));
      box-sizing: border-box;
      width: clamp(260px, 22vw, 320px);
      max-height: calc(100vh - 5rem);
      padding: 0.25rem;
      border: 1px solid rgba(128, 128, 128, 0.25);
      border-radius: 0.75rem;
      background: var(--secondary-background-color);
      z-index: 5;
    }
    .st-key-calculator-scroll-content {
      max-height: calc(100vh - 5.5rem);
      overflow-y: auto;
      overscroll-behavior-y: contain;
      scrollbar-gutter: stable;
      padding: 0.5rem;
    }
    @media (max-width: 1100px) {
      .st-key-mission-calculator-layout
      > [data-testid="stLayoutWrapper"]
      > [data-testid="stHorizontalBlock"] {
        flex-direction: column;
        align-items: stretch;
      }
      .st-key-mission-calculator-layout
      > [data-testid="stLayoutWrapper"]
      > [data-testid="stHorizontalBlock"]
      > [data-testid="stColumn"] {
        width: 100% !important;
        flex: 1 1 100% !important;
      }
      .st-key-calculator-sticky-panel {
        position: static;
        top: auto;
        right: auto;
        width: auto;
        max-height: none;
      }
      .st-key-mission-calculator-layout
      .st-key-calculator-scroll-content {
        max-height: none;
        overflow: visible;
        overscroll-behavior-y: auto;
        scrollbar-gutter: auto;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pages = ("도입부", "MISSION1", "MISSION2", "MISSION3")
page = st.sidebar.radio("게임 진행", pages, key="current_page")

if page == "도입부":
    render_intro()
else:
    with st.container(key="mission-calculator-layout"):
        mission_column, calculator_column = st.columns(
            [3, 1.15],
            gap="large",
        )
        with mission_column:
            if page == "MISSION1":
                render_mission1()
            elif page == "MISSION2":
                if st.session_state.get("mission1_completed", False):
                    render_mission2()
                else:
                    st.header("MISSION 2")
                    st.info("MISSION1 교육을 마치면 다음 단계가 열립니다.")
                    st.button(
                        "MISSION1으로 이동",
                        key="mission2_locked_back",
                        on_click=_return_to_mission1,
                    )
            else:
                render_mission3()
        with calculator_column:
            render_calculator()
