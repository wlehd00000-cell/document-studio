"""Actual authored markup must trace to every approved rule and page element."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/report-html-pptx/scripts'))
sys.path.insert(0,str(ROOT/'tests'))
from test_layout_plan import brief  # noqa: E402
from test_layout_grammar_selection import relational_pack  # noqa: E402
from layout_plan import build_layout_plan  # noqa: E402
from html_grammar_contract import inspect_html_grammar  # noqa: E402


def markup(title='A result', body='Verified description', variant='editorial'):
    return f'''<!doctype html><html><head><title>Original composition</title></head><body>
      <section class="page {variant}" data-page-id="P1">
        <h1 data-grammar-element-id="title" data-grammar-rule-ids="heading-above-body">{title}</h1>
        <p data-grammar-element-id="copy" data-grammar-rule-ids="heading-above-body">{body}</p>
      </section>
    </body></html>'''


def test_valid_html_traces_rule_and_element_on_correct_page(tmp_path):
    plan=build_layout_plan(relational_pack(tmp_path),brief())
    result=inspect_html_grammar(markup(),plan)
    assert result['status']=='PASS'
    assert result['findings']==[]
    assert result['inspected_pages']==['P1']


def test_missing_or_duplicate_page_or_element_anchor_fails(tmp_path):
    plan=build_layout_plan(relational_pack(tmp_path),brief())
    for invalid in [markup().replace('data-page-id="P1"','data-page-id="wrong"'),
                    markup().replace('data-grammar-element-id="copy"','data-grammar-element-id="title"'),
                    markup().replace('<p data-grammar','<p data-no-grammar')]:
        result=inspect_html_grammar(invalid,plan)
        assert result['status']=='FAIL'
        assert result['findings']


def test_unknown_rule_and_cross_page_anchor_fail(tmp_path):
    plan=build_layout_plan(relational_pack(tmp_path),brief())
    unknown=markup().replace('heading-above-body','malicious-foreign-rule')
    assert inspect_html_grammar(unknown,plan)['status']=='FAIL'
    other=markup().replace('data-grammar-element-id="copy"','data-grammar-element-id="foreign"')
    assert inspect_html_grammar(other,plan)['status']=='FAIL'


def test_invalid_markup_attribute_identifier_is_rejected(tmp_path):
    plan=build_layout_plan(relational_pack(tmp_path),brief())
    changed=markup().replace('data-grammar-element-id="title"',
                            'data-grammar-element-id="<script>"')
    assert inspect_html_grammar(changed,plan)['status']=='FAIL'


def test_distinct_html_compositions_satisfy_same_semantic_contract(tmp_path):
    plan=build_layout_plan(relational_pack(tmp_path),brief())
    editorial=markup(variant='editorial')
    poster=markup(variant='poster')
    assert editorial!=poster
    assert inspect_html_grammar(editorial,plan)['status']=='PASS'
    assert inspect_html_grammar(poster,plan)['status']=='PASS'


def test_neutral_page_keeps_generic_html_without_company_rule_ids():
    plan=build_layout_plan(None,brief())
    html='<main><section class="page" data-page-id="P1"><h1>Unbranded</h1></section></main>'
    result=inspect_html_grammar(html,plan)
    assert result['status']=='NOT_APPLICABLE'


def test_needs_revision_plan_is_never_static_approved(tmp_path):
    plan=build_layout_plan(relational_pack(tmp_path),brief(reading_order=['copy','title']))
    result=inspect_html_grammar(markup(),plan)
    assert result['status']=='FAIL'
    assert any('plan' in f.lower() for f in result['findings'])
