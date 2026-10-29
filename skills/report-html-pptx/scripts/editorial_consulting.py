"""Opt-in, compact state for consultant-led Document Studio editorial planning.

Planning state is separate from production intake and workflow receipts.
"""

import argparse
import copy
import json
from pathlib import Path, PurePosixPath
import re

_USER_ORIGIN = re.compile(r"^(?:user_message|user_request|chat_turn):\S+$")
_PHASES = (
    "discovery", "reconnaissance", "options", "preview", "editorial",
    "manuscript_accepted", "handoff",
)
_NEXT = {
    "discovery": {"reconnaissance"},
    "reconnaissance": {"options"},
    "options": {"preview", "editorial"},
    "preview": {"editorial"},
    "editorial": {"manuscript_accepted"},
    "manuscript_accepted": {"handoff"},
    "handoff": set(),
}


def _author_origin(origin: str) -> str:
    if not isinstance(origin, str) or not _USER_ORIGIN.fullmatch(origin):
        raise ValueError("Consultation requires located explicit author origin")
    return origin


def _session(brief: dict) -> dict:
    session = brief.get("editorial_consulting")
    if not isinstance(session, dict) or session.get("phase") not in _PHASES:
        raise ValueError("No active editorial consultation")
    return session


def _chosen(session: dict, decision_id: str) -> bool:
    record = session.get("decisions", {}).get(decision_id)
    return (isinstance(record, dict)
            and isinstance(record.get("value"), str)
            and record["value"] not in {"", "pending", "rejected"}
            and bool(_USER_ORIGIN.fullmatch(record.get("origin", ""))))


def _manuscript_accepted(session: dict) -> bool:
    record = session.get("decisions", {}).get("manuscript", {})
    return _chosen(session, "manuscript") and record.get("value") == "accepted"


def _canonical_units(brief: dict) -> list[dict]:
    """Reuse whichever established section/page map the document owns."""
    units = brief.get("sections") or brief.get("page_map") or []
    if isinstance(units, dict):
        if any(not isinstance(value, dict) for value in units.values()):
            raise ValueError("Canonical page map contains invalid records")
        return [
            {**value, "id": value.get("id", key)}
            for key, value in units.items()
        ]
    if not isinstance(units, list) or any(
        not isinstance(unit, dict) for unit in units
    ):
        raise ValueError("Canonical section/page map must contain records")
    return units


def begin(brief: dict, origin: str) -> dict:
    """Start only after an explicitly sourced author opt-in."""
    _author_origin(origin)
    if "editorial_consulting" in brief:
        raise ValueError("Existing consultation must be resumed, not overwritten")
    updated = copy.deepcopy(brief)
    updated["editorial_consulting"] = {
        "schema_version": 1, "phase": "discovery",
        "activation_origin": origin, "decisions": {},
        "references": [], "previews": [], "claim_impacts": [],
    }
    return updated


def advance(brief: dict, phase: str, decision_id: str | None = None) -> dict:
    """Move to a valid phase without inferring author acceptance."""
    session = _session(brief)
    current = session["phase"]
    if phase not in _NEXT[current]:
        raise ValueError(f"Invalid consultation transition: {current} -> {phase}")
    if phase == "editorial" and not _chosen(session, "direction"):
        raise ValueError("Author direction decision is required")
    if phase == "manuscript_accepted" and not _manuscript_accepted(session):
        raise ValueError("Author manuscript acceptance is required")
    if phase == "manuscript_accepted" and session.get(
        "pending_pivotal_decisions"
    ):
        raise ValueError("Unresolved pivotal decision blocks manuscript acceptance")
    if phase == "handoff":
        ready, reasons = handoff_ready(brief)
        if not ready:
            raise ValueError("Handoff blocked: " + ", ".join(reasons))
    if decision_id and not _chosen(session, decision_id):
        raise ValueError(f"Unapproved decision: {decision_id}")
    updated = copy.deepcopy(brief)
    updated["editorial_consulting"]["phase"] = phase
    return updated


def record_decision(brief: dict, decision_id: str, value: str, origin: str) -> dict:
    """Record the author's actual choice, retaining its provenance."""
    _session(brief)
    _author_origin(origin)
    if not isinstance(decision_id, str) or not decision_id.strip():
        raise ValueError("Decision ID is required")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Decision value is required")
    updated = copy.deepcopy(brief)
    target = updated["editorial_consulting"]
    prior = target["decisions"].get(decision_id, {}).get("value")
    value = value.strip()
    target["decisions"][decision_id] = {"value": value, "origin": origin}
    if (decision_id == "direction" and prior not in {None, value}
            and target["phase"] in {
                "editorial", "manuscript_accepted", "handoff"
            }):
        target["phase"] = "options"
        target["decisions"].pop("manuscript", None)
    elif (decision_id == "manuscript" and value != "accepted"
          and target["phase"] in {"manuscript_accepted", "handoff"}):
        target["phase"] = "editorial"
    return updated


def status(brief: dict) -> dict:
    """Return a small, non-mutating handoff view."""
    if "editorial_consulting" not in brief:
        return {"active": False, "phase": None, "pending": [], "ready": False}
    session = _session(brief)
    phase = session["phase"]
    pending = []
    if phase in {"options", "preview"} and not _chosen(session, "direction"):
        pending.append("direction")
    if phase == "editorial" and not _manuscript_accepted(session):
        pending.append("manuscript")
    ready = handoff_ready(brief)[0] if phase in {
        "manuscript_accepted", "handoff"
    } else False
    return {
        "active": True, "phase": phase, "pending": pending,
        "ready": ready,
    }


def validate_reference(record: dict) -> dict:
    """Validate an inspected precedent without turning inspiration into proof."""
    if not isinstance(record, dict):
        raise ValueError("Reference must be a record")
    required = (
        "id", "role", "title", "publisher", "url_or_file", "checked_scope",
        "access_limit", "transferable_pattern", "nontransferable_content",
        "claim_ids", "section_ids",
    )
    for key in required:
        value = record.get(key)
        if key in {"claim_ids", "section_ids"}:
            if (not isinstance(value, list)
                    or any(not isinstance(item, str) or not item.strip()
                           for item in value)
                    or len(set(value)) != len(value)):
                raise ValueError(f"Invalid reference {key}")
        elif not isinstance(value, str) or (
            key not in {"access_limit"} and not value.strip()
        ):
            raise ValueError(f"Invalid reference {key}")
    if record["role"] not in {"content", "editorial", "visual"}:
        raise ValueError("Unknown reference role")
    if record["checked_scope"] not in {
        "none", "description_only", "source_text", "visual_media"
    }:
        raise ValueError("Unknown checked scope")
    if not isinstance(record.get("visual_inspected", False), bool):
        raise ValueError("Invalid visual inspection status")
    if (record.get("visual_inspected", False)
            and record["checked_scope"] != "visual_media"):
        raise ValueError("Cannot claim visual inspection without visual media")
    if record["role"] != "content" and record["claim_ids"]:
        raise ValueError("Editorial/visual reference cannot prove factual claim")
    if record["role"] == "content" and record["claim_ids"] and (
        record["checked_scope"] not in {"source_text", "visual_media"}
    ):
        raise ValueError("Factual claim requires inspected original source")
    relation = record.get("thesis_relation", "unknown")
    if relation not in {"confirm", "qualify", "contradict", "unknown"}:
        raise ValueError("Unknown thesis relation")
    if relation != "unknown" and record["role"] != "content":
        raise ValueError("Only content evidence can relate to thesis claims")
    checked = copy.deepcopy(record)
    checked["needs_argument_review"] = relation in {"contradict", "qualify"}
    checked["argument_impact"] = (
        "pending_review" if checked["needs_argument_review"] else "none"
    )
    return checked


def comparison_required(options: list[dict]) -> bool:
    """Limit early HTML samples to genuinely different explanation forms."""
    if not isinstance(options, list) or len(options) < 2:
        return False
    relationships = set()
    for option in options:
        if not isinstance(option, dict):
            return False
        visual = option.get("visual_relationship")
        reader_impact = option.get("reader_impact")
        if not isinstance(visual, str) or not visual.strip():
            return False
        if not isinstance(reader_impact, str) or not reader_impact.strip():
            return False
        relationships.add(visual.strip())
    return len(relationships) > 1


def register_preview(
    brief: dict, preview_id: str, path: str, concept_id: str, observation: str
) -> dict:
    """Register concept metadata, never a finished production artifact."""
    session = _session(brief)
    if session["phase"] != "preview":
        raise ValueError("Preview phase required")
    if not isinstance(path, str):
        raise ValueError("Invalid preview path")
    rel = PurePosixPath(path)
    if (rel.is_absolute() or len(rel.parts) < 3
            or rel.parts[:2] != ("planning", "previews")
            or ".." in rel.parts or rel.suffix.lower() != ".html"):
        raise ValueError("Invalid preview path: use planning/previews/*.html")
    for label, value in (
        ("preview_id", preview_id), ("concept_id", concept_id),
        ("observation", observation),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing {label}")
    if any(item.get("id") == preview_id for item in session.get("previews", [])):
        raise ValueError("Duplicate preview ID")
    updated = copy.deepcopy(brief)
    updated["editorial_consulting"]["previews"].append({
        "id": preview_id,
        "path": rel.as_posix(),
        "concept_id": concept_id,
        "observation": observation,
        "status": "concept_only",
    })
    return updated


def register_reference(
    brief: dict, record: dict, replace_existing: bool = False
) -> dict:
    """Keep a compact, checked precedent record in the optional session."""
    session = _session(brief)
    if session["phase"] not in {
        "reconnaissance", "options", "preview", "editorial"
    }:
        raise ValueError("Reference is outside the research/editorial phases")
    validated = validate_reference(record)
    matches = [
        index for index, item in enumerate(session.get("references", []))
        if item["id"] == validated["id"]
    ]
    if matches and not replace_existing:
        raise ValueError("Duplicate reference ID")
    updated = copy.deepcopy(brief)
    refs = updated["editorial_consulting"]["references"]
    if matches:
        refs[matches[0]] = validated
    else:
        refs.append(validated)
    return updated


def review_impact(
    brief: dict, claim_ids: list[str], impact: str, section_ids: list[str]
) -> dict:
    """Scope a new finding without mutating approved unrelated copy."""
    _session(brief)
    if impact not in {"confirm", "qualify", "contradict", "reframe"}:
        raise ValueError("Unknown evidence impact")
    if not claim_ids or not section_ids:
        raise ValueError("Located claim and section IDs are required")
    sections = _canonical_units(brief)
    by_id = {section.get("id"): index for index, section in enumerate(sections)}
    if len(by_id) != len(sections) or any(sid not in by_id for sid in section_ids):
        raise ValueError("Unknown or duplicate section IDs")
    for sid in section_ids:
        source_claims = sections[by_id[sid]].get("claim_ids", [])
        if not set(claim_ids).intersection(source_claims):
            raise ValueError(f"No located claim link for section {sid}")
    pivotal = impact in {"contradict", "reframe"}
    affected = list(dict.fromkeys(section_ids)) if impact != "confirm" else []
    live = (brief.get("genre") == "presentation"
            or brief.get("communication", {}).get("use") == "live")
    transitions = []
    if pivotal and live:
        for sid in affected:
            index = by_id[sid]
            for neighbor in (index - 1, index + 1):
                if 0 <= neighbor < len(sections):
                    nid = sections[neighbor]["id"]
                    if nid not in affected and nid not in transitions:
                        transitions.append(nid)
    return {
        "claim_ids": list(dict.fromkeys(claim_ids)), "impact": impact,
        "affected_section_ids": affected,
        "transition_section_ids": transitions,
        "pivotal": pivotal, "author_decision_required": pivotal,
    }


def handoff_ready(brief: dict) -> tuple[bool, list[str]]:
    """Check manuscript approval separately from the production intake gate."""
    session = brief.get("editorial_consulting")
    if not isinstance(session, dict):
        return False, ["consultation_inactive"]
    reasons = []
    if not _chosen(session, "direction"):
        reasons.append("direction")
    if not _manuscript_accepted(session):
        reasons.append("manuscript")
    if session.get("phase") not in {"manuscript_accepted", "handoff"}:
        reasons.append("editorial_phase")
    if session.get("pending_pivotal_decisions"):
        reasons.append("pivotal_decision")
    links = session.get("claim_links", {})
    try:
        required = {
            claim_id
            for section in _canonical_units(brief)
            for claim_id in section.get("claim_ids", [])
        }
    except ValueError:
        reasons.append("invalid_map")
        required = set()
    if not isinstance(links, dict) or any(
        not isinstance(links.get(cid), list) or not links[cid]
        or any(not isinstance(source_id, str) or not source_id.strip()
               for source_id in links[cid])
        for cid in required
    ):
        reasons.append("claim_links")
    intake = brief.get("intake", {})
    production_allowed = (
        intake["production_allowed"] is True
        if "production_allowed" in intake
        else brief.get("intake_gate", {}).get("status") == "complete"
    )
    if not production_allowed:
        reasons.append("production_intake")
    return not reasons, reasons


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("status")
    start = actions.add_parser("begin")
    start.add_argument("--origin", required=True)
    transition = actions.add_parser("advance")
    transition.add_argument("--phase", choices=_PHASES, required=True)
    transition.add_argument("--decision-id")
    choice = actions.add_parser("decision")
    choice.add_argument("--id", required=True)
    choice.add_argument("--value", required=True)
    choice.add_argument("--origin", required=True)
    preview = actions.add_parser("preview")
    preview.add_argument("--id", required=True)
    preview.add_argument("--path", required=True)
    preview.add_argument("--concept-id", required=True)
    preview.add_argument("--observation", required=True)
    reference = actions.add_parser("reference")
    reference.add_argument("--record-json", required=True)
    reference.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    path = project / "content/brief.json"
    brief = json.loads(path.read_text(encoding="utf-8-sig"))
    if args.action == "status":
        result = status(brief)
    else:
        if args.action == "begin":
            changed = begin(brief, args.origin)
        elif args.action == "advance":
            changed = advance(brief, args.phase, args.decision_id)
        elif args.action == "decision":
            changed = record_decision(brief, args.id, args.value, args.origin)
        elif args.action == "preview":
            changed = register_preview(
                brief, args.id, args.path, args.concept_id, args.observation
            )
            rel = changed["editorial_consulting"]["previews"][-1]["path"]
            source = (project / rel).resolve()
            if not source.is_relative_to(project) or not source.is_file():
                raise FileNotFoundError(f"Preview file not found in project: {rel}")
        else:
            record_path = Path(args.record_json)
            record = json.loads(record_path.read_text(encoding="utf-8-sig"))
            changed = register_reference(brief, record, args.replace)
        from render_text_flow import save_audit
        save_audit(path, changed)
        result = status(changed)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
