import math
import unittest

from data.planets import PLANETS
from logic.orbit_calculations import (
    focus_distance,
    semi_minor_axis,
    semi_minor_axis_from_focus,
    transfer_eccentricity,
    transfer_semi_major_axis,
    transfer_time_days,
)
from logic.rendezvous import (
    RENDEZVOUS_TOLERANCE_KM,
    arrival_distance_km,
    fine_tune_angle_degrees,
    normalize_angle_degrees,
    shortest_angle_difference_degrees,
)
from ui.mission3_rendezvous import _extract_simulation_data
from ui.orbit_plot import mission2_orbit_simulation


class RendezvousTests(unittest.TestCase):
    def test_target_phase_places_planet_at_transfer_apoapsis(self) -> None:
        mars = PLANETS["mars"]
        semi_major = transfer_semi_major_axis(mars)
        eccentricity = transfer_eccentricity(mars)
        transfer_days = transfer_time_days(semi_major)
        travel_angle = 360 * transfer_days / mars.orbital_period_days
        target_angle = normalize_angle_degrees(180 - travel_angle)
        spacecraft_arrival = (-mars.orbit_radius_au, 0.0)

        self.assertLessEqual(
            arrival_distance_km(
                spacecraft_arrival,
                mars,
                target_angle,
                transfer_days,
            ),
            RENDEZVOUS_TOLERANCE_KM,
        )
        self.assertGreater(
            arrival_distance_km(
                spacecraft_arrival,
                mars,
                target_angle + 1,
                transfer_days,
            ),
            RENDEZVOUS_TOLERANCE_KM,
        )

    def test_fine_adjust_uses_the_shortest_direction_and_caps_each_step(self) -> None:
        self.assertEqual(
            fine_tune_angle_degrees(358, 2),
            2,
        )
        self.assertEqual(
            fine_tune_angle_degrees(10, 40),
            15,
        )
        self.assertEqual(shortest_angle_difference_degrees(2, 358), 4)

    def test_mission2_simulation_provides_the_mission3_transfer_path(self) -> None:
        for planet in PLANETS.values():
            with self.subTest(destination=planet.name):
                semi_major = transfer_semi_major_axis(planet)
                eccentricity = transfer_eccentricity(planet)
                focus = focus_distance(semi_major, eccentricity)
                semi_minor = semi_minor_axis(semi_major, eccentricity)
                focus_based_semi_minor = semi_minor_axis_from_focus(
                    semi_major,
                    focus,
                )
                self.assertAlmostEqual(semi_minor, focus_based_semi_minor, places=12)

                transfer_path, spacecraft_path = _extract_simulation_data(
                    planet,
                    semi_major,
                    eccentricity,
                    focus,
                    semi_minor,
                )
                figure = mission2_orbit_simulation(
                    planet,
                    semi_major,
                    eccentricity,
                    focus,
                    semi_minor,
                )
                mission2_transfer = next(
                    trace
                    for trace in figure.data
                    if trace.name == "호만 전이 궤도"
                )
                self.assertEqual(
                    transfer_path,
                    [
                        [float(x), float(y)]
                        for x, y in zip(mission2_transfer.x, mission2_transfer.y)
                    ],
                )
                self.assertEqual(len(spacecraft_path), len(figure.frames))
                self.assertEqual(
                    spacecraft_path,
                    [
                        [float(frame.data[1].x[0]), float(frame.data[1].y[0])]
                        for frame in figure.frames
                    ],
                )
                self.assertAlmostEqual(spacecraft_path[0][0], 1.0)
                self.assertAlmostEqual(spacecraft_path[0][1], 0.0)
                self.assertAlmostEqual(
                    spacecraft_path[-1][0],
                    -planet.orbit_radius_au,
                )
                self.assertAlmostEqual(spacecraft_path[-1][1], 0.0)
                self.assertTrue(
                    all(
                        math.isfinite(coordinate)
                        for point in transfer_path
                        for coordinate in point
                    )
                )


if __name__ == "__main__":
    unittest.main()
