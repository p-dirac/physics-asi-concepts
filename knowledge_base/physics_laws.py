"""
The 'known physics' input to the pipeline: the theoretical framework
already established and trusted circa 1900, before any of the ten
candidate modifications in this project were proposed or tested. This is
real, documented data -- not a stub -- since it genuinely is the input a
physicist (or a real ASI-for-physics system) would have had available.

Newton's laws here are stated as historical fact, not derived -- a real
system that discovers laws from raw data (see AI-Newton,
github.com/Science-Discovery/AI-Newton) would produce something like this
list as *output* of an earlier discovery stage, not as a given input.
This project starts one step later: given these laws already established,
which of ten proposed *modifications* to gravitation survives Mercury,
Venus, Earth, Mars, the Moon, and Kepler's third law.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnownLaw:
    name: str
    statement: str
    year_established: int
    mathematical_form: str


NEWTONS_LAWS_OF_MOTION = KnownLaw(
    name="Newton's Laws of Motion",
    statement=(
        "An object's motion changes only in response to a net force; "
        "force equals mass times acceleration; every action has an equal "
        "and opposite reaction."
    ),
    year_established=1687,
    mathematical_form="F = ma",
)

NEWTONS_LAW_OF_GRAVITATION = KnownLaw(
    name="Newton's Law of Universal Gravitation",
    statement=(
        "Every point mass attracts every other point mass with a force "
        "proportional to the product of their masses and inversely "
        "proportional to the square of the distance between them. This "
        "is the baseline every candidate in models/families.py modifies."
    ),
    year_established=1687,
    mathematical_form="F = GMm/r\u00b2",
)

KEPLERS_FIRST_LAW = KnownLaw(
    name="Kepler's First Law",
    statement="Planets move in ellipses with the Sun at one focus.",
    year_established=1609,
    mathematical_form="r(\u03b8) = p / (1 + e\u00b7cos\u03b8)",
)

KEPLERS_SECOND_LAW = KnownLaw(
    name="Kepler's Second Law",
    statement="A line joining a planet and the Sun sweeps out equal areas in equal times.",
    year_established=1609,
    mathematical_form="dA/dt = constant",
)

KEPLERS_THIRD_LAW = KnownLaw(
    name="Kepler's Third Law",
    statement=(
        "The square of a planet's orbital period is proportional to the "
        "cube of its semi-major axis. This project checks every candidate "
        "against how much it would have distorted this exact relationship."
    ),
    year_established=1619,
    mathematical_form="T\u00b2 \u221d a\u00b3",
)

ALL_KNOWN_LAWS: list[KnownLaw] = [
    NEWTONS_LAWS_OF_MOTION,
    NEWTONS_LAW_OF_GRAVITATION,
    KEPLERS_FIRST_LAW,
    KEPLERS_SECOND_LAW,
    KEPLERS_THIRD_LAW,
]
