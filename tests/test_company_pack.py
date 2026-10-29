"""Company Pack validation, inheritance and tenant-isolation regression tests."""

import json
import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "skills/report-html-pptx/scripts"
sys.path.insert(0, str(SCRIPTS))

from company_pack import (  # noqa: E402
    CompanyPackError,
    load_company_pack,
    resolve_design_tokens,
    validate_company_pack,
)


def make_pack(root, pack_id, *, parent_pack=None, design=None, writing=None, status="approved"):
    folder = root / pack_id
    folder.mkdir()
    (folder / "pack.json").write_text(json.dumps({
        "schema_version": "company-pack/1.0", "pack_id": pack_id,
        "company_name": pack_id.title(), "version": "1.0.0",
        "status": status, "default_language": "en-US",
        "enabled_languages": ["en-US"], "parent_pack": parent_pack,
    }), encoding="utf8")
    if design is not None:
        (folder / "design").mkdir()
        (folder / "design/tokens.json").write_text(json.dumps(design), encoding="utf8")
    if writing is not None:
        (folder / "writing").mkdir()
        (folder / "writing/references.json").write_text(json.dumps({"references": writing}), encoding="utf8")
    return folder


def test_independent_packs_and_deep_merge(tmp_path):
    make_pack(tmp_path, "group", design={"palette": {"brand": {"blue": "#111111"}}})
    child = make_pack(tmp_path, "child", parent_pack="group",
                      design={"palette": {"brand": {"green": "#222222"}}})
    other = make_pack(tmp_path, "other", design={"palette": {"brand": {"blue": "#333333"}}})
    a = load_company_pack(child)
    b = load_company_pack(other)
    base = {"palette": {"brand": {"blue": "#000000", "green": "#000000"}}, "profiles": {"reading_report": {}}}
    assert resolve_design_tokens(base, a, "executive_report")["palette"]["brand"] == {"blue": "#111111", "green": "#222222"}
    assert resolve_design_tokens(base, b, "executive_report")["palette"]["brand"]["blue"] == "#333333"
    assert not validate_company_pack(a)


@pytest.mark.parametrize("invalid", [
    {"pack_id": "../escape"}, {"enabled_languages": []},
    {"default_language": "ja-JP"}, {"status": "fictional"},
    {"version": "not-semver"},
])
def test_reject_invalid_fields(tmp_path, invalid):
    folder = make_pack(tmp_path, "example")
    data = json.loads((folder / "pack.json").read_text())
    data.update(invalid)
    (folder / "pack.json").write_text(json.dumps(data))
    with pytest.raises(CompanyPackError):
        load_company_pack(folder)


def test_reject_invalid_json(tmp_path):
    folder = make_pack(tmp_path, "example")
    (folder / "pack.json").write_text("{")
    with pytest.raises(CompanyPackError):
        load_company_pack(folder)


def test_reject_parent_cycles(tmp_path):
    make_pack(tmp_path, "alpha", parent_pack="beta")
    make_pack(tmp_path, "beta", parent_pack="alpha")
    with pytest.raises(CompanyPackError, match="cycle"):
        load_company_pack(tmp_path / "alpha")


def test_reject_external_paths_and_symlinks(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    folder = make_pack(tmp_path, "inside", parent_pack="../../outside")
    with pytest.raises(CompanyPackError):
        load_company_pack(folder)
    data = json.loads((folder / "pack.json").read_text())
    data["parent_pack"] = None
    (folder / "pack.json").write_text(json.dumps(data))
    (folder / "design").symlink_to(outside, target_is_directory=True)
    with pytest.raises(CompanyPackError, match="symlink"):
        load_company_pack(folder)


def test_writing_reference_provenance_required(tmp_path):
    folder = make_pack(tmp_path, "example", writing=[{"id": "x", "text": "No source"}])
    with pytest.raises(CompanyPackError, match="source"):
        load_company_pack(folder)


def test_reject_css_injection_in_company_tokens(tmp_path):
    folder = make_pack(tmp_path, "example", design={"palette": {"brand": {"blue": "red;}body{display:none"}}})
    with pytest.raises(CompanyPackError, match="Unsafe CSS"):
        load_company_pack(folder)


def test_design_cases_inherit_with_source_trace(tmp_path):
    parent=make_pack(tmp_path,'group')
    (parent/'design').mkdir()
    (parent/'design/design-casebook.json').write_text(json.dumps({'cases':[
        {'case_id':'cover','source_ids':['SOURCE-1'],'status':'observed','jobs':['cover']}
    ]}))
    child=make_pack(tmp_path,'child',parent_pack='group')
    pack=load_company_pack(child)
    assert pack.design_cases[0]['origin_pack']=='group'
    assert pack.design_cases[0]['source_ids']==['SOURCE-1']
