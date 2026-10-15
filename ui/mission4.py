from collections.abc import Callable

import streamlit as st

from data.constants import AU_TO_KM, SUN_GRAVITATIONAL_PARAMETER_KM3_S2
from data.planets import PLANETS, Planet
from logic.mission4_calculations import (
    FlybyResult,
    closest_distance_km,
    compare_flyby_altitudes,
    deflection_angle_degrees,
    educational_excess_speed_km_s,
    hyperbolic_eccentricity,
    mission4_solar_parameters,
    planet_orbital_speed_km_s,
    spacecraft_arrival_speed_km_s,
)
from ui.formula_problems import (
    FormulaInput,
    render_formula_problem,
)
from ui.orbit_plot import mission4_flyby_plot


HINTS = {
    "m4_arrival_speed": (
        "행성의 공전 궤도 반지름과 전이 장반경을 km로 바꿔 식에 대입합니다.",
        "비스비바 식의 괄호 안은 2/r_T - 1/a 입니다.",
        "v_sc = √[μ_S(2/r_T - 1/a)] 를 km/s로 계산합니다.",
    ),
    "m4_planet_speed": (
        "원형 궤도의 공전 속력은 태양 중력계수와 궤도 반지름으로 구합니다.",
        "먼저 μ_S를 r_T로 나눈 뒤 제곱근을 구합니다.",
        "v_T = √(μ_S/r_T) 입니다.",
    ),
    "m4_excess_speed": (
        "교육용 모델에서는 두 속도가 같은 접선 방향입니다.",
        "우주선 도착 속력과 행성 공전 속력의 차이를 구합니다.",
        "v_∞ = |v_sc - v_T| 입니다.",
    ),
    "m4_eccentricity": (
        "최근접 거리와 초과속도, 선택한 행성의 중력계수를 사용합니다.",
        "먼저 r_closest × v_∞² 를 계산한 뒤 행성 중력계수로 나눕니다.",
        "e = 1 + r_closest v_∞² / μ_T 이며 쌍곡선이면 e > 1 입니다.",
    ),
    "m4_deflection_angle": (
        "방향 전환각은 쌍곡선 이심률을 역삼각함수에 대입해 구합니다.",
        "1/e의 arcsin을 구한 후 2를 곱합니다.",
        "δ = 2 asin(1/e) 입니다. 라디안 결과를 도로 변환하세요.",
    ),
}


def _render_numeric_step(
    *,
    key: str,
    label: str,
    formula: str,
    formula_layout: str,
    inputs: tuple[FormulaInput, ...],
    calculate: Callable[[dict[str, float]], float],
    expected: float,
    tolerance: float,
    success_message: str,
    hints: tuple[str, ...],
    result_unit: str,
) -> bool:
    return render_formula_problem(
        key=key,
        title=label,
        formula=formula,
        formula_layout=formula_layout,
        inputs=inputs,
        calculate=calculate,
        expected=expected,
        tolerance=tolerance,
        result_label=f"계산 결과 {label.split(' (', maxsplit=1)[0]}",
        result_unit=result_unit,
        success_message=success_message,
        hints=hints,
    )


def _render_step1(planet: Planet, semi_major_axis_au: float) -> float | None:
    target_orbit_radius_km = planet.orbit_radius_au * AU_TO_KM
    semi_major_axis_km = semi_major_axis_au * AU_TO_KM
    try:
        arrival_speed, planet_speed, excess_speed = mission4_solar_parameters(
            planet,
            semi_major_axis_au,
        )
    except ValueError as error:
        st.error(f"MISSION 4 계산에 필요한 궤도 값이 올바르지 않습니다: {error}")
        return None

    st.subheader("STEP 1 · 행성 도착 속력 및 초과속도")
    st.markdown(
        f"""
        - 목적 행성: **{planet.name}**
        - 태양 중력계수 μ_S: **{SUN_GRAVITATIONAL_PARAMETER_KM3_S2:g} km³/s²**
        - 행성 공전 궤도 반지름 r_T: **{planet.orbit_radius_au:g} AU**
          (**{target_orbit_radius_km:,.10g} km**)
        - MISSION 2 전이 타원 장반경 a: **{semi_major_axis_au:g} AU**
          (**{semi_major_axis_km:,.10g} km**)
        """
    )
    st.caption("우주선 도착 속력 v_sc 단위: km/s")
    if not _render_numeric_step(
        key="m4_arrival_speed",
        label="우주선 도착 속력 v_sc (km/s)",
        formula=r"v_{sc}=\sqrt{\mu_S\left(\frac{2}{r_T}-\frac{1}{a}\right)}",
        formula_layout="""
            <span>v<sub>sc</sub> = </span>
            <span class="formula-radical">
                <span>√</span>
                <span class="formula-radicand">
                    <span data-formula-slot="mu"></span>
                    <span>× (</span>
                    <span class="formula-fraction">
                        <span class="formula-numerator">2</span>
                        <span class="formula-denominator">
                            <span data-formula-slot="radius"></span>
                        </span>
                    </span>
                    <span>−</span>
                    <span class="formula-fraction">
                        <span class="formula-numerator">1</span>
                        <span class="formula-denominator">
                            <span data-formula-slot="axis"></span>
                        </span>
                    </span>
                    <span>)</span>
                </span>
            </span>
        """,
        inputs=(
            FormulaInput("mu", "태양 중력계수 μ_S", SUN_GRAVITATIONAL_PARAMETER_KM3_S2, "km³/s²", "%.8g", strictly_positive=True),
            FormulaInput("radius", "행성 궤도 반지름 r_T", target_orbit_radius_km, "km", "%.8g", strictly_positive=True),
            FormulaInput("axis", "전이 장반경 a", semi_major_axis_km, "km", "%.8g", strictly_positive=True),
        ),
        calculate=lambda values: spacecraft_arrival_speed_km_s(
            values["mu"],
            values["radius"],
            values["axis"],
        ),
        expected=arrival_speed,
        tolerance=0.005,
        success_message="정답입니다. 행성 공전 속력을 계산합니다.",
        hints=HINTS["m4_arrival_speed"],
        result_unit="km/s",
    ):
        return None
    st.success(f"우주선 도착 속력: {st.session_state.m4_arrival_speed:.8f} km/s")

    st.caption("원형 궤도로 가정한 행성 공전 속력 v_T 단위: km/s")
    if not _render_numeric_step(
        key="m4_planet_speed",
        label="행성 공전 속력 v_T (km/s)",
        formula=r"v_T=\sqrt{\frac{\mu_S}{r_T}}",
        formula_layout="""
            <span>v<sub>T</sub> = </span>
            <span class="formula-radical">
                <span>√</span>
                <span class="formula-radicand">
                    <span class="formula-fraction">
                        <span class="formula-numerator">
                            <span data-formula-slot="mu"></span>
                        </span>
                        <span class="formula-denominator">
                            <span data-formula-slot="radius"></span>
                        </span>
                    </span>
                </span>
            </span>
        """,
        inputs=(
            FormulaInput("mu", "태양 중력계수 μ_S", SUN_GRAVITATIONAL_PARAMETER_KM3_S2, "km³/s²", "%.8g", strictly_positive=True),
            FormulaInput("radius", "행성 궤도 반지름 r_T", target_orbit_radius_km, "km", "%.8g", strictly_positive=True),
        ),
        calculate=lambda values: planet_orbital_speed_km_s(
            values["mu"],
            values["radius"],
        ),
        expected=planet_speed,
        tolerance=0.005,
        success_message="정답입니다. 행성 기준 초과속도를 계산합니다.",
        hints=HINTS["m4_planet_speed"],
        result_unit="km/s",
    ):
        return None
    st.success(f"행성 공전 속력: {st.session_state.m4_planet_speed:.8f} km/s")

    st.caption("같은 접선 방향으로 이동한다고 가정한 교육용 초과속도 v_∞ 단위: km/s")
    if not _render_numeric_step(
        key="m4_excess_speed",
        label="행성 기준 초과속도 v_∞ (km/s)",
        formula=r"v_\infty=|v_{sc}-v_T|",
        formula_layout="""
            <span>v<sub>∞</sub> = |</span>
            <span data-formula-slot="spacecraft"></span>
            <span>−</span>
            <span data-formula-slot="planet"></span>
            <span>|</span>
        """,
        inputs=(
            FormulaInput("spacecraft", "우주선 도착 속력 v_sc", arrival_speed, "km/s", "%.8f", strictly_positive=True),
            FormulaInput("planet", "행성 공전 속력 v_T", planet_speed, "km/s", "%.8f", strictly_positive=True),
        ),
        calculate=lambda values: educational_excess_speed_km_s(
            values["spacecraft"],
            values["planet"],
        ),
        expected=excess_speed,
        tolerance=0.005,
        success_message="정답입니다. 최근접 고도를 선택합니다.",
        hints=HINTS["m4_excess_speed"],
        result_unit="km/s",
    ):
        return None
    st.success(f"행성 기준 초과속도: {st.session_state.m4_excess_speed:.8f} km/s")
    st.warning(
        "이 값은 이상적인 호만 전이와 원형 행성 궤도, 같은 접선 방향을 가정한 교육용 근삿값입니다. "
        "실제 초과속도는 우주선과 행성 속도 벡터의 차이로 계산합니다."
    )
    return st.session_state.m4_excess_speed


def _render_step2(planet: Planet) -> None:
    st.subheader("STEP 2 · 최근접 고도 선택")
    if planet.reference_surface is None or planet.reference_radius_km is None:
        st.error(f"{planet.name}의 근접 통과 기준면 데이터가 없습니다.")
        return
    if planet.flyby_altitudes_km is None:
        st.error(f"{planet.name}의 근접 통과 고도 선택 데이터가 없습니다.")
        return
    st.markdown(
        f"기준면: **{planet.reference_surface}** · 기준 반지름: "
        f"**{planet.reference_radius_km:,.10g} km**"
    )
    altitudes = planet.flyby_altitudes_km
    selection = st.radio(
        "최근접 고도 선택",
        options=(0, 1),
        index=None,
        format_func=lambda index: (
            f"선택 {'A' if index == 0 else 'B'} · {planet.reference_surface} 위 "
            f"{altitudes[index]:,.10g} km"
        ),
        key="m4_altitude_selection",
    )
    if selection is not None:
        altitude = altitudes[selection]
        distance = closest_distance_km(planet.reference_radius_km, altitude)
        st.write(f"최근접 거리 r_closest = R_ref + h = **{distance:,.10g} km**")
        if st.button(
            "최근접 거리 확정 · 다음 단계",
            key="m4_confirm_altitude",
        ):
            st.session_state.m4_selected_altitude_km = altitude
            st.session_state.m4_closest_distance_km = distance
            st.session_state.m4_step2_complete = True
            st.rerun()
    else:
        st.button(
            "최근접 거리 확정 · 다음 단계",
            key="m4_confirm_altitude_disabled",
            disabled=True,
        )


def _render_step3(planet: Planet) -> bool:
    st.subheader("STEP 3 · 쌍곡선 이심률과 방향 전환각")
    if planet.gravitational_parameter_km3_s2 is None:
        st.error(f"{planet.name}의 중력계수 데이터가 없습니다.")
        return False
    try:
        eccentricity = hyperbolic_eccentricity(
            st.session_state.m4_closest_distance_km,
            st.session_state.m4_excess_speed,
            planet.gravitational_parameter_km3_s2,
        )
        angle = deflection_angle_degrees(eccentricity)
    except ValueError as error:
        st.error(f"쌍곡선 궤도를 계산할 수 없습니다: {error}")
        return False

    st.markdown(
        f"행성 중력계수 μ_T = **{planet.gravitational_parameter_km3_s2:g} km³/s²** · "
        f"최근접 거리 = **{st.session_state.m4_closest_distance_km:,.10g} km** · "
        f"초과속도 = **{st.session_state.m4_excess_speed:.10g} km/s**"
    )
    st.caption("쌍곡선 궤도는 e > 1 입니다.")
    if not _render_numeric_step(
        key="m4_eccentricity",
        label="쌍곡선 이심률 e",
        formula=r"e=1+\frac{r_{\mathrm{closest}}v_\infty^2}{\mu_T}",
        formula_layout="""
            <span>e = 1 + </span>
            <span class="formula-fraction">
                <span class="formula-numerator">
                    <span data-formula-slot="distance"></span>
                    <span>×</span>
                    <span data-formula-slot="speed"></span><sup>2</sup>
                </span>
                <span class="formula-denominator">
                    <span data-formula-slot="mu"></span>
                </span>
            </span>
        """,
        inputs=(
            FormulaInput("distance", "최근접 거리 r_closest", st.session_state.m4_closest_distance_km, "km", "%.8g", strictly_positive=True),
            FormulaInput("speed", "초과속도 v_∞", st.session_state.m4_excess_speed, "km/s", "%.8g", strictly_positive=True),
            FormulaInput("mu", "행성 중력계수 μ_T", planet.gravitational_parameter_km3_s2, "km³/s²", "%.8g", strictly_positive=True),
        ),
        calculate=lambda values: hyperbolic_eccentricity(
            values["distance"],
            values["speed"],
            values["mu"],
        ),
        expected=eccentricity,
        tolerance=0.005,
        success_message="정답입니다. 방향 전환각을 계산합니다.",
        hints=HINTS["m4_eccentricity"],
        result_unit="",
    ):
        return False
    st.success(f"쌍곡선 이심률: {st.session_state.m4_eccentricity:.8f}")

    st.caption("내부 계산은 라디안, 사용자 입력과 화면 표시는 도(degree) 단위입니다.")
    if not _render_numeric_step(
        key="m4_deflection_angle",
        label="방향 전환각 δ (도)",
        formula=r"\delta_{\mathrm{degree}}=2\sin^{-1}\left(\frac{1}{e}\right)\frac{180}{\pi}",
        formula_layout="""
            <span>δ = 2 sin⁻¹(</span>
            <span class="formula-fraction">
                <span class="formula-numerator">1</span>
                <span class="formula-denominator">
                    <span data-formula-slot="eccentricity"></span>
                </span>
            </span>
            <span>) × 180 / π</span>
        """,
        inputs=(
            FormulaInput("eccentricity", "쌍곡선 이심률 e", st.session_state.m4_eccentricity, "", "%.8f", strictly_positive=True),
        ),
        calculate=lambda values: deflection_angle_degrees(values["eccentricity"]),
        expected=angle,
        tolerance=0.005,
        success_message="정답입니다. 근접 통과 궤도 비교를 확인하세요.",
        hints=HINTS["m4_deflection_angle"],
        result_unit="°",
    ):
        return False
    st.session_state.m4_complete = True
    st.success(f"방향 전환각: {st.session_state.m4_deflection_angle:.8f}°")
    return True


def _render_step4(planet: Planet) -> None:
    st.subheader("STEP 4 · 두 고도의 근접 통과 결과 비교")
    try:
        result_a, result_b = compare_flyby_altitudes(
            planet,
            st.session_state.m4_excess_speed,
        )
    except ValueError as error:
        st.error(f"비교 결과를 계산할 수 없습니다: {error}")
        return

    results: tuple[FlybyResult, FlybyResult] = (result_a, result_b)
    rows = [
        {
            "비교 항목": "최근접 고도 (km)",
            "선택 A": f"{result_a.altitude_km:,.10g}",
            "선택 B": f"{result_b.altitude_km:,.10g}",
        },
        {
            "비교 항목": "최근접 거리 (km)",
            "선택 A": f"{result_a.closest_distance_km:,.10g}",
            "선택 B": f"{result_b.closest_distance_km:,.10g}",
        },
        {
            "비교 항목": "초과속도 (km/s)",
            "선택 A": f"{result_a.excess_speed_km_s:.10g}",
            "선택 B": f"{result_b.excess_speed_km_s:.10g}",
        },
        {
            "비교 항목": "쌍곡선 이심률",
            "선택 A": f"{result_a.eccentricity:.10g}",
            "선택 B": f"{result_b.eccentricity:.10g}",
        },
        {
            "비교 항목": "방향 전환각 (°)",
            "선택 A": f"{result_a.deflection_angle_degrees:.10g}",
            "선택 B": f"{result_b.deflection_angle_degrees:.10g}",
        },
    ]
    st.table(rows)
    st.pyplot(mission4_flyby_plot(planet, results))
    st.caption(
        "고도 선택지는 게임용 예시값이며 실제 임무의 안전 기준이 아닙니다. "
        "대기 저항, 비구형 중력장, 복사 환경은 계산에 포함하지 않았습니다."
    )
    if planet.name == "토성":
        st.info(
            "토성의 고리는 이 기본 2체 근사에 포함하지 않습니다. "
            "그림은 고리 충돌 가능성을 검증한 실제 비행 경로가 아닙니다."
        )
    elif planet.name == "목성":
        st.info(
            "목성은 고체 표면이 없으며, 그림의 기준 반지름은 "
            "1 bar 대기압 기준 적도 반지름입니다."
        )


def render_mission4() -> None:
    st.header("MISSION 4: 행성 근접 통과 궤도 설계")
    st.write(
        "행성에 도착한 우주선의 속도와 행성 중력에 의한 방향 전환을 계산합니다. "
        "착륙이나 궤도 포획이 아닌 중력 근접 통과(flyby)를 다룹니다."
    )

    result = st.session_state.get("m2_result")
    if (
        not st.session_state.get("m2_complete", False)
        or not isinstance(result, dict)
        or result.get("planet_key") not in PLANETS
    ):
        st.info("MISSION 2의 궤도 설계를 완료하면 MISSION 4를 진행할 수 있습니다.")
        st.button(
            "MISSION2로 이동",
            key="mission4_locked_back",
            on_click=lambda: st.session_state.update(current_page="MISSION2"),
        )
        return

    planet_key = result["planet_key"]
    if planet_key != st.session_state.selected_planet:
        st.warning("현재 행성 선택과 MISSION 2 결과가 다릅니다. MISSION 2를 다시 진행해 주세요.")
        return

    planet = PLANETS[planet_key]
    if (
        planet.gravitational_parameter_km3_s2 is None
        or planet.reference_radius_km is None
        or planet.reference_surface is None
        or planet.flyby_altitudes_km is None
    ):
        st.error(f"{planet.name}의 MISSION 4 행성 데이터가 완전하지 않습니다.")
        return
    semi_major_axis_au = float(result["semi_major_axis_au"])
    st.caption(
        f"목적 행성: {planet.name} · MISSION 2 장반경: {semi_major_axis_au:g} AU"
    )
    with st.container(border=True):
        excess_speed = _render_step1(planet, semi_major_axis_au)
    if excess_speed is None:
        return

    if not st.session_state.get("m4_step2_complete", False):
        with st.container(border=True):
            _render_step2(planet)
        return

    with st.container(border=True):
        step3_complete = _render_step3(planet)
    if not step3_complete:
        return

    with st.container(border=True):
        _render_step4(planet)
