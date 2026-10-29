"""A reviewed grammar must become a deterministic, scoped page contract."""
from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/report-html-pptx/scripts'))
sys.path.insert(0,str(ROOT/'tests'))
from test_layout_grammar_selection import relational_pack  # noqa: E402
from layout_plan import build_layout_plan, validate_page_brief, parse_relationship  # noqa: E402


def brief(**page_updates):
    page={'page_id':'P1','page_family':'cover', 'reader_question':'What changed?',
          'reading_order':['title','copy'],
          'elements':[{'element_id':'title','role':'heading'},
                      {'element_id':'copy','role':'body'}],
          'density':'medium','intended_use':'reading','canvas':'widescreen',
          'language':'en-US','assets':[]}
    page.update(page_updates)
    return {'schema_version':'layout-page-brief/1.0','document_family':'profile','pages':[page]}


def test_plan_is_deterministic_and_binds_approved_source(tmp_path):
    pack=relational_pack(tmp_path)
    result=build_layout_plan(pack,brief())
    assert result==build_layout_plan(pack,brief())
    assert result['schema_version']=='layout-plan/1.0'
    assert len(result['plan_sha256'])==64
    assert len(result['pack_snapshot_sha256'])==64
    assert result['review_status']=='pending_render_review'
    page=result['pages'][0]
    assert page['mode']=='approved_grammar'
    assert page['rules'][0]['rule_id']=='heading-above-body'
    assert page['rules'][0]['relationships']==[{'leader_role':'heading','operator':'above',
                      'follower_role':'body','leader_element_id':'title','follower_element_id':'copy'}]
    assert page['rules'][0]['evidence_refs'][0]['source_id']=='SRC-A'
    assert page['rules'][0]['variation']==['scale','spacing','alignment']


def test_relationship_is_semantic_and_never_invents_source_geometry(tmp_path):
    record=build_layout_plan(relational_pack(tmp_path),brief())
    assert 'bbox' not in json.dumps(record)
    assert 'coordinates' not in json.dumps(record)
    assert record['pages'][0]['rules'][0]['relationships'][0]['operator']=='above'


def test_ambiguous_role_requires_explicit_element_anchor(tmp_path):
    pack=relational_pack(tmp_path)
    elements=[{'element_id':'title','role':'heading'}, {'element_id':'title2','role':'heading'},
              {'element_id':'copy','role':'body'}]
    page=brief(elements=elements,reading_order=['title','title2','copy'])
    output=build_layout_plan(pack,page)['pages'][0]
    assert output['mode']=='needs_revision'
    assert 'ambiguous' in ' '.join(output['conflicts']).lower()
    page['pages'][0]['role_anchors']={'heading':'title','body':'copy'}
    resolved=build_layout_plan(pack,page)['pages'][0]
    assert resolved['mode']=='approved_grammar'
    assert resolved['rules'][0]['relationships'][0]['leader_element_id']=='title'


def test_conflicting_reading_order_cannot_be_silently_reordered(tmp_path):
    output=build_layout_plan(relational_pack(tmp_path),brief(reading_order=['copy','title']))['pages'][0]
    assert output['mode']=='needs_revision'
    assert any('reading_order' in issue for issue in output['conflicts'])


def test_fallback_is_not_misrepresented_as_approved(tmp_path):
    output=build_layout_plan(relational_pack(tmp_path),brief(page_family='appendix'))['pages'][0]
    assert output['mode']=='neutral_fallback'
    assert output['rules']==[]
    assert output['fallback_reason']
    neutral=build_layout_plan(None,brief())['pages'][0]
    assert neutral['mode']=='neutral_fallback'


def test_unknown_operators_and_embedded_instructions_are_not_activated(tmp_path):
    pack=relational_pack(tmp_path,relationships=['heading <script> body'])
    output=build_layout_plan(pack,brief())['pages'][0]
    assert output['mode']=='needs_revision'
    assert any('unsupported' in issue for issue in output['conflicts'])
    assert parse_relationship('heading execute body',['heading','body']) is None


@pytest.mark.parametrize('bad_page',[
    {'assets':[{'path':'../private.png','status':'verified','rights':'licensed'}]},
    {'assets':[{'path':'html/assets/chart.svg','status':'unverified','rights':'licensed'}]},
    {'assets':[{'path':'html/assets/chart.svg','status':'verified','rights':'unknown'}]},
    {'elements':[{'element_id':'<script>','role':'heading'}]},
    {'reading_order':['title','title']},
    {'canvas':'<script>'},
])
def test_rejects_untrusted_assets_and_invalid_page_fields(bad_page):
    with pytest.raises(ValueError):
        validate_page_brief(brief(**bad_page))


def test_plan_hash_and_pack_snapshot_change_on_rule_revision(tmp_path):
    pack=relational_pack(tmp_path)
    first=build_layout_plan(pack,brief())
    changed=replace(pack,layout_grammar=({**pack.layout_grammar[0],
                 'variation':['crop']},))
    second=build_layout_plan(changed,brief())
    assert first['pack_snapshot_sha256']!=second['pack_snapshot_sha256']
    assert first['plan_sha256']!=second['plan_sha256']


def test_brief_requires_known_schema_and_nonempty_pages():
    with pytest.raises(ValueError):
        validate_page_brief({'schema_version':'layout-page-brief/0.0','pages':[]})
    with pytest.raises(ValueError):
        validate_page_brief({'schema_version':'layout-page-brief/1.0','pages':[]})


def test_cli_writes_pending_plan_from_actual_project_brief(tmp_path):
    from plan_layout_grammar import write_layout_plan
    pack=relational_pack(tmp_path)
    project=tmp_path/'project'
    (project/'content').mkdir(parents=True)
    (project/'content/page-brief.json').write_text(json.dumps(brief()),encoding='utf-8')
    result=write_layout_plan(project,'content/page-brief.json',pack.root)
    file=project/'content/layout-plan.json'
    saved=json.loads(file.read_text(encoding='utf-8'))
    assert result['plan']==str(file)
    assert result['status']=='pending_render_review'
    assert saved['pages'][0]['rules'][0]['rule_id']=='title-band'
    assert saved['pages'][0]['mode']=='approved_grammar'


def test_cli_refuses_outside_project_brief(tmp_path):
    from plan_layout_grammar import write_layout_plan
    project=tmp_path/'project'
    (project/'content').mkdir(parents=True)
    outside=tmp_path/'private.json'
    outside.write_text(json.dumps(brief()),encoding='utf-8')
    with pytest.raises(ValueError):
        write_layout_plan(project,'../private.json')
    assert not (project/'content/layout-plan.json').exists()
