import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from ui.intro import _planet_image_path


class PlanetSelectionTests(unittest.TestCase):
    def test_resolves_planets_to_the_inspected_image_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image_dir = Path(directory)
            expected_files = {
                "mars": "j.webp",
                "jupiter": "m.jpeg",
                "saturn": "S.jpg",
            }
            for image_name in expected_files.values():
                (image_dir / image_name).touch()

            with patch("ui.intro.PLANET_IMAGE_DIR", image_dir):
                for planet_key, image_name in expected_files.items():
                    with self.subTest(planet=planet_key):
                        self.assertEqual(
                            _planet_image_path(planet_key),
                            image_dir / image_name,
                        )

    def test_missing_images_use_the_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch("ui.intro.PLANET_IMAGE_DIR", Path(directory)):
                self.assertIsNone(_planet_image_path("mars"))

    def test_intro_selection_preserves_mission_state(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path), default_timeout=30)
        app.session_state["selected_planet"] = "mars"
        app.session_state["planet_select"] = "mars"
        app.session_state["mission1_completed"] = True
        app.session_state["m2_a"] = 1.262
        app.run()

        self.assertFalse(app.exception)
        app.button(key="select_planet_jupiter").click().run()

        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["selected_planet"], "jupiter")
        self.assertEqual(app.session_state["planet_select"], "jupiter")
        self.assertTrue(app.session_state["mission1_completed"])
        self.assertEqual(app.session_state["m2_a"], 1.262)


if __name__ == "__main__":
    unittest.main()
