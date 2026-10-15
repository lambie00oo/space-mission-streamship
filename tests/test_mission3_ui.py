import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class Mission3UiTests(unittest.TestCase):
    def test_mission3_completion_renders_and_navigates_with_values_retained(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path), default_timeout=30)
        values = {
            "m3_time_years": 0.7,
            "m3_time_days": 255.7,
            "m3_omega": 0.5,
            "m3_travel_angle": 127.8,
            "m3_phase_angle": 52.2,
        }
        app.session_state["current_page"] = "MISSION3"
        app.session_state["selected_planet"] = "mars"
        app.session_state["m2_complete"] = True
        app.session_state["m2_result"] = {
            "planet_key": "mars",
            "planet_name": "화성",
            "semi_major_axis_au": 1.26,
            "eccentricity": 0.2,
            "focus_distance_au": 0.25,
        }
        for key, value in values.items():
            app.session_state[key] = value

        app.run()

        self.assertFalse(
            any("MISSION2 계산 결과" in element.value for element in app.markdown)
        )
        self.assertTrue(any(button.label == "학습 완료" for button in app.button))
        self.assertTrue(
            any(
                "STEP 3 · 궤도에서 각도 확인" in element.value
                for element in app.subheader
            )
        )
        self.assertIn("m3_rendezvous_component", app.session_state)
        self.assertEqual(
            app.session_state["m3_rendezvous_component"]["snapshot"]["angle"],
            values["m3_phase_angle"],
        )
        self.assertEqual(
            app.session_state["m3_rendezvous_component"]["snapshot"]["status"],
            "ready",
        )

        app.button(key="mission3_complete_button").click().run()

        self.assertEqual(app.session_state["current_page"], "MISSION4")
        self.assertTrue(app.session_state["m3_complete"])
        self.assertEqual(
            app.session_state["m3_final_approach_snapshot"],
            {
                "angle_degrees": values["m3_phase_angle"],
                "progress": 0.0,
                "status": "ready",
            },
        )
        for key, value in values.items():
            self.assertEqual(app.session_state[key], value)


if __name__ == "__main__":
    unittest.main()
