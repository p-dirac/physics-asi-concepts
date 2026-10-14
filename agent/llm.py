"""
Thin wrapper around a local Ollama model -- asks it to pick the next
family to try from the fixed menu.

Anti-repetition is enforced in CODE here, not just requested in the
prompt. An earlier version only told the model which family was best via
the prompt and asked it not to repeat already-tried, worse options -- that
turned out not to be reliable: confirmed directly from a real run where
qwen2.5:7b repeated already-tried, already-bad families anyway, despite
the instruction. A 7B local model complying with a soft, conditional
instruction embedded in a longer prompt just isn't something to depend on
for correctness. So now: every already-tried family and its score is
listed explicitly (not left to RAG retrieval to maybe surface), and if the
model's response repeats one of them while untried families remain, the
choice is deterministically redirected to the untried family with the
lowest complexity -- transparently, with the override visible in the
returned rationale, not silently substituted.

Requires: `ollama pull qwen2.5:7b` and Ollama running locally.
"""
from __future__ import annotations

import json

import ollama

from models.families import FAMILIES

MODEL = "qwen2.5:7b"

SYSTEM_PROMPT_TEMPLATE = """You are choosing which historical modification to Newton's law of gravity
best explains Mercury's anomalous perihelion precession, while also
surviving checks against Venus, Earth, Mars, the Moon, and Kepler's third
law -- exactly the test Newcomb, Hall, and Seeliger applied circa 1900.

You may ONLY choose one of these family names: {family_names}
Formulas for reference: {formulas}

Every family is calibrated to Mercury's observed precession exactly (that
part always "fits" by construction) -- what distinguishes them is whether
the SAME fitted parameter also survives being checked against the other
four bodies and Kepler's third law.

Rule: you must try every family at least once before repeating any of
them. You will be given a list of families already tried this run and a
list of families not yet tried -- if the "not yet tried" list is
non-empty, you MUST propose one of those, never one already tried. Only
once every family has been tried at least once may you propose repeating
one (normally the best one found so far).

Respond with ONLY a JSON object, no prose, no markdown fences:
{{"family": "<one of the allowed names>", "rationale": "<one short sentence>"}}
"""


def propose_family(
    current_family: str,
    metrics: dict,
    retrieved_notes: list[str],
    best_result: dict | None,
    tried_families: dict[str, float],
) -> dict:
    """Calls the local LLM and returns a validated family choice.

    Two layers of fallback, both important: if the response can't be
    parsed or names something outside the fixed menu, keep the current
    family rather than crash the loop. If the response names something
    already tried while untried families remain, redirect to the untried
    family with the lowest complexity, rather than trust the model to have
    followed the "try everything once" rule on its own.
    """
    family_names = list(FAMILIES.keys())
    formulas = ", ".join(f"{name}: {f.formula}" for name, f in FAMILIES.items())
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(family_names=family_names, formulas=formulas)

    notes_block = "\n".join(f"- {n}" for n in retrieved_notes) or "(no prior attempts yet)"

    if best_result:
        best_block = (
            f"family={best_result['family']}, "
            f"accuracy_penalty={best_result['metrics']['accuracy_penalty']:.4f}, "
            f"complexity_score={best_result['metrics']['complexity_score']}, "
            f"overall_score={best_result['metrics']['overall_score']:.4f}"
        )
    else:
        best_block = "(none yet -- this is the first iteration)"

    tried_block = "\n".join(
        f"- {name}: overall_score={score:.4f}" for name, score in tried_families.items()
    ) or "(none yet)"
    untried = [name for name in FAMILIES if name not in tried_families]
    untried_block = ", ".join(untried) if untried else "(none -- every family has been tried at least once)"

    user_prompt = f"""Current family: {current_family}
Current metrics: {json.dumps(metrics)}
Best result found so far this run: {best_block}
Already tried this run:
{tried_block}
Not yet tried: {untried_block}
Notes from earlier attempts:
{notes_block}

Propose the next family to try."""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        format="json",
        options={"temperature": 0.7},
    )
    raw = response["message"]["content"]

    try:
        parsed = json.loads(raw)
        family = parsed.get("family")
        rationale = str(parsed.get("rationale", ""))
        if family not in FAMILIES:
            raise ValueError(f"unknown family: {family}")
    except (json.JSONDecodeError, TypeError, ValueError):
        family = current_family
        rationale = "(fallback: could not parse LLM output)"
        raw = raw + "  [PARSE FAILED - used fallback]"

    if family in tried_families and untried:
        original_family = family
        family = min(untried, key=lambda n: (FAMILIES[n].structural_cost, FAMILIES[n].num_params))
        rationale = f"(auto-redirected: model proposed already-tried '{original_family}'; exploring untried '{family}' instead)"

    return {"family": family, "rationale": rationale, "raw": raw}


def summarize_reflection(family: str, metrics: dict, best_so_far_metrics: dict, is_new_best: bool) -> str:
    label = "new best" if is_new_best else "no improvement over best"
    return (
        f"family={family} -> {label} "
        f"(best so far {best_so_far_metrics['overall_score']:.3f} -> this round {metrics['overall_score']:.3f}, "
        f"accuracy_penalty={metrics['accuracy_penalty']:.4f})"
    )
