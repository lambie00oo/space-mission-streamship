import math
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from data.planets import EARTH_ORBIT_RADIUS_AU, PLANETS
from logic.orbit_calculations import (
    focus_distance,
    semi_minor_axis,
    semi_minor_axis_from_focus,
    transfer_time_years,
    transfer_eccentricity,
    transfer_semi_major_axis,
)
from ui.ellipse_design import (
    create_ellipse_figure,
    expected_ellipse_points,
)
from ui.orbit_plot import mission2_orbit_simulation


class Mission2SimulationTests(unittest.TestCase):
    def test_semi_minor_axis_uses_focus_distance_and_checks_ellipse_condition(self) -> None:
        semi_major = 1.262
        focus = 0.262
        expected = math.sqrt(semi_major**2 - focus**2)
        self.assertAlmostEqual(
            semi_minor_axis_from_focus(semi_major, focus),
            expected,
        )
        with self.assertRaisesRegex(ValueError, "a² > c²"):
            semi_minor_axis_from_focus(1.0, 1.0)
        with self.assertRaisesRegex(ValueError, "유한한 숫자"):
            semi_minor_axis_from_focus(math.inf, 0.2)

    def test_ellipse_plot_shows_all_landmarks_with_equal_axis_scale(self) -> None:
        a, c = 1.262, 0.262
        b = semi_minor_axis_from_focus(a, c)
        points = expected_ellipse_points(a, b, c)
        figure = create_ellipse_figure(a, b, c)
        self.assertEqual(
            tuple(trace.name for trace in figure.data[1:]),
            (
                "태양 · 초점 F",
                "중심 C",
                "다른 초점 F′",
                "장축 끝점 A",
                "장축 끝점 A′",
                "단축 끝점 B",
                "단축 끝점 B′",
            ),
        )
        self.assertEqual(figure.layout.xaxis.scaleanchor, "y")
        self.assertEqual(figure.layout.xaxis.scaleratio, 1)
        expected = points
        self.assertEqual(
            tuple((trace.x[0], trace.y[0]) for trace in figure.data[1:]),
            (
                (0.0, 0.0),
                (-c, 0.0),
                (-2 * c, 0.0),
                expected["A"],
                expected["A′"],
                expected["B"],
                expected["B′"],
            ),
        )

    def test_ellipse_uses_each_planets_calculated_orbit(self) -> None:
        axis_lengths = []
        for planet in PLANETS.values():
            semi_major = transfer_semi_major_axis(planet)
            eccentricity = transfer_eccentricity(planet)
            focus = focus_distance(semi_major, eccentricity)
            semi_minor = semi_minor_axis_from_focus(semi_major, focus)
            figure = create_ellipse_figure(semi_major, semi_minor, focus)
            axis_lengths.append((figure.data[0].x[0], figure.data[0].y[90]))

        self.assertEqual(len(set(axis_lengths)), len(PLANETS))

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

        self.assertEqual(len(figure.frames), 121)
        self.assertAlmostEqual(figure.frames[0].data[1].x[0], 1.0)
        self.assertAlmostEqual(figure.frames[0].data[1].y[0], 0.0)
        self.assertEqual(figure.data[5].mode, "markers+text")
        self.assertEqual(figure.data[5].marker.symbol, "star")
        self.assertEqual(figure.data[5].text[0], "🚀 우주선")
        self.assertEqual(figure.layout.images[1].layer, "below")
        transfer_arc = figure.data[2]
        self.assertEqual(len(transfer_arc.x), len(figure.frames))
        self.assertAlmostEqual(transfer_arc.x[0], EARTH_ORBIT_RADIUS_AU)
        self.assertAlmostEqual(transfer_arc.y[0], 0.0)
        self.assertAlmostEqual(transfer_arc.x[-1], -planet.orbit_radius_au)
        self.assertAlmostEqual(transfer_arc.y[-1], 0.0)
        self.assertTrue(all(y >= -1e-12 for y in transfer_arc.y))
        self.assertEqual(
            figure.layout.title.text,
            figure.frames[0].layout.title.text,
        )
        self.assertIn("전이 시간: 0.0 /", figure.frames[0].layout.title.text)
        self.assertIn(
            f"/ {transfer_time_years(semi_major):.3f}년",
            figure.frames[-1].layout.title.text,
        )

        for frame in figure.frames:
            spacecraft_x = frame.data[1].x[0]
            spacecraft_y = frame.data[1].y[0]
            self.assertAlmostEqual(frame.data[0].x[-1], spacecraft_x)
            self.assertAlmostEqual(frame.data[0].y[-1], spacecraft_y)
            self.assertGreaterEqual(spacecraft_y, -1e-12)
            ellipse_value = (
                ((spacecraft_x + focus_distance(semi_major, eccentricity)) / semi_major) ** 2
                + (spacecraft_y / semi_minor_axis(semi_major, eccentricity)) ** 2
            )
            self.assertAlmostEqual(ellipse_value, 1.0)

        self.assertAlmostEqual(
            figure.frames[-1].data[1].x[0],
            -planet.orbit_radius_au,
        )
        self.assertAlmostEqual(figure.frames[-1].data[1].y[0], 0.0)
        self.assertEqual(len(figure.frames[-1].data[0].x), len(figure.frames))
        self.assertEqual(len(figure.layout.images), 3)
        self.assertEqual(len(figure.frames[-1].layout.images), 3)
        self.assertTrue(
            all(
                image.source.startswith("data:image/png;base64,")
                for image in figure.layout.images
            )
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

        self.assertNotEqual(list(mars_plot.data[2].x), list(jupiter_plot.data[2].x))
        self.assertEqual(
            tuple(mars_plot.layout.xaxis.range),
            (-PLANETS["mars"].orbit_radius_au * 1.12, PLANETS["mars"].orbit_radius_au * 1.12),
        )
        self.assertEqual(
            tuple(jupiter_plot.layout.xaxis.range),
            (-PLANETS["jupiter"].orbit_radius_au * 1.12, PLANETS["jupiter"].orbit_radius_au * 1.12),
        )
        self.assertEqual(
            tuple(trace.name for trace in mars_plot.data[:2]),
            ("지구 공전 궤도", "화성 공전 궤도"),
        )
        self.assertEqual(
            tuple(trace.name for trace in jupiter_plot.data[:2]),
            ("지구 공전 궤도", "목성 공전 궤도"),
        )

    def test_only_selected_planet_and_earth_are_shown(self) -> None:
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

                self.assertEqual(
                    tuple(trace.name for trace in figure.data[:2]),
                    ("지구 공전 궤도", f"{planet.name} 공전 궤도"),
                )
                self.assertEqual(
                    tuple(trace.name for trace in figure.data[6:8]),
                    ("지구 현재 위치", f"{planet.name} 현재 위치"),
                )
                self.assertEqual(len(figure.data), 10)
                self.assertEqual(figure.data[5].text[0], "🚀 우주선")
                self.assertEqual(len(figure.frames), 121)
                self.assertAlmostEqual(figure.data[2].x[0], EARTH_ORBIT_RADIUS_AU)
                self.assertAlmostEqual(figure.data[2].y[0], 0.0)
                self.assertAlmostEqual(
                    figure.data[2].x[-1],
                    -planet.orbit_radius_au,
                )
                self.assertAlmostEqual(figure.data[2].y[-1], 0.0)
                self.assertTrue(all(y >= -1e-12 for y in figure.data[2].y))
                transfer_focus = focus_distance(semi_major, eccentricity)
                transfer_minor = semi_minor_axis(semi_major, eccentricity)
                for frame in figure.frames:
                    spacecraft_x = frame.data[1].x[0]
                    spacecraft_y = frame.data[1].y[0]
                    self.assertAlmostEqual(
                        ((spacecraft_x + transfer_focus) / semi_major) ** 2
                        + (spacecraft_y / transfer_minor) ** 2,
                        1.0,
                    )
                    self.assertGreaterEqual(spacecraft_y, -1e-12)
                for orbit, radius in zip(
                    figure.data[:2],
                    (1.0, planet.orbit_radius_au),
                ):
                    self.assertAlmostEqual(
                        math.hypot(orbit.x[0], orbit.y[0]),
                        radius,
                    )

                destination_position = figure.frames[-1].data[4]
                self.assertAlmostEqual(
                    destination_position.x[0],
                    -planet.orbit_radius_au,
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

                image = figure.frames[-1].layout.images[2]
                self.assertAlmostEqual(
                    image.x,
                    -planet.orbit_radius_au,
                )
                self.assertAlmostEqual(image.y, 0.0)
                self.assertEqual(len(figure.frames[-1].layout.images), 3)
                self.assertEqual(
                    tuple(figure.frames[-1].traces),
                    (4, 5, 6, 8, 7, 9),
                )

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
            [figure.data[index].mode for index in (6, 7)],
            ["markers"] * 2,
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

    def test_mission2_hides_dynamic_simulation_and_keeps_completion_flow(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        planet = PLANETS["mars"]
        semi_major = transfer_semi_major_axis(planet)
        eccentricity = transfer_eccentricity(planet)
        app = AppTest.from_file(str(app_path), default_timeout=30)
        app.session_state["current_page"] = "MISSION2"
        app.session_state["mission1_completed"] = True
        app.session_state["selected_planet"] = "mars"
        app.session_state["planet_select"] = "mars"
        app.session_state["m2_a"] = semi_major
        app.session_state["m2_e"] = eccentricity
        app.session_state["m2_c"] = focus_distance(semi_major, eccentricity)
        app.session_state["m2_result"] = {
            "planet_key": "mars",
            "semi_major_axis_au": semi_major,
            "eccentricity": eccentricity,
            "focus_distance_au": focus_distance(semi_major, eccentricity),
        }
        app.session_state["m2_ellipse_formula_input"] = {
            "values": {"old_input": "1"},
        }
        app.session_state["m2_ellipse_result"] = {"correct": True}
        app.run()

        self.assertFalse(app.exception)
        self.assertEqual(len(app.get("plotly_chart")), 1)
        self.assertFalse(
            any(
                "전이 궤도 동적 시뮬레이션" in element.value
                for element in app.subheader
            )
        )
        self.assertFalse(any(button.label in ("정답 확인", "수식 입력 초기화") for button in app.button))
        self.assertTrue(
            any(button.key == "mission2_complete_button" for button in app.button)
        )
        self.assertNotIn("m2_ellipse_formula_input", app.session_state)
        self.assertNotIn("m2_ellipse_result", app.session_state)
        self.assertTrue(any("b = √(" in element.value for element in app.markdown))
        self.assertAlmostEqual(app.session_state["m2_a"], semi_major)
        self.assertAlmostEqual(
            app.session_state["m2_c"],
            focus_distance(semi_major, eccentricity),
        )


if __name__ == "__main__":
    unittest.main()
