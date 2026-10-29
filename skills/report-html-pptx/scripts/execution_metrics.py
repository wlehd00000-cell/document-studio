"""Opt-in stage timing, independent of verified production receipts.

Metrics are observations, not proof a model ran, output was correct, or a user
approved it. Unknown counts/tokens remain null. No manuscript or chat text is
ever copied into this file.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re

from document_runtime import atomic_json

STAGES = frozenset(("architecture", "research", "writing", "design", "assets", "export", "japanese", "korean"))
STATUSES = frozenset(("verified", "not_needed", "failed"))
COUNTS = ("qa_reused", "qa_rerun", "image_jobs", "export_attempts", "input_tokens", "output_tokens", "tool_call_count")
HASH_LISTS = ("input_hashes", "output_hashes")


def path_of(root):
    return Path(root).resolve() / "qa/execution-metrics.json"


def _load(root):
    path = path_of(root)
    if not path.is_file():
        return {"schema_version": 1, "attempts": []}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1 or not isinstance(value.get("attempts"), list):
        raise ValueError("Unsupported execution metrics schema")
    return value


def _clock(now):
    when = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(when, datetime) or when.tzinfo is None or when.utcoffset() is None:
        raise ValueError("Metrics timestamp must be timezone-aware")
    return when.astimezone(timezone.utc)


def _scope(scope):
    values = scope if isinstance(scope, list) else [scope]
    if not values or any(not isinstance(item, str) or not item.strip() or len(item)>80 for item in values):
        raise ValueError("Invalid stage scope")
    return scope


def start_attempt(root: Path, stage: str, operation: str, profile: str, scope: str | list[str], *, now: datetime | None = None) -> dict:
    if stage not in STAGES:
        raise ValueError("Unknown stage")
    if operation not in ("full", "revision", "conversion", "translation") or profile not in ("focused", "standard", "showcase"):
        raise ValueError("Unknown operation or profile")
    scope = _scope(scope)
    state = _load(root)
    if any(row.get("stage") == stage and row.get("ended_at") is None for row in state["attempts"]):
        return state
    start = _clock(now).isoformat()
    state["attempts"].append({
        "stage": stage, "operation": operation, "profile": profile, "scope": scope,
        "started_at": start, "ended_at": None, "elapsed_ms": None, "clock_status": "pending",
        "status": "in_progress", "input_hashes": None, "output_hashes": None,
        **{name: None for name in COUNTS}, "model_id": None,
    })
    atomic_json(path_of(root), state)
    return state


def finish_attempt(root: Path, stage: str, status: str, *, now: datetime | None = None, observed: dict | None = None) -> dict:
    if stage not in STAGES or status not in STATUSES:
        raise ValueError("Unknown stage or completion status")
    state = _load(root)
    opened = next((row for row in reversed(state["attempts"]) if row.get("stage") == stage and row.get("ended_at") is None), None)
    if opened is None:
        # A repeated complete/skip must not invent an attempt or a timing result.
        return state
    end = _clock(now)
    start = datetime.fromisoformat(opened["started_at"])
    elapsed = (end - start).total_seconds() * 1000
    opened["ended_at"] = end.isoformat()
    opened["elapsed_ms"] = round(elapsed) if elapsed >= 0 else None
    opened["clock_status"] = "verified" if elapsed >= 0 else "unverified"
    opened["status"] = status
    observed = observed or {}
    for key in COUNTS:
        value = observed.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            opened[key] = value
    for key in HASH_LISTS:
        value = observed.get(key)
        if isinstance(value, list) and all(isinstance(x, str) and re.fullmatch(r"[a-f0-9]{64}", x) for x in value):
            opened[key] = value
    model = observed.get("model_id")
    if isinstance(model, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", model):
        opened["model_id"] = model
    atomic_json(path_of(root), state)
    return state
