from dataclasses import dataclass


DAYS_PER_YEAR = 365.25


@dataclass(frozen=True)
class Planet:
    name: str
    orbit_radius_au: float
    orbital_period_days: float
    description: str

    @property
    def orbital_period_years(self) -> float:
        return self.orbital_period_days / DAYS_PER_YEAR


EARTH = Planet("지구", 1.000, DAYS_PER_YEAR, "태양으로부터 평균 1 AU 거리에 있는 지구")
EARTH_ORBIT_RADIUS_AU = EARTH.orbit_radius_au
PLANETS: dict[str, Planet] = {
    "mars": Planet("화성", 1.524, 686.98, "붉은 표면과 얇은 대기를 가진 행성"),
    "jupiter": Planet("목성", 5.203, 4332.59, "태양계에서 가장 큰 행성"),
    "saturn": Planet("토성", 9.537, 10759.22, "뚜렷한 고리로 잘 알려진 행성"),
}
