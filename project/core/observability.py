"""
Observability & Logging
Tracks trace IDs, execution timings, and structured JSON logs
for every step taken by the multi-agent system.
"""

import json
import time
import uuid
from datetime import datetime, timezone


class TraceLogger:
    """
    Collects structured execution logs for a single trace (i.e. a
    single end-to-end user request flowing through the agent system).
    """

    def __init__(self, trace_id: str = None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.logs = []

    def _timestamp(self):
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def start_step(self, step_name: str):
        entry = {
            "trace_id": self.trace_id,
            "step": step_name,
            "start_time": time.time(),
            "start_ts": self._timestamp(),
        }
        self.logs.append(entry)
        return entry

    def end_step(self, entry: dict, extra: dict = None):
        entry["end_time"] = time.time()
        entry["end_ts"] = self._timestamp()
        entry["latency_ms"] = round((entry["end_time"] - entry["start_time"]) * 1000, 2)
        if extra:
            entry.update(extra)
        return entry

    def log_event(self, step_name: str, **kwargs):
        """Log a one-shot event without separate start/end calls."""
        entry = {
            "trace_id": self.trace_id,
            "step": step_name,
            "timestamp": self._timestamp(),
        }
        entry.update(kwargs)
        self.logs.append(entry)
        return entry

    def get_logs(self):
        return self.logs

    def to_json(self, indent: int = 2):
        return json.dumps(self.logs, indent=indent, default=str)


def new_trace_logger() -> TraceLogger:
    return TraceLogger()
