"""Exported plugins must be installable and exclude unselected/private resources."""
import json
from pathlib import Path
import shutil
import sys
import zipfile

import pytest


ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'skills/report-html-pptx/scripts'))
from export_company_plugin import export_company_plugin  # noqa: E402
from install_local import verify_package,install  # noqa: E402
from company_pack import load_company_pack  # noqa: E402
sys.path.insert(0,str(ROOT/'skills/company-profile-analyzer/scripts'))
sys.path.insert(0,str(ROOT/'tests'))
from test_visual_review_approval import fixture,decision  # noqa: E402
from record_visual_review import record_visual_review  # noqa: E402
from build_company_pack import change_review_status  # noqa: E402


def test_export_selected_skills_and_install(tmp_path):
    archive=tmp_path/'retail.zip'
    result=export_company_plugin(ROOT/'company-packs/demo-retail',archive,language_skills='ja')
    assert len(result['skills'])==9
    assert archive.exists()
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        assert not any('business-korean-translation' in name for name in names)
        assert any('business-japanese-translation/SKILL.md' in name for name in names)
        assert not any(name.endswith(('.woff2','.ttf','.otf')) for name in names)
        z.extractall(tmp_path/'unpacked')
    root=tmp_path/'unpacked/demo-retail-documents'
    assert verify_package(root)['included_language_skills']=='ja'
    assert load_company_pack(root/'company-pack').pack_id=='demo-retail'
    assert load_company_pack(root/'skills/company-profile-analyzer/assets/company-pack').pack_id=='demo-retail'
    target=tmp_path/'installed'
    outcome=install(root,target)
    assert len(outcome['skills'])==9
    assert (target/'company-profile-analyzer/assets/company-pack/pack.json').exists()
    assert not (target/'business-korean-translation').exists()


def test_public_export_rejects_unapproved_pack(tmp_path):
    folder=tmp_path/'draft'
    shutil.copytree(ROOT/'company-packs/demo-retail',folder)
    # Path must use its own pack_id for the shared loader.
    draft=tmp_path/'demo-retail'
    folder.rename(draft)
    metadata=json.loads((draft/'pack.json').read_text())
    metadata['status']='draft'
    (draft/'pack.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError,match='approved'):
        export_company_plugin(draft,tmp_path/'no.zip')


def test_public_export_blocks_private_or_unknown_rights(tmp_path):
    folder=tmp_path/'demo-retail'
    shutil.copytree(ROOT/'company-packs/demo-retail',folder)
    metadata=json.loads((folder/'pack.json').read_text())
    metadata.pop('synthetic')
    (folder/'pack.json').write_text(json.dumps(metadata))
    (folder/'sources.json').write_text(json.dumps({'sources':[
        {'source_id':'SOURCE-1','visibility':'private','rights':'unverified'}]}))
    with pytest.raises(ValueError,match='private or unverified'):
        export_company_plugin(folder,tmp_path/'no.zip')


def test_two_exported_companies_have_distinct_profiles(tmp_path):
    paths=[]
    for pack in ('demo-retail','demo-manufacturing'):
        out=tmp_path/(pack+'.zip')
        export_company_plugin(ROOT/'company-packs'/pack,out)
        with zipfile.ZipFile(out) as z:
            name=pack+'-documents/company-pack/design/tokens.json'
            paths.append(json.loads(z.read(name)))
    assert paths[0]['palette']['brand']['blue']=='#C1456B'
    assert paths[1]['palette']['brand']['blue']=='#184967'


def test_export_preserves_approved_visual_rules_and_review_provenance(tmp_path):
    pack,index,_=fixture(tmp_path)
    record_visual_review(pack_dir=pack,grammar_file=pack/'design/layout-grammar.json',
                         decision_file=decision(pack,index),reviewer='Reviewer')
    change_review_status(pack,reviewer='Reviewer',note='Visual board verified',action='review')
    change_review_status(pack,reviewer='Owner',note='Publish fictional pack',action='approve')
    archive=tmp_path/'acme.zip'
    export_company_plugin(pack,archive)
    with zipfile.ZipFile(archive) as z:
        contents=z.namelist()
        path='acme-documents/company-pack/design/'
        assert path+'layout-grammar.json' in contents
        assert path+'visual-review.json' in contents
        assert path+'visual-evidence.json' in contents
        assert not any('preview' in name.lower() and name.endswith('.png') for name in contents)
        assert json.loads(z.read(path+'layout-grammar.json'))['rules'][0]['status']=='accepted'
