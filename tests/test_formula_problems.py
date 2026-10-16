import math
import unittest
from pathlib import Path

from data.planets import PLANETS
from logic.final_approach import (
    FINAL_APPROACH_PLANET_DATA,
    GRAVITATIONAL_CONSTANT_KM3_PER_KG_S2,
    SUN_MASS_KG,
    find_sphere_of_influence_entry,
    sphere_of_influence_radius_km,
)
from logic.orbit_calculations import semi_minor_axis
from streamlit.testing.v1 import AppTest
from ui.mission3_rendezvous import _extract_simulation_data


class FormulaProblemTests(unittest.TestCase):
    def _mission2_app(self, values: dict[str, str]) -> AppTest:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path), default_timeout=30)
        app.session_state["current_page"] = "MISSION2"
        app.session_state["mission1_completed"] = True
        app.session_state["selected_planet"] = "mars"
        app.session_state["planet_select"] = "mars"
        app.session_state["m2_a_formula_input"] = {"values": values}
        app.run()
        return app

    def _mission4_app(self, angle_degrees: float) -> tuple[AppTest, tuple]:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path), default_timeout=30)
        app.session_state["current_page"] = "MISSION4"
        app.session_state["selected_planet"] = "mars"
        app.session_state["m2_complete"] = True
        app.session_state["m2_result"] = {
            "planet_key": "mars",
            "planet_name": "화성",
            "semi_major_axis_au": 1.262,
            "eccentricity": 0.20761,
            "focus_distance_au": 0.262,
        }
        app.session_state["m3_complete"] = True
        app.session_state["m3_time_days"] = 258.0
        app.session_state["m3_final_approach_snapshot"] = {
            "angle_degrees": angle_degrees,
            "progress": 0.5,
            "status": "paused",
        }
        context = ("mars", 1.262, 0.20761, 0.262, 258.0, angle_degrees)
        return app, context

    def _mars_entry(self):
        planet = PLANETS["mars"]
        semi_major_axis_au = 1.262
        eccentricity = 0.20761
        focus_distance_au = 0.262
        transfer_days = 258.0
        angle_degrees = (
            180 - 360 * transfer_days / planet.orbital_period_days
        ) % 360
        _, spacecraft_path = _extract_simulation_data(
            planet,
            semi_major_axis_au,
            eccentricity,
            focus_distance_au,
            semi_minor_axis(semi_major_axis_au, eccentricity),
        )
        orbit_radius_km, planet_mass_kg, _ = FINAL_APPROACH_PLANET_DATA["mars"]
        influence_radius_km = sphere_of_influence_radius_km(
            orbit_radius_km,
            planet_mass_kg,
        )
        entry = find_sphere_of_influence_entry(
            spacecraft_path,
            planet,
            angle_degrees,
            transfer_days,
            influence_radius_km,
        )
        self.assertIsNotNone(entry)
        assert entry is not None
        return planet_mass_kg, influence_radius_km, entry, angle_degrees

    def test_formula_calculates_automatically_and_checks_answer(self) -> None:
        app = self._mission2_app({"r_e": "1", "r_p": "1.5"})

        self.assertFalse(app.exception)
        self.assertIn("1.25 AU", [metric.value for metric in app.metric])

        app.session_state["m2_a_formula_input"] = {
            "values": {"r_e": "1", "r_p": "1.524"}
        }
        app.run()
        self.assertIn("1.262 AU", [metric.value for metric in app.metric])

        app.button(key="m2_a_check").click().run()
        self.assertAlmostEqual(app.session_state["m2_a"], 1.262)
        self.assertFalse(app.exception)

    def test_repeated_wrong_answers_remain_submitable_without_revealing_answer(self) -> None:
        app = self._mission2_app({"r_e": "1", "r_p": "1.5"})
        for _ in range(5):
            app.button(key="m2_a_check").click().run()
            self.assertFalse(app.button(key="m2_a_check").disabled)
            self.assertTrue(
                any("다시 시도해 주세요" in item.value for item in app.error)
            )
            self.assertFalse(
                any("시도 횟수" in item.value for item in app.caption)
            )
        self.assertFalse(app.exception)

    def test_correct_answer_after_repeated_wrong_answers_completes_problem(self) -> None:
        app = self._mission2_app({"r_e": "1", "r_p": "1.5"})
        for _ in range(5):
            app.button(key="m2_a_check").click().run()

        app.session_state["m2_a_formula_input"] = {
            "values": {"r_e": "1", "r_p": "1.524"}
        }
        app.run()
        app.button(key="m2_a_check").click().run()

        self.assertTrue(
            any("정답입니다" in message.value for message in app.success)
        )
        self.assertFalse(app.exception)

    def test_empty_formula_blanks_do_not_calculate_or_submit(self) -> None:
        app = self._mission2_app({})

        self.assertFalse(app.exception)
        self.assertFalse(
            any(metric.label == "계산 결과 a" for metric in app.metric)
        )
        self.assertTrue(
            any("필수 입력값을 모두 채워 주세요" in message.value for message in app.info)
        )
        self.assertTrue(app.button(key="m2_a_check").disabled)

    def test_mission3_and_mission4_formula_panels_render(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        mission3 = AppTest.from_file(str(app_path), default_timeout=30)
        mission3.session_state["current_page"] = "MISSION3"
        mission3.session_state["selected_planet"] = "mars"
        mission3.session_state["m2_complete"] = True
        mission3.session_state["m2_result"] = {
            "planet_key": "mars",
            "planet_name": "화성",
            "semi_major_axis_au": 1.262,
            "eccentricity": 0.20761,
            "focus_distance_au": 0.262,
        }
        mission3.session_state["m3_time_years_formula_input"] = {
            "values": {"a": "1.262"}
        }
        mission3.run()

        self.assertFalse(mission3.exception)
        self.assertTrue(
            any(
                metric.label == "계산 결과 t_year"
                for metric in mission3.metric
            )
        )
        self.assertIn("0.708", [metric.value[:5] for metric in mission3.metric])

        _, _, _, arrival_angle = self._mars_entry()
        mission4, input_context = self._mission4_app(arrival_angle)
        mission4.session_state["m4_final_approach_input_context"] = input_context
        mission4.session_state["m4_final_approach_soi"] = True
        mission4.session_state["m4_final_approach_angular_momentum"] = True
        mission4.session_state["m4_final_approach_energy"] = True
        mission4.session_state["m4_final_approach_eccentricity"] = True
        mission4.run()

        self.assertFalse(mission4.exception)
        self.assertEqual(
            mission4.session_state["m4_final_approach_input_context"],
            input_context,
        )
        self.assertTrue(
            any(
                metric.label == "계산된 영향권 반지름"
                for metric in mission4.metric
            )
        )
        self.assertEqual(len(mission4.get("plotly_chart")), 2)
        self.assertTrue(
            any(
                "MISSION 4. 새로운 세계의 경계를 넘어라!" in header.value
                for header in mission4.header
            )
        )
        self.assertFalse(
            any(
                "FINAL APPROACH COMPLETE" in message.value
                for message in mission4.success
            )
        )
        self.assertTrue(mission4.session_state["m4_final_approach_entered"])
        self.assertTrue(mission4.session_state["m4_final_approach_hyperbolic"])

    def test_mission4_step1_formula_recalculates_from_formula_slots(self) -> None:
        app, _ = self._mission4_app(45.0)
        app.run()
        app.session_state["m4_final_approach_soi_formula_input"] = {
            "values": {
                "planet_axis": str(FINAL_APPROACH_PLANET_DATA["mars"][0]),
                "planet_mass": "6.417e23",
                "sun_mass": f"{SUN_MASS_KG:.4e}",
            }
        }
        app.run()

        self.assertFalse(app.exception)
        self.assertTrue(
            any(metric.label == "계산 결과 r_SOI" for metric in app.metric)
        )
        self.assertFalse(
            any(metric.label == "계산된 영향권 반지름" for metric in app.metric)
        )
        app.button(key="m4_final_approach_soi_check").click().run()
        self.assertTrue(app.session_state["m4_final_approach_soi"])

    def test_mission4_reports_miss_distance_without_fabricating_entry(self) -> None:
        app, input_context = self._mission4_app(180.0)
        app.session_state["m4_final_approach_input_context"] = input_context
        app.session_state["m4_final_approach_soi"] = True
        app.run()

        self.assertFalse(app.exception)
        self.assertFalse(app.session_state["m4_final_approach_entered"])
        self.assertTrue(
            any(
                "최소 거리:" in message.value
                and "영향권 경계와의 차이:" in message.value
                for message in app.warning
            )
        )

    def test_mission4_step4_formula_slots_recalculate_energy_and_eccentricity(self) -> None:
        planet_mass_kg, _, entry, angle = self._mars_entry()
        app, context = self._mission4_app(angle)
        mu = GRAVITATIONAL_CONSTANT_KM3_PER_KG_S2 * planet_mass_kg
        rx, ry = entry.relative_position_km
        vx, vy = entry.relative_velocity_km_s
        angular_momentum = rx * vy - ry * vx
        radius = math.hypot(rx, ry)
        energy = (vx**2 + vy**2) / 2 - mu / radius
        eccentricity = math.sqrt(
            1 + 2 * energy * angular_momentum**2 / mu**2
        )

        app.session_state["m4_final_approach_input_context"] = context
        app.session_state["m4_final_approach_soi"] = True
        app.session_state["m4_final_approach_angular_momentum"] = True
        app.session_state["m4_final_approach_energy_formula_input"] = {
            "values": {
                "vx": f"{vx:.10f}",
                "vy": f"{vy:.10f}",
                "mu": f"{mu:.10g}",
                "radius": f"{radius:.3f}",
            }
        }
        app.run()

        self.assertFalse(app.exception)
        self.assertTrue(
            any(metric.label == "계산 결과 ε" for metric in app.metric)
        )
        self.assertFalse(app.session_state.get("m4_final_approach_energy", False))

        app.session_state["m4_final_approach_energy"] = True
        app.session_state["m4_final_approach_eccentricity_formula_input"] = {
            "values": {
                "energy": f"{energy:.10g}",
                "angular_momentum": f"{angular_momentum:.10g}",
                "mu": f"{mu:.10g}",
            }
        }
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(
            any(metric.label == "계산 결과 e" for metric in app.metric)
        )
        self.assertGreater(eccentricity, 1)


if __name__ == "__main__":
    unittest.main()
