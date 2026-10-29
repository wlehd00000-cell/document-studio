"""Reject hallucinated visual evidence and unreviewed model approvals."""
import copy
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/company-profile-analyzer/scripts'))
from layout_grammar import validate_observations, validate_grammar, compute_evidence_digest  # noqa: E402
from visual_evidence import build_evidence_index  # noqa: E402


def index():
    return build_evidence_index({'format':'pdf','pages':[{'number':1,'size_pt':[100,100],
                  'shapes':[{'kind':'text','bbox_pt':[10,10,90,35]}]}]},
                source_id='SRC-A',document_family='corporate_profile')


def observation():
    return {'schema_version':'visual-observations/1.0','observations':[
        {'observation_id':'EV-001','source_id':'SRC-A','page':1,'region_id':'SRC-A-P1-R1',
         'bbox_norm':[0.1,0.1,0.9,0.35],'role':'heading','observation':'Large upper text zone',
         'evidence_kind':'visually_observed','confidence':'medium','status':'suggested'}]}


def grammar():
    return {'schema_version':'layout-grammar/1.0','rules':[
        {'rule_id':'title-band','layer':'layout_grammar','document_family':'corporate_profile',
         'page_families':['evidence'],'element_roles':['heading'],
         'relationships':[],'constraints':{},'variation':['scale','column_count'],
         'evidence_ids':['EV-001'],'evidence_refs':[{'source_id':'SRC-A','page':1,'region_id':'SRC-A-P1-R1'}],
         'status':'suggested','confidence':'medium'}]}


def test_observation_is_source_grounded_and_digest_stable():
    result=validate_observations(observation(),index(),{'SRC-A'})
    assert result['observations'][0]['role']=='heading'
    assert compute_evidence_digest(['EV-001'],result)==compute_evidence_digest(['EV-001'],result)


@pytest.mark.parametrize('field,value',[('source_id','SRC-FAKE'),('page',9),
             ('region_id','missing'),('bbox_norm',[0,0,1.1,1]),('status','approved')])
def test_reject_untrusted_anchors_and_approval(field,value):
    obj=observation()
    obj['observations'][0][field]=value
    with pytest.raises(ValueError):
        validate_observations(obj,index(),{'SRC-A'})


def test_unknown_role_remains_unknown_with_review_flag():
    obj=observation()
    obj['observations'][0]['role']='alien-structure'
    result=validate_observations(obj,index(),{'SRC-A'})
    assert result['observations'][0]['role']=='unknown'
    assert result['observations'][0]['needs_review'] is True


def test_page_family_annotation_survives_validation():
    obj=observation()
    obj['observations'][0]['page_family']='cover'
    result=validate_observations(obj,index(),{'SRC-A'})
    assert result['observations'][0]['page_family']=='cover'
    obj['observations'][0]['page_family']='unsupported'
    with pytest.raises(ValueError):
        validate_observations(obj,index(),{'SRC-A'})


def test_flexible_grammar_accepts_grounded_rule_and_rejects_fake():
    valid=validate_grammar(grammar(),index())
    assert valid['rules'][0]['status']=='suggested'
    for field,value in [('status','approved'),('layer','other'),('evidence_ids',[]),
                        ('page_families',[]),('element_roles',['bogus'])]:
        altered=copy.deepcopy(grammar())
        altered['rules'][0][field]=value
        with pytest.raises(ValueError):
            validate_grammar(altered,index())
    altered=copy.deepcopy(grammar())
    altered['rules'][0]['evidence_refs'][0]['region_id']='missing'
    with pytest.raises(ValueError):
        validate_grammar(altered,index())


def test_duplicate_rule_id_rejected():
    obj=grammar()
    obj['rules'].append(copy.deepcopy(obj['rules'][0]))
    with pytest.raises(ValueError):
        validate_grammar(obj,index())
