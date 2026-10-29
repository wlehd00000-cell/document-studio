"""Human rule decisions and existing pack-level review remain separate gates."""
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/company-profile-analyzer/scripts'))
sys.path.insert(0,str(ROOT/'skills/report-html-pptx/scripts'))
from layout_grammar import compute_evidence_digest  # noqa: E402
from record_visual_review import record_visual_review, invalidate_affected_rules  # noqa: E402
from build_company_pack import change_review_status  # noqa: E402
from company_pack import load_company_pack,CompanyPackError  # noqa: E402


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data),encoding='utf8')


def fixture(tmp_path):
    pack=tmp_path/'acme'
    pack.mkdir()
    write(pack/'pack.json',{'schema_version':'company-pack/1.0','pack_id':'acme',
      'company_name':'Fictional Acme','version':'1.0.0','status':'draft',
      'default_language':'en-US','enabled_languages':['en-US'],'parent_pack':None,'synthetic':True})
    write(pack/'review.json',{'status':'draft','reviewer':None,'notes':[]})
    index={'schema_version':'visual-evidence/1.0','source_id':'SRC-A','document_family':'profile',
           'format':'pdf','pages':[{'number':1,'size_pt':[100,100],
           'regions':[{'region_id':'SRC-A-P1-R1','kind':'text','bbox_norm':[0.1,0.1,0.9,0.3]}]}],
           'observations':[{'observation_id':'EV-001','source_id':'SRC-A','page':1,
           'region_id':'SRC-A-P1-R1','role':'heading','bbox_norm':[0.1,0.1,0.9,0.3],
           'evidence_kind':'visually_observed','confidence':'medium','status':'suggested',
           'observation':'Large title region'}]}
    grammar={'schema_version':'layout-grammar/1.0','rules':[{'rule_id':'title-band',
        'layer':'brand_dna','document_family':'profile','page_families':['cover'],
        'element_roles':['heading'],'relationships':[],'constraints':{},'variation':['scale'],
        'evidence_ids':['EV-001'],'evidence_refs':[{'source_id':'SRC-A','page':1,'region_id':'SRC-A-P1-R1'}],
        'status':'suggested','confidence':'medium'}]}
    write(pack/'design/visual-evidence.json',index)
    write(pack/'design/layout-grammar.json',grammar)
    return pack,index,grammar


def decision(pack,index,action='accept',digest=None):
    decisions={'schema_version':'visual-review-decisions/1.0','preview_ids':['study-editorial'],
               'decisions':[{'rule_id':'title-band','action':action,'note':'Inspected evidence and novel layout',
                             'evidence_digest':digest or compute_evidence_digest(['EV-001'],index)}]}
    target=pack.parent/'decisions.json'
    write(target,decisions)
    return target


def test_pack_approval_requires_separate_visual_review(tmp_path):
    pack,index,grammar=fixture(tmp_path)
    with pytest.raises(ValueError,match='visual'):
        change_review_status(pack,reviewer='Reviewer',note='Saw samples',action='review')
    record=record_visual_review(pack_dir=pack,grammar_file=pack/'design/layout-grammar.json',
                                decision_file=decision(pack,index),reviewer='Jane Analyst')
    assert record['accepted']==['title-band']
    loaded=load_company_pack(pack)
    assert loaded.layout_grammar[0]['status']=='accepted'
    assert loaded.visual_review['reviewer']=='Jane Analyst'
    assert change_review_status(pack,reviewer='Jane Analyst',note='Visual evidence reviewed',action='review')['status']=='reviewed'
    assert change_review_status(pack,reviewer='Owner',note='Production approved',action='approve')['status']=='approved'


def test_forged_evidence_digest_rejected(tmp_path):
    pack,index,_=fixture(tmp_path)
    with pytest.raises(ValueError,match='digest'):
        record_visual_review(pack_dir=pack,grammar_file=pack/'design/layout-grammar.json',
                             decision_file=decision(pack,index,digest='fake'),reviewer='Jane')


def test_unrecorded_accepted_rule_not_trusted(tmp_path):
    pack,_,grammar=fixture(tmp_path)
    grammar['rules'][0]['status']='accepted'
    write(pack/'design/layout-grammar.json',grammar)
    with pytest.raises(CompanyPackError):
        load_company_pack(pack)


def test_changed_source_selectively_stales_rules_without_mutation(tmp_path):
    pack,index,grammar=fixture(tmp_path)
    record_visual_review(pack_dir=pack,grammar_file=pack/'design/layout-grammar.json',
                         decision_file=decision(pack,index),reviewer='Jane')
    old=load_company_pack(pack)
    updated=invalidate_affected_rules(old,{'SRC-A':'changed-hash'})
    assert updated['rules'][0]['status']=='stale'
    assert old.layout_grammar[0]['status']=='accepted'
    assert invalidate_affected_rules(old,{'SRC-OTHER':'changed-hash'})['rules'][0]['status']=='accepted'
