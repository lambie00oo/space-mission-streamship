import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


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

        mission4 = AppTest.from_file(str(app_path), default_timeout=30)
        mission4.session_state["current_page"] = "MISSION4"
        mission4.session_state["selected_planet"] = "mars"
        mission4.session_state["m2_complete"] = True
        mission4.session_state["m2_result"] = mission3.session_state["m2_result"]
        mission4.session_state["m4_arrival_speed_formula_input"] = {
            "values": {
                "mu": "1.32712440018e11",
                "radius": "227939200",
                "axis": "188800000",
            }
        }
        mission4.run()

        self.assertFalse(mission4.exception)
        self.assertTrue(any(metric.value.endswith("km/s") for metric in mission4.metric))


if __name__ == "__main__":
    unittest.main()
