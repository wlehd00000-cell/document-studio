"""Detect invalid or stale public plugin metadata and links."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from audit_plugin_package import audit  # noqa: E402


def test_source_audit():
    report = audit(ROOT)
    assert report["status"] == "PASS", report["errors"]
    assert report["skills"] == 10
    assert report["relative_links_checked"] > 0


def test_read_only_audit_cli():
    run = subprocess.run([sys.executable, str(ROOT/"scripts/audit_plugin_package.py")],
                         cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    assert json.loads(run.stdout)["status"] == "PASS"
