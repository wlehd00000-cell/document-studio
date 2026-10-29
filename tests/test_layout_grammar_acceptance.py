"""A truly reviewed synthetic pack supports different original compositions."""
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/report-html-pptx/scripts'))
sys.path.insert(0,str(ROOT/'skills/company-profile-analyzer/scripts'))
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'tests'))
from test_visual_review_approval import fixture,write  # noqa: E402
from test_layout_plan import brief  # noqa: E402
from layout_grammar import compute_evidence_digest  # noqa: E402
from record_visual_review import record_visual_review  # noqa: E402
from build_company_pack import change_review_status  # noqa: E402
from company_pack import load_company_pack  # noqa: E402
from layout_plan import build_layout_plan  # noqa: E402
from html_grammar_contract import inspect_html_grammar  # noqa: E402
from audit_layout_grammar import audit_layout_grammar  # noqa: E402
from package_account_plugin import build_account_plugin  # noqa: E402
from zipfile import ZipFile


CASES=ROOT/'tests/fixtures/layout-grammar'


def approved_relation_pack(tmp_path):
    pack,index,grammar=fixture(tmp_path)
    index['pages'][0]['regions'].append({'region_id':'SRC-A-P1-R2','kind':'text','bbox_norm':[0.1,0.5,0.9,0.75]})
    index['observations'].append({'observation_id':'EV-002','source_id':'SRC-A',
        'page':1,'region_id':'SRC-A-P1-R2','role':'body','bbox_norm':[0.1,0.5,0.9,0.75],
        'evidence_kind':'visually_observed','confidence':'medium','status':'suggested',
        'observation':'Body prose below heading'})
    rule=grammar['rules'][0]
    rule.update(rule_id='heading-above-body',element_roles=['heading','body'],
                relationships=['heading above body'],variation=['scale','alignment','spacing'],
                evidence_ids=['EV-001','EV-002'],
                evidence_refs=[{'source_id':'SRC-A','page':1,'region_id':'SRC-A-P1-R1'},
                               {'source_id':'SRC-A','page':1,'region_id':'SRC-A-P1-R2'}])
    write(pack/'design/visual-evidence.json',index)
    write(pack/'design/layout-grammar.json',grammar)
    write(tmp_path/'visual-decisions.json',{'schema_version':'visual-review-decisions/1.0',
          'preview_ids':['study-editorial'],
          'decisions':[{'rule_id':'heading-above-body','action':'accept',
                        'note':'Both roles inspected on an original fictional source',
                        'evidence_digest':compute_evidence_digest(['EV-001','EV-002'],index)}]})
    record_visual_review(pack_dir=pack,grammar_file=pack/'design/layout-grammar.json',
                         decision_file=tmp_path/'visual-decisions.json',reviewer='Synthetic reviewer')
    change_review_status(pack,reviewer='Synthetic reviewer',note='Reviewed source evidence',action='review')
    change_review_status(pack,reviewer='Synthetic owner',note='Production accepted for synthetic fixture',action='approve')
    return load_company_pack(pack)


def html_cases():
    return [(key,(CASES/key).read_text(encoding='utf-8'))
            for key in ('typography-led.html','illustration-led.html')]


def test_persisted_reviewed_pack_accepts_two_distinct_authored_html_compositions(tmp_path):
    pack=approved_relation_pack(tmp_path)
    plan=build_layout_plan(pack,brief())
    assert plan['pages'][0]['mode']=='approved_grammar'
    assert plan['pages'][0]['rules'][0]['relationships'][0]['operator']=='above'
    samples=html_cases()
    assert samples[0][1]!=samples[1][1]
    for _,html in samples:
        result=inspect_html_grammar(html,plan)
        assert result['status']=='PASS',result['findings']


def test_browser_really_measures_two_different_approved_compositions(tmp_path):
    pack=approved_relation_pack(tmp_path)
    plan=build_layout_plan(pack,brief())
    measured=[]
    for index,(_,html) in enumerate(html_cases()):
        project=tmp_path/f'composed-{index}'
        (project/'content').mkdir(parents=True)
        (project/'html').mkdir()
        (project/'content/layout-plan.json').write_text(json.dumps(plan))
        (project/'html/index.html').write_text(html)
        result=audit_layout_grammar(project)
        if result['status']=='UNVERIFIED':
            reason=result.get('reason','')
            if reason.startswith('Browser unavailable:'):
                pytest.skip('Actual browser unavailable; separate HTML semantic tests remain required')
            pytest.fail(f'Browser execution was incomplete, not legitimately unavailable: {reason}')
        assert result['status']=='PASS',result['findings']
        assert result['relationships'][0]['passed'] is True
        measured.append((result['relationships'][0]['leader_rect'],result['screenshots'][0]['sha256']))
    assert measured[0][0]!=measured[1][0]
    assert measured[0][1]!=measured[1][1]


def test_public_plugin_package_excludes_real_company_source_files(tmp_path):
    output=tmp_path/'document-studio-audit.zip'
    result=build_account_plugin(ROOT,output,language_skills='ko,ja')
    assert result['skill_count']==10
    with ZipFile(output) as archive:
        files=archive.namelist()
        assert not any(path.lower().endswith(('.pdf','.pptx','.ai','.woff2','.docx')) for path in files)
        assert not any('/company-packs/' in path or '/private/' in path for path in files)
        assert 'document-studio/skills/report-html-pptx/scripts/layout_plan.py' in files
        assert 'document-studio/skills/report-html-pptx/scripts/audit_layout_grammar.mjs' in files
