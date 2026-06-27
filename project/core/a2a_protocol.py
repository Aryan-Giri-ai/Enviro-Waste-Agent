"""
Agent-to-Agent (A2A) Protocol
Defines the standardized JSON message envelope used for all
inter-agent communication within the ENVIRO-WASTE-AGENT system.
"""

import uuid
from datetime import datetime, timezone


REQUIRED_FIELDS = [
    "trace_id",
    "sender",
    "receiver",
    "timestamp",
    "message_type",
    "payload",
]

VALID_MESSAGE_TYPES = {"request", "response", "error"}


def new_trace_id() -> str:
    """Generate a new unique trace identifier."""
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_message(trace_id, sender, receiver, message_type, payload):
    """Construct a standardized A2A envelope."""
    if message_type not in VALID_MESSAGE_TYPES:
        raise ValueError(f"Invalid message_type: {message_type}")

    envelope = {
        "trace_id": trace_id or new_trace_id(),
        "sender": sender,
        "receiver": receiver,
        "timestamp": _now_iso(),
        "message_type": message_type,
        "payload": payload or {},
    }
    return envelope


def validate_message(envelope: dict) -> bool:
    """Validate that an envelope contains all required fields and a recognized message_type."""
    if not isinstance(envelope, dict):
        return False
    for field in REQUIRED_FIELDS:
        if field not in envelope:
            return False
    if envelope["message_type"] not in VALID_MESSAGE_TYPES:
        return False
    if not isinstance(envelope["payload"], dict):
        return False
    return True


def make_request(trace_id, sender, receiver, task, parameters=None):
    return build_message(
        trace_id=trace_id,
        sender=sender,
        receiver=receiver,
        message_type="request",
        payload={"task": task, "parameters": parameters or {}},
    )


def make_response(trace_id, sender, receiver, task, result=None, success=True):
    return build_message(
        trace_id=trace_id,
        sender=sender,
        receiver=receiver,
        message_type="response",
        payload={"task": task, "success": success, "result": result or {}},
    )


def make_error(trace_id, sender, receiver, task, error_message):
    return build_message(
        trace_id=trace_id,
        sender=sender,
        receiver=receiver,
        message_type="error",
        payload={"task": task, "error": error_message},
    )
