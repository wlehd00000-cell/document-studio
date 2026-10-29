"""Production must choose explicit reviewed company rules or neutral fallback."""
import json
from dataclasses import replace
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'skills/report-html-pptx/scripts'))
sys.path.insert(0,str(ROOT/'skills/company-profile-analyzer/scripts'))
from test_visual_review_approval import fixture,decision  # noqa: E402
from record_visual_review import record_visual_review  # noqa: E402
from build_company_pack import change_review_status  # noqa: E402
from company_pack import load_company_pack  # noqa: E402
from select_layout_grammar import select_layout_grammar  # noqa: E402


def approved_pack(tmp_path):
    pack,index,_=fixture(tmp_path)
    record_visual_review(pack_dir=pack,grammar_file=pack/'design/layout-grammar.json',
                         decision_file=decision(pack,index),reviewer='Jane')
    change_review_status(pack,reviewer='Jane',note='Inspected visual board',action='review')
    change_review_status(pack,reviewer='Owner',note='Approved company pack',action='approve')
    return load_company_pack(pack)


def choose(pack,**overrides):
    kwargs={'document_family':'profile','page_family':'cover','content_roles':['heading'],
            'density':'medium','intended_use':'reading'}
    kwargs.update(overrides)
    return select_layout_grammar(pack,**kwargs)


def test_approved_rules_are_ranked_and_explained(tmp_path):
    result=choose(approved_pack(tmp_path))
    assert result['mode']=='approved_grammar'
    assert result['rules'][0]['rule_id']=='title-band'
    assert result['rules'][0]['evidence_ids']==['EV-001']
    assert result['rules'][0]['reason']


def test_unapproved_pack_is_not_usable(tmp_path):
    pack,_,_=fixture(tmp_path)
    assert choose(load_company_pack(pack))['mode']=='neutral_fallback'


def test_wrong_company_document_family_or_content_has_fallback(tmp_path):
    pack=approved_pack(tmp_path)
    assert choose(pack,document_family='sales_report')['mode']=='neutral_fallback'
    assert choose(pack,content_roles=['chart'])['mode']=='neutral_fallback'
    assert choose(pack,page_family='appendix')['mode']=='neutral_fallback'
    assert choose(pack,page_family='unknown')['mode']=='neutral_fallback'


def test_no_company_pack_returns_explicit_fallback():
    assert choose(None)['mode']=='neutral_fallback'


def test_child_cannot_promote_rule_from_unapproved_parent(tmp_path):
    parent=approved_pack(tmp_path)
    metadata=json.loads((parent.root/'pack.json').read_text())
    metadata['status']='draft'
    (parent.root/'pack.json').write_text(json.dumps(metadata))
    child=tmp_path/'child'
    child.mkdir()
    child_meta=dict(metadata,pack_id='child',company_name='Child',
                    status='approved',parent_pack='acme')
    (child/'pack.json').write_text(json.dumps(child_meta))
    assert choose(load_company_pack(child))['mode']=='neutral_fallback'


def relational_pack(tmp_path, **edits):
    original=approved_pack(tmp_path)
    rule={**original.layout_grammar[0],
          'rule_id':'heading-above-body',
          'element_roles':['heading','body'],
          'relationships':['heading above body'],
          'variation':['scale','spacing','alignment'],
          'constraints':{'allowed_densities':['medium'],'allowed_uses':['reading']},
          **edits}
    return replace(original,layout_grammar=(rule,))


def test_multi_role_requires_every_participating_content_role(tmp_path):
    pack=relational_pack(tmp_path)
    assert choose(pack,content_roles=['heading'])['mode']=='neutral_fallback'
    assert choose(pack,content_roles=['body'])['mode']=='neutral_fallback'
    result=choose(pack,content_roles=['heading','body'])
    assert result['mode']=='approved_grammar'
    assert result['rules'][0]['rule_id']=='heading-above-body'


def test_selected_relationship_and_source_metadata_survive(tmp_path):
    rule=choose(relational_pack(tmp_path),content_roles=['body','heading'])['rules'][0]
    assert rule['relationships']==['heading above body']
    assert rule['element_roles']==['heading','body']
    assert rule['variation']==['scale','spacing','alignment']
    assert rule['constraints']['allowed_densities']==['medium']
    assert rule['evidence_refs']==[{'source_id':'SRC-A','page':1,'region_id':'SRC-A-P1-R1'}]
    assert rule['confidence']=='medium'


def test_unapproved_inherited_rule_does_not_enter_selection(tmp_path):
    pack=relational_pack(tmp_path,origin_pack_status='draft',origin_pack='ancestor')
    assert choose(pack,content_roles=['heading','body'])['mode']=='neutral_fallback'


def test_stale_relation_or_wrong_use_and_density_do_not_enter_selection(tmp_path):
    pack=relational_pack(tmp_path)
    assert choose(pack,content_roles=['heading','body'],intended_use='live')['mode']=='neutral_fallback'
    assert choose(pack,content_roles=['heading','body'],density='high')['mode']=='neutral_fallback'
    stale=replace(pack,layout_grammar=({**pack.layout_grammar[0],'status':'stale'},))
    assert choose(stale,content_roles=['heading','body'])['mode']=='neutral_fallback'
