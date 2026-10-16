# Physics ASI Concepts

This app recreates an
actual historical episode: in the late 1800s, astronomers (Newcomb, Hall,
Seeliger) tried to explain Mercury's anomalous perihelion precession
(43″/century, unexplained by Newtonian perturbations from other planets)
by modifying Newton's law of gravity. Any proposed fix had to survive a
harder test than just fitting Mercury: applied to Venus, Earth, Mars, and
the Moon, did it predict precessions nobody had observed? Did it distort
Kepler's third law beyond what was already measured precisely?

A LangGraph agent plays this game: each round it picks one of ten
candidate modifications to gravity, fits its single free parameter to
Mercury exactly, and finds out whether that same fit survives everywhere
else. It remembers past attempts via RAG(Retrieval-Augmented Generation) so it doesn't re-propose a family
it's already ruled out.

For the complete project description and installation instructions, please read:
    'docs/Physics-ASI-Concepts.pdf'

## Framing: this is a meta-level task, not an in-environment one


- **Meta-level algorithmic choice task** (this project): the agent
  chooses *between qualitatively different hypotheses* to explain a
  dataset — not "how many terms of the same expansion" but "which
  mathematical machinery entirely." Newton's inverse-square law and
  Einstein's field equations aren't the same family at different
  polynomial orders; recognizing that a problem needs different machinery,
  not just better-tuned parameters, is a harder and more ASI-relevant
  capability.

Is this simulating artificial superintelligence? No, and this project is
explicit about where the actual boundary is (see "What's real, what's a
documented stub" below). `propose_family` chooses among ten pre-derived
candidates — a constrained *selection* problem. It never invents an
eleventh. Tom Zahavy's "LLMs Can't Jump" (Zahavy, 2026) argues current
LLMs are reasonably capable at induction (fitting patterns in existing
data) and increasingly capable at deduction (proving results from given
axioms), but structurally lack reliable **abduction** — proposing a
genuinely new explanatory axiom that isn't implied by what's already
there, the way Einstein's elevator thought-experiment produced the
Equivalence Principle with no supporting dataset. Actually deriving a new
perturbation equation for a force law nobody has analyzed yet *would* be
that abductive leap. This project doesn't attempt it — see
`pipeline/derivation.py`.

*Counterpoint, worth knowing before treating this as settled:* Zahavy's
claim is specifically that Einstein's own path to General Relativity was
abductive, not that abduction is the *only* path to the same result.
Yong Zheng-Xin's response, "Hot Take: LLM can jump," grants that premise
but argues it doesn't follow that LLMs can't jump in general — he points
to Richard Feynman's largely deductive reconstruction of General
Relativity (starting from special relativity plus the requirement that
gravity be mediated by a massless spin-2 field, then imposing
consistency constraints until the full nonlinear Einstein equations fall
out — see Di Mauro, Esposito & Naddeo, "A look inside Feynman's route to
gravitation," 2021) as a counterexample: a different, far less embodied
route to the same theory. Zheng-Xin's broader argument is that as an
LLM's cross-domain knowledge gets denser, more of what looks like
abduction collapses into deduction over an interconnected knowledge
graph. That matters here specifically because `derive_perturbation_equation`'s
actual job — deriving the perturbation equation *for a given, already-
specified force law* — is arguably closer to Feynman's consistency-driven
synthesis than to Einstein's embodied abduction from zero prior axioms.
This project still treats the step as out of scope (see
`pipeline/derivation.py`), but on the narrower, more defensible grounds
that the derivations were done and cross-checked by hand rather than
trusted to an unverified LLM output — not on the stronger claim that an
LLM could never do this in principle.

## What's real, what's a documented stub

This project distinguishes three kinds of code, on purpose, rather than
blurring them:

1. **Real, working input** — `knowledge_base/` (Newton's laws, Kepler's
   laws, the mathematical tools — calculus, perturbation theory, the
   Binet equation — actually available circa 1900) and
   `data/orbital_data.py`'s `ObservationDatabase` (the real measured
   orbital elements and Mercury's real observed precession). These are
   genuinely what a pre-1900 physicist had access to, not placeholders.
2. **Real, working search** — the LangGraph loop, the ten hand-derived
   (and independently cross-checked) formulas in `models/families.py`,
   and the multi-constraint evaluator. This is the part that actually
   runs and produces the correct answer.
3. **Documented stubs** — `pipeline/derivation.py`'s
   `derive_perturbation_equation` and `generate_solving_code`. These are
   real function calls, made at exactly the point a full derive-then-
   generate-code pipeline would make them (see `models/evaluate.py`), but
   their bodies are `pass`. They exist so the *shape* of a genuine
   ASI-for-physics pipeline is visible in running code, not just claimed
   in a comment — while being explicit that actually implementing them
   would mean either building a serious symbolic-AI research system (see
   AI-Newton, github.com/Science-Discovery/AI-Newton — which claims to discover
   physical concepts and laws from raw data with no prior physical
   knowledge at all, a substantially harder and different problem than
   this project's fixed-menu selection) or trusting LLM-generated code
   enough to execute it, which this project deliberately doesn't do.

A related mapping, for readers coming from RSI/MDP vocabulary: this
project's `overall_score = -accuracy_penalty - complexity_weight *
complexity_score` already *is* a reward function trading off performance
against complexity, and `max_iterations` already functions as a compute
budget — the anti-repetition guard (see below) and the plateau-stop
condition are what force convergence, playing the same role a formal
compute-budget-in-the-state-space would in a more elaborate MDP (Markov Decision Process)
formulation. This project doesn't implement a separate formal MDP layer
on top, because the existing mechanism already does that job and adding
one wouldn't change what the demo teaches — but the correspondence is
worth knowing if you're comparing this against that kind of design.

## The ten gravity model candidates

- **inverse_cube × 3 mass-scalings** (`F = -GM/r² - k/r³`, with k constant,
  k∝GM, or k∝(GM)²) — only the (GM)² scaling survives every constraint.
  It's not a coincidence: fit to Mercury, it reduces to exactly the GR
  weak-field precession formula `6πGM/[c²a(1-e²)]`.
- **inverse_fourth × 3 mass-scalings** — the (GM)² scaling resolves the
  worst lunar and terrestrial-surface-gravity problems, but its radial
  falloff (∝1/p^3.5) is steeper than the correct pattern (∝1/p^2.5), so it
  under-predicts Venus/Earth/Mars and sits only marginally within the
  lunar tolerance. A clean example of "passes some constraints, still
  wrong."
- **hall_law** (`F ∝ r^-(2+δ)`) and **log_suppressed**
  (`F ∝ 1/[r²ln(r/r₀)]`) — mathematically unrelated formulas that turn out
  to make *numerically identical* precession predictions at every body
  (confirmed directly, not assumed). Both fail badly on lunar precession;
  log_suppressed additionally breaks the shell theorem (Gauss's law),
  reflected in a higher structural cost rather than the numeric checks.
- **yukawa** (`F = -(GM/r²)(1+αr)e^-αr`) — fit to Mercury, the implied
  screening length turns out to be ~958 AU, in a regime where precession
  *grows* with distance instead of shrinking. Fails Venus/Earth/Mars badly
  in the wrong direction; passes the Moon only because it's close-in, for
  the opposite reason it fails everywhere else.
- **gerber** — an 1898 velocity-dependent "retarded potential" theory.
  Numerically indistinguishable from the correct inverse-cube/(GM)² case
  (same formula, arrived at via unsound physics: violates momentum
  conservation, no field equations, no light-bending prediction). It's
  the one candidate the constraint battery alone can't rule out — labeled
  `"numerically fine, theoretically ad-hoc"` rather than penalized
  numerically for something it doesn't actually get wrong.

## How this was verified (worth knowing before you trust any of it)

Every formula in `models/families.py` was cross-checked against
independent derivations before being trusted.


See
`models/families.py`'s docstrings for the formula-by-formula reasoning,
including which formulas are exact closed-form solutions (inverse-cube,
from a Binet equation that reduces to a harmonic oscillator for this
specific power) versus first-order perturbative approximations
(inverse-fourth, Yukawa) that would break down outside the regimes tested
here.

## Scoring

Unlike the sibling curve-fitting-style Minimum Description Length (MDL) demos, there's no held-out
noisy sample here — Mercury is a single exact calibration point, and the
"held-out set" is four *structurally different* constraints (Venus,
Earth, Mars, Moon precession) plus Kepler's third law. Precession
violations are in arcsec/century; Kepler violations are dimensionless
fractions — not directly comparable, so each constraint's excess-over-
tolerance is normalized by its own tolerance before summing:

```
accuracy_penalty = sum over all 8 checks of max(0, (|predicted| - tolerance) / tolerance)
overall_score = -accuracy_penalty - complexity_weight * complexity_score
```

`accuracy_penalty = 0` means a family passes every single constraint.
Only `inverse_cube_quadratic` and `gerber` achieve this — and
`inverse_cube_quadratic` wins the tie-break on complexity alone (7.0 vs
Gerber's 8.0, reflecting Gerber's more exotic velocity-dependent
machinery), which is the actual point of including Gerber at all: two
theories can be observationally indistinguishable, and MDL-style
reasoning gives a principled (if not decisive on its own) reason to
prefer the less ad-hoc one.

### Why `overall_score` is always negative

It's built as "start from a hypothetical perfect 0 and subtract
penalties." Every real family has `complexity_score > 0` (nothing has zero
structure), so `overall_score` is mathematically always below zero — 0 is
a ceiling no family can reach, not a typical value. This is the same
convention as negative-loss or log-likelihood in ML: you maximize toward
zero rather than toward some positive "good" number. The best family here
(`inverse_cube_quadratic`) scores -0.35, which is *entirely* its
complexity penalty (0.05 × 7) — its accuracy penalty is exactly 0.

### Why the chart plots `display_score`, not `overall_score`

`accuracy_penalty` has a floor of 0 but no ceiling, and across the ten
families it spans about 13 orders of magnitude (0 up to ~482 billion,
because a family whose predicted lunar precession is astronomically large
contributes an astronomically large penalty). Plotting `overall_score`
linearly would let the two catastrophic outliers consume the whole axis,
squashing every meaningful difference among the plausible candidates
(`inverse_fourth_quadratic`, `yukawa`, `hall_law`) into an indistinguishable
sliver. So the chart plots a log-compressed version instead:

```
display_score = -log10(1 + accuracy_penalty) - complexity_weight * complexity_score
```

This is the standard treatment for heavy-tailed data: it preserves the
ranking exactly (log is monotonic) and keeps every family visually
distinguishable, compressing the full spread to roughly -0.35 to -11.9.
It's still zero-anchored — 0 remains the unreachable ideal and more
negative is worse — which is why the bar chart hangs bars *downward* from a
zero baseline and labels it "0 = best ↑". One thing it deliberately does
not do is rescale to 0–100: that would need an arbitrary choice of "worst
case" reference point, and a relative rescale would shift every time a
different set of families was plotted, making figures from different runs
non-comparable. `overall_score` itself is unchanged and still drives the
agent's decisions; `display_score` exists purely for plotting.

| family | accuracy_penalty | overall_score | display_score |
|---|---|---|---|
| inverse_cube_quadratic | 0 | -0.35 | -0.35 |
| gerber | 0 | -0.40 | -0.40 |
| inverse_fourth_quadratic | 3.35 | -3.70 | -0.99 |
| yukawa | 42.7 | -43.1 | -2.04 |
| hall_law | 70.2 | -70.4 | -2.10 |
| log_suppressed | 70.2 | -70.6 | -2.25 |
| inverse_cube_linear | 10,017 | -10,017 | -4.30 |
| inverse_fourth_linear | 1.45 million | -1.45 million | -6.46 |
| inverse_cube_const | 1.69 billion | -1.69 billion | -9.48 |
| inverse_fourth_const | 482.7 billion | -482.7 billion | -11.93 |

## Requirements

- Python 3.13, Node.js 18+
- [Ollama](https://ollama.com) running locally, with:
  ```
  ollama pull qwen2.5:7b
  ollama pull nomic-embed-text
  ```

## Setup

```
pip install -r requirements.txt
cd frontend && npm install
```

## Running

```
ollama serve                              # if not already running
uvicorn backend.main:app --reload --port 8001
cd frontend && npm run dev                # opens on :5174
```

## Project layout

```
knowledge_base/  Real, documented pre-1900 physics laws and math tools --
                 the "known theory + known math" input to the pipeline
data/        Real orbital data (Mercury/Venus/Earth/Mars/Moon) behind
             ObservationDatabase, physical constants, and historical
             precession/Kepler tolerances -- the "observational" input
pipeline/    Documented STUBS for the derivation/code-generation stages a
             full ASI-for-physics system would need (see above) -- called
             at the right point in the code path, but do no real work
models/      The ten ForceLawFamily classes, complexity scoring, and the
             ForceLawEvaluator facade (fit from Mercury, check everywhere else)
agent/       LangGraph loop, Ollama proposal calls, LanceDB-backed memory
backend/     FastAPI: synchronous + SSE streaming run endpoints
frontend/    React dashboard: per-body constraint table, metrics charts,
             iteration log, and reference panels for the orbital data,
             candidate families, and known physics/math
```

## Notes

- `lancedb/` is created on first run and gitignored — delete it to reset
  the agent's memory.
- `logs/runs/run_<timestamp>.jsonl` is written for every run — one JSON
  line per completed iteration (config, metrics, reflection). This is
  independent of both the frontend's in-memory state (lost on refresh) and
  the agent's RAG memory (which stores free-text summaries for retrieval,
  not a structured, replayable record) — it's the place to look for a
  permanent, inspectable record of what a run actually did.
- Iteration 0 evaluates whatever `starting_family` you select directly —
  the agent only starts proposing changes from iteration 1 onward. This
  wasn't always true: earlier, the agent's first proposal ran *before*
  anything was evaluated, so the selected starting family was only ever a
  seed for that first proposal, not something that was guaranteed to
  actually get evaluated.
- The plateau/stop condition compares each iteration against the **best
  overall_score found so far in the run**, not the immediately preceding
  iteration. This matters more than it sounds: comparing only to the
  previous iteration let the agent oscillate forever between a
  known-good family and worse ones without ever tripping the stop
  condition, because returning to the good family after a bad one always
  looked like "improvement" relative to that one bad round — confirmed
  directly from a real run that started already at the optimum
  (`inverse_cube_quadratic`, accuracy_penalty=0) and kept wandering away
  from it. The best result found is tracked explicitly (`best_result`,
  surfaced in its own frontend panel, separate from "Latest attempt" which
  shows whatever the current iteration is, even mid-regression) and also
  handed directly to the LLM's prompt each round, rather than relying on
  RAG retrieval to happen to surface it.
- **Repetition is prevented in code, not just requested in the prompt.**
  An earlier version only told the LLM which families were already tried
  and asked it not to repeat them — that wasn't reliable in practice: a
  real run showed qwen2.5:7b repeating already-tried, already-bad families
  anyway. Now every proposal is checked against the run's history, and if
  it names something already tried while untried families remain, it's
  deterministically redirected to the untried family with the lowest
  complexity, with the override stated plainly in that round's rationale
  rather than silently substituted. Stress-tested against a simulated
  model that *always* tries to repeat the same two families: zero repeats
  resulted across 9 iterations, all handled by the redirect. A genuine
  repeat (normally of the best family) is only ever allowed once every
  single family has been tried at least once. `max_iterations` now
  defaults to 10 (one per family) so a default run can show the whole
  menu exactly once with this guarantee in place.
- All physical constants (GM_sun, GM_earth, c, AU) and orbital elements
  are real, current values, not rounded for convenience.

## References

- Zahavy, T. "Position: LLMs can't jump." *Proceedings of the 43rd
  International Conference on Machine Learning*, PMLR 306, 2026.
- Zheng-Xin, Y. "Hot Take: LLM can 'jump'." 2026. (Response to Zahavy,
  above — see the counterpoint note earlier in this README.)
- Di Mauro, M., Esposito, S., and Naddeo, A. "A look inside Feynman's
  route to gravitation." *WSPC Proceedings*, 2021. arXiv:2111.00333.
- Seeliger, H. and von Laue, M. *Annalen der Physik*, Vol. 53, 1917,
  pp. 31–32 and 214–216.
- Chazy, J. 1928; Roseveare, N.T. 1982 — later confirmations of the
  Seeliger/von Laue three-body result (see the Gerber note above).
