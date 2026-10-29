"""One content-addressed DEMO document state; stdlib, local files, no execution/imports.

Receipts attest inspected scope and bind real files. They do not certify human
approval or prevent an authorized editor from fabricating evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
import zipfile
import shutil
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parent))
from document_runtime import atomic_json

VERSION = 1
STATE = "content/project-state.json"
LAYERS = ("automated", "editorial", "visual", "export", "user_acceptance")
CHECKS = {
    "editorial": {"source_equivalence", "status_conditions", "language", "copy_clarity", "spacing_consistency", "rendered_lineflow", "semantic_breaks"},
    "visual": {"hierarchy", "readability", "assets_crop", "reference_application", "design_tokens_actual"},
    "export": {"file_integrity", "rendered_comparison", "editability", "text_fidelity", "rendered_lineflow", "semantic_breaks"},
    "user_acceptance": {"acceptance"},
}
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$")
SHA = re.compile(r"^[a-f0-9]{64}$")


class PageRanges(HTMLParser):
    """Exact source slices, with global shell retained; no HTML execution."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text, self.stack, self.ranges = text, [], []
        self.offsets = [0]
        self.offsets.extend(m.end() for m in re.finditer("\n", text))
        self.active = None

    def position(self):
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        is_page = "page" in attrs.get("class", "").split() or "data-pptx-slide" in attrs
        if is_page and self.active is None:
            self.active = (self.position(), len(self.stack), tag)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            raise ValueError("Malformed page markup; use conservative whole-file QA")
        self.stack.pop()
        if self.active and len(self.stack) == self.active[1] and tag == self.active[2]:
            start = self.active[0]
            end = self.text.find(">", self.position()) + 1
            self.ranges.append((start, end))
            self.active = None


def html_scope_hash(path, page_order, scope):
    """Unknown markup falls back to the full byte hash, never optimistic reuse."""
    try:
        text = Path(path).read_text(encoding="utf-8")
        parser = PageRanges(text)
        parser.feed(text)
        if parser.active or len(parser.ranges) != len(page_order):
            return digest_file(path)
        parts, last, selected = [], 0, {}
        for number, (start, end) in zip(page_order, parser.ranges):
            parts.extend([text[last:start], "<DEMO-PAGE:" + number + ">"])
            if number in scope:
                selected[number] = text[start:end]
            last = end
        parts.append(text[last:])
        return digest_json({"shell": "".join(parts), "pages": selected})
    except (ValueError, UnicodeError):
        return digest_file(path)


def copy_scope_hash(path,page_order,scope):
    """Exact canonical Markdown page slices; unmarked/ambiguous copy is global."""
    try:
        text=Path(path).read_text(encoding='utf-8')
        markers=list(re.finditer(r'^<!--\s*demo-page:([A-Za-z0-9_.-]+)\s*-->\s*$',text,re.M))
        if [m[1] for m in markers]!=page_order:return digest_file(path)
        pages={m[1]:text[m.end():markers[i+1].start() if i+1<len(markers) else len(text)]
               for i,m in enumerate(markers) if m[1] in scope}
        return digest_json({'global':text[:markers[0].start()],'order':page_order,'pages':pages})
    except (UnicodeError,ValueError):return digest_file(path)


def digest_file(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def digest_json(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be a nonempty string")
    return value


def text_flow_findings(report):
    """Stable candidates merge only identical page/block/warning observations."""
    findings, candidates = [], {}
    for mode_name in ("screen", "print"):
        mode = report.get(mode_name, {})
        for page in mode.get("pages", []):
            number = str(page["page"])
            findings.extend({"severity": "blocking", "code": "layout", "page": number,
                             "detail": str(f)} for f in page.get("layout_findings", []))
            for block_index, block in enumerate(page.get("blocks", []), 1):
                block_id = str(block.get("id") or "block-" + str(block_index))
                for warning in block.get("warnings", []):
                    identity = {"page": number, "block_id": block_id, "warning": warning}
                    finding_id = "tf-" + digest_json(identity)[:24]
                    if finding_id not in candidates:
                        candidate = {"severity": "warning", "code": "text_flow_candidate",
                                     "page": number, "block_id": block_id,
                                     "finding_id": finding_id, "detail": str(warning), "modes": []}
                        candidates[finding_id] = candidate
                        findings.append(candidate)
                    if mode_name not in candidates[finding_id]["modes"]:
                        candidates[finding_id]["modes"].append(mode_name)
        findings.extend({"severity": "blocking", "code": "missing_image", "detail": str(f)}
                        for f in mode.get("missing_images", []))
        findings.extend({"severity": "blocking", "code": "font_failure", "detail": str(f)}
                        for f in mode.get("fonts", []) if f.get("status") == "error")
    findings.extend({"severity": "blocking", "code": "resource_failure", "detail": str(f)}
                    for f in report.get("resource_failures", []) + report.get("font_errors", []))
    return findings


def validate_dispositions(page, layer):
    items = page.get("warning_dispositions", [])
    if not isinstance(items, list):
        raise ValueError("warning_dispositions must be a list")
    seen = set()
    for item in items:
        if layer != "editorial" or not isinstance(item, dict):
            raise ValueError("Text-flow dispositions belong to editorial pages")
        finding_id = item.get("finding_id", "")
        if not re.fullmatch(r"tf-[a-f0-9]{24}", finding_id) or finding_id in seen:
            raise ValueError("Invalid or duplicate warning finding_id")
        seen.add(finding_id)
        if item.get("decision") not in {"accepted", "fixed", "unresolved"}:
            raise ValueError("Warning decision must be accepted, fixed or unresolved")
        nonempty(item.get("reason"), "Warning disposition reason")
        if item["decision"] == "accepted" and not any(
                PurePosixPath(ref.get("path", "")).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                for ref in page.get("evidence", [])):
            raise ValueError("Accepting a warning requires actual page image evidence")


class ProjectState:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("Project must be an existing directory")
        self.state_path = self.path(STATE, must_exist=False)
        self.state = None
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.validate()

    def path(self, value, must_exist=True):
        """No traversal, absolute/UNC/drive/ADS paths or symlink escapes."""
        nonempty(value, "Relative path")
        if "\\" in value or ":" in value or "\x00" in value:
            raise ValueError("Use a relative project path with forward slashes")
        raw = PurePosixPath(value)
        if raw.is_absolute() or any(part in {"..", "."} for part in value.split("/")):
            raise ValueError("Path must stay inside the project")
        if not raw.parts:
            raise ValueError("Empty path")
        resolved = (self.root / Path(*raw.parts)).resolve(strict=must_exist)
        if not resolved.is_relative_to(self.root):
            raise ValueError("Path escapes project via a link")
        if must_exist and not resolved.is_file():
            raise ValueError("Expected a regular file: " + value)
        return resolved

    def require(self):
        if self.state is None:
            raise ValueError("Initialize project state first")

    def validate(self):
        s = self.state
        if not isinstance(s, dict) or s.get("schema_version") != VERSION:
            raise ValueError("Unsupported project-state schema")
        if not isinstance(s.get("nodes"), dict) or not isinstance(s.get("receipts"), list):
            raise ValueError("Invalid nodes/receipts")
        self.validate_pages(s.get("page_order"))
        for key, node in s["nodes"].items():
            self.check_id(key)
            if node.get("kind") not in {"source", "artifact"}:
                raise ValueError("Invalid node kind")
            self.path(node.get("path"), must_exist=False)
            self.scope(node.get("pages"))
            if not isinstance(node.get("depends"), list):
                raise ValueError("Invalid dependency list")
            for dep in node["depends"]:
                if dep not in s["nodes"]:
                    raise ValueError("Unknown dependency: " + dep)
            if key in node["depends"]:
                raise ValueError("A node cannot depend on itself")
        for key in s["nodes"]:
            self.walk(key)  # cycle check
        for receipt in s["receipts"]:
            if receipt.get("target") not in s["nodes"] or receipt.get("layer") not in LAYERS:
                raise ValueError("Invalid receipt target/layer")
            self.validate_pages(receipt.get("pages"))
            self.validate_pages(receipt.get("page_order"))
            if not set(receipt["pages"]) <= set(receipt["page_order"]):
                raise ValueError("Receipt scope exceeds its historical page order")
            self.path(receipt.get("evidence", {}).get("path"), must_exist=False)
            for evidence in receipt.get("files", []):
                self.path(evidence.get("path"), must_exist=False)

    @staticmethod
    def check_id(value):
        if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
            raise ValueError("Use a short alphanumeric identifier")

    @staticmethod
    def validate_pages(pages):
        if not isinstance(pages, list) or not pages or len(set(pages)) != len(pages):
            raise ValueError("page_order must be a nonempty unique list")
        for page in pages:
            ProjectState.check_id(page)

    def scope(self, pages):
        if pages == "all":
            return list(self.state["page_order"])
        if not isinstance(pages, list) or not pages or len(set(pages)) != len(pages):
            raise ValueError("Scope must be all or a nonempty unique page list")
        if any(page not in self.state["page_order"] for page in pages):
            raise ValueError("Scope contains an unknown page")
        return pages

    def save(self):
        self.validate()
        atomic_json(self.state_path,self.state)

    def init(self, pages, canonical=None):
        if self.state is not None:
            raise ValueError("State already exists; reuse it")
        self.validate_pages(pages)
        if canonical:
            self.check_id(canonical)
        self.state = {"schema_version": VERSION, "page_order": pages,
                      "canonical": canonical, "nodes": {}, "receipts": []}
        self.save()
        return self.state

    def set_pages(self, pages):
        self.require()
        self.validate_pages(pages)
        # Existing scoped page receipts must remain interpretable. Use all for
        # removed pages on affected nodes; receipts retain history, never pass.
        self.state["page_order"] = pages
        for node in self.state["nodes"].values():
            if node["pages"] != "all":
                node["pages"] = [p for p in node["pages"] if p in pages] or "all"
        self.save()

    def register(self, key, path, kind="source", role="copy", pages="all", depends=None):
        self.require()
        self.check_id(key)
        self.path(path)
        if path == STATE:
            raise ValueError("State cannot be its own content dependency")
        if kind not in {"source", "artifact"}:
            raise ValueError("Invalid node kind")
        nonempty(role, "Role")
        self.scope(pages)
        depends = sorted(set(depends or []))
        if key in depends or any(dep not in self.state["nodes"] for dep in depends):
            raise ValueError("Dependencies must already exist and exclude self")
        if kind == "source" and depends:
            raise ValueError("A source has no generated dependency; use artifact")
        if any(n["path"] == path for k, n in self.state["nodes"].items() if k != key):
            raise ValueError("One file has one canonical node")
        previous = self.state["nodes"].get(key)
        node = {"kind": kind, "role": role, "path": path, "pages": pages, "depends": depends}
        if previous and all(previous.get(k) == v for k, v in node.items()):
            return previous  # Do not bless a changed artifact by registering it again.
        prior_state = copy.deepcopy(self.state)
        self.state["nodes"][key] = node
        try:
            self.validate()
            if kind == "source":
                node["initial_hash"] = digest_file(self.path(path))
            self.save()
        except Exception:
            self.state = prior_state
            raise
        return node

    def walk(self, key, trail=()):
        if key in trail:
            raise ValueError("Dependency cycle: " + " -> ".join(trail + (key,)))
        result = {key}
        for dep in self.state["nodes"][key]["depends"]:
            result.update(self.walk(dep, trail + (key,)))
        return result

    def hashes(self, keys):
        result = {}
        for key in sorted(keys):
            node = self.state["nodes"][key]
            try:
                result[key] = digest_file(self.path(node["path"]))
            except (ValueError, OSError):
                result[key] = None
        return result

    def signature(self, key):
        return digest_json({"files": self.hashes(self.walk(key)),
                            "graph": {k: {field: self.state["nodes"][k][field]
                                          for field in ("path", "kind", "role", "depends", "pages")}
                                      for k in sorted(self.walk(key))},
                            "page_order": self.state["page_order"]})

    def scope_signature(self, key, pages):
        scope = self.scope(pages)
        selected = {}
        for dep in sorted(self.walk(key)):
            node = self.state["nodes"][dep]
            if dep != key and not set(scope).intersection(self.scope(node["pages"])):
                continue
            try:
                file = self.path(node["path"])
                sha = html_scope_hash(file, self.state["page_order"], scope) if file.suffix.lower() in {".html", ".htm"} else copy_scope_hash(file,self.state['page_order'],scope) if node['role']=='copy' and file.suffix.lower()=='.md' else digest_file(file)
            except (ValueError, OSError):
                sha = None
            selected[dep] = {"sha256": sha, "path": node["path"], "role": node["role"], "depends": node["depends"], "pages": node["pages"]}
        return digest_json({"inputs": selected, "page_order": self.state["page_order"], "scope": sorted(scope)})

    def freshness(self, key, trail=()):
        node = self.state["nodes"][key]
        live = self.hashes([key])[key]
        reasons = []
        if live is None:
            reasons.append("missing_file")
        if node["kind"] == "source":
            return {"fresh": live is not None, "changed": live != node.get("initial_hash"), "reasons": reasons}
        build = node.get("build")
        if not build:
            reasons.append("no_production_receipt")
        else:
            if live != build.get("sha256"):
                reasons.append("artifact_bytes_changed")
            if self.state["page_order"] != build.get("page_order"):
                reasons.append("page_order_changed")
            expected = build.get("dependencies", {})
            if set(expected) != set(node["depends"]):
                reasons.append("dependency_set_changed")
            for dep in node["depends"]:
                if self.signature(dep) != expected.get(dep):
                    reasons.append("dependency_changed:" + dep)
                if not self.freshness(dep, trail + (key,))["fresh"]:
                    reasons.append("dependency_stale:" + dep)
        return {"fresh": not reasons, "changed": bool(reasons), "reasons": reasons}

    def snapshot(self, key):
        self.require()
        node = self.state["nodes"][key]
        if node["kind"] != "artifact" or not node["depends"]:
            raise ValueError("Generated artifact must declare at least one source/dependency")
        if any(not self.freshness(dep)["fresh"] for dep in node["depends"]):
            raise ValueError("Cannot snapshot an artifact with stale dependencies")
        node["build"] = {"at": timestamp(), "sha256": digest_file(self.path(node["path"])),
                         "dependencies": {d: self.signature(d) for d in node["depends"]},
                         "page_order": list(self.state["page_order"])}
        self.save()
        return {"target": key, "target_signature": self.signature(key), **node["build"]}

    def file_record(self, item):
        if not isinstance(item, dict) or not SHA.fullmatch(str(item.get("sha256", ""))):
            raise ValueError("Evidence needs path and SHA-256")
        path = self.path(item.get("path"))
        if digest_file(path) != item["sha256"]:
            raise ValueError("Evidence file hash mismatch: " + item["path"])
        return {"path": item["path"], "sha256": item["sha256"]}

    def audit_relative(self, raw):
        """Reject external names lexically before touching their filesystem."""
        nonempty(raw, "Audit dependency path")
        candidate = Path(raw)
        if not candidate.is_absolute() or not candidate.is_relative_to(self.root):
            raise ValueError("Audit dependency is outside project: " + raw)
        relative = candidate.relative_to(self.root).as_posix()
        self.path(relative)  # traversal, ADS and symlink containment
        return relative

    def add_receipt(self, key, layer, evidence, pages, files, findings, proof):
        self.scope(pages)
        if not set(pages) <= set(self.scope(self.state["nodes"][key]["pages"])):
            raise ValueError("Review scope exceeds target scope")
        receipt = {"id": digest_json({"target": key, "layer": layer, "evidence": evidence,
                                       "signature": self.signature(key), "pages": pages})[:20],
                   "target": key, "layer": layer, "target_signature": self.signature(key),
                   "scope_signature": self.scope_signature(key, pages),
                   "pages": list(pages), "page_order": list(self.state["page_order"]),
                   "evidence": self.file_record(evidence), "files": files,
                   "findings": findings, "proof": proof, "recorded_at": timestamp()}
        self.state["receipts"] = [r for r in self.state["receipts"] if r["id"] != receipt["id"]] + [receipt]
        self.save()
        return receipt

    def review(self, key, layer, evidence_path, pages=None, split_evidence=False):
        self.require()
        if key not in self.state["nodes"] or layer not in LAYERS:
            raise ValueError("Unknown target/layer")
        if not self.freshness(key)["fresh"]:
            raise ValueError("Review target is stale; produce current artifact first")
        evidence_file = self.path(evidence_path)
        report = json.loads(evidence_file.read_text(encoding="utf-8"))
        evidence = {"path": evidence_path, "sha256": digest_file(evidence_file)}
        if layer == "automated":
            receipt=self.import_text_flow(key, evidence, report, pages)
            if split_evidence:self.split_review(key,layer,report,receipt['pages'],evidence_path)
            return receipt
        if report.get("schema_version") != 1 or report.get("format") != "demo-review-v1" or report.get("layer") != layer:
            raise ValueError("Use demo-review-v1 evidence for editorial/visual/export/acceptance")
        if report.get("target") != key or report.get("target_signature") != self.signature(key):
            raise ValueError("Review does not bind the current target signature")
        reviewer = report.get("reviewer", {})
        nonempty(reviewer.get("id"), "Reviewer id")
        if reviewer.get("kind") not in {"agent", "human"}:
            raise ValueError("Reviewer kind must be agent or human")
        records = report.get("pages")
        if not isinstance(records, list) or not records:
            raise ValueError("Per-page review observations are required")
        observed, files, findings = [], [], []
        for page in records:
            number = page.get("page")
            self.scope([number])
            if number in observed:
                raise ValueError("Duplicate review page")
            observed.append(number)
            if not CHECKS[layer] <= set(page.get("checked", [])):
                raise ValueError("Missing required review categories for " + layer)
            nonempty(page.get("observations"), "Page observations")
            validate_dispositions(page, layer)
            references = page.get("evidence", [])
            if not isinstance(references, list) or not references:
                raise ValueError("Each page requires actual file evidence")
            files.extend(self.file_record(ref) for ref in references)
            for finding in page.get("findings", []):
                if finding.get("severity") not in {"blocking", "warning"}:
                    raise ValueError("Finding severity must be blocking or warning")
                nonempty(finding.get("code"), "Finding code")
                nonempty(finding.get("detail"), "Finding detail")
                findings.append({**finding, "page": number})
        if pages is not None and set(pages) != set(observed):
            raise ValueError("Requested review scope must equal observed pages")
        if layer == "user_acceptance":
            if reviewer["kind"] != "human" or report.get("decision") not in {"accepted", "rejected"}:
                raise ValueError("Acceptance requires a recorded human decision")
            if report["decision"] == "rejected":
                findings.append({"severity": "blocking", "code": "user_rejected", "detail": "User rejected this revision"})
        receipt=self.add_receipt(key, layer, evidence, observed, files, findings,
                                 {"format": "demo-review-v1", "reviewer": reviewer,
                                  "decision": report.get("decision")})
        if split_evidence:self.split_review(key,layer,report,observed,evidence_path)
        return receipt

    def split_review(self,key,layer,report,pages,evidence_path):
        """Opt-in immutable per-page reports for safe partial-review reuse."""
        registered={n['path'] for n in self.state['nodes'].values()}
        for number in pages:
            child=copy.deepcopy(report)
            name=digest_json({'target':key,'layer':layer,'report':report,'page':number})[:24]
            directory=PurePosixPath('qa/receipts')/name
            destination=self.path((directory/'review.json').as_posix(),must_exist=False)
            destination.parent.mkdir(parents=True,exist_ok=True)
            def preserve(ref):
                if ref['path'] in registered:return ref
                source=self.path(ref['path']);content=digest_file(source)
                filename=content[:20]+source.suffix.lower()
                relative=(directory/filename).as_posix();target=self.path(relative,must_exist=False)
                if not target.exists():shutil.copy2(source,target)
                if digest_file(target)!=content:raise ValueError('Immutable evidence snapshot changed')
                return {'path':relative,'sha256':content}
            if layer=='automated':
                for mode in ('screen','print'):
                    child[mode]['pages']=[p for p in child[mode]['pages'] if str(p['page'])==number]
                shots=[]
                for shot in child['screenshots']:
                    if str(shot['page'])!=number:continue
                    original=(PurePosixPath(evidence_path).parent/shot['file']).as_posix()
                    snapshot=preserve({'path':original,'sha256':shot['sha256']})
                    shots.append({**shot,'file':PurePosixPath(snapshot['path']).name,'sha256':snapshot['sha256']})
                child['screenshots']=shots
            else:
                child['pages']=[p for p in child['pages'] if p['page']==number]
                for page in child['pages']:page['evidence']=[preserve(ref) for ref in page['evidence']]
            if destination.is_file() and json.loads(destination.read_text(encoding='utf-8'))!=child:
                raise ValueError('Immutable review report changed')
            if not destination.exists():atomic_json(destination,child)
            self.review(key,layer,destination.relative_to(self.root).as_posix(),[number],False)

    def import_text_flow(self, key, evidence, report, pages):
        if report.get("schema_version") != 1 or report.get("status") != "measured":
            raise ValueError("Automated evidence must be a completed text-flow audit")
        local = report.get("source_evidence", {}).get("local_files", {})
        if not local or report.get("source_evidence", {}).get("external_resources_unhashed"):
            raise ValueError("Missing local dependencies or unhashed external resources")
        bound, files = set(), []
        for raw, sha in local.items():
            # Renderer currently emits absolute paths. Resolve ONLY known files
            # inside root, then apply the same normal relative-path validator.
            rel = self.audit_relative(raw)
            files.append(self.file_record({"path": rel, "sha256": sha}))
            bound.add(rel)
        if self.state["nodes"][key]["path"] not in bound:
            raise ValueError("Audit does not bind its target file")
        dependencies = self.walk(key)
        render_roles = {"font", "style", "asset", "layout", "html"}
        for node_id in dependencies:
            node = self.state["nodes"][node_id]
            if node["role"] in render_roles and node["path"] not in bound:
                raise ValueError("Audit misses a declared rendering dependency: " + node_id)
        implementations = report.get("implementation_hashes", {})
        required = {"text_flow_measure.js"}
        if "render_text_flow.mjs" in implementations:
            required.add("render_text_flow.mjs")
        else:
            required.add("render_text_flow.py")
        if not required <= set(implementations):
            raise ValueError("Missing measurement implementation hashes")
        for name in required:
            # Ignore caller-supplied extra names; never resolve them.
            if digest_file(Path(__file__).with_name(name)) != implementations[name]:
                raise ValueError("Measurement implementation changed")
        scope = None
        findings = []
        for mode_name in ("screen", "print"):
            mode = report.get(mode_name, {})
            if mode.get("total_pages") != len(self.state["page_order"]):
                raise ValueError("Audit page count differs from project page order")
            records = mode.get("pages", [])
            measured = [str(p.get("page")) for p in records if p.get("status") == "measured"]
            self.scope(measured)
            if len(set(measured)) != len(measured) or any(not p.get("blocks") for p in records):
                raise ValueError("Incomplete page measurement")
            if scope is not None and set(scope) != set(measured):
                raise ValueError("Screen/print scopes differ")
            scope = measured
        findings = text_flow_findings(report)
        screenshots = report.get("screenshots", [])
        if {str(s.get("page")) for s in screenshots} != set(scope):
            raise ValueError("Screenshot coverage must match measured pages")
        for shot in screenshots:
            rel = (PurePosixPath(evidence["path"]).parent / shot["file"]).as_posix()
            files.append(self.file_record({"path": rel, "sha256": shot.get("sha256")}))
        if pages is not None and set(pages) != set(scope):
            raise ValueError("Requested scope exceeds actual measurement")
        return self.add_receipt(key, "automated", evidence, scope, files, findings,
                                {"format": "text-flow-audit-v1", "implementation_hashes": {k: implementations[k] for k in required}})

    def verify_pptx(self, key, evidence_path):
        """Actual package checks for native-route automated QA, not visual review."""
        self.require()
        if not self.freshness(key)["fresh"]:
            raise ValueError("Target is stale")
        target = self.path(self.state["nodes"][key]["path"])
        if target.suffix.lower() != ".pptx":
            raise ValueError("Built-in verification supports PPTX only")
        destination = self.path(evidence_path, must_exist=False)
        if not evidence_path.startswith("qa/") or destination.suffix.lower() != ".json":
            raise ValueError("Built-in verification writes only a JSON evidence file under qa/")
        if destination == target or evidence_path == STATE or any(n["path"] == evidence_path for n in self.state["nodes"].values()):
            raise ValueError("Evidence must not overwrite state or registered content")
        findings, runs = [], 0
        namespace = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main",
                     "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        with zipfile.ZipFile(target) as package:
            bad = package.testzip()
            if bad:
                raise ValueError("Broken ZIP member: " + bad)
            manifest = ET.fromstring(package.read("ppt/presentation.xml"))
            canvas = manifest.find("p:sldSz", namespace)
            if canvas is None:
                raise ValueError("Missing PPTX canvas")
            width, height = int(canvas.get("cx")), int(canvas.get("cy"))
            slide_ids = manifest.findall("p:sldIdLst/p:sldId", namespace)
            relns = "http://schemas.openxmlformats.org/package/2006/relationships"
            rels = ET.fromstring(package.read("ppt/_rels/presentation.xml.rels"))
            relmap = {r.get("Id"): r for r in rels.findall("{" + relns + "}Relationship")}
            attrns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            if len(slide_ids) != len(self.state["page_order"]):
                findings.append({"severity": "blocking", "code": "page_count", "detail": "PPTX page count differs from project"})
            for index, slide_id in enumerate(slide_ids):
                relation = relmap.get(slide_id.get(attrns))
                if relation is None or relation.get("TargetMode") == "External":
                    raise ValueError("Invalid slide relationship")
                raw = relation.get("Target", "")
                # Read ZIP members only; never extract package paths to disk.
                name = raw.lstrip("/") if raw.startswith("/") else "ppt/" + raw
                name = str(PurePosixPath(name))
                if ".." in PurePosixPath(name).parts:
                    raise ValueError("Unexpected slide relationship traversal")
                slide = ET.fromstring(package.read(name))
                page = self.state["page_order"][index] if index < len(self.state["page_order"]) else str(index + 1)
                texts = slide.findall(".//a:t", namespace)
                runs += sum(bool(t.text) for t in texts)
                for shape in slide.findall(".//p:sp", namespace):
                    if not any(t.text for t in shape.findall(".//a:t", namespace)):
                        continue
                    transform = shape.find("p:spPr/a:xfrm", namespace)
                    if transform is None:
                        continue  # Inherited layout geometry requires visual verification.
                    off, ext = transform.find("a:off", namespace), transform.find("a:ext", namespace)
                    if off is None or ext is None:
                        continue
                    x, y, w, h = (int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy")))
                    if x < 0 or y < 0 or x + w > width or y + h > height:
                        findings.append({"severity": "blocking", "code": "text_bounds", "page": page,
                                         "detail": "Native text box crosses the page canvas"})
        if not runs:
            findings.append({"severity": "blocking", "code": "no_native_text", "detail": "No editable text runs found"})
        report = {"schema_version": 1, "format": "pptx-intrinsic-v1", "target": key,
                  "target_signature": self.signature(key), "canvas": [width, height],
                  "slide_count": len(slide_ids), "native_text_runs": runs, "findings": findings,
                  "limitations": "ZIP/OOXML checks do not measure glyph clipping, fonts, crop or final appearance"}
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return self.add_receipt(key, "automated", {"path": evidence_path, "sha256": digest_file(destination)},
                                self.state["page_order"], [], findings,
                                {"format": "pptx-intrinsic-v1", "implementation_sha256": digest_file(Path(__file__))})

    def receipt_current(self, receipt):
        if not self.freshness(receipt["target"])["fresh"]:
            return False
        if receipt["page_order"] != self.state["page_order"]:
            return False
        if receipt.get("scope_signature") != self.scope_signature(receipt["target"], receipt["pages"]):
            return False
        registered = {n["path"] for n in self.state["nodes"].values()}
        for ref in [receipt["evidence"]] + receipt["files"]:
            try:
                # Registered production inputs are verified by scoped hashes.
                # The immutable report and screenshot evidence always hash-check.
                if ref is not receipt["evidence"] and ref["path"] in registered:
                    continue
                if digest_file(self.path(ref["path"])) != ref["sha256"]:
                    return False
            except (ValueError, OSError):
                return False
        proof = receipt.get("proof", {})
        if not self.proof_valid(receipt):
            return False
        if proof.get("format") == "text-flow-audit-v1":
            for name, sha in proof["implementation_hashes"].items():
                if name not in {"render_text_flow.py", "render_text_flow.mjs", "text_flow_measure.js"}:
                    return False
                if digest_file(Path(__file__).with_name(name)) != sha:
                    return False
        if proof.get("format") == "pptx-intrinsic-v1" and proof.get("implementation_sha256") != digest_file(Path(__file__)):
            return False
        return True

    def proof_valid(self, receipt):
        """A manifest stage flag cannot stand in for a review evidence record."""
        try:
            report = json.loads(self.path(receipt["evidence"]["path"]).read_text(encoding="utf-8"))
            proof = receipt["proof"]
            if proof.get("format") == "demo-review-v1":
                if report.get("format") != "demo-review-v1" or report.get("schema_version") != 1:
                    return False
                if report.get("target") != receipt["target"] or report.get("target_signature") != receipt["target_signature"] or report.get("layer") != receipt["layer"]:
                    return False
                if report.get("reviewer") != proof.get("reviewer"):
                    return False
                records = report.get("pages", [])
                if {p.get("page") for p in records} != set(receipt["pages"]) or len(records) != len(receipt["pages"]):
                    return False
                files, findings = [], []
                for page in records:
                    if not CHECKS[receipt["layer"]] <= set(page.get("checked", [])) or not page.get("observations", "").strip() or not page.get("evidence"):
                        return False
                    validate_dispositions(page, receipt["layer"])
                    files.extend(page["evidence"])
                    findings.extend({**f, "page": page["page"]} for f in page.get("findings", []))
                if receipt["layer"] == "user_acceptance":
                    if report.get("reviewer", {}).get("kind") != "human" or report.get("decision") not in {"accepted", "rejected"}:
                        return False
                    if report["decision"] == "rejected":
                        findings.append({"severity": "blocking", "code": "user_rejected", "detail": "User rejected this revision"})
                return files == receipt["files"] and findings == receipt["findings"]
            if proof.get("format") == "text-flow-audit-v1":
                if receipt["layer"] != "automated" or report.get("schema_version") != 1 or report.get("status") != "measured":
                    return False
                if report.get("source_evidence", {}).get("external_resources_unhashed"):
                    return False
                for name, sha in proof["implementation_hashes"].items():
                    if report.get("implementation_hashes", {}).get(name) != sha:
                        return False
                if not {"text_flow_measure.js"} <= set(proof["implementation_hashes"]):
                    return False
                if not {"render_text_flow.py", "render_text_flow.mjs"}.intersection(proof["implementation_hashes"]):
                    return False
                expected_files, expected_findings = [], []
                local = report.get("source_evidence", {}).get("local_files", {})
                if not local:
                    return False
                for raw, sha in local.items():
                    expected_files.append({"path": self.audit_relative(raw), "sha256": sha})
                bound = {f["path"] for f in expected_files}
                if self.state["nodes"][receipt["target"]]["path"] not in bound:
                    return False
                for dep in self.walk(receipt["target"]):
                    node = self.state["nodes"][dep]
                    if node["role"] in {"font", "style", "asset", "layout", "html"} and node["path"] not in bound:
                        return False
                for mode in (report.get("screen", {}), report.get("print", {})):
                    records = mode.get("pages", [])
                    if mode.get("total_pages") != len(self.state["page_order"]) or {str(p.get("page")) for p in records if p.get("status") == "measured"} != set(receipt["pages"]):
                        return False
                    if any(not p.get("blocks") for p in records):
                        return False
                expected_findings = text_flow_findings(report)
                screenshots = report.get("screenshots", [])
                if {str(s.get("page")) for s in screenshots} != set(receipt["pages"]):
                    return False
                expected_files.extend({"path": (PurePosixPath(receipt["evidence"]["path"]).parent / shot["file"]).as_posix(), "sha256": shot.get("sha256")} for shot in screenshots)
                return expected_files == receipt["files"] and expected_findings == receipt["findings"]
            if proof.get("format") == "pptx-intrinsic-v1":
                return receipt["layer"] == "automated" and report.get("format") == "pptx-intrinsic-v1" and report.get("target") == receipt["target"] and report.get("target_signature") == receipt["target_signature"] and report.get("findings") == receipt["findings"] and report.get("slide_count") == len(self.state["page_order"])
        except (ValueError, OSError, KeyError, TypeError):
            return False
        return False

    def layer_status(self, key, layer):
        pages = self.scope(self.state["nodes"][key]["pages"])
        receipts = [r for r in self.state["receipts"] if r["target"] == key and r["layer"] == layer]
        current = [r for r in receipts if self.receipt_current(r)]
        # Newest current observation owns each page. A re-review can resolve an
        # old finding but a narrower receipt cannot clear another page's issue.
        latest = {}
        for r in current:
            for page in r["pages"]:
                latest[page] = r
        missing = [p for p in pages if p not in latest]
        findings = []
        for receipt in {r["id"]: r for r in latest.values()}.values():
            findings.extend(f for f in receipt["findings"] if not f.get("page") or latest.get(f["page"], {}).get("id") == receipt["id"])
        blocking = [f for f in findings if f["severity"] == "blocking"]
        state = "blocked" if blocking else "pending" if missing else "checked_with_warnings" if findings else "checked"
        return {"state": state, "missing_pages": missing, "current_receipts": len(current),
                "stale_receipts": len(receipts) - len(current), "findings": findings}

    def status(self):
        self.require()
        return {"schema_version": VERSION, "revision": digest_json({"sources": self.hashes(self.state["nodes"]), "page_order": self.state["page_order"]}),
                "canonical": self.state.get("canonical"), "page_order": self.state["page_order"],
                "nodes": {key: {"path": node["path"], "kind": node["kind"], "role": node["role"],
                                "signature": self.signature(key), **self.freshness(key),
                                "qa": {layer: self.layer_status(key, layer) for layer in LAYERS} if node["kind"] == "artifact" else {}}
                          for key, node in self.state["nodes"].items()}}

    def unresolved_text_flow(self, key):
        candidates = [f for f in self.layer_status(key, "automated")["findings"]
                      if f["code"] == "text_flow_candidate"]
        latest = {}
        for receipt in self.state["receipts"]:
            if receipt["target"] == key and receipt["layer"] == "editorial" and self.receipt_current(receipt):
                report = json.loads(self.path(receipt["evidence"]["path"]).read_text(encoding="utf-8"))
                for page in report["pages"]:
                    latest[page["page"]] = page
        unresolved = []
        for candidate in candidates:
            page = latest.get(candidate["page"], {})
            disposition = next((d for d in page.get("warning_dispositions", [])
                                if d["finding_id"] == candidate.get("finding_id")), None)
            if not disposition or disposition["decision"] != "accepted":
                unresolved.append({"target": key, "layer": "editorial",
                                   "reason": "unresolved_text_flow_candidate",
                                   "candidate": candidate,
                                   "decision": disposition["decision"] if disposition else "missing"})
        return unresolved

    def change_plan(self, changed):
        """Read-only dependency impact; changing a source never blesses outputs."""
        self.require()
        if not changed or any(key not in self.state['nodes'] for key in changed):
            raise ValueError('Choose actual registered changed nodes')
        global_roles={'font','style','layout','config','brief'}
        pages=set()
        for key in changed:
            node=self.state['nodes'][key]
            pages.update(self.state['page_order'] if node['role'] in global_roles else self.scope(node['pages']))
        affected=[key for key,node in self.state['nodes'].items() if node['kind']=='artifact' and set(changed)&self.walk(key)]
        return {'changed':changed,'pages':[p for p in self.state['page_order'] if p in pages],
            'rebuild':affected,'freshness':{key:self.freshness(key) for key in affected},
            'note':'Scope derives from registered dependencies. Undeclared/global changes require full review; snapshot records production, not QA.'}

    def gate(self, canonical=None, exports=None, require_acceptance=False):
        self.require()
        canonical = canonical or self.state.get("canonical")
        exports = exports or []
        if canonical not in self.state["nodes"] or self.state["nodes"][canonical]["kind"] != "artifact":
            raise ValueError("Choose a registered canonical artifact")
        required = {canonical: ["automated", "editorial", "visual"]}
        for output in exports:
            if output not in self.state["nodes"] or self.state["nodes"][output]["kind"] != "artifact":
                raise ValueError("Choose registered export artifacts")
            if canonical != output and canonical not in self.walk(output):
                raise ValueError("Requested export does not depend on the canonical artifact")
            required.setdefault(output, []).extend(["automated", "export"])
        if require_acceptance:
            required[canonical].append("user_acceptance")
        blocking, warnings = [], []
        for key, layers in required.items():
            fresh = self.freshness(key)
            if not fresh["fresh"]:
                blocking.append({"target": key, "reason": "stale_artifact", "details": fresh["reasons"]})
            for layer in sorted(set(layers)):
                report = self.layer_status(key, layer)
                if report["state"] in {"pending", "blocked"}:
                    blocking.append({"target": key, "layer": layer, **report})
                warnings.extend({"target": key, "layer": layer, **f} for f in report["findings"] if f["severity"] == "warning")
            blocking.extend(self.unresolved_text_flow(key))
        brief_path = self.root / "content/brief.json"
        if brief_path.is_file():
            from production_contract import contract_findings
            export_paths = [self.path(self.state["nodes"][key]["path"]) for key in exports]
            blocking.extend(contract_findings(self.root, self.path(self.state["nodes"][canonical]["path"]), export_paths))
        return {"delivery_state": "blocked" if blocking else "ready_with_warnings" if warnings else "ready",
                "blocking": blocking, "warnings": warnings,
                "user_acceptance": self.layer_status(canonical, "user_acceptance"),
                "acceptance_required": require_acceptance,
                "scope": "Registered local dependencies and evidence; does not certify deployment or independent human approval"}


def list_arg(value):
    return [v.strip() for v in value.split(",") if v.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init"); init.add_argument("--pages", required=True); init.add_argument("--canonical")
    pages = commands.add_parser("pages"); pages.add_argument("--pages", required=True)
    reg = commands.add_parser("register"); reg.add_argument("id"); reg.add_argument("path")
    reg.add_argument("--kind", choices=["source", "artifact"], default="source")
    reg.add_argument("--role", default="copy"); reg.add_argument("--pages", default="all"); reg.add_argument("--depends", default="")
    snap = commands.add_parser("snapshot"); snap.add_argument("id")
    review = commands.add_parser("review"); review.add_argument("id"); review.add_argument("--layer", choices=LAYERS, required=True)
    review.add_argument("--evidence", required=True); review.add_argument("--pages")
    review.add_argument('--split-evidence',action='store_true',help='Preserve immutable per-page evidence for bounded future edits')
    verify = commands.add_parser("verify"); verify.add_argument("id"); verify.add_argument("--evidence", required=True)
    commands.add_parser("status")
    changes = commands.add_parser('changes'); changes.add_argument('--changed', action='append', required=True)
    gate = commands.add_parser("gate"); gate.add_argument("--canonical"); gate.add_argument("--exports", default=""); gate.add_argument("--require-acceptance", action="store_true")
    args = parser.parse_args()
    project = ProjectState(args.project)
    if args.command == "init": result = project.init(list_arg(args.pages), args.canonical)
    elif args.command == "pages": project.set_pages(list_arg(args.pages)); result = project.status()
    elif args.command == "register": result = project.register(args.id, args.path, args.kind, args.role, "all" if args.pages == "all" else list_arg(args.pages), list_arg(args.depends))
    elif args.command == "snapshot": result = project.snapshot(args.id)
    elif args.command == "review": result = project.review(args.id, args.layer, args.evidence, list_arg(args.pages) if args.pages else None,args.split_evidence)
    elif args.command == "verify": result = project.verify_pptx(args.id, args.evidence)
    elif args.command == "status": result = project.status()
    elif args.command == 'changes': result = project.change_plan(args.changed)
    elif args.command == "gate": result = project.gate(args.canonical, list_arg(args.exports), args.require_acceptance)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result.get("delivery_state") == "blocked" else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError, zipfile.BadZipFile, ET.ParseError) as error:
        print(json.dumps({"status": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
