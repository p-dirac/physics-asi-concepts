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
explicit about where the actual boundary is.

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
   would mean either building a serious symbolic-AI research system or trusting LLM-generated code
   enough to execute it, which this project deliberately doesn't do.


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


### Why `overall_score` is always negative

It's built as "start from a hypothetical perfect 0 and subtract
penalties." Every real family has `complexity_score > 0` (nothing has zero
structure), so `overall_score` is mathematically always below zero — 0 is
a ceiling no family can reach, not a typical value. This is the same
convention as negative-loss or log-likelihood in ML: you maximize toward
zero rather than toward some positive "good" number. 


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
  the agent only starts proposing changes from iteration 1 onward. 
  - The plateau/stop condition compares each iteration against the **best
  overall_score found so far in the run**, not the immediately preceding
  iteration. 
- **Repetition is prevented in code, not just requested in the prompt.**
  Now every proposal is checked against the run's history, and if
  it names something already tried while untried families remain, it's
  deterministically redirected to the untried family with the lowest
  complexity, with the override stated plainly in that round's rationale
  rather than silently substituted. `max_iterations` now
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
