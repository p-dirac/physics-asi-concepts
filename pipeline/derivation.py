"""
Stub steps standing in for the parts of a genuine ASI-for-physics system
this project deliberately does NOT implement: symbolically deriving a
perturbation equation from a proposed force-law modification, and
generating code to solve that equation numerically.

Why these are stubs, not real implementations, in two parts:

1. derive_perturbation_equation is an ABDUCTIVE step -- given a new force
   law, propose which mathematical machinery (which substitution, which
   approximation) turns it into a solvable equation. Tom Zahavy's "LLMs
   Can't Jump" argues current LLMs are reasonably capable at induction
   (fitting patterns in existing data) and increasingly capable at
   deduction (proving a result from given axioms), but structurally lack
   reliable abduction -- proposing a genuinely new explanatory axiom that
   isn't implied by what's already there. That is exactly the leap this
   project's own agent/llm.py does NOT attempt: propose_family chooses
   among ten pre-derived candidates (a constrained selection problem), it
   never invents an eleventh. Actually deriving a new perturbation
   equation for a genuinely novel force law is the harder, different
   capability this stub marks the absence of.

2. AI-Newton (Fang et al., github.com/Science-Discovery/AI-Newton) tackles
   a substantially harder version of this same territory: discovering the
   concepts and laws themselves from raw experimental data, with no prior
   physical knowledge at all, via a symbolic knowledge base and a
   physics-specific domain language. It's a serious multi-year research
   system. Reimplementing any real fraction of it is out of scope for a
   demo whose actual point is showing the SHAPE of the full pipeline.

Every closed-form formula this project actually uses (see
models/families.py) was hand-derived once, offline, using the tools in
knowledge_base/mathematical_tools.py, and cross-checked against
independent derivations before being trusted (see the README's
verification history). These stubs exist so that fact is visible in the
running code path -- called at exactly the point a real derive-then-code
pipeline would run -- rather than left as something the reader has to
take on faith from a comment.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DerivedEquation:
    """What a real symbolic-derivation step would produce: e.g. a
    Binet-equation perturbation series, an apsidal-angle expression, or a
    closed-form precession formula, for a force law nobody has derived by
    hand yet. See models/families.py's docstrings for what these actually
    look like when a human (or the independent AI cross-checks documented
    in the README) does this derivation for real."""
    symbolic_form: str
    method: str


@dataclass(frozen=True)
class GeneratedSolver:
    """What a real code-generation step would produce: executable code
    implementing the derived equation numerically, generated fresh rather
    than hand-written. This project's actual `predict_precession` and
    `kepler_deviation` methods are the hand-written equivalent of what
    this class would represent if produced automatically."""
    source_code: str
    language: str = "python"


def derive_perturbation_equation(family_name: str, force_law_formula: str) -> Optional[DerivedEquation]:
    """
    STUB -- does not derive anything. See this module's docstring for why.

    In a real pipeline, this is where a proposed force-law modification
    (e.g. "F = -GM/r\u00b2 - k/r\u00b3") would be turned into a symbolic
    perturbation equation -- the abductive step of deciding which
    mathematical machinery applies. Called here at exactly the point a
    real system would call it, immediately after a family is chosen and
    before it's evaluated, so the pipeline's shape is visible even though
    this step does no real work. The caller (see
    models/evaluate.py:ForceLawEvaluator.evaluate) proceeds using the
    hand-derived, independently cross-checked formula already built into
    the family, exactly as if this had produced it.
    """
    pass


def generate_solving_code(derived_equation: Optional[DerivedEquation]) -> Optional[GeneratedSolver]:
    """
    STUB -- does not generate anything. See this module's docstring for why.

    This step is closer to something current LLMs can do reasonably well
    (translating a known closed-form expression into code is closer to
    deduction/translation than the abductive leap in
    derive_perturbation_equation above) -- but there is no derived
    equation to translate, since that step is also a stub, so this
    function has nothing real to act on either. A genuine implementation
    would plug into an LLM code-generation call the same way
    agent/llm.py's propose_family already calls Ollama -- but generating
    NOVEL, correct numerical code is a materially harder and riskier
    capability than selecting a name from a fixed menu, and any real
    version of this step would need to execute its output in a sandboxed
    environment before trusting it, never directly.
    """
    pass
