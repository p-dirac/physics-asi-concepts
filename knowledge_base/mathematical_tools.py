"""
The 'known math' input to the pipeline: the mathematical machinery
available circa 1900 that a derivation step (see pipeline/derivation.py)
would draw on. Real, documented data -- these are genuinely the tools
Newcomb, Hall, and Seeliger had available, not a stub. Every closed-form
formula in models/families.py was hand-derived using exactly these tools;
this module exists to make that fact explicit and inspectable rather than
leaving it implicit in code comments scattered across ten classes.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnownMathTool:
    name: str
    description: str
    year_available: int


CALCULUS = KnownMathTool(
    name="Differential and Integral Calculus",
    description=(
        "Newton and Leibniz's calculus, giving the derivatives and "
        "integrals needed to go from a force law to an orbit at all."
    ),
    year_available=1687,
)

DIFFERENTIAL_EQUATIONS = KnownMathTool(
    name="Ordinary Differential Equations",
    description=(
        "Methods for solving equations relating a function to its "
        "derivatives -- the orbit equation itself is a second-order ODE."
    ),
    year_available=1750,
)

PERTURBATION_THEORY = KnownMathTool(
    name="Perturbation Theory",
    description=(
        "Techniques (Laplace, Lagrange, Poincar\u00e9) for finding "
        "approximate solutions to a system by treating a small additional "
        "term as a correction to an exactly-solvable base system -- "
        "exactly what every family in this project does: treat the "
        "modification to 1/r\u00b2 as a small perturbation to the "
        "exactly-solvable Kepler problem."
    ),
    year_available=1799,
)

BINET_EQUATION = KnownMathTool(
    name="Binet's Equation",
    description=(
        "Rewrites the orbit equation in terms of u=1/r, turning the "
        "two-body problem into a linear ODE in u(\u03b8) for an "
        "inverse-square force -- the actual tool used to hand-derive the "
        "exact inverse-cube precession formula in this project (see "
        "InverseCubeFamily's docstring in models/families.py)."
    ),
    year_available=1811,
)

APSIDAL_PRECESSION_THEOREM = KnownMathTool(
    name="Newton's Apsidal Precession Theorem",
    description=(
        "For a central force F(r) \u221d r^-n, gives the exact apsidal "
        "angle for a nearly-circular orbit as \u03c0/\u221a(3-n) -- used "
        "directly to derive Hall's law's formula in this project (see "
        "HallLawFamily's docstring in models/families.py)."
    ),
    year_available=1687,
)

ALL_KNOWN_MATH_TOOLS: list[KnownMathTool] = [
    CALCULUS,
    DIFFERENTIAL_EQUATIONS,
    PERTURBATION_THEORY,
    BINET_EQUATION,
    APSIDAL_PRECESSION_THEOREM,
]
