"""Synthesize conservative, adaptable visual grammar proposals from observations.

No human review/approval is performed here, and all outputs are hypotheses.
"""
from __future__ import annotations

from collections import defaultdict
import re

from layout_grammar import PAGE_FAMILIES,REGION_ROLES,validate_grammar


DNA={'heading','subheading','section_label','page_number','navigation','divider'}
CREATIVE={'decorative_shape','accent_band'}


def _spatial_relation(first: dict, second: dict) -> tuple[str,str,str,float] | None:
    """Infer only nearby, measurable ordering; no subjective composition claims."""
    a,b=first.get('bbox_norm'),second.get('bbox_norm')
    if not all(isinstance(box,list) and len(box)==4 for box in (a,b)):
        return None
    x_overlap=max(0,min(a[2],b[2])-max(a[0],b[0]))
    y_overlap=max(0,min(a[3],b[3])-max(a[1],b[1]))
    width=min(a[2]-a[0],b[2]-b[0])
    height=min(a[3]-a[1],b[3]-b[1])
    # Horizontal correspondence is needed before declaring vertical reading order.
    if width>0 and x_overlap/width>=0.35:
        if 0<=b[1]-a[3]<=0.1:
            return first['role'],'above',second['role'],round(b[1]-a[3],6)
        if 0<=a[1]-b[3]<=0.1:
            return second['role'],'above',first['role'],round(a[1]-b[3],6)
    if height>0 and y_overlap/height>=0.35:
        if 0<=b[0]-a[2]<=0.1:
            return first['role'],'left_of',second['role'],round(b[0]-a[2],6)
        if 0<=a[0]-b[2]<=0.1:
            return second['role'],'left_of',first['role'],round(a[0]-b[2],6)
    return None


def _relation_rules(observations: list[dict], document_family: str) -> list[dict]:
    by_page=defaultdict(list)
    for obs in observations:
        if obs.get('status')=='suggested' and obs.get('role') in REGION_ROLES-{'unknown'}:
            by_page[(obs['source_id'],obs['page'],obs.get('page_family','evidence'))].append(obs)
    relations=defaultdict(list)
    for (sid,page,family),members in sorted(by_page.items()):
        # Per-page nearest-neighbor role pairs: prevent one dense PDF page from
        # overwhelming the grammar with unrelated long-distance combinations.
        nearest={}
        for i,a in enumerate(members):
            for b in members[i+1:]:
                if a['role']==b['role']:
                    continue
                rel=_spatial_relation(a,b)
                if rel is None:
                    continue
                leader,relation,follower,distance=rel
                key=(family,leader,relation,follower)
                pair=tuple(sorted((a,b),key=lambda x:x['role']==follower))
                if key not in nearest or distance<nearest[key][0]:
                    nearest[key]=(distance,pair)
        for key,(_,pair) in nearest.items():
            relations[key].append(pair)
    rules=[]
    for (family,leader,relation,follower),pairs in sorted(relations.items()):
        sources={(a['source_id'],a['page']) for a,_ in pairs}
        support=len(sources)
        confidence=('high' if support>=3 and len({sid for sid,_ in sources})>=2 else
                    'medium' if support>=2 else 'low')
        unique={obs['observation_id']:obs for pair in pairs for obs in pair}
        roles=[leader,follower]
        refs={(obs['source_id'],obs['page'],obs['region_id']) for obs in unique.values()}
        rules.append({'rule_id':f'relation-{family}-{leader}-{relation}-{follower}',
                      'layer':'layout_grammar','document_family':document_family,
                      'page_families':[family],'element_roles':roles,
                      'relationships':[f'{leader} {relation} {follower}'],
                      'constraints':{'relationship_basis':'measured_neighbor_geometry',
                                     'required':False,'company_wide_invariant':False},
                      'variation':['scale','alignment','spacing','omit'],
                      'evidence_ids':sorted(unique),
                      'evidence_refs':[{'source_id':sid,'page':p,'region_id':rid}
                                       for sid,p,rid in sorted(refs)],
                      'support_count':support,'status':'suggested','confidence':confidence,
                      'reason':f'Observed adjacent {leader} {relation} {follower} on {support} source/page instances; verify visually.'})
    return rules


def propose_grammar(observations: list[dict], measured_designs: list[dict], *,
                    document_family: str) -> dict:
    if not isinstance(document_family,str) or not document_family:
        raise ValueError('Document family required')
    groups=defaultdict(list)
    for observation in observations:
        if observation.get('status')!='suggested':
            raise ValueError('Rule proposal requires validated suggested observations')
        role=observation.get('role')
        if role not in REGION_ROLES or role=='unknown':
            continue
        page_family=observation.get('page_family','evidence')
        if page_family not in PAGE_FAMILIES:
            raise ValueError('Unknown page family')
        for field in ('observation_id','source_id','page','region_id'):
            if not observation.get(field):
                raise ValueError('Observation lacks a source anchor')
        groups[(page_family,role)].append(observation)
    rules=[]
    for (page_family,role),members in sorted(groups.items()):
        by_page={(m['source_id'],m['page']) for m in members}
        support=len(by_page)
        layer='brand_dna' if role in DNA else ('creative_vocabulary' if role in CREATIVE else 'layout_grammar')
        confidence=('high' if support>=3 and len({sid for sid,_ in by_page})>=2 else
                    'medium' if support>=2 else 'low')
        # Geometry is an observed envelope, never a literal page template.
        boxes=[m.get('bbox_norm') for m in members if isinstance(m.get('bbox_norm'),list) and len(m['bbox_norm'])==4]
        envelope={'top_band':[round(min(b[1] for b in boxes),2),round(max(b[3] for b in boxes),2)]} if boxes else {}
        uniq_refs={(m['source_id'],m['page'],m['region_id']) for m in members}
        rules.append({'rule_id':f'{page_family}-{re.sub("[^a-z0-9-]","-",role)}',
                      'layer':layer,'document_family':document_family,
                      'page_families':[page_family],'element_roles':[role],
                      'relationships':[],
                      'constraints':{'observed_envelope':envelope,'required':False,
                                     'company_wide_invariant':False},
                      'variation':['scale','alignment','spacing','omit'] if layer!='creative_vocabulary' else ['crop','scale','omit'],
                      'evidence_ids':sorted({m['observation_id'] for m in members}),
                      'evidence_refs':[{'source_id':sid,'page':page,'region_id':rid}
                                       for sid,page,rid in sorted(uniq_refs)],
                      'support_count':support,'status':'suggested','confidence':confidence,
                      'reason':f'Observed {role} on {support} independent source/page instances; review before applying.'})
    rules.extend(_relation_rules(observations,document_family))
    proposal={'schema_version':'layout-grammar/1.0','rules':rules,
              'analysis_status':'proposed_visual_hypotheses',
              'measured_source_count':len(measured_designs)}
    validate_grammar(proposal)
    return proposal
