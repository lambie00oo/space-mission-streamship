import math
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from data.planets import PLANETS
from logic.orbit_calculations import (
    focus_distance,
    semi_minor_axis,
    transfer_time_years,
    transfer_eccentricity,
    transfer_semi_major_axis,
)
from ui.orbit_plot import (
    SIMULATION_ORBIT_RADII_AU,
    mission2_orbit_simulation,
)


class Mission2SimulationTests(unittest.TestCase):
    def test_animation_uses_calculated_orbit_and_reaches_destination(self) -> None:
        planet = PLANETS["mars"]
        semi_major = transfer_semi_major_axis(planet)
        eccentricity = transfer_eccentricity(planet)
        figure = mission2_orbit_simulation(
            planet,
            semi_major,
            eccentricity,
            focus_distance(semi_major, eccentricity),
            semi_minor_axis(semi_major, eccentricity),
        )

        self.assertEqual(len(figure.frames), 61)
        self.assertAlmostEqual(figure.frames[0].data[1].x[0], 1.0)
        self.assertAlmostEqual(figure.frames[0].data[1].y[0], 0.0)
        self.assertAlmostEqual(
            figure.frames[-1].data[1].x[0],
            -planet.orbit_radius_au,
        )
        self.assertAlmostEqual(figure.frames[-1].data[1].y[0], 0.0)
        self.assertEqual(len(figure.frames[-1].data[0].x), len(figure.frames))
        self.assertEqual(len(figure.layout.images), 5)
        self.assertEqual(len(figure.frames[-1].layout.images), 5)
        self.assertTrue(
            all(image.source.startswith("data:image/png;base64,") for image in figure.layout.images)
        )

        buttons = figure.layout.updatemenus[0].buttons
        self.assertEqual(
            [button.label for button in buttons],
            ["재생", "일시 정지", "처음부터 재생"],
        )

    def test_simulation_changes_with_the_calculated_orbit(self) -> None:
        mars = PLANETS["mars"]
        mars_axis = transfer_semi_major_axis(mars)
        mars_eccentricity = transfer_eccentricity(mars)
        mars_plot = mission2_orbit_simulation(
            mars,
            mars_axis,
            mars_eccentricity,
            focus_distance(mars_axis, mars_eccentricity),
            semi_minor_axis(mars_axis, mars_eccentricity),
        )

        jupiter = PLANETS["jupiter"]
        jupiter_axis = transfer_semi_major_axis(jupiter)
        jupiter_eccentricity = transfer_eccentricity(jupiter)
        jupiter_plot = mission2_orbit_simulation(
            jupiter,
            jupiter_axis,
            jupiter_eccentricity,
            focus_distance(jupiter_axis, jupiter_eccentricity),
            semi_minor_axis(jupiter_axis, jupiter_eccentricity),
        )

        self.assertNotEqual(list(mars_plot.data[4].x), list(jupiter_plot.data[4].x))
        self.assertEqual(
            tuple(jupiter_plot.layout.xaxis.range),
            (-SIMULATION_ORBIT_RADII_AU["토성"] * 1.12, SIMULATION_ORBIT_RADII_AU["토성"] * 1.12),
        )

    def test_all_planet_orbits_and_period_driven_arrival_positions(self) -> None:
        body_names = tuple(SIMULATION_ORBIT_RADII_AU)
        for planet in PLANETS.values():
            with self.subTest(destination=planet.name):
                semi_major = transfer_semi_major_axis(planet)
                eccentricity = transfer_eccentricity(planet)
                figure = mission2_orbit_simulation(
                    planet,
                    semi_major,
                    eccentricity,
                    focus_distance(semi_major, eccentricity),
                    semi_minor_axis(semi_major, eccentricity),
                )

                for index, body_name in enumerate(body_names):
                    orbit = figure.data[index]
                    self.assertAlmostEqual(
                        math.hypot(orbit.x[0], orbit.y[0]),
                        SIMULATION_ORBIT_RADII_AU[body_name],
                    )

                destination_index = body_names.index(planet.name)
                destination_position = figure.frames[-1].data[
                    2 + 2 * destination_index
                ]
                self.assertAlmostEqual(
                    destination_position.x[0],
                    -SIMULATION_ORBIT_RADII_AU[planet.name],
                )
                self.assertAlmostEqual(destination_position.y[0], 0.0)

                earth_position = figure.frames[-1].data[2]
                transfer_years = transfer_time_years(semi_major)
                self.assertAlmostEqual(
                    earth_position.x[0],
                    math.cos(2 * math.pi * transfer_years),
                )
                self.assertAlmostEqual(
                    earth_position.y[0],
                    math.sin(2 * math.pi * transfer_years),
                )

                image = figure.frames[-1].layout.images[destination_index + 1]
                self.assertAlmostEqual(
                    image.x,
                    -SIMULATION_ORBIT_RADII_AU[planet.name],
                )
                self.assertAlmostEqual(image.y, 0.0)

    def test_missing_planet_images_fall_back_to_visible_body_markers(self) -> None:
        planet = PLANETS["mars"]
        semi_major = transfer_semi_major_axis(planet)
        eccentricity = transfer_eccentricity(planet)
        with patch("ui.orbit_plot._planet_image_data_uri", return_value=None):
            figure = mission2_orbit_simulation(
                planet,
                semi_major,
                eccentricity,
                focus_distance(semi_major, eccentricity),
                semi_minor_axis(semi_major, eccentricity),
            )

        self.assertEqual(len(figure.layout.images), 0)
        self.assertEqual(len(figure.frames[0].layout.images), 0)
        self.assertEqual(
            [figure.data[index].mode for index in range(8, 12)],
            ["markers"] * 4,
        )

    def test_simulation_rejects_invalid_orbit_parameters(self) -> None:
        planet = PLANETS["mars"]
        with self.assertRaises(ValueError):
            mission2_orbit_simulation(
                planet,
                math.inf,
                0.2,
                0.2,
                1.0,
            )

    def test_mission2_renders_the_simulation_from_session_state(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path), default_timeout=30)
        app.session_state["current_page"] = "MISSION2"
        app.session_state["mission1_completed"] = True
        app.session_state["selected_planet"] = "mars"
        app.session_state["planet_select"] = "mars"
        app.session_state["m2_a"] = 1.262
        app.session_state["m2_e"] = 0.2076069731
        app.session_state["m2_c"] = 1.262 * 0.2076069731
        app.run()

        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("plotly_chart")), 1)
        self.assertTrue(
            any(
                button.key == "mission2_complete_button"
                for button in app.button
            )
        )


if __name__ == "__main__":
    unittest.main()
