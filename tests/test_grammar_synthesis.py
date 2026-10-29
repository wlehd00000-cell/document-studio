"""Proposals are evidence-backed hypotheses, not approved corporate templates."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/company-profile-analyzer/scripts'))
from grammar_synthesis import propose_grammar  # noqa: E402


def item(num, role, source='SRC-A', page=1, family='evidence'):
    return {'observation_id':f'EV-{num:03}','source_id':source,'page':page,
            'region_id':f'{source}-P{page}-R1','role':role,
            'page_family':family,'bbox_norm':[0.05,0.07,0.95,0.24],
            'evidence_kind':'visually_observed','confidence':'medium','status':'suggested',
            'observation':'Original hierarchy hypothesis'}


def test_repeated_rhythm_has_explicit_scope_sources_and_no_approval():
    data=[item(1,'heading',page=1),item(2,'heading',page=2),
          item(3,'decorative_shape',page=1)]
    grammar=propose_grammar(data,[],document_family='corporate_profile')
    assert grammar['schema_version']=='layout-grammar/1.0'
    heading=next(rule for rule in grammar['rules'] if 'heading' in rule['element_roles'])
    decoration=next(rule for rule in grammar['rules'] if 'decorative_shape' in rule['element_roles'])
    assert heading['layer']=='brand_dna'
    assert heading['support_count']==2
    assert heading['status']=='suggested'
    assert heading['page_families']==['evidence']
    assert heading['evidence_ids']==['EV-001','EV-002']
    assert heading['variation']
    assert decoration['layer']=='creative_vocabulary'
    assert decoration['confidence']=='low'


def test_duplicate_page_regions_do_not_inflate_support():
    data=[item(1,'heading',page=1),item(2,'heading',page=1)]
    grammar=propose_grammar(data,[],document_family='corporate_profile')
    assert grammar['rules'][0]['support_count']==1
    assert grammar['rules'][0]['confidence']=='low'


def test_unreviewed_unknown_is_not_silent_brand_rule():
    grammar=propose_grammar([item(1,'unknown')],[],document_family='corporate_profile')
    assert grammar['rules']==[]


def test_conflicting_page_families_remain_separate():
    data=[item(1,'image',family='cover'),item(2,'image',page=2,family='evidence')]
    grammar=propose_grammar(data,[],document_family='corporate_profile')
    assert len(grammar['rules'])==2
    assert {tuple(r['page_families']) for r in grammar['rules']}=={('cover',),('evidence',)}


def test_infers_evidence_backed_heading_above_body_relationship():
    heading=item(1,'heading',page=1)
    heading['bbox_norm']=[0.1,0.1,0.9,0.19]
    body=item(2,'body',page=1)
    body['region_id']='SRC-A-P1-R2'
    body['bbox_norm']=[0.1,0.23,0.9,0.47]
    grammar=propose_grammar([heading,body],[],document_family='corporate_profile')
    pairs=[r for r in grammar['rules'] if r['element_roles']==['heading','body']]
    assert len(pairs)==1
    pair=pairs[0]
    assert pair['relationships']==['heading above body']
    assert pair['confidence']=='low' and pair['status']=='suggested'
    assert pair['evidence_ids']==['EV-001','EV-002']
    assert len(pair['evidence_refs'])==2


def test_relationships_need_same_page_and_same_family():
    heading=item(1,'heading',page=1,family='cover')
    heading['bbox_norm']=[0.1,0.1,0.9,0.19]
    body=item(2,'body',page=2,family='cover')
    body['bbox_norm']=[0.1,0.23,0.9,0.47]
    other=item(3,'body',page=1,family='evidence')
    other['bbox_norm']=[0.1,0.23,0.9,0.47]
    grammar=propose_grammar([heading,body,other],[],document_family='corporate_profile')
    assert not [r for r in grammar['rules'] if len(r['element_roles'])>1]
