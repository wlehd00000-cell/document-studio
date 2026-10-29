"""Company isolation through style, writing, scaffold, and optional install selection."""

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / 'company-packs'
SCRIPTS = ROOT / 'skills/report-html-pptx/scripts'
sys.path.insert(0,str(SCRIPTS))
sys.path.insert(0,str(ROOT / 'scripts'))

from company_pack import load_company_pack  # noqa: E402
from design_registry import tokens_for  # noqa: E402
from build_design_css import generate  # noqa: E402
from font_policy import evaluate_font_policy  # noqa: E402
from install_local import CORE_SKILLS, selected_skills, install  # noqa: E402


def run_cli(script, *args):
    return subprocess.run([sys.executable,str(script),*map(str,args)],
                          cwd=ROOT,check=True,capture_output=True,text=True)


def test_company_styles_are_isolated():
    retail=tokens_for(PACKS/'demo-retail','executive_report')
    manufacturing=tokens_for(PACKS/'demo-manufacturing','executive_report')
    assert '#C1456B' in generate(retail)
    assert '#184967' in generate(manufacturing)
    assert '#C1456B' not in generate(manufacturing)
    assert retail['profiles']['reading_report']['typography']['title_pt']==24
    assert manufacturing['profiles']['reading_report']['typography']['title_pt']==21


def test_casebook_and_writing_never_mix_companies():
    selector=SCRIPTS/'select_esg_reference.py'
    a=json.loads(run_cli(selector,'cover','--company-pack',PACKS/'demo-retail').stdout)
    b=json.loads(run_cli(selector,'process','--company-pack',PACKS/'demo-manufacturing').stdout)
    assert {c['case_id'] for c in a['cases']}=={'retail-cover'}
    assert {c['case_id'] for c in b['cases']}=={'manufacturing-process'}
    absent=json.loads(run_cli(selector,'cover','--company-pack',PACKS/'demo-manufacturing').stdout)
    assert absent['cases']==[]
    writing=ROOT/'skills/document-writing/scripts/find_writing_reference.py'
    flags=['--language','en-US','--document-family','business_proposal','--writing-function','recommendation']
    x=json.loads(run_cli(writing,'--company-pack',PACKS/'demo-retail',*flags).stdout)
    y=json.loads(run_cli(writing,'--company-pack',PACKS/'demo-manufacturing',*flags).stdout)
    assert x['references'][0]['id']=='retail-proposal-en'
    assert y['references'][0]['id']=='manufacturing-proposal-en'
    assert x['references'][0]['status']=='suggested'


def test_selective_language_install_inventory():
    assert selected_skills('none')==CORE_SKILLS
    assert selected_skills('ja')[-1]=='business-japanese-translation'
    assert 'business-korean-translation' not in selected_skills('ja')
    assert len(selected_skills('ko,ja'))==10


def test_core_only_install_does_not_copy_languages(tmp_path):
    destination=tmp_path/'installed'
    result=install(ROOT,destination,language_skills='none')
    assert result['status']=='installed'
    assert sorted(p.name for p in destination.iterdir() if p.is_dir())==sorted(CORE_SKILLS)
    assert not (destination/'business-korean-translation').exists()
    assert not (destination/'business-japanese-translation').exists()


def test_company_css_cli_creates_an_isolated_output(tmp_path):
    script=SCRIPTS/'build_design_css.py'
    output=tmp_path/'company.css'
    run_cli(script,'--company-pack',PACKS/'demo-retail','--output',output)
    assert '#C1456B' in output.read_text()
    run_cli(script,'--company-pack',PACKS/'demo-retail','--output',output,'--check')


def test_font_policy_stays_unverified_without_rendering():
    pack=load_company_pack(PACKS/'demo-retail')
    report=evaluate_font_policy(pack,'ja-JP')
    assert report['status']=='UNVERIFIED'
    assert report['redistribution'] is False
    assert evaluate_font_policy(pack,'ko-KR')['status']=='FAIL'


def test_scaffold_records_versioned_company_snapshot(tmp_path):
    script=SCRIPTS/'scaffold_report.py'
    common=['--title','Pilot','--language','en-US','--genre','proposal',
            '--interaction-mode','one_shot','--audience','Team leadership',
            '--reader-action','Decide on the pilot','--output-format','HTML',
            '--canvas','widescreen','--use','reading']
    for packid,shade in [('demo-retail','#C1456B'),('demo-manufacturing','#184967')]:
        folder=tmp_path/packid
        run_cli(script,folder,'--company-pack',PACKS/packid,*common)
        config=json.loads((folder/'report-config.json').read_text())
        snapshot=json.loads((folder/'content/company-pack-snapshot.json').read_text())
        assert config['company_pack']['pack_id']==packid
        assert config['company_pack']['snapshot_sha256']==snapshot['sha256']
        assert shade in (folder/'html/index.html').read_text()
        assert 'demo-mark.svg' not in (folder/'html/index.html').read_text()
        assert (PACKS/packid/'pack.json').is_file()
        assert json.loads((folder/'content/font-policy-review.json').read_text())['status']=='UNVERIFIED'


def test_unbranded_legacy_scaffold_still_runs(tmp_path):
    folder=tmp_path/'legacy'
    run_cli(SCRIPTS/'scaffold_report.py',folder,'--title','General report',
            '--language','ko-KR','--genre','report',
            '--interaction-mode','one_shot','--audience','Reviewers',
            '--reader-action','Review the findings','--output-format','HTML',
            '--canvas','a4-landscape','--use','reading')
    config=json.loads((folder/'report-config.json').read_text())
    assert 'company_pack' not in config
    assert (folder/'html/index.html').is_file()
