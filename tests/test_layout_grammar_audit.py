"""A PASS must come from real DOM geometry, not only valid data attributes."""
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/report-html-pptx/scripts'))
sys.path.insert(0,str(ROOT/'tests'))
from test_layout_plan import brief  # noqa: E402
from test_layout_grammar_selection import relational_pack  # noqa: E402
from layout_plan import build_layout_plan  # noqa: E402
from audit_layout_grammar import audit_layout_grammar  # noqa: E402


def document(*, relation='above', shifted=False, hidden=False, clipped=False):
    # Browser measures actual transformed rectangles, not source CSS values.
    left,top=('90px','210px') if relation=='above' else ('370px','80px')
    if shifted:left,top=('20px','30px')
    if clipped:left,top=('720px','530px')
    visibility='visibility:hidden;' if hidden else ''
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
        .page {{position:relative;width:800px;height:600px;background:white;overflow:hidden}}
        #title {{position:absolute;left:80px;top:50px;width:220px;height:90px}}
        #copy {{position:absolute;left:{left};top:{top};width:230px;height:65px;{visibility}}}
        body {{margin:0}}
        </style></head><body><main class="page" data-page-id="P1">
        <h1 id="title" data-grammar-element-id="title" data-grammar-rule-ids="heading-above-body">Fictional studio</h1>
        <p id="copy" data-grammar-element-id="copy" data-grammar-rule-ids="heading-above-body">New data, independent copy.</p>
        </main></body></html>'''


def project(tmp_path, **options):
    pack=relational_pack(tmp_path)
    if options.get('relation')=='left_of':
        from dataclasses import replace
        pack=replace(pack,layout_grammar=({**pack.layout_grammar[0],
                    'relationships':['heading left_of body']},))
    root=tmp_path/'project'
    (root/'content').mkdir(parents=True)
    (root/'html').mkdir()
    plan=build_layout_plan(pack,brief())
    (root/'content/layout-plan.json').write_text(json.dumps(plan),encoding='utf-8')
    (root/'html/index.html').write_text(document(**options),encoding='utf-8')
    return root


def real_browser_or_skip(result):
    if result['status']=='UNVERIFIED':
        pytest.skip('No functioning existing browser: '+str(result.get('reason')))


def test_missing_browser_yields_unverified_not_pass(tmp_path):
    root=project(tmp_path)
    result=audit_layout_grammar(root,browser_path=Path('/nonexistent/browser-bin'))
    assert result['status']=='UNVERIFIED'
    assert result['requires_visual_review'] is True
    assert (root/'qa/layout-grammar-application.json').is_file()


def test_invalid_static_trace_fails_before_browser(tmp_path):
    root=project(tmp_path)
    file=root/'html/index.html'
    file.write_text(file.read_text().replace('data-grammar-element-id="copy"',
                 'data-grammar-element-id="wrong"'),encoding='utf-8')
    result=audit_layout_grammar(root,browser_path=Path('/nonexistent/browser-bin'))
    assert result['status']=='FAIL'
    assert any('anchor' in str(issue).lower() for issue in result['findings'])


@pytest.mark.parametrize('relation',['above','left_of'])
def test_browser_measures_both_spatial_relationships(tmp_path,relation):
    root=project(tmp_path,relation=relation)
    result=audit_layout_grammar(root)
    real_browser_or_skip(result)
    assert result['status']=='PASS',result['findings']
    assert result['relationships'][0]['operator']==relation
    assert result['relationships'][0]['passed'] is True
    assert (root/'qa/layout-grammar-pages/P1.png').is_file()
    assert result['screenshots'][0]['page_id']=='P1'


@pytest.mark.parametrize('case',[
    {'shifted':True}, {'hidden':True}, {'clipped':True},
])
def test_browser_rejects_overlap_hidden_or_off_canvas_content(tmp_path,case):
    root=project(tmp_path,**case)
    result=audit_layout_grammar(root)
    real_browser_or_skip(result)
    assert result['status']=='FAIL'
    assert result['findings']


def test_qa_receipt_binds_actual_html_plan_and_checker(tmp_path):
    root=project(tmp_path)
    result=audit_layout_grammar(root,browser_path=Path('/nonexistent/browser-bin'))
    assert result['schema_version']=='layout-grammar-audit/1.0'
    assert result['plan_sha256']==json.loads((root/'content/layout-plan.json').read_text())['plan_sha256']
    assert len(result['html_sha256'])==64
    assert 'checker' in result['tool_receipt']
    assert result['inspected_pages']==[]


def test_neutral_page_audit_not_applicable_without_browser(tmp_path):
    root=tmp_path/'neutral'
    (root/'content').mkdir(parents=True)
    (root/'html').mkdir()
    (root/'content/layout-plan.json').write_text(json.dumps(build_layout_plan(None,brief())))
    (root/'html/index.html').write_text('<section data-page-id="P1">General design</section>')
    result=audit_layout_grammar(root,browser_path=Path('/nonexistent/browser-bin'))
    assert result['status']=='NOT_APPLICABLE'
