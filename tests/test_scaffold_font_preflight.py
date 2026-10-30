"""Optional WOFF2 reader errors must be detected before scaffold writes."""
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"skills/report-html-pptx/scripts"))
import quality_floor  # noqa: E402
from scaffold_report import scaffold  # noqa: E402


def test_failed_font_preflight_leaves_no_project(tmp_path, monkeypatch):
    target = tmp_path/"new-report"
    def missing_reader(*args, **kwargs):
        raise RuntimeError("Brotli reader missing")
    monkeypatch.setattr(quality_floor, "preflight_bundled_font_inspection", missing_reader)
    with pytest.raises(RuntimeError, match="Brotli"):
        scaffold(target, title="Test", subtitle="Draft", language="ko-KR",
                 genre="report", interaction_mode="one_shot",
                 audience="Team", reader_action="Review",
                 output_format="HTML", canvas="a4-landscape", use="reading")
    assert not target.exists()


def test_no_bundled_fonts_retains_unverified_path(tmp_path):
    assert quality_floor.preflight_bundled_font_inspection(tmp_path, ["ko-KR"]) is False


def test_missing_brotli_is_blocking_with_supplied_fonts(tmp_path, monkeypatch):
    for filename in quality_floor.FONT_FILES.values():
        (tmp_path/filename).write_bytes(b"fake")
    def missing_brotli(_path):
        raise ModuleNotFoundError("brotli")
    monkeypatch.setattr(quality_floor, "font_metadata", missing_brotli)
    with pytest.raises(RuntimeError, match="fontTools and Brotli"):
        quality_floor.preflight_bundled_font_inspection(tmp_path, ["ja-JP"])
