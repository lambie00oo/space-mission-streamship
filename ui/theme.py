from pathlib import Path

import streamlit as st


NASA_LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "nasa-logo.svg"


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .st-key-app-header {
            align-items: center;
            background: #0b1b33;
            border: 1px solid #24415f;
            border-radius: 1rem;
            margin-bottom: 1.5rem;
            padding: 0.6rem 1.25rem;
        }
        .st-key-app-header [data-testid="stImage"] img {
            object-fit: contain;
        }
        .st-key-mission-card {
            background: #0b1b33;
            border: 1px solid #2b4d70;
            border-radius: 1rem;
            padding: 1rem 1.25rem;
        }
        .st-key-mission-card [data-testid="stHeading"] h3 {
            background: #102742;
            border-left: 3px solid #50c8ff;
            border-radius: 0.25rem;
            color: #b9efff;
            margin-top: 1.1rem;
            padding: 0.45rem 0.75rem;
        }
        .st-key-mission-card [data-testid="stVerticalBlockBorderWrapper"] {
            background: #0d2038;
            border-color: #315575;
            border-radius: 0.75rem;
        }
        .st-key-planet-selection-mars [data-testid="stImage"] img,
        .st-key-planet-selection-jupiter [data-testid="stImage"] img,
        .st-key-planet-selection-saturn [data-testid="stImage"] img {
            box-sizing: border-box;
            height: 200px;
            object-fit: contain;
            width: 100%;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid #203c58;
        }
        [data-testid="stSidebar"] [aria-checked="true"] {
            color: #50c8ff;
        }
        [data-testid="stButton"] button,
        [data-testid="stFormSubmitButton"] button {
            border: 1px solid #50c8ff;
            border-radius: 0.5rem;
            font-weight: 650;
            min-height: 2.6rem;
            transition: background-color 120ms ease, border-color 120ms ease;
        }
        [data-testid="stButton"] button[kind="primary"],
        [data-testid="stFormSubmitButton"] button[kind="primary"] {
            background: #0877b9;
            color: #ffffff;
        }
        [data-testid="stButton"] button:hover,
        [data-testid="stFormSubmitButton"] button:hover {
            border-color: #8be4ff;
            color: #ffffff;
        }
        [data-testid="stAlert"] {
            border-radius: 0.65rem;
        }
        @media (max-width: 700px) {
            .st-key-mission-card {
                padding: 0.75rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_app_header() -> None:
    with st.container(key="app-header"):
        logo_column, title_column = st.columns(
            [1, 7],
            vertical_alignment="center",
        )
        with logo_column:
            st.image(str(NASA_LOGO_PATH), width=76, alt="NASA insignia")
        with title_column:
            st.title("SPACE ODYSSEY")
            st.caption("MISSION CONTROL · 우주 궤도 설계 교육 게임")
