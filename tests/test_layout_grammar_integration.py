"""Production cannot pretend an accepted grammar was applied or freshly reviewed."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/report-html-pptx/scripts'
sys.path.insert(0,str(SCRIPTS))
sys.path.insert(0,str(ROOT/'tests'))
from test_company_integration import run_cli,PACKS  # noqa: E402
from test_layout_grammar_audit import project  # noqa: E402
from test_layout_plan import brief  # noqa: E402
from plan_layout_grammar import write_layout_plan  # noqa: E402
from project_state import ProjectState  # noqa: E402
from audit_layout_grammar import audit_layout_grammar  # noqa: E402
from production_contract import grammar_audit_findings  # noqa: E402


def scaffold(tmp_path,pack='demo-retail'):
    destination=tmp_path/'document'
    run_cli(SCRIPTS/'scaffold_report.py',destination,'--company-pack',PACKS/pack,
            '--title','Original report','--language','en-US','--genre','proposal',
            '--interaction-mode','one_shot','--audience','Team leadership',
            '--reader-action','Decide on the pilot','--output-format','HTML',
            '--canvas','widescreen','--use','reading')
    return destination


def test_branded_scaffold_defers_grammar_until_real_copy(tmp_path):
    folder=scaffold(tmp_path)
    config=json.loads((folder/'report-config.json').read_text())
    snapshot=json.loads((folder/'content/company-pack-snapshot.json').read_text())
    assert config['company_pack']['visual_grammar']['stage']=='pending_final_manuscript'
    assert config['company_pack']['visual_grammar'].get('rule_ids',[])==[]
    assert 'layout_grammar' in snapshot['snapshot']
    assert not (folder/'content/layout-plan.json').exists()


def test_new_plan_registers_explicit_html_dependency(tmp_path):
    root=scaffold(tmp_path)
    page=brief()
    page['document_family']='business_proposal'
    (root/'content/page-brief.json').write_text(json.dumps(page),encoding='utf-8')
    write_layout_plan(root,'content/page-brief.json',PACKS/'demo-retail')
    state=ProjectState(root)
    assert 'page_brief' in state.state['nodes']
    assert 'layout_plan' in state.state['nodes']
    assert 'layout_plan' in state.state['nodes']['html']['depends']
    assert 'company_pack' in state.state['nodes']['layout_plan']['depends']
    assert state.freshness('layout_plan')['fresh'] is True
    assert state.freshness('html')['fresh'] is False


def test_other_company_pack_cannot_be_substituted_after_scaffold(tmp_path):
    root=scaffold(tmp_path)
    page=brief();page['document_family']='business_proposal'
    (root/'content/page-brief.json').write_text(json.dumps(page),encoding='utf-8')
    with pytest.raises(ValueError,match='Company Pack'):
        write_layout_plan(root,'content/page-brief.json',PACKS/'demo-manufacturing')


def test_missing_or_unverified_browser_measurement_blocks_branded_gate(tmp_path):
    root=project(tmp_path)
    (root/'report-config.json').write_text(json.dumps({'company_pack':{'pack_id':'acme'}}))
    assert any('missing' in str(item) for item in grammar_audit_findings(root,root/'html/index.html'))
    audit_layout_grammar(root,browser_path=Path('/nonexistent/browser-bin'))
    result=grammar_audit_findings(root,root/'html/index.html')
    assert result
    assert any('unverified' in str(item).lower() for item in result)


@pytest.mark.parametrize('changed_file',[
    'html/index.html','content/layout-plan.json','report-config.json','html/assets/new.svg',
])
def test_changed_inputs_invalidate_previous_grammar_receipt(tmp_path,changed_file):
    root=project(tmp_path)
    (root/'report-config.json').write_text(json.dumps({'company_pack':{'pack_id':'acme'},'canvas':'widescreen'}))
    (root/'html/assets').mkdir()
    (root/'html/assets/new.svg').write_text('<svg/>',encoding='utf-8')
    audit_layout_grammar(root,browser_path=Path('/nonexistent/browser-bin'))
    target=root/changed_file
    target.write_text(target.read_text()+' ',encoding='utf-8')
    findings=grammar_audit_findings(root,root/'html/index.html')
    assert any('stale' in str(item).lower() for item in findings),findings


def test_unbranded_legacy_project_has_no_new_grammar_gate(tmp_path):
    root=tmp_path/'plain'; (root/'html').mkdir(parents=True)
    (root/'html/index.html').write_text('<h1>General</h1>')
    assert grammar_audit_findings(root,root/'html/index.html')==[]


def test_missing_measured_relationships_cannot_be_disguised_as_pass(tmp_path):
    root=project(tmp_path)
    (root/'report-config.json').write_text(json.dumps({'company_pack':{'pack_id':'acme'}}))
    receipt=audit_layout_grammar(root,browser_path=Path('/nonexistent/browser-bin'))
    assert receipt['status']=='UNVERIFIED'
    screenshot=root/'qa/layout-grammar-pages/P1.png'
    screenshot.parent.mkdir(parents=True)
    screenshot.write_bytes(b'fixture: synthetic image receipt')
    receipt['status']='PASS'
    receipt['inspected_pages']=['P1']
    receipt['screenshots']=[{'page_id':'P1','path':'qa/layout-grammar-pages/P1.png',
                            'sha256':hashlib.sha256(screenshot.read_bytes()).hexdigest()}]
    receipt['relationships']=[]
    (root/'qa/layout-grammar-application.json').write_text(json.dumps(receipt),encoding='utf-8')
    result=grammar_audit_findings(root,root/'html/index.html')
    assert any('relation_coverage' in entry['reason'] for entry in result),result
