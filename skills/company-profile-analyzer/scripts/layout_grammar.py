"""Pure, conservative contracts for visual observations and adaptable rules."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math


LAYERS={'brand_dna','layout_grammar','creative_vocabulary'}
PAGE_FAMILIES={'cover','section_divider','executive_summary','evidence','comparison',
               'process','data_visualization','image_story','decision','appendix'}
REGION_ROLES={'unknown','heading','subheading','body','section_label','accent_band',
              'evidence_body','image','caption','chart','table','logo_placeholder',
              'page_number','divider','decorative_shape','callout','navigation'}
CONFIDENCE={'low','medium','high'}
PROVENANCE={'measured','visually_observed','inferred'}
VARIATION={'scale','crop','column_count','alignment','spacing','image_ratio','reorder','omit'}
STATUSES={'suggested','accepted','rejected','stale'}


def _regions(index: dict) -> dict:
    if index.get('schema_version')=='visual-review-workspace/1.0':
        index=index['evidence']
    result={}
    for page in index.get('pages',[]):
        for region in page.get('regions',[]):
            key=(index['source_id'],page['number'],region['region_id'])
            if key in result:
                raise ValueError('Duplicate evidence region')
            result[key]=region
    return result


def _bbox(box: object) -> bool:
    return (isinstance(box,(list,tuple)) and len(box)==4 and all(
            isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and 0<=v<=1 for v in box)
            and box[2]>box[0] and box[3]>box[1])


def validate_observations(observations: dict, evidence_index: dict,
                          registered_source_ids: set[str]) -> dict:
    if observations.get('schema_version')!='visual-observations/1.0' or not isinstance(observations.get('observations'),list):
        raise ValueError('Invalid observation schema')
    known=_regions(evidence_index)
    seen=set()
    clean=[]
    for item in observations['observations']:
        identifier=item.get('observation_id')
        if not isinstance(identifier,str) or not identifier or identifier in seen:
            raise ValueError('Missing or duplicate observation id')
        seen.add(identifier)
        sid,page,rid=item.get('source_id'),item.get('page'),item.get('region_id')
        if sid not in registered_source_ids or (sid,page,rid) not in known:
            raise ValueError('Unregistered source/page/region evidence')
        box=item.get('bbox_norm')
        if not _bbox(box) or any(abs(a-b)>0.005 for a,b in zip(box,known[(sid,page,rid)]['bbox_norm'])):
            raise ValueError('Observed geometry disagrees with measured source')
        if item.get('status')!='suggested' or item.get('evidence_kind') not in PROVENANCE or item.get('confidence') not in CONFIDENCE:
            raise ValueError('Unreviewed observations must be suggested with provenance/confidence')
        role=item.get('role')
        if not isinstance(item.get('observation'),str) or len(item['observation'])>300:
            raise ValueError('Observation description missing or too long')
        page_family=item.get('page_family','evidence')
        if page_family not in PAGE_FAMILIES:
            raise ValueError('Unknown page-family classification')
        clean.append({'observation_id':identifier,'source_id':sid,'page':page,'region_id':rid,
                      'bbox_norm':list(box),'role':role if role in REGION_ROLES else 'unknown',
                      'page_family':page_family,'needs_review':role not in REGION_ROLES,
                      'observation':item['observation'],
                      'evidence_kind':item['evidence_kind'],'confidence':item['confidence'],
                      'status':'suggested'})
    return {'schema_version':'visual-observations/1.0','observations':clean}


def compute_evidence_digest(evidence_ids: list[str], evidence_index: dict) -> str:
    """Bind human review to precisely the observations considered, not their list position."""
    found={item['observation_id']:item for item in evidence_index.get('observations',[])}
    if not evidence_ids or len(set(evidence_ids))!=len(evidence_ids) or any(ident not in found for ident in evidence_ids):
        raise ValueError('Unknown or duplicate evidence identifier')
    canonical=json.dumps([found[ident] for ident in sorted(evidence_ids)],sort_keys=True,
                         ensure_ascii=False,separators=(',',':'))
    return hashlib.sha256(canonical.encode('utf8')).hexdigest()


def validate_grammar(grammar: dict, evidence_index: dict | None = None) -> dict:
    if grammar.get('schema_version')!='layout-grammar/1.0' or not isinstance(grammar.get('rules'),list):
        raise ValueError('Invalid layout grammar schema')
    known=_regions(evidence_index) if evidence_index is not None else None
    ids=set()
    for rule in grammar['rules']:
        ident=rule.get('rule_id')
        if not isinstance(ident,str) or not ident or ident in ids:
            raise ValueError('Rule ID must be unique and nonempty')
        ids.add(ident)
        if rule.get('layer') not in LAYERS or rule.get('status') not in STATUSES or rule.get('confidence') not in CONFIDENCE:
            raise ValueError('Invalid layer/status/confidence')
        if not isinstance(rule.get('document_family'),str) or not rule['document_family']:
            raise ValueError('Rule needs a document family')
        page_families=rule.get('page_families')
        roles=rule.get('element_roles')
        if (not isinstance(page_families,list) or not page_families or any(p not in PAGE_FAMILIES for p in page_families)
                or not isinstance(roles,list) or not roles or any(r not in REGION_ROLES for r in roles)):
            raise ValueError('Rule needs supported page families and element roles')
        if (not isinstance(rule.get('relationships'),list) or
                not all(isinstance(x,str) and len(x)<180 for x in rule['relationships']) or
                not isinstance(rule.get('constraints'),dict) or
                not isinstance(rule.get('variation'),list) or any(v not in VARIATION for v in rule['variation'])):
            raise ValueError('Invalid relationships, constraints or variation')
        ids_list=rule.get('evidence_ids')
        refs=rule.get('evidence_refs')
        if not isinstance(ids_list,list) or not ids_list or not all(isinstance(x,str) and x for x in ids_list):
            raise ValueError('Rule must cite observation IDs')
        if not isinstance(refs,list) or not refs:
            raise ValueError('Rule must cite source regions')
        for ref in refs:
            if not isinstance(ref,dict) or not isinstance(ref.get('source_id'),str) or not isinstance(ref.get('page'),int) or ref['page']<1 or not isinstance(ref.get('region_id'),str):
                raise ValueError('Invalid source anchor')
            if known is not None and (ref['source_id'],ref['page'],ref['region_id']) not in known:
                raise ValueError('Unregistered grammar evidence')
    return deepcopy(grammar)
