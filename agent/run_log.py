"""
Persists each run's iteration history to a JSONL file on disk, separate
from both the frontend's in-memory state (lost on refresh) and the
agent's RAG memory (LanceDB stores free-text summaries for retrieval, not
a structured, replayable record). One file per run, named by start time,
so concurrent or repeated runs never interleave in the same file.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

LOG_DIR = Path("logs/runs")


def new_run_log_path() -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    return str(LOG_DIR / f"run_{timestamp}.jsonl")


class RunLogger:
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_iteration(self, entry: dict) -> None:
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
