import math
import unittest

import matplotlib.pyplot as plt

from data.constants import AU_TO_KM, SUN_GRAVITATIONAL_PARAMETER_KM3_S2
from data.planets import PLANETS
from logic.mission4_calculations import (
    closest_distance_km,
    compare_flyby_altitudes,
    deflection_angle_degrees,
    educational_excess_speed_km_s,
    hyperbolic_eccentricity,
    mission4_solar_parameters,
    planet_orbital_speed_km_s,
    spacecraft_arrival_speed_km_s,
)
from logic.answer_checker import check_numeric_answer
from logic.orbit_calculations import (
    phase_angle_degrees,
    planet_angular_velocity_degrees_per_day,
    planet_travel_angle_degrees,
    transfer_eccentricity,
    transfer_semi_major_axis,
    transfer_time_days,
    transfer_time_years,
)
from ui.orbit_plot import mission4_flyby_plot


class Mission4CalculationTests(unittest.TestCase):
    def test_solar_speed_calculations_for_supported_planets(self) -> None:
        for planet in PLANETS.values():
            with self.subTest(planet=planet.name):
                semi_major_axis_au = transfer_semi_major_axis(planet)
                arrival, orbital, excess = mission4_solar_parameters(
                    planet,
                    semi_major_axis_au,
                )
                radius_km = planet.orbit_radius_au * AU_TO_KM
                axis_km = semi_major_axis_au * AU_TO_KM
                self.assertAlmostEqual(
                    arrival,
                    spacecraft_arrival_speed_km_s(
                        SUN_GRAVITATIONAL_PARAMETER_KM3_S2,
                        radius_km,
                        axis_km,
                    ),
                )
                self.assertEqual(
                    arrival,
                    math.sqrt(
                        SUN_GRAVITATIONAL_PARAMETER_KM3_S2
                        * (2 / radius_km - 1 / axis_km)
                    ),
                )
                self.assertAlmostEqual(
                    orbital,
                    planet_orbital_speed_km_s(
                        SUN_GRAVITATIONAL_PARAMETER_KM3_S2,
                        radius_km,
                    ),
                )
                self.assertEqual(
                    orbital,
                    math.sqrt(
                        SUN_GRAVITATIONAL_PARAMETER_KM3_S2 / radius_km
                    ),
                )
                self.assertAlmostEqual(
                    excess,
                    educational_excess_speed_km_s(arrival, orbital),
                )
                self.assertGreater(excess, 0)

    def test_altitude_comparison_uses_planet_data_and_shared_excess_speed(self) -> None:
        for planet in PLANETS.values():
            with self.subTest(planet=planet.name):
                result_a, result_b = compare_flyby_altitudes(planet, 4.0)
                self.assertEqual(
                    (result_a.altitude_km, result_b.altitude_km),
                    planet.flyby_altitudes_km,
                )
                self.assertEqual(result_a.excess_speed_km_s, 4.0)
                self.assertEqual(result_b.excess_speed_km_s, 4.0)
                for result in (result_a, result_b):
                    self.assertAlmostEqual(
                        result.closest_distance_km,
                        planet.reference_radius_km + result.altitude_km,
                    )
                    self.assertGreater(result.eccentricity, 1)
                    self.assertGreater(result.deflection_angle_degrees, 0)
                    self.assertLess(result.deflection_angle_degrees, 180)

    def test_individual_flyby_calculations(self) -> None:
        distance = closest_distance_km(3389.5, 300)
        eccentricity = hyperbolic_eccentricity(distance, 2.65, 4.2828e4)
        angle = deflection_angle_degrees(eccentricity)
        self.assertEqual(distance, 3689.5)
        self.assertGreater(eccentricity, 1)
        self.assertEqual(
            angle,
            math.degrees(2 * math.asin(1 / eccentricity)),
        )

    def test_mission2_and_mission3_retain_full_calculation_precision(self) -> None:
        planet = PLANETS["mars"]
        semi_major_axis = transfer_semi_major_axis(planet)
        eccentricity = transfer_eccentricity(planet)
        transfer_years = transfer_time_years(semi_major_axis)
        transfer_days = transfer_time_days(semi_major_axis)
        angular_velocity = planet_angular_velocity_degrees_per_day(planet)
        travel_angle = planet_travel_angle_degrees(planet, transfer_days)
        phase_angle = phase_angle_degrees(travel_angle)
        self.assertEqual(semi_major_axis, (1 + planet.orbit_radius_au) / 2)
        self.assertEqual(
            eccentricity,
            (planet.orbit_radius_au - 1) / (planet.orbit_radius_au + 1),
        )
        self.assertEqual(
            transfer_years,
            math.sqrt(semi_major_axis**3) / 2,
        )
        self.assertEqual(
            transfer_days,
            transfer_years * 365.25,
        )
        self.assertEqual(angular_velocity, 360 / planet.orbital_period_days)
        self.assertEqual(
            travel_angle,
            angular_velocity * transfer_days,
        )
        self.assertEqual(phase_angle, (180 - travel_angle) % 360)

    def test_answer_checker_uses_inclusive_absolute_tolerance(self) -> None:
        self.assertTrue(check_numeric_answer(1.25, 1.0, 0.25))
        self.assertFalse(check_numeric_answer(1.250001, 1.0, 0.25))
        with self.assertRaises(ValueError):
            check_numeric_answer(1.0, 1.0, -0.01)

    def test_documented_mission_tolerances_accept_unrounded_inputs(self) -> None:
        examples = (
            ("M2 semi-major axis", 0.005, 0.01),
            ("M2 eccentricity", 0.005, 0.01),
            ("M2 focus distance", 0.005, 0.01),
            ("M3 years", 0.005, 0.01),
            ("M3 days", 1.0, 2.0),
            ("M3 angular velocity", 0.00005, 0.0001),
            ("M3 travel angle", 0.05, 0.1),
            ("M3 phase angle", 0.05, 0.1),
            ("M4 arrival speed", 0.004, 0.005),
            ("M4 planet speed", 0.004, 0.005),
            ("M4 excess speed", 0.004, 0.005),
            ("M4 eccentricity", 0.004, 0.005),
            ("M4 deflection angle", 0.004, 0.005),
        )
        for stage, difference, tolerance in examples:
            with self.subTest(stage=stage):
                self.assertTrue(
                    check_numeric_answer(
                        1.0 + difference,
                        1.0,
                        tolerance,
                    )
                )
                self.assertFalse(
                    check_numeric_answer(
                        1.0 + tolerance + 0.001,
                        1.0,
                        tolerance,
                    )
                )

    def test_rejects_non_hyperbolic_and_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            spacecraft_arrival_speed_km_s(1, 1, 0)
        with self.assertRaises(ValueError):
            closest_distance_km(100, -1)
        with self.assertRaises(ValueError):
            hyperbolic_eccentricity(100, 0, 10)
        with self.assertRaises(ValueError):
            deflection_angle_degrees(1)

    def test_flyby_plot_shows_two_trajectories_and_reference_radius(self) -> None:
        for planet in PLANETS.values():
            with self.subTest(planet=planet.name):
                results = compare_flyby_altitudes(planet, 4.0)
                figure = mission4_flyby_plot(planet, results)
                figure.canvas.draw()
                self.assertEqual(len(figure.axes[0].lines), 2)
                self.assertGreaterEqual(len(figure.axes[0].patches), 1)
                labels = [line.get_label() for line in figure.axes[0].lines]
                self.assertTrue(all("δ=" in label for label in labels))
                for axis in (*figure.axes, *figure.axes[0].child_axes):
                    self.assertIsNotNone(axis.xaxis.get_major_formatter())
                    self.assertIsNotNone(axis.yaxis.get_major_formatter())
                velocity_ax = figure.axes[0].child_axes[0]
                vectors = velocity_ax.collections
                self.assertEqual(len(vectors), 4)
                for index, result in enumerate(results):
                    for vector_index in (index * 2, index * 2 + 1):
                        vector = vectors[vector_index]
                        self.assertAlmostEqual(
                            math.hypot(vector.U[0], vector.V[0]),
                            result.excess_speed_km_s,
                            delta=1e-12,
                        )
                    self.assertIn(
                        f"{result.deflection_angle_degrees:.6g}°",
                        velocity_ax.texts[index].get_text(),
                    )
                plt.close(figure)


if __name__ == "__main__":
    unittest.main()
