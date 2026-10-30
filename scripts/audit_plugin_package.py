#!/usr/bin/env python3
"""Read-only audit of source integrity, skill entrypoints and local references."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "company-profile-analyzer", "report-html-pptx", "document-research",
    "document-architecture", "document-writing", "document-design",
    "visual-assets", "html-to-pptx",
    "business-korean-translation", "business-japanese-translation",
}
IGNORE = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "dist", "build"}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")


def audit(root: Path = ROOT) -> dict:
    root = Path(root)
    problems = []
    package = json.loads((root/"package-manifest.json").read_text(encoding="utf8"))
    main = json.loads((root/"plugin.json").read_text(encoding="utf8"))
    compat = json.loads((root/".codex-plugin/plugin.json").read_text(encoding="utf8"))
    version = main.get("version")
    if package.get("version") != version or compat.get("version") != version:
        problems.append("Plugin and package versions differ")
    if main.get("name") != compat.get("name"):
        problems.append("Plugin identity differs")
    if main.get("extensions", {}).get("com.openai", {}).get("interface") != compat.get("interface"):
        problems.append("Plugin listing interface differs")
    skills = {p.parent.name for p in (root/"skills").glob("*/SKILL.md")}
    if skills != REQUIRED:
        problems.append(f"Unexpected skill entrypoints: {sorted(skills ^ REQUIRED)}")
    actual = {}
    broken = []
    links = 0
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if IGNORE.intersection(rel.parts) or path.suffix in (".pyc", ".pyo"):
            continue
        if path.is_symlink():
            problems.append(f"Disallowed symlink: {rel}")
            continue
        if not path.is_file() or rel.as_posix() == "package-manifest.json":
            continue
        actual[rel.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        if rel.suffix != ".md" or "skills" not in rel.parts:
            continue
        for href in MARKDOWN_LINK.findall(path.read_text(encoding="utf8")):
            if href.startswith(("https:", "http:", "#", "mailto:", "plugin:", "data:", "app:")):
                continue
            link = href.split("#", 1)[0].split("?", 1)[0]
            if not link:
                continue
            links += 1
            if not (path.parent / link).exists():
                broken.append(f"{rel} -> {href}")
    tracked = package.get("files", {})
    missing = sorted(set(tracked)-set(actual))
    extra = sorted(set(actual)-set(tracked))
    mismatch = sorted(path for path in set(actual)&set(tracked) if actual[path] != tracked[path])
    if missing or extra or mismatch:
        problems.append(f"Inventory: missing={missing[:8]}, extra={extra[:8]}, SHA={mismatch[:8]}")
    if broken:
        problems.append(f"Broken relative skill links: {broken[:16]}")
    start = (root/"START_HERE.md").read_text(encoding="utf8")
    if version not in start or "Eight core skills" not in start or "Two optional language skills" not in start:
        problems.append("Stale start guide or incorrect skill count")
    orchestrator = (root/"skills/report-html-pptx/SKILL.md").read_text(encoding="utf8")
    intake = (root/"skills/report-html-pptx/references/intake-and-collaboration.md").read_text(encoding="utf8")
    if "automatic company-document extraction is planned, not implemented" in orchestrator or "v4.2부터" in intake:
        problems.append("Legacy instruction contradicts installed architecture")
    return {"status": "PASS" if not problems else "FAIL",
            "version": version, "skills": len(skills), "tracked_files": len(tracked),
            "relative_links_checked": links, "errors": problems}


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
