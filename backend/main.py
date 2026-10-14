"""
FastAPI backend for the pre-1900-gravity model-selection demo.
  GET  /api/families        -> the fixed menu of 10 candidate force-law families
  GET  /api/bodies           -> the real orbital data + historical tolerances
  GET  /api/knowledge_base   -> the known physics laws + math tools this
                                 project's formulas were hand-derived from
  POST /api/run              -> runs the full loop, returns everything at once
  GET  /api/run/stream       -> same run, as Server-Sent Events -- one event
                                 per completed iteration, including that
                                 round's full constraint breakdown

Requires a live Ollama server (qwen2.5:7b for proposals, nomic-embed-text
for RAG memory) reachable at Ollama's default localhost:11434.

Run with:
    uvicorn backend.main:app --reload --port 8001
"""
from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.graph import build_graph
from agent.state import initial_state
from data.orbital_data import KEPLER_THIRD_LAW_TOLERANCE, PRECESSION_TOLERANCE, ObservationDatabase
from knowledge_base.mathematical_tools import ALL_KNOWN_MATH_TOOLS
from knowledge_base.physics_laws import ALL_KNOWN_LAWS
from models.families import FAMILIES

app = FastAPI(title="Pre-1900 Gravity Model Selection Demo")

# A different port from the sibling RSI gridworld's frontend (5173), so
# both demos can run side by side without a port clash.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_graph = build_graph()  # compiled once at import time, reused across requests
_observations = ObservationDatabase()


class RunRequest(BaseModel):
    max_iterations: int = 10
    starting_family: str = "hall_law"


def _serialize_entry(entry: dict) -> dict:
    return {
        "iteration": entry["iteration"],
        "config": entry["config"],
        "metrics": entry["metrics"],
        "reflection": entry["reflection"],
    }


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/families")
def get_families() -> dict:
    return {
        name: {
            "formula": f.formula,
            "num_params": f.num_params,
            "structural_cost": f.structural_cost,
            "note": f.note,
        }
        for name, f in FAMILIES.items()
    }


@app.get("/api/bodies")
def get_bodies() -> dict:
    """Real orbital data and historical tolerances -- static context the
    frontend can show alongside a run's results. Served through
    ObservationDatabase rather than importing the raw constants directly,
    so this endpoint reflects the same 'observational input' abstraction
    the evaluator itself uses (see data/orbital_data.py)."""
    mercury = _observations.get_calibration_body()
    return {
        "mercury": {
            "a_au": mercury.a_m / 1.495978707e11,
            "e": mercury.e,
            "observed_precession": _observations.get_calibration_target(),
            "role": "calibration",
        },
        **{
            b.name: {
                "a_au": b.a_m / 1.495978707e11,
                "e": b.e,
                "precession_tolerance": PRECESSION_TOLERANCE[b.name],
                "role": "validation",
            }
            for b in _observations.get_validation_bodies()
        },
        "kepler_third_law_tolerance": KEPLER_THIRD_LAW_TOLERANCE,
    }


@app.get("/api/knowledge_base")
def get_knowledge_base() -> dict:
    """The known physics laws and mathematical tools this project's
    formulas were hand-derived from -- the 'known theory + known math'
    input to the pipeline, alongside the observational input in
    /api/bodies. See knowledge_base/ for why these are real, documented
    data rather than a stub -- unlike the derivation/code-generation
    stages (pipeline/derivation.py), this genuinely is what was available
    circa 1900, not a placeholder for a capability this project skips."""
    return {
        "laws": [
            {
                "name": law.name,
                "statement": law.statement,
                "year_established": law.year_established,
                "mathematical_form": law.mathematical_form,
            }
            for law in ALL_KNOWN_LAWS
        ],
        "math_tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "year_available": tool.year_available,
            }
            for tool in ALL_KNOWN_MATH_TOOLS
        ],
    }


@app.post("/api/run")
def run(request: RunRequest) -> dict:
    final_state = _graph.invoke(
        initial_state(max_iterations=request.max_iterations, starting_family=request.starting_family)
    )
    return {
        "history": [_serialize_entry(e) for e in final_state["history"]],
        "final_family": final_state["config"]["family"],
        "final_formula": final_state["formula"],
        "final_note": final_state["note"],
        "final_precession_checks": final_state["precession_checks"],
        "final_kepler_checks": final_state["kepler_checks"],
        "best_result": final_state["best_result"],
    }


@app.get("/api/run/stream")
def run_stream(max_iterations: int = 10, starting_family: str = "hall_law") -> StreamingResponse:
    def event_generator():
        last_len = 0
        for state in _graph.stream(
            initial_state(max_iterations=max_iterations, starting_family=starting_family),
            stream_mode="values",
        ):
            if len(state["history"]) > last_len:
                last_len = len(state["history"])
                payload = {
                    "type": "iteration",
                    **_serialize_entry(state["history"][-1]),
                    "formula": state["formula"],
                    "note": state["note"],
                    "precession_checks": state["precession_checks"],
                    "kepler_checks": state["kepler_checks"],
                    "best_result": state["best_result"],
                }
                yield f"data: {json.dumps(payload)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
