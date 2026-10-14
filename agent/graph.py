"""
The model-selection RSI loop as a LangGraph StateGraph:

retrieve_node --[iter 0]--> evaluate_node -> reflect_node -> store_node
      |                          ^                               |
      +--[iter > 0]--> propose_node                (loop back) <-+-> END

Iteration 0 evaluates the user's selected starting_family directly,
skipping propose_node -- this matters because before this fix, the LLM's
first proposal ran *before* anything was evaluated, so the family the user
picked in the UI was only ever a seed for that first proposal, not
something that actually got evaluated. Confirmed confusing in practice:
a run started with "inverse_fourth_quadratic" selected showed
"inverse_fourth_const" as iteration 0's family instead. From iteration 1
onward, the agent proposes based on what it just saw, same as before.
"""
from dataclasses import asdict

from langgraph.graph import StateGraph, START, END

from agent import llm
from agent.memory import MDLMemory
from agent.run_log import RunLogger
from agent.state import MDLState

from models.evaluate import ForceLawEvaluator
from models.families import FAMILIES

_memory = MDLMemory()  # one persistent memory, shared across all runs
_evaluator = ForceLawEvaluator()


def retrieve_node(state: MDLState) -> dict:
    query = f"force law family {state['config']['family']}"
    return {"retrieved": _memory.retrieve(query, k=3)}


def propose_node(state: MDLState) -> dict:
    tried_families = {
        entry["config"]["family"]: entry["metrics"]["overall_score"]
        for entry in state["history"]
    }
    result = llm.propose_family(
        state["config"]["family"], dict(state["metrics"]), state["retrieved"],
        state["best_result"], tried_families,
    )
    return {"config": {"family": result["family"]}, "proposal_raw": result["raw"]}


def evaluate_node(state: MDLState) -> dict:
    result = _evaluator.evaluate(state["config"]["family"])
    metrics = {
        "accuracy_penalty": result.accuracy_penalty,
        "complexity_score": result.complexity_score,
        "overall_score": result.overall_score,
        "display_score": result.display_score,
    }
    return {
        "metrics": metrics,
        "formula": result.formula,
        "note": result.note,
        "fit_params": result.params,
        "precession_checks": [asdict(c) for c in result.precession_checks],
        "kepler_checks": [asdict(c) for c in result.kepler_checks],
    }


def reflect_node(state: MDLState) -> dict:
    best_score_so_far = state["best_result"]["metrics"]["overall_score"] if state["best_result"] else float("-inf")
    is_new_best = state["metrics"]["overall_score"] > best_score_so_far + 1e-4

    reflection = llm.summarize_reflection(
        state["config"]["family"], state["metrics"],
        {"overall_score": best_score_so_far}, is_new_best,
    )
    plateau_count = 0 if is_new_best else state["plateau_count"] + 1

    update = {"reflection": reflection, "plateau_count": plateau_count}
    if is_new_best:
        update["best_result"] = {
            "iteration": state["iteration"],
            "family": state["config"]["family"],
            "formula": state["formula"],
            "note": state["note"],
            "metrics": state["metrics"],
            "precession_checks": state["precession_checks"],
            "kepler_checks": state["kepler_checks"],
        }
    return update


def store_node(state: MDLState) -> dict:
    entry = {
        "iteration": state["iteration"],
        "config": state["config"],
        "metrics": state["metrics"],
        "reflection": state["reflection"],
    }
    _memory.store(entry)
    RunLogger(state["run_log_path"]).log_iteration(entry)
    new_iteration = state["iteration"] + 1
    tried_so_far = {h["config"]["family"] for h in state["history"]} | {state["config"]["family"]}
    all_tried = len(tried_so_far) >= len(FAMILIES)
    # Plateau check only applies when all families are exhausted -- while
    # untried families remain the agent should keep exploring, not stop
    # because recent proposals happened to be worse than the current best.
    plateau_stop = all_tried and state["plateau_count"] >= 3
    should_continue = (
        new_iteration < state["max_iterations"]
        and not all_tried      # stop cleanly once every family has been evaluated
        and not plateau_stop
    )
    return {
        "history": state["history"] + [entry],
        "iteration": new_iteration,
        "should_continue": should_continue,
    }


def route_after_retrieve(state: MDLState) -> str:
    # Iteration 0 evaluates the user's actual selection; the agent only
    # starts proposing changes from iteration 1 onward.
    return "evaluate_node" if state["iteration"] == 0 else "propose_node"


def route_after_store(state: MDLState) -> str:
    return "retrieve_node" if state["should_continue"] else END


def build_graph():
    graph = StateGraph(MDLState)
    graph.add_node("retrieve_node", retrieve_node)
    graph.add_node("propose_node", propose_node)
    graph.add_node("evaluate_node", evaluate_node)
    graph.add_node("reflect_node", reflect_node)
    graph.add_node("store_node", store_node)
    graph.add_edge(START, "retrieve_node")
    graph.add_conditional_edges("retrieve_node", route_after_retrieve, {
        "evaluate_node": "evaluate_node",
        "propose_node": "propose_node",
    })
    graph.add_edge("propose_node", "evaluate_node")
    graph.add_edge("evaluate_node", "reflect_node")
    graph.add_edge("reflect_node", "store_node")
    graph.add_conditional_edges("store_node", route_after_store, {
        "retrieve_node": "retrieve_node",
        END: END,
    })
    return graph.compile()
