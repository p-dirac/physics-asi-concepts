"""
Complexity for a force-law family: structural_cost (fixed per family, see
models/families.py docstrings for the reasoning behind each number) plus
num_params * bits_per_param. Gerber is the interesting edge case: zero
fitted parameters (its coefficient is theoretically derived, not reverse-
engineered from Mercury) but a high structural_cost, reflecting that
"simple in parameter count" and "simple machinery" are different axes --
exactly the distinction this whole redesign was built to capture.
"""
from __future__ import annotations

from models.families import ForceLawFamily

BITS_PER_PARAM = 2.0


class DescriptionLengthScorer:
    def __init__(self, bits_per_param: float = BITS_PER_PARAM):
        self.bits_per_param = bits_per_param

    def score(self, family: ForceLawFamily) -> float:
        return family.structural_cost + family.num_params * self.bits_per_param
