#!/usr/bin/env python3
"""Read-only release checks for the independent, fictional public edition."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "report-html-pptx", "document-research", "document-architecture",
    "document-writing", "document-design", "visual-assets",
    "business-korean-translation", "business-japanese-translation", "html-to-pptx",
}
DENY = (
    re.compile(r"GS Japan", re.I),
    re.compile(r"GS건설|GS칼텍스|GS글로벌"),
    re.compile(r"2026 Sustainability Report_Ko\.pdf"),
    re.compile(r"data:image/png;base64,[A-Za-z0-9+/=]{500}"),
)

def check() -> None:
    actual_skills = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
    if actual_skills != SKILLS:
        raise AssertionError(f"skill inventory mismatch: {actual_skills ^ SKILLS}")
    from install_local import verify_package
    verify_package(ROOT)
    for f in ROOT.rglob("*"):
        if not f.is_file() or f.suffix in {".woff2", ".png", ".zip"}:
            continue
        if f.suffix == ".py":
            ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        if f.suffix == ".json":
            json.loads(f.read_text(encoding="utf-8"))
        if f.suffix in {".py", ".md", ".html", ".css", ".js", ".mjs", ".json", ".yaml"}:
            text = f.read_text(encoding="utf-8")
            if f.name != "verify_public_release.py" and any(p.search(text) for p in DENY):
                raise AssertionError(f"source-derived or encoded brand found: {f.relative_to(ROOT)}")
    casebook = json.loads((ROOT / "skills/report-html-pptx/references/demo-esg-casebook.json").read_text(encoding="utf-8"))
    library = json.loads((ROOT / "skills/document-writing/references/demo-report-library.json").read_text(encoding="utf-8"))
    if len(casebook["cases"]) < 9 or len(library["excerpts"]) < 9:
        raise AssertionError("synthetic references are too small")
    if not all(case.get("synthetic") for case in casebook["cases"]):
        raise AssertionError("casebook must only contain synthetic cases")
    commands = [
        [sys.executable, "skills/document-writing/scripts/find_writing_reference.py", "--company", "retail", "--limit", "1"],
        [sys.executable, "skills/report-html-pptx/scripts/select_esg_reference.py", "process", "--summary", "--limit", "1"],
    ]
    for command in commands:
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
        json.loads(proc.stdout)
    print(json.dumps({"status":"passed","skills":len(SKILLS),"synthetic_cases":len(casebook["cases"]),"synthetic_excerpts":len(library["excerpts"])}, ensure_ascii=False))

if __name__ == "__main__":
    check()
