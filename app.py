import streamlit as st

from ui.intro import render_intro
from ui.mission1 import render_mission1
from ui.mission2 import render_mission2
from ui.mission3 import render_mission3
from ui.mission4 import render_mission4
from ui.theme import apply_theme, render_app_header


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

apply_theme()
render_app_header()

pages = ("도입부", "MISSION1", "MISSION2", "MISSION3", "MISSION4")
page = st.sidebar.radio("게임 진행", pages, key="current_page")

if page == "도입부":
    render_intro()
else:
    with st.container(key="mission-card"):
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
        elif page == "MISSION3":
            render_mission3()
        else:
            render_mission4()
