"""
Shared state for the model-selection RSI loop. Structurally similar to the
sibling RSI gridworld project's agent/state.py, but the accuracy metric is
fundamentally different: there's no held-out RMSE here, because there's no
noisy sample to hold out. accuracy_penalty is a sum of normalized
constraint violations across Venus/Earth/Mars/Moon precession and Kepler's
third law -- zero means the family passes every historical constraint.
"""
from typing import Optional, TypedDict

from agent.run_log import new_run_log_path


class Config(TypedDict):
    """The bounded 'DSL': a categorical choice from models.families.FAMILIES
    (ten named force-law candidates), not free-form. The agent picks a
    NAME; it never proposes a functional form of its own."""
    family: str


class Metrics(TypedDict):
    accuracy_penalty: float   # sum of normalized excess-over-tolerance across all constraints; 0 = passes everything
    complexity_score: float   # structural_cost + num_params * bits_per_param
    overall_score: float      # -accuracy_penalty - complexity_weight * complexity_score
    display_score: float      # log10-compressed version of overall_score, for plotting all
                               # families together -- accuracy_penalty spans ~13 orders of
                               # magnitude (0 to ~480 billion) across the ten families, which
                               # would make a linear plot show only "catastrophic or not,"
                               # flattening the real, meaningful differences among the more
                               # plausible candidates. Still zero-anchored and negative (0 is
                               # the unreachable ideal, more negative is worse), just compressed
                               # to a visually usable range (~-0.35 to ~-12 across all ten).


class ConstraintCheckDict(TypedDict):
    body: str
    predicted: float
    tolerance: float
    normalized_excess: float


class BestResult(TypedDict):
    """The best iteration found so far in this run -- tracked explicitly
    rather than derived by re-scanning history each time, and used for
    three things: (1) correctly detecting a genuine plateau (see
    reflect_node -- comparing each iteration only to the one immediately
    before it let the agent oscillate back to a known-good family forever
    without ever tripping the stop condition, since "better than the
    previous, worse, iteration" kept resetting the counter even when nothing
    new was being found), (2) giving propose_node a fixed, reliable
    reference point instead of hoping RAG retrieval happens to surface the
    best past attempt, and (3) letting the frontend show a 'best result'
    view that never regresses, separate from the live 'latest attempt' view.
    """
    iteration: int
    family: str
    formula: str
    note: str
    metrics: Metrics
    precession_checks: list[ConstraintCheckDict]
    kepler_checks: list[ConstraintCheckDict]


class HistoryEntry(TypedDict):
    iteration: int
    config: Config
    metrics: Metrics
    reflection: str


class MDLState(TypedDict):
    iteration: int
    max_iterations: int

    config: Config
    metrics: Metrics

    # Populated by evaluate_node so the FastAPI layer can return the
    # per-body constraint breakdown without evaluate_node needing to know
    # anything about HTTP.
    formula: str
    note: str                                   # e.g. "numerically fine, theoretically ad-hoc" for Gerber
    fit_params: dict[str, float]
    precession_checks: list[ConstraintCheckDict]
    kepler_checks: list[ConstraintCheckDict]

    history: list[HistoryEntry]
    retrieved: list[str]

    proposal_raw: Optional[str]
    reflection: Optional[str]

    plateau_count: int
    should_continue: bool

    run_log_path: str   # where store_node appends this run's iterations (see agent/run_log.py)
    best_result: Optional[BestResult]   # None until the first iteration completes


def initial_state(max_iterations: int = 10, starting_family: str = "hall_law") -> MDLState:
    return MDLState(
        iteration=0,
        max_iterations=max_iterations,
        config=Config(family=starting_family),
        metrics=Metrics(
            accuracy_penalty=float("inf"), complexity_score=0.0,
            overall_score=float("-inf"), display_score=float("-inf"),
        ),
        formula="",
        note="",
        fit_params={},
        precession_checks=[],
        kepler_checks=[],
        history=[],
        retrieved=[],
        proposal_raw=None,
        reflection=None,
        plateau_count=0,
        should_continue=True,
        run_log_path=new_run_log_path(),
        best_result=None,
    )
