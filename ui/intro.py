from pathlib import Path

import streamlit as st

from data.planets import PLANETS


ASSET_DIR = Path(__file__).resolve().parent.parent / "images"
PLANET_IMAGE_DIR = ASSET_DIR
PLANET_IMAGE_FILES = {
    "mars": "j.webp",
    "jupiter": "m.jpeg",
    "saturn": "S.jpg",
}


def _planet_image_path(planet_key: str) -> Path | None:
    image_name = PLANET_IMAGE_FILES.get(planet_key)
    if image_name is None:
        return None

    image_path = PLANET_IMAGE_DIR / image_name
    return image_path if image_path.is_file() else None


def _select_planet(planet_key: str) -> None:
    st.session_state.selected_planet = planet_key
    st.session_state.planet_select = planet_key


def _start_mission1() -> None:
    st.session_state.current_page = "MISSION1"


def render_intro() -> None:
    st.image(str(ASSET_DIR / "hero.jpg"), width="stretch")
    st.header("인류의 새로운 우주 탐사를 시작할 시간이다! 🚀")
    st.write(
        "여러분은 우주 탐사선의 궤도를 설계하는 임무를 맡았다.  \n"
        "목표는 지구를 출발해 행성에 안전하게 도착하는 것!  \n"
        "이번 미션에서는 원과 타원의 기하학적 특징을 알아보고, 지구와 화성을 연결하는 "
        "호만 전이 궤도와 적절한 발사 시기를 설계하는 방법을 배운다. 더 나아가 행성 주변의 "
        "쌍곡선 궤도를 살펴보며 실제 우주 비행을 근사하는 패치드 코닉 모델도 만나게 된다.  \n"
        "이제 우주를 향한 여정을 시작하라. 여러분의 설계가 화성 탐사의 운명을 결정한다!"
    )
    st.subheader("목적 행성 선택")
    st.caption("임무에서 탐사할 행성을 선택하세요.")
    columns = st.columns(len(PLANETS))
    for (planet_key, planet), column in zip(PLANETS.items(), columns):
        with column:
            with st.container(border=True, key=f"planet-selection-{planet_key}"):
                image_path = _planet_image_path(planet_key)
                if image_path is not None:
                    st.image(
                        str(image_path),
                        width="stretch",
                        alt=planet.name,
                    )
                else:
                    st.markdown("### 🪐")
                    st.caption("행성 이미지가 준비되지 않았습니다.")
                st.markdown(f"**{planet.name}**")
                is_selected = (
                    st.session_state.get("selected_planet", "mars") == planet_key
                )
                if is_selected:
                    st.caption("현재 선택")
                st.button(
                    "선택됨" if is_selected else "이 행성 선택",
                    key=f"select_planet_{planet_key}",
                    type="primary" if is_selected else "secondary",
                    on_click=_select_planet,
                    args=(planet_key,),
                )
    st.divider()
    st.button(
        "교육 시작 · MISSION1",
        key="start_mission1",
        on_click=_start_mission1,
    )
