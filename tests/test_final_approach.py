import math
import unittest

from data.constants import AU_TO_KM
from data.planets import PLANETS, Planet
from logic.final_approach import (
    FINAL_APPROACH_PLANET_DATA,
    GRAVITATIONAL_CONSTANT_KM3_PER_KG_S2,
    RendezvousPosition,
    SUN_MASS_KG,
    closest_approach_to_sphere_of_influence,
    find_sphere_of_influence_entry,
    hyperbolic_orbit_from_entry,
    rendezvous_positions_at,
    sphere_of_influence_radius_km,
    sphere_of_influence_status,
)
from logic.orbit_calculations import (
    focus_distance,
    phase_angle_degrees,
    planet_travel_angle_degrees,
    semi_minor_axis,
    transfer_eccentricity,
    transfer_semi_major_axis,
    transfer_time_days,
)
from ui.mission3_rendezvous import _extract_simulation_data


class FinalApproachTests(unittest.TestCase):
    def _mission3_data(
        self, planet_key: str, angle_offset_degrees: float = 0.0
    ) -> tuple[Planet, list[list[float]], float, float, float]:
        planet = PLANETS[planet_key]
        semi_major_axis = transfer_semi_major_axis(planet)
        eccentricity = transfer_eccentricity(planet)
        focus = focus_distance(semi_major_axis, eccentricity)
        transfer_days = transfer_time_days(semi_major_axis)
        arrival_angle = phase_angle_degrees(
            planet_travel_angle_degrees(planet, transfer_days)
        )
        _, spacecraft_path = _extract_simulation_data(
            planet,
            semi_major_axis,
            eccentricity,
            focus,
            semi_minor_axis(semi_major_axis, eccentricity),
        )
        return (
            planet,
            spacecraft_path,
            arrival_angle + angle_offset_degrees,
            transfer_days,
            semi_major_axis,
        )

    def test_sphere_of_influence_radii_use_planet_data(self) -> None:
        self.assertEqual(set(FINAL_APPROACH_PLANET_DATA), set(PLANETS))
        for planet_key, (distance_km, mass_kg, radius_km) in (
            FINAL_APPROACH_PLANET_DATA.items()
        ):
            with self.subTest(planet=planet_key):
                self.assertEqual(
                    distance_km,
                    PLANETS[planet_key].orbit_radius_au * AU_TO_KM,
                )
                expected = distance_km * (mass_kg / SUN_MASS_KG) ** (2 / 5)
                self.assertEqual(
                    sphere_of_influence_radius_km(distance_km, mass_kg),
                    expected,
                )
                self.assertGreater(radius_km, 0)

    def test_sphere_of_influence_entry_includes_exact_boundary(self) -> None:
        radius = 100.0
        inside = sphere_of_influence_status((0.0, 0.0), (0.0, 0.0), radius, 1.0)
        boundary = sphere_of_influence_status((radius, 0.0), (0.0, 0.0), radius, 1.0)
        outside = sphere_of_influence_status(
            (radius + 1e-6, 0.0),
            (0.0, 0.0),
            radius,
            1.0,
        )

        self.assertTrue(inside.entered)
        self.assertTrue(boundary.entered)
        self.assertEqual(boundary.remaining_km, 0.0)
        self.assertFalse(outside.entered)
        self.assertGreater(outside.remaining_km, 0.0)

    def test_distance_converts_relative_coordinates_from_au_to_km(self) -> None:
        status = sphere_of_influence_status(
            (1.0, 1.0),
            (1.0, 0.0),
            influence_radius_km=10_000,
            au_to_km=100_000,
        )
        self.assertEqual(status.distance_km, 100_000)
        self.assertEqual(status.remaining_km, 90_000)
        self.assertFalse(status.entered)

    def test_real_mission3_paths_find_boundary_entry_for_each_target(self) -> None:
        for planet_key, (planet_orbit_km, mass_kg, _) in (
            FINAL_APPROACH_PLANET_DATA.items()
        ):
            planet, path, initial_angle, duration, _ = self._mission3_data(planet_key)
            soi_radius = sphere_of_influence_radius_km(planet_orbit_km, mass_kg)
            entry = find_sphere_of_influence_entry(
                path, planet, initial_angle, duration, soi_radius
            )
            with self.subTest(planet=planet_key):
                self.assertIsNotNone(entry)
                assert entry is not None
                distance = math.hypot(*entry.relative_position_km)
                self.assertAlmostEqual(distance, soi_radius, delta=soi_radius * 1e-9)

                same_time_state = rendezvous_positions_at(
                    path,
                    entry.progress,
                    initial_angle,
                    duration,
                    planet,
                )
                self.assertEqual(same_time_state.spacecraft_au, entry.spacecraft_au)
                self.assertEqual(same_time_state.planet_au, entry.planet_au)
                self.assertEqual(
                    same_time_state.spacecraft_velocity_km_s,
                    entry.spacecraft_velocity_km_s,
                )
                self.assertEqual(
                    same_time_state.planet_velocity_km_s,
                    entry.planet_velocity_km_s,
                )
                self.assertAlmostEqual(
                    entry.relative_position_km[0],
                    (entry.spacecraft_au[0] - entry.planet_au[0]) * AU_TO_KM,
                )
                self.assertAlmostEqual(
                    entry.relative_position_km[1],
                    (entry.spacecraft_au[1] - entry.planet_au[1]) * AU_TO_KM,
                )
                self.assertAlmostEqual(
                    entry.relative_velocity_km_s[0],
                    entry.spacecraft_velocity_km_s[0]
                    - entry.planet_velocity_km_s[0],
                )
                self.assertAlmostEqual(
                    entry.relative_velocity_km_s[1],
                    entry.spacecraft_velocity_km_s[1]
                    - entry.planet_velocity_km_s[1],
                )

    def test_non_crossing_mission3_path_does_not_report_entry(self) -> None:
        for planet_key in PLANETS:
            planet, path, initial_angle, duration, _ = self._mission3_data(
                planet_key, 180.0
            )
            planet_orbit_km, planet_mass_kg, _ = FINAL_APPROACH_PLANET_DATA[
                planet_key
            ]
            soi_radius = sphere_of_influence_radius_km(
                planet_orbit_km,
                planet_mass_kg,
            )
            with self.subTest(planet=planet_key):
                self.assertIsNone(
                    find_sphere_of_influence_entry(
                        path,
                        planet,
                        initial_angle,
                        duration,
                        soi_radius,
                    )
                )
                closest = closest_approach_to_sphere_of_influence(
                    path,
                    planet,
                    initial_angle,
                    duration,
                    soi_radius,
                )
                self.assertIsNotNone(closest)
                assert closest is not None
                self.assertGreater(
                    math.hypot(*closest.relative_position_km),
                    soi_radius,
                )

    def test_valid_non_target_launch_angle_still_finds_entry(self) -> None:
        planet, path, initial_angle, duration, _ = self._mission3_data(
            "mars", 0.5
        )
        planet_orbit_km, planet_mass_kg, _ = FINAL_APPROACH_PLANET_DATA["mars"]
        soi_radius = sphere_of_influence_radius_km(
            planet_orbit_km,
            planet_mass_kg,
        )

        entry = find_sphere_of_influence_entry(
            path,
            planet,
            initial_angle,
            duration,
            soi_radius,
        )

        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertAlmostEqual(
            math.hypot(*entry.relative_position_km),
            soi_radius,
            delta=soi_radius * 1e-9,
        )

    def test_hyperbola_requires_positive_energy_and_eccentricity_above_one(self) -> None:
        planet_mass = FINAL_APPROACH_PLANET_DATA["mars"][1]
        mu = GRAVITATIONAL_CONSTANT_KM3_PER_KG_S2 * planet_mass
        radius_km = 100_000.0
        circular_speed_km_s = math.sqrt(mu / radius_km)
        circular_state = RendezvousPosition(
            progress=0.5,
            elapsed_days=1.0,
            spacecraft_au=(radius_km / AU_TO_KM, 0.0),
            planet_au=(0.0, 0.0),
            spacecraft_velocity_km_s=(0.0, circular_speed_km_s),
            planet_velocity_km_s=(0.0, 0.0),
        )
        with self.assertRaisesRegex(ValueError, "쌍곡선이 아닙니다"):
            hyperbolic_orbit_from_entry(
                circular_state,
                planet_mass,
                influence_radius_km=200_000,
            )

    def test_hyperbola_matches_entry_and_handles_planet_impact(self) -> None:
        for planet_key, (planet_orbit_km, planet_mass, planet_radius) in (
            FINAL_APPROACH_PLANET_DATA.items()
        ):
            planet, path, initial_angle, duration, _ = self._mission3_data(planet_key)
            soi_radius = sphere_of_influence_radius_km(planet_orbit_km, planet_mass)
            entry = find_sphere_of_influence_entry(
                path, planet, initial_angle, duration, soi_radius
            )
            self.assertIsNotNone(entry)
            assert entry is not None
            orbit = hyperbolic_orbit_from_entry(
                entry,
                planet_mass,
                soi_radius,
                planet_radius_km=planet_radius,
            )
            with self.subTest(planet=planet_key):
                self.assertGreater(orbit.specific_energy_km2_s2, 0)
                self.assertGreater(orbit.eccentricity, 1)
                self.assertLess(orbit.periapsis_km, soi_radius)
                self.assertLess(orbit.position_residual_km, 0.01)
                self.assertLess(orbit.velocity_residual_km_s, 1e-8)
                self.assertAlmostEqual(
                    math.hypot(*orbit.orbit_path_km[0]),
                    soi_radius,
                    delta=soi_radius * 1e-9,
                )
                if orbit.periapsis_km <= planet_radius:
                    self.assertIsNone(orbit.exit_position_km)
                    self.assertIsNotNone(orbit.impact_position_km)
                    assert orbit.impact_position_km is not None
                    self.assertAlmostEqual(
                        math.hypot(*orbit.impact_position_km),
                        planet_radius,
                        delta=planet_radius * 1e-9,
                    )
                    self.assertLess(
                        math.hypot(*orbit.orbit_path_km[-1]),
                        soi_radius,
                    )
                else:
                    self.assertIsNotNone(orbit.exit_position_km)
                    assert orbit.exit_position_km is not None
                    self.assertAlmostEqual(
                        math.hypot(*orbit.exit_position_km),
                        soi_radius,
                        delta=soi_radius * 1e-9,
                    )
                    self.assertIsNone(orbit.impact_position_km)


if __name__ == "__main__":
    unittest.main()
