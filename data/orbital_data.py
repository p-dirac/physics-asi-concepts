"""
Real orbital data for the pre-1900 Mercury-anomaly scenario: Mercury's
observed excess perihelion precession is the single calibration point;
Venus, Earth, Mars, and the Moon are the held-out validation constraints.

All (a, e, period) values and physical constants below were used to
independently verify every candidate family's formula against three
separate derivations (two different AI-generated cross-checks plus this
project's own from-scratch derivations) before any of this was trusted.
See the project README for the full verification history, including two
real errors those cross-checks caught and corrected.
"""
from __future__ import annotations

from dataclasses import dataclass

AU = 1.495978707e11            # m
GM_SUN = 1.32712440018e20      # m^3/s^2
GM_EARTH = 3.986004418e14      # m^3/s^2
C = 2.99792458e8               # m/s
ARCSEC_PER_RAD = 206264.80625
DAYS_PER_CENTURY = 100 * 365.25

MERCURY_OBSERVED_PRECESSION = 43.0  # arcsec/century -- the one calibration target


@dataclass(frozen=True)
class OrbitalBody:
    name: str
    a_m: float          # semi-major axis, meters
    e: float             # eccentricity
    period_days: float
    gm_central: float    # GM of whatever it orbits (Sun, or Earth for the Moon)

    @property
    def p_m(self) -> float:
        """Semi-latus rectum, a(1-e^2) -- the natural radial scale that
        appears in every precession formula here."""
        return self.a_m * (1 - self.e**2)

    @property
    def orbits_per_century(self) -> float:
        return DAYS_PER_CENTURY / self.period_days


MERCURY = OrbitalBody("mercury", 0.3871 * AU, 0.2056, 87.969, GM_SUN)
VENUS = OrbitalBody("venus", 0.7233 * AU, 0.0068, 224.701, GM_SUN)
EARTH = OrbitalBody("earth", 1.0000 * AU, 0.0167, 365.256, GM_SUN)
MARS = OrbitalBody("mars", 1.5237 * AU, 0.0934, 686.980, GM_SUN)
MOON = OrbitalBody("moon", 3.844e8, 0.0549, 27.321661, GM_EARTH)

VALIDATION_BODIES = [VENUS, EARTH, MARS, MOON]

# Historical acceptable-precession ceilings (arcsec/century), and the
# Kepler-third-law fractional-deviation ceiling, reflecting roughly what
# pre-1900 observational precision could and couldn't have detected. These
# are deliberately round numbers set comfortably above the correct family's
# own predictions (8.6, 3.8, 1.35, 0.06) and comfortably below the failing
# candidates' predictions (which run from ~17 up to tens of thousands) --
# see models/families.py and the project README for the verified
# per-family numbers these were chosen against.
PRECESSION_TOLERANCE = {
    "venus": 12.0,
    "earth": 6.0,
    "mars": 3.0,
    "moon": 2.0,
}
KEPLER_THIRD_LAW_TOLERANCE = 1e-4


class ObservationDatabase:
    """
    Represents the 'observational input' stage of the pipeline: the real
    measured orbital elements and Mercury's anomalous precession -- the
    experimental facts that trigger the whole discovery process, in the
    same sense that Mercury's anomaly was the actual historical starting
    point for Newcomb, Hall, and Seeliger's search.

    In a general ASI-for-physics system, this would be a live connection
    to an observational archive (e.g. JPL Horizons for modern elements, or
    digitized 19th-century almanac/USNO data for a strictly period-accurate
    simulation). Here it's a fixed table of the same real values already
    defined above in this module -- building or connecting to an actual
    historical-astronomy archive is out of scope for a demo. What matters
    is that the INTERFACE below is written the way a real lookup would be,
    so swapping in a real data source later is a change to this one class,
    not to every place that currently reads MERCURY/VENUS/etc. directly.
    """

    def __init__(self) -> None:
        self._bodies: dict[str, OrbitalBody] = {
            b.name: b for b in (MERCURY, VENUS, EARTH, MARS, MOON)
        }

    def get_calibration_body(self) -> OrbitalBody:
        """The one body used to fit each family's free parameter(s)."""
        return self._bodies["mercury"]

    def get_calibration_target(self) -> float:
        """Mercury's observed excess precession, arcsec/century -- the
        experimental anomaly the whole search is trying to explain."""
        return MERCURY_OBSERVED_PRECESSION

    def get_validation_bodies(self) -> list[OrbitalBody]:
        """The held-out bodies every fitted family is checked against."""
        return [self._bodies[name] for name in ("venus", "earth", "mars", "moon")]

    def get_body(self, name: str) -> OrbitalBody:
        return self._bodies[name]
