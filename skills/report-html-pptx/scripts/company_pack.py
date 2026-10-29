"""Strict, dependency-free Company Pack loader and design overlay resolver.

Pack references can only name sibling pack IDs. All optional resources have fixed
paths and are never resolved from untrusted JSON-provided filesystem paths.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


PACK_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
VERSION = re.compile(r"^\d+\.\d+\.\d+$")
LANGUAGE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})+$")
STATUSES = {"draft", "reviewed", "approved", "superseded"}
REFERENCE_STATUSES = {"observed", "suggested"}


class CompanyPackError(ValueError):
    """Untrusted Company Pack is malformed, unsafe, or inconsistent."""


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str
    severity: str = "FAIL"


@dataclass(frozen=True)
class CompanyPack:
    root: Path
    metadata: dict[str, Any]
    design: dict[str, Any]
    design_cases: tuple[dict[str, Any], ...]
    writing_references: tuple[dict[str, Any], ...]
    font_policy: dict[str, Any]
    lineage: tuple[str, ...]

    @property
    def pack_id(self) -> str:
        return self.metadata["pack_id"]

    @property
    def version(self) -> str:
        return self.metadata["version"]


def _check_tree(path: Path, boundary: Path) -> Path:
    """Reject link traversal, including optional resource directories and files."""
    boundary = boundary.absolute()
    path = path.absolute()
    if not path.is_relative_to(boundary):
        raise CompanyPackError("Company Pack path outside packs root")
    current = boundary
    if current.is_symlink():
        raise CompanyPackError("Pack root symlink is forbidden")
    for part in path.relative_to(boundary).parts:
        current = current / part
        if current.is_symlink():
            raise CompanyPackError(f"Company Pack symlink is forbidden: {current}")
    if not path.resolve().is_relative_to(boundary.resolve()):
        raise CompanyPackError("Company Pack path escapes packs root")
    return path


def _read_json(path: Path, boundary: Path, default: Any = None) -> Any:
    _check_tree(path, boundary)
    if not path.exists():
        if default is not None:
            return deepcopy(default)
        raise CompanyPackError(f"Missing required file: {path.name}")
    if not path.is_file():
        raise CompanyPackError(f"Expected ordinary JSON file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise CompanyPackError(f"Invalid JSON: {path}") from exc


def _validate_metadata(metadata: Any, directory: Path) -> None:
    required = {"schema_version", "pack_id", "company_name", "version", "status", "default_language", "enabled_languages", "parent_pack"}
    if not isinstance(metadata, dict) or required - metadata.keys():
        raise CompanyPackError("Missing required Company Pack metadata")
    if set(metadata) - required - {'synthetic'}:
        raise CompanyPackError('Unknown Company Pack metadata fields')
    if 'synthetic' in metadata and not isinstance(metadata['synthetic'],bool):
        raise CompanyPackError('synthetic must be boolean')
    if metadata["schema_version"] != "company-pack/1.0":
        raise CompanyPackError("Unsupported Company Pack schema")
    if not isinstance(metadata["pack_id"], str) or not PACK_ID.fullmatch(metadata["pack_id"]):
        raise CompanyPackError("Invalid pack_id")
    if directory.name != metadata["pack_id"]:
        raise CompanyPackError("pack_id must match the directory name")
    if not isinstance(metadata["company_name"], str) or not metadata["company_name"].strip():
        raise CompanyPackError("Invalid company_name")
    if not isinstance(metadata["version"], str) or not VERSION.fullmatch(metadata["version"]):
        raise CompanyPackError("Invalid version")
    if metadata["status"] not in STATUSES:
        raise CompanyPackError("Invalid approval status")
    languages = metadata["enabled_languages"]
    if (not isinstance(languages, list) or not languages or
            any(not isinstance(x, str) or not LANGUAGE.fullmatch(x) for x in languages) or
            len(languages) != len(set(languages))):
        raise CompanyPackError("Invalid enabled_languages")
    if metadata["default_language"] not in languages:
        raise CompanyPackError("default_language must be enabled")
    parent = metadata["parent_pack"]
    if parent is not None and (not isinstance(parent, str) or not PACK_ID.fullmatch(parent)):
        raise CompanyPackError("Invalid parent_pack: use a sibling pack ID only")


def deep_merge(base: dict, overlay: dict) -> dict:
    if not isinstance(base, dict) or not isinstance(overlay, dict):
        raise CompanyPackError("Design and policy overrides must be JSON objects")
    result = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def _safe_design_override(overlay: dict) -> None:
    """Refuse raw CSS injection before the palette becomes a stylesheet."""
    def visit(value: Any, key_path: str = ''):
        if isinstance(value, dict):
            for key, child in value.items():
                if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', key):
                    raise CompanyPackError('Invalid design token key: ' + key_path)
                visit(child, key_path + '.' + key)
        elif isinstance(value, list):
            for item in value:
                visit(item, key_path)
        elif isinstance(value, str):
            if re.search(r'[;{}<>\r\n"\']|url\s*\(|@import', value, re.I):
                raise CompanyPackError('Unsafe CSS design token: ' + key_path)
    visit(overlay)


def _load(path: Path, packs_root: Path, stack: tuple[str, ...]) -> CompanyPack:
    path = _check_tree(path, packs_root)
    if not path.is_dir():
        raise CompanyPackError(f"Pack directory not found: {path}")
    metadata = _read_json(path / "pack.json", packs_root)
    _validate_metadata(metadata, path)
    identifier = metadata["pack_id"]
    if identifier in stack:
        raise CompanyPackError("Company Pack inheritance cycle: " + " -> ".join((*stack, identifier)))
    # Disallow silent access to arbitrary symlinked content anywhere under a pack.
    for item in path.rglob("*"):
        if item.is_symlink():
            raise CompanyPackError(f"Company Pack symlink is forbidden: {item}")
    ancestor = None
    if metadata["parent_pack"]:
        ancestor = _load(packs_root / metadata["parent_pack"], packs_root, (*stack, identifier))
    design = _read_json(path / "design/tokens.json", packs_root, {})
    casebook = _read_json(path / "design/design-casebook.json", packs_root, {"cases": []})
    writing = _read_json(path / "writing/references.json", packs_root, {"references": []})
    fonts = _read_json(path / "fonts/policy.json", packs_root, {})
    if not isinstance(design, dict) or not isinstance(fonts, dict):
        raise CompanyPackError("Design tokens and font policy must be objects")
    _safe_design_override(design)
    if not isinstance(casebook, dict) or not isinstance(casebook.get('cases'), list):
        raise CompanyPackError('Design casebook must contain a cases list')
    cases = list(ancestor.design_cases if ancestor else ())
    case_by_id = {case['case_id']: index for index, case in enumerate(cases)}
    for case in casebook['cases']:
        if not isinstance(case, dict) or not isinstance(case.get('case_id'), str) or not case['case_id']:
            raise CompanyPackError('Design casebook entry requires case_id')
        if not isinstance(case.get('source_ids'), list) or not case['source_ids'] or any(not isinstance(x, str) or not x for x in case['source_ids']):
            raise CompanyPackError('Design casebook entry requires source_ids')
        if case.get('status') not in REFERENCE_STATUSES:
            raise CompanyPackError('Design casebook entry requires observed/suggested status')
        item = {**case, 'origin_pack': identifier}
        if case['case_id'] in case_by_id:
            cases[case_by_id[case['case_id']]] = item
        else:
            case_by_id[case['case_id']] = len(cases)
            cases.append(item)
    if not isinstance(writing, dict) or not isinstance(writing.get("references"), list):
        raise CompanyPackError("Writing references must be a JSON object containing a list")
    references = list(ancestor.writing_references if ancestor else ())
    by_id = {ref["id"]: i for i, ref in enumerate(references)}
    for ref in writing["references"]:
        if not isinstance(ref, dict) or not isinstance(ref.get("id"), str) or not ref["id"]:
            raise CompanyPackError("Writing reference requires an id")
        if not isinstance(ref.get("source_ids"), list) or not ref["source_ids"] or any(not isinstance(x, str) or not x.strip() for x in ref["source_ids"]):
            raise CompanyPackError("Writing reference requires source_ids")
        if ref.get("status") not in REFERENCE_STATUSES:
            raise CompanyPackError("Writing reference status must be observed or suggested")
        if ref.get("language") not in metadata["enabled_languages"]:
            raise CompanyPackError("Writing reference language is not enabled in this pack")
        if not isinstance(ref.get("document_family"), str) or not isinstance(ref.get("writing_function"), str):
            raise CompanyPackError("Writing reference needs document_family and writing_function")
        if not isinstance(ref.get("text"), str) or not ref["text"].strip():
            raise CompanyPackError("Writing reference text must be non-empty")
        enriched = {**ref, "origin_pack": identifier}
        if ref["id"] in by_id:
            references[by_id[ref["id"]]] = enriched
        else:
            by_id[ref["id"]] = len(references)
            references.append(enriched)
    return CompanyPack(path, metadata,
                       deep_merge(ancestor.design if ancestor else {}, design),tuple(cases),
                       tuple(references), deep_merge(ancestor.font_policy if ancestor else {}, fonts),
                       (*ancestor.lineage, identifier) if ancestor else (identifier,))


def load_company_pack(path: Path, *, packs_root: Path | None = None) -> CompanyPack:
    """Load an immutable snapshot; parents must be sibling directories."""
    path = Path(path).expanduser().absolute()
    if path.name == "pack.json":
        path = path.parent
    root = Path(packs_root).expanduser().absolute() if packs_root else path.parent
    _check_tree(path, root)
    return _load(path, root, ())


def validate_company_pack(pack: CompanyPack) -> list[ValidationIssue]:
    """Return non-blocking usage warnings; structural errors fail at load time."""
    result = []
    if pack.metadata["status"] != "approved":
        result.append(ValidationIssue("status", "Pack is not approved for production", "UNVERIFIED"))
    return result


def resolve_design_tokens(base_tokens: dict, pack: CompanyPack | None, document_family: str) -> dict:
    """Overlay pack defaults and document-family choices without mutating base tokens."""
    if pack is None:
        return deepcopy(base_tokens)
    design = deepcopy(pack.design)
    families = design.pop("document_families", {})
    if not isinstance(families, dict):
        raise CompanyPackError("document_families must be an object")
    family = families.get(document_family, {})
    return deep_merge(deep_merge(base_tokens, design), family)
