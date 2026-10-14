"""
The single entry point agent/graph.py's evaluate_node calls into.

Accuracy here is fundamentally different from the old curve-fitting
version of this project: there's no held-out RMSE, because there's no
noisy sample to hold out. Instead, a family is fit from Mercury's single
observed data point, then checked against four *structurally different*
held-out constraints (Venus/Earth/Mars/Moon precession) plus Kepler's
third law -- much closer to the actual historical test.

Precession violations are in arcsec/century; Kepler violations are
dimensionless fractions. Those aren't directly comparable, so each
constraint's excess-over-tolerance is normalized by its own tolerance
before summing -- "1.0" always means "exactly at the edge of what 19th-
century precision could have detected," regardless of which constraint or
which units it's measured in.

This is also where the pipeline's two stub stages get called (see
pipeline/derivation.py for why they're stubs, not real implementations):
immediately after a family is fit, a real derive-then-generate-code
pipeline would symbolically derive the perturbation equation and write
code to solve it, *before* any of the checks below could run. Both calls
happen here, at exactly that point, and both return nothing usable --
this project proceeds using the hand-derived, independently cross-checked
formulas already built into `family` (see models/families.py), exactly as
if a real pipeline had produced them.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from data.orbital_data import KEPLER_THIRD_LAW_TOLERANCE, PRECESSION_TOLERANCE, ObservationDatabase
from models.complexity import DescriptionLengthScorer
from models.families import FAMILIES, ForceLawFamily
from pipeline.derivation import derive_perturbation_equation, generate_solving_code

DEFAULT_COMPLEXITY_WEIGHT = 0.05
# Calibrated the same way as the sibling project's lambda: checked that it
# doesn't let complexity dominate regardless of accuracy. Here the
# accuracy penalty is a normalized-excess sum that's exactly 0 for a
# passing family and grows quickly (into the hundreds or more) for a
# failing one, so complexity only meaningfully breaks ties among
# near-equally-accurate families rather than overriding the accuracy
# signal -- see evaluate() below.


@dataclass
class ConstraintCheck:
    body: str
    predicted: float
    tolerance: float
    normalized_excess: float  # 0 if within tolerance, grows from there


@dataclass
class EvaluationResult:
    family_name: str
    formula: str
    note: str
    params: dict[str, float]
    precession_checks: list[ConstraintCheck]
    kepler_checks: list[ConstraintCheck]
    accuracy_penalty: float     # sum of all normalized excesses; 0 = passes everything
    complexity_score: float
    overall_score: float
    display_score: float       # log10-compressed overall_score, for plotting all families together


class ForceLawEvaluator:
    def __init__(self, complexity_weight: float = DEFAULT_COMPLEXITY_WEIGHT):
        self.complexity_weight = complexity_weight
        self._complexity_scorer = DescriptionLengthScorer()
        self._observations = ObservationDatabase()

    def evaluate(self, family_name: str) -> EvaluationResult:
        family: ForceLawFamily = FAMILIES[family_name]
        fit = family.fit()

        # Pipeline stub stage -- see pipeline/derivation.py and this
        # module's docstring. Neither call's return value is used; they
        # exist so the pipeline's full shape (derive -> generate code ->
        # evaluate) is visible in the actual code path, not just in a
        # comment, even though this project proceeds with its own
        # hand-derived formulas regardless of what these return.
        derived_equation = derive_perturbation_equation(family.name, family.formula)
        generate_solving_code(derived_equation)

        precession_checks = []
        kepler_checks = []
        for body in self._observations.get_validation_bodies():
            predicted = family.predict_precession(fit.params, body)
            tol = PRECESSION_TOLERANCE[body.name]
            precession_checks.append(ConstraintCheck(
                body=body.name, predicted=predicted, tolerance=tol,
                normalized_excess=self._normalized_excess(predicted, tol),
            ))

            deviation = family.kepler_deviation(fit.params, body)
            kepler_checks.append(ConstraintCheck(
                body=body.name, predicted=deviation, tolerance=KEPLER_THIRD_LAW_TOLERANCE,
                normalized_excess=self._normalized_excess(deviation, KEPLER_THIRD_LAW_TOLERANCE),
            ))

        accuracy_penalty = sum(c.normalized_excess for c in precession_checks) + \
            sum(c.normalized_excess for c in kepler_checks)
        complexity_score = self._complexity_scorer.score(family)
        overall_score = -accuracy_penalty - self.complexity_weight * complexity_score
        # accuracy_penalty spans ~13 orders of magnitude across the ten
        # families (0 to ~480 billion) -- log10-compressing it before
        # plotting keeps every family visually distinguishable on one
        # chart, rather than the two catastrophic outliers swallowing the
        # entire axis. Still zero-anchored (0 = unreachable ideal), just
        # on a scale a single bar chart can actually show.
        display_score = -math.log10(1 + accuracy_penalty) - self.complexity_weight * complexity_score

        return EvaluationResult(
            family_name=family.name,
            formula=family.formula,
            note=fit.note,
            params=fit.params,
            precession_checks=precession_checks,
            kepler_checks=kepler_checks,
            accuracy_penalty=round(accuracy_penalty, 6),
            complexity_score=complexity_score,
            overall_score=round(overall_score, 6),
            display_score=round(display_score, 6),
        )

    @staticmethod
    def _normalized_excess(predicted: float, tolerance: float) -> float:
        return max(0.0, (abs(predicted) - tolerance) / tolerance)
