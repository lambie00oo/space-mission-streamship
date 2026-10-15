import unittest

import matplotlib.pyplot as plt

from data.planets import PLANETS
from ui.orbit_plot import mission2_orbit_plot, mission3_orbit_plot


class Mission3PlotTests(unittest.TestCase):
    def test_mission3_axes_match_mission2_axes(self) -> None:
        for planet in PLANETS.values():
            with self.subTest(planet=planet.name):
                mission2_figure = mission2_orbit_plot(planet)
                mission3_figure = mission3_orbit_plot(planet, 45.0, 90.0)
                try:
                    mission2_axis = mission2_figure.axes[0]
                    mission3_axis = mission3_figure.axes[0]
                    self.assertEqual(mission3_axis.get_xlim(), mission2_axis.get_xlim())
                    self.assertEqual(mission3_axis.get_ylim(), mission2_axis.get_ylim())
                    self.assertEqual(
                        list(mission3_axis.get_xticks()),
                        list(mission2_axis.get_xticks()),
                    )
                    self.assertEqual(
                        list(mission3_axis.get_yticks()),
                        list(mission2_axis.get_yticks()),
                    )
                    self.assertEqual(
                        mission3_axis.get_xlabel(),
                        mission2_axis.get_xlabel(),
                    )
                    self.assertEqual(
                        mission3_axis.get_ylabel(),
                        mission2_axis.get_ylabel(),
                    )
                    self.assertEqual(
                        type(mission3_axis.xaxis.get_major_formatter()),
                        type(mission2_axis.xaxis.get_major_formatter()),
                    )
                    self.assertEqual(
                        type(mission3_axis.yaxis.get_major_formatter()),
                        type(mission2_axis.yaxis.get_major_formatter()),
                    )
                finally:
                    plt.close(mission2_figure)
                    plt.close(mission3_figure)


if __name__ == "__main__":
    unittest.main()
