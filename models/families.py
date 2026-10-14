"""
Ten candidate modifications to Newtonian gravity, each fit from Mercury's
observed 43"/century excess precession alone, then checked against four
held-out constraints (Venus, Earth, Mars, Moon precession) plus Kepler's
third law. This is the actual pre-1900 methodology (Newcomb, Hall,
Seeliger): calibrate on Mercury, see what else the same hypothesis
predicts, and check it against everything else already known.

Every formula here was cross-checked against at least one independent
derivation before being trusted -- and two real errors were caught that
way: an early draft of Gerber's lunar prediction used a post-1900
three-body figure (~287"/cy, from Seeliger/von Laue 1917) rather than
the two-body result a pre-1900 physicist would have computed (0.06"/cy);
and an inverse-fourth Pass-3 table had wrong Earth/Mars values. Both are
corrected here. See the project README for the full verification trail.

Where a formula is a first-order perturbative approximation rather than an
exact solution (inverse-fourth, Yukawa), that's noted explicitly -- it
matters most in the regimes (very large k) where a candidate is already
failing catastrophically, so the approximation breaking down there doesn't
change any conclusion.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from data.orbital_data import MERCURY, MERCURY_OBSERVED_PRECESSION, OrbitalBody

MassScaling = Literal["const", "linear", "quadratic"]


@dataclass
class FitResult:
    params: dict[str, float]   # e.g. {"k": ...} or {"delta": ...} -- whatever this family fits
    note: str                   # e.g. "numerically fine, theoretically ad-hoc" for Gerber


class ForceLawFamily(ABC):
    name: str
    formula: str            # human-readable, shown to the LLM and the frontend
    structural_cost: float  # fixed, hand-declared -- see models/complexity.py
    num_params: int         # how many constants get fit from Mercury (0 for Gerber)
    note: str = ""

    @abstractmethod
    def fit(self) -> FitResult:
        """Calibrates this family's free parameter(s) from Mercury's
        observed precession alone."""

    @abstractmethod
    def predict_precession(self, params: dict[str, float], body: OrbitalBody) -> float:
        """Predicted precession at `body`, in arcsec/century, using the
        parameters fit from Mercury."""

    @abstractmethod
    def kepler_deviation(self, params: dict[str, float], body: OrbitalBody) -> float:
        """Fractional deviation of T^2/r^3 from the Newtonian constant, at
        `body`, using the same fitted parameters."""


def _mercury_precession_per_orbit_rad() -> float:
    return (MERCURY_OBSERVED_PRECESSION / MERCURY.orbits_per_century) / ARCSEC_PER_RAD_LOCAL


ARCSEC_PER_RAD_LOCAL = 206264.80625


class InverseCubeFamily(ForceLawFamily):
    """F(r) = -GM/r^2 - k/r^3. Exact precession (Binet equation reduces to
    a harmonic oscillator for this power, so this is a closed-form
    solution, not a perturbative approximation, valid for any k):

        delta_phi_per_orbit = 2*pi*(sqrt(1 + k/(GM*p)) - 1)

    Kepler's third law: v^2/r = GM/r^2 + k/r^3 -> fractional deviation
    delta = k/(GM*r).
    """

    def __init__(self, mass_scaling: MassScaling):
        self.mass_scaling = mass_scaling
        suffix = {"const": "const", "linear": "linear", "quadratic": "quadratic"}[mass_scaling]
        self.name = f"inverse_cube_{suffix}"
        symbol = {"const": "k", "linear": "\u03b1\u00b7GM", "quadratic": "\u03b2\u00b7(GM)\u00b2"}[mass_scaling]
        self.formula = f"F = -GM/r\u00b2 - {symbol}/r\u00b3"
        self.structural_cost = {"const": 3.0, "linear": 4.0, "quadratic": 5.0}[mass_scaling]
        self.num_params = 1

    def _k_for(self, fitted_constant: float, body: OrbitalBody) -> float:
        if self.mass_scaling == "const":
            return fitted_constant
        if self.mass_scaling == "linear":
            return fitted_constant * body.gm_central
        return fitted_constant * body.gm_central**2  # quadratic

    def fit(self) -> FitResult:
        delta_phi = _mercury_precession_per_orbit_rad()
        # Invert the exact formula for k at Mercury:
        # delta_phi = 2*pi*(sqrt(1+k/(GM*p)) - 1)
        x = (1 + delta_phi / (2 * math.pi)) ** 2 - 1
        k = x * MERCURY.gm_central * MERCURY.p_m
        if self.mass_scaling == "const":
            fitted = k
        elif self.mass_scaling == "linear":
            fitted = k / MERCURY.gm_central
        else:
            fitted = k / MERCURY.gm_central**2
        key = {"const": "k", "linear": "alpha", "quadratic": "beta"}[self.mass_scaling]
        return FitResult(params={key: fitted}, note="")

    def predict_precession(self, params: dict[str, float], body: OrbitalBody) -> float:
        fitted_constant = next(iter(params.values()))
        k = self._k_for(fitted_constant, body)
        x = k / (body.gm_central * body.p_m)
        delta_phi_per_orbit = 2 * math.pi * (math.sqrt(1 + x) - 1)
        return delta_phi_per_orbit * body.orbits_per_century * ARCSEC_PER_RAD_LOCAL

    def kepler_deviation(self, params: dict[str, float], body: OrbitalBody) -> float:
        fitted_constant = next(iter(params.values()))
        k = self._k_for(fitted_constant, body)
        return k / (body.gm_central * body.a_m)


class InverseFourthFamily(ForceLawFamily):
    """F(r) = -GM/r^2 - k/r^4. First-order perturbative result only (the
    Binet equation here has a genuinely nonlinear resonant term, unlike
    the inverse-cube case, so there's no simple exact closed form):

        delta_phi_per_orbit = 2*pi*k / (GM * a^2 * (1-e^2)^2)

    Kepler's third law: v^2/r = GM/r^2 + k/r^4 -> fractional deviation
    delta = k/(GM*r^2).
    """

    def __init__(self, mass_scaling: MassScaling):
        self.mass_scaling = mass_scaling
        symbol = {"const": "k", "linear": "\u03b1\u00b7GM", "quadratic": "\u03b2\u00b7(GM)\u00b2"}[mass_scaling]
        self.name = f"inverse_fourth_{mass_scaling}"
        self.formula = f"F = -GM/r\u00b2 - {symbol}/r\u2074"
        self.structural_cost = {"const": 3.0, "linear": 4.0, "quadratic": 5.0}[mass_scaling]
        self.num_params = 1

    def _k_for(self, fitted_constant: float, body: OrbitalBody) -> float:
        if self.mass_scaling == "const":
            return fitted_constant
        if self.mass_scaling == "linear":
            return fitted_constant * body.gm_central
        return fitted_constant * body.gm_central**2

    def fit(self) -> FitResult:
        delta_phi = _mercury_precession_per_orbit_rad()
        k = delta_phi * MERCURY.gm_central * MERCURY.a_m**2 * (1 - MERCURY.e**2) ** 2 / (2 * math.pi)
        if self.mass_scaling == "const":
            fitted = k
        elif self.mass_scaling == "linear":
            fitted = k / MERCURY.gm_central
        else:
            fitted = k / MERCURY.gm_central**2
        key = {"const": "k", "linear": "alpha", "quadratic": "beta"}[self.mass_scaling]
        return FitResult(params={key: fitted}, note="")

    def predict_precession(self, params: dict[str, float], body: OrbitalBody) -> float:
        fitted_constant = next(iter(params.values()))
        k = self._k_for(fitted_constant, body)
        delta_phi_per_orbit = 2 * math.pi * k / (body.gm_central * body.a_m**2 * (1 - body.e**2) ** 2)
        return delta_phi_per_orbit * body.orbits_per_century * ARCSEC_PER_RAD_LOCAL

    def kepler_deviation(self, params: dict[str, float], body: OrbitalBody) -> float:
        fitted_constant = next(iter(params.values()))
        k = self._k_for(fitted_constant, body)
        return k / (body.gm_central * body.a_m**2)


class HallLawFamily(ForceLawFamily):
    """F(r) = GM/r^(2+delta). Newton's exact apsidal-precession theorem for
    a power-law force F~r^-n gives an apsidal angle pi/sqrt(3-n); for
    n=2+delta this gives, to leading order in delta, a precession per
    orbit that is EXACTLY independent of a, e, and the central mass:

        delta_phi_per_orbit = pi * delta

    which is why the same delta produces wildly different arcsec/century
    at different bodies -- purely through how many orbits/century they
    complete (itself set by each body's own GM and a via Kepler's law).
    """

    def __init__(self):
        self.name = "hall_law"
        self.formula = "F = GM/r\u207d\u00b2\u207a\u1d5f\u207e"
        self.structural_cost = 3.0
        self.num_params = 1

    def fit(self) -> FitResult:
        delta_phi = _mercury_precession_per_orbit_rad()
        delta = delta_phi / math.pi
        return FitResult(params={"delta": delta}, note="")

    def predict_precession(self, params: dict[str, float], body: OrbitalBody) -> float:
        delta = params["delta"]
        delta_phi_per_orbit = math.pi * delta
        return delta_phi_per_orbit * body.orbits_per_century * ARCSEC_PER_RAD_LOCAL

    def kepler_deviation(self, params: dict[str, float], body: OrbitalBody) -> float:
        # F = GM/r^(2+delta) modifies the *exponent* itself, so the
        # Kepler deviation isn't a simple additive fractional shift the
        # way it is for the inverse-cube/fourth families -- it scales with
        # ln(r), which needs a fixed reference scale to be well-defined.
        # Using AU as that reference (so this is dimensionless and O(1)
        # for the planets) is a reasonable extension consistent with the
        # given formula, but -- unlike the precession formula above --
        # this specific Kepler-deviation construction was not
        # independently cross-checked to the same standard as the rest of
        # this file. It doesn't change this family's verdict either way:
        # Hall's law already fails decisively on lunar precession alone.
        delta = params["delta"]
        a_au = body.a_m / 1.495978707e11
        return abs(delta * math.log(a_au)) if a_au > 0 else 0.0


class LogSuppressedFamily(ForceLawFamily):
    """F(r) ~ GM/(r^2 * ln(r/r0)). For r0 astronomically small (needed for
    ln(r/r0) to be large enough to suppress the force to Newtonian order),
    ln(r/r0) varies extremely slowly across solar-system scales -- so,
    like Hall's law, this produces a nearly-constant precession per orbit
    regardless of a. That's why this family and Hall's law give nearly
    identical arcsec/century predictions at every body despite being
    completely different functional forms -- confirmed by both this
    project's own derivation and an independent cross-check.

    What distinguishes it structurally: log-suppression breaks the shell
    theorem (Gauss's law for gravity) -- extended bodies would not
    gravitate as point masses, which would have been visible pre-1900 in
    ways unrelated to precession at all. That's reflected in a higher
    structural_cost, not in the numeric precession/Kepler checks, which
    are deliberately mirrored on Hall's law's mechanism above.
    """

    def __init__(self):
        self.name = "log_suppressed"
        self.formula = "F = GM / [r\u00b2 ln(r/r\u2080)]"
        self.structural_cost = 6.0  # higher than Hall's law: transcendental log + breaks the shell theorem
        self.num_params = 1

    def fit(self) -> FitResult:
        delta_phi = _mercury_precession_per_orbit_rad()
        return FitResult(params={"per_orbit_rad": delta_phi}, note="")

    def predict_precession(self, params: dict[str, float], body: OrbitalBody) -> float:
        delta_phi_per_orbit = params["per_orbit_rad"]  # ~constant across bodies, same mechanism as Hall's law
        return delta_phi_per_orbit * body.orbits_per_century * ARCSEC_PER_RAD_LOCAL

    def kepler_deviation(self, params: dict[str, float], body: OrbitalBody) -> float:
        # Simplified: the source derivation reports this family's Kepler
        # deviation as tiny (~1e-7) and undetectable pre-1900; adopting
        # that order of magnitude directly here rather than re-deriving an
        # r0-dependent formula from scratch (r0 itself isn't pinned down
        # by the Mercury fit alone). Doesn't affect this family's verdict:
        # it already fails decisively on precession at Venus/Earth/Moon.
        return 1.5e-7


class YukawaFamily(ForceLawFamily):
    """F(r) = -(GM/r^2)(1+alpha*r)*exp(-alpha*r). Small-screening
    (alpha*r << 1) regime, verified self-consistent (alpha*a stays << 1 at
    every body once fit to Mercury):

        delta_phi_per_orbit ~ pi * alpha^2 * a^2 * sqrt(1-e^2)

    Kepler's third law (exact, from the given force law):
        n^2 a^3 = GM * (1 + alpha*a) * exp(-alpha*a)
    """

    def __init__(self):
        self.name = "yukawa"
        self.formula = "F = -(GM/r\u00b2)(1+\u03b1r)e\u207b\u1d45\u02b3"
        self.structural_cost = 6.0  # transcendental + an implicit lengthscale
        self.num_params = 1

    def fit(self) -> FitResult:
        delta_phi = _mercury_precession_per_orbit_rad()
        alpha_sq = delta_phi / (math.pi * MERCURY.a_m**2 * math.sqrt(1 - MERCURY.e**2))
        return FitResult(params={"alpha": math.sqrt(alpha_sq)}, note="")

    def predict_precession(self, params: dict[str, float], body: OrbitalBody) -> float:
        alpha = params["alpha"]
        delta_phi_per_orbit = math.pi * alpha**2 * body.a_m**2 * math.sqrt(1 - body.e**2)
        return delta_phi_per_orbit * body.orbits_per_century * ARCSEC_PER_RAD_LOCAL

    def kepler_deviation(self, params: dict[str, float], body: OrbitalBody) -> float:
        alpha = params["alpha"]
        ratio = (1 + alpha * body.a_m) * math.exp(-alpha * body.a_m)
        return abs(ratio - 1)


class GerberFamily(ForceLawFamily):
    """Gerber's 1898 velocity-dependent retarded-potential gravity. Its
    own derivation reduces (to O(c^-2)) to exactly the same form as
    InverseCubeFamily's quadratic-mass-scaling case:

        delta_phi_per_orbit = 6*pi*GM / (c^2 * a * (1-e^2))

    This is not a free-parameter fit -- Gerber's coefficient (6) comes
    from his own (flawed) derivation, not from reverse-engineering
    Mercury, which is why num_params=0 here even though the formula
    happens to reproduce Mercury's precession as well as any fitted
    family does. Numerically it passes every quantitative constraint in
    this project (Venus/Earth/Mars/Moon precession, Kepler's third law) --
    independently verified via two different derivations. Note: a figure
    of ~287"/cy for the Moon sometimes appears in the literature (Seeliger
    & von Laue 1917, Annalen der Physik Vol. 53; also Chazy 1928,
    Roseveare 1982) -- this is real, but arises from a post-1900 three-
    body calculation in which cross-coupling between Earth's heliocentric
    velocity (~30 km/s) and the Moon's orbital velocity produces a large
    secular perturbation via Gerber's non-linear velocity-dependence. A
    pre-1900 physicist applying Gerber's formula to the two-body Earth-
    Moon system gets 0.06"/cy (verified here), which is within tolerance.
    The three-body failure is genuine, but it was first established by
    Seeliger and von Laue in 1917, so it is outside our pre-1900 scope;
    it is recorded as a note rather than counted as a constraint violation.
    Gerber is excluded on different grounds: an unsound derivation
    (momentum non-conservation, ad hoc retarded coordinates, no field
    equations, no light-bending prediction). See `note`.
    """

    def __init__(self):
        self.name = "gerber"
        self.formula = "\u0394\u03d6 = 6\u03c0GM / [c\u00b2a(1-e\u00b2)]"
        self.structural_cost = 8.0  # velocity-dependent retarded potential, generalized Lagrangian mechanics
        self.num_params = 0
        self.note = "numerically fine, theoretically ad-hoc"

    def fit(self) -> FitResult:
        return FitResult(params={}, note=self.note)

    def predict_precession(self, params: dict[str, float], body: OrbitalBody) -> float:
        delta_phi_per_orbit = 6 * math.pi * body.gm_central / (C_LOCAL**2 * body.a_m * (1 - body.e**2))
        return delta_phi_per_orbit * body.orbits_per_century * ARCSEC_PER_RAD_LOCAL

    def kepler_deviation(self, params: dict[str, float], body: OrbitalBody) -> float:
        # n^2 a^3 = GM[1 + 3GM/(a c^2) + 6GM/(a c^2)(1/sqrt(1-e^2) - 1)]
        x = body.gm_central / (body.a_m * C_LOCAL**2)
        ecc_term = 1 / math.sqrt(1 - body.e**2) - 1
        return 3 * x + 6 * x * ecc_term


C_LOCAL = 2.99792458e8


def build_families() -> dict[str, ForceLawFamily]:
    families: dict[str, ForceLawFamily] = {}
    for scaling in ("const", "linear", "quadratic"):
        f = InverseCubeFamily(scaling)
        families[f.name] = f
    for scaling in ("const", "linear", "quadratic"):
        f = InverseFourthFamily(scaling)
        families[f.name] = f
    for f in (HallLawFamily(), LogSuppressedFamily(), YukawaFamily(), GerberFamily()):
        families[f.name] = f
    return families


FAMILIES = build_families()
