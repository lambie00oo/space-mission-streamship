import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from ui import mission3


class SessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as error:
            raise AttributeError(key) from error

    def __setattr__(self, key, value):
        self[key] = value


class Mission3NavigationTests(unittest.TestCase):
    def test_incomplete_results_keep_mission3_open(self) -> None:
        state = SessionState(current_page="MISSION3")
        fake_streamlit = SimpleNamespace(session_state=state, error=Mock())

        with patch.object(mission3, "st", fake_streamlit):
            mission3._complete_mission3()

        self.assertEqual(state.current_page, "MISSION3")
        self.assertNotIn("m3_complete", state)
        fake_streamlit.error.assert_called_once()

    def test_complete_results_navigate_without_clearing_values(self) -> None:
        values = {
            "m3_time_years": 0.7,
            "m3_time_days": 255.7,
            "m3_omega": 0.5,
            "m3_travel_angle": 127.8,
            "m3_phase_angle": 52.2,
        }
        state = SessionState(current_page="MISSION3", **values)
        fake_streamlit = SimpleNamespace(session_state=state, error=Mock())

        with patch.object(mission3, "st", fake_streamlit):
            mission3._complete_mission3()

        self.assertEqual(state.current_page, "MISSION4")
        self.assertTrue(state.m3_complete)
        for key, value in values.items():
            self.assertEqual(state[key], value)
        fake_streamlit.error.assert_not_called()


if __name__ == "__main__":
    unittest.main()
