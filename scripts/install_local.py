"""Install the bundled document skills locally; no network or dependency installation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

CORE_SKILLS = ("company-profile-analyzer", "report-html-pptx", "document-architecture",
               "document-research", "document-writing", "document-design",
               "visual-assets", "html-to-pptx")
OPTIONAL_LANGUAGE_SKILLS = {"ko": "business-korean-translation", "ja": "business-japanese-translation"}
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
NAMES = CORE_SKILLS + tuple(OPTIONAL_LANGUAGE_SKILLS.values())


def selected_skills(language_skills: str = "ko,ja") -> tuple[str, ...]:
    """Keep legacy full-install behavior unless modules are explicitly selected."""
    if language_skills == "none":
        return CORE_SKILLS
    selected = language_skills.split(",")
    if not selected or any(value not in OPTIONAL_LANGUAGE_SKILLS for value in selected) or len(set(selected)) != len(selected):
        raise ValueError("--language-skills must be none, ko, ja, or ko,ja")
    return CORE_SKILLS + tuple(OPTIONAL_LANGUAGE_SKILLS[key] for key in selected)


def generated_cache(relative: Path) -> bool:
    return bool({".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "dist", "build"}.intersection(relative.parts)) or relative.suffix in {".pyc", ".pyo"}


def contained(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()) or resolved == root.resolve():
        raise ValueError("Path is outside the intended directory")
    return resolved


def verify_package(root: Path) -> dict:
    manifest = json.loads((root / "package-manifest.json").read_text(encoding="utf-8"))
    listed = manifest["files"]
    actual = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("Package symlinks are not supported")
        if path.is_file() and path != root / "package-manifest.json" and not generated_cache(path.relative_to(root)):
            actual.add(path.relative_to(root).as_posix())
    if actual != set(listed):
        raise ValueError("Package file inventory differs from the manifest")
    for rel, digest in listed.items():
        path = contained(root / rel, root)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Package integrity mismatch: " + rel)
    names=tuple(manifest.get('included_skills',NAMES))
    if not set(CORE_SKILLS).issubset(names) or not set(names).issubset(NAMES) or len(names)!=len(set(names)):
        raise ValueError('Invalid packaged skill selection')
    for name in names:
        if not (root / "skills" / name / "SKILL.md").is_file():
            raise ValueError("Required skill is missing: " + name)
    return manifest


def default_destination() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured:
        return Path(configured).expanduser() / "skills"
    choices = [Path.home() / ".agents" / "skills", Path.home() / ".codex" / "skills"]
    occupied = [p for p in choices if any((p / name).exists() for name in NAMES)]
    if len(occupied) > 1:
        raise ValueError("Existing copies use multiple locations; select --skills-dir after reviewing them")
    return occupied[0] if occupied else choices[0]


def directory_hashes(directory: Path) -> dict:
    result = {}
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError("Existing skill contains a symlink; review it before updating")
        if path.is_file() and not generated_cache(path.relative_to(directory)):
            result[path.relative_to(directory).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def install(root: Path, destination: Path, replace: bool = False, language: str = "ko",
            language_skills: str | None = None) -> dict:
    root = root.resolve()
    manifest = verify_package(root)
    if language_skills is None:
        language_skills=manifest.get('included_language_skills','ko,ja')
    names = selected_skills(language_skills)
    if not set(names).issubset(manifest.get('included_skills',NAMES)):
        raise ValueError('Requested language skill is not included in this package')
    destination = destination.expanduser().resolve()
    if destination == root or destination.is_relative_to(root) or root.is_relative_to(destination):
        raise ValueError("Install destination must be separate from the distribution package")
    for name in names:
        target = destination / name
        if target.is_symlink() or (target.exists() and not target.is_dir()):
            raise ValueError("Existing target is not an ordinary skill folder: " + name)
    expected = {name: directory_hashes(root / "skills" / name) for name in names}
    existing = {name: directory_hashes(destination / name) if (destination / name).exists() else None for name in names}
    changed = [name for name in names if existing[name] != expected[name]]
    conflicts = [name for name in changed if existing[name] is not None]
    if conflicts and not replace:
        raise ValueError("Existing skills differ; review them and use --replace to update with a backup")
    backup_root = None
    if changed:
        destination.mkdir(parents=True, exist_ok=True)
        backup_base = destination.parent / "document-backups"
        backup_root = backup_base / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        with tempfile.TemporaryDirectory(prefix="document-stage-", dir=destination.parent) as staging:
            stage = contained(Path(staging), destination.parent)
            for name in changed:
                staged = contained(stage / name, stage)
                shutil.copytree(root / "skills" / name, staged)
                if directory_hashes(staged) != expected[name]:
                    raise ValueError("Staged copy verification failed: " + name)
            moved_old = []
            moved_new = []
            try:
                for name in changed:
                    target = contained(destination / name, destination)
                    staged = contained(stage / name, stage)
                    if target.exists():
                        backup_root.mkdir(parents=True, exist_ok=True)
                        backup = contained(backup_root / name, backup_base)
                        target.replace(backup)
                        moved_old.append(name)
                    staged.replace(target)
                    moved_new.append(name)
                for name in names:
                    if directory_hashes(destination / name) != expected[name]:
                        raise ValueError("Installed copy verification failed: " + name)
            except Exception:
                for name in reversed(moved_new):
                    target = contained(destination / name, destination)
                    target.replace(contained(stage / (name + "-failed"), stage))
                for name in reversed(moved_old):
                    backup = contained(backup_root / name, backup_base)
                    backup.replace(contained(destination / name, destination))
                raise
            # TemporaryDirectory removes only this verified, newly created staging directory.
            contained(stage, destination.parent)
    guide_name = "staff-quickstart-ja.md" if language == "ja" else "staff-quickstart-ko.md"
    guide = (destination / "report-html-pptx" / "references" / guide_name).read_text(encoding="utf-8")
    return {
        "status": "installed" if changed else "already_installed",
        "version": manifest["version"],
        "skills_directory": str(destination),
        "skills": list(names),
        "language_skills": language_skills,
        "backup_directory": str(backup_root) if backup_root and backup_root.exists() else None,
        "verification": "Installed skill files match the package manifest",
        "tool_readiness": "Not certified by installation; check the requested output tools at first use",
        "guide_to_show_in_chat": guide,
        "next_step": "Use the skill on the next turn; if it is not discovered, start a new chat or restart the local app",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--language", choices=("ko", "ja"), default="ko")
    parser.add_argument("--language-skills", choices=("none", "ko", "ja", "ko,ja"), default=None,
                        help="Optional modules; defaults to the packaged selection (both in the source edition)")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.verify_only:
            manifest = verify_package(root)
            result = {"status": "package_verified", "version": manifest["version"], "installed": False}
        else:
            result = install(root, args.skills_dir or default_destination(), args.replace, args.language,
                             args.language_skills)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "installed": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
