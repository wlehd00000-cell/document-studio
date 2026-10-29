"""Choose only evidence-reviewed, content-suitable patterns from an approved pack."""
from __future__ import annotations

from company_pack import CompanyPack


PAGE_FAMILIES={'cover','section_divider','executive_summary','evidence','comparison',
               'process','data_visualization','image_story','decision','appendix'}


def _fallback(reason: str) -> dict:
    return {'mode':'neutral_fallback','rules':[],'reason':reason}


def select_layout_grammar(pack: CompanyPack | None, *, document_family: str,
                          page_family: str, content_roles: list[str],
                          density: str, intended_use: str) -> dict:
    if pack is None:
        return _fallback('No organization Company Pack selected')
    if pack.metadata['status']!='approved':
        return _fallback('Company Pack has not been approved for production')
    if page_family not in PAGE_FAMILIES or not content_roles:
        return _fallback('Page family or content roles are not sufficiently specified')
    candidates=[]
    for rule in pack.layout_grammar:
        if (rule.get('status')!='accepted' or rule.get('document_family')!=document_family
                or rule.get('origin_pack_status',pack.metadata['status'])!='approved'):
            continue
        if page_family not in rule.get('page_families',[]):
            continue
        overlap=set(content_roles).intersection(rule.get('element_roles',[]))
        if not overlap:
            continue
        if rule.get('relationships') and not set(rule.get('element_roles',[])).issubset(content_roles):
            continue
        if not rule.get('evidence_ids') or not rule.get('evidence_refs'):
            continue
        constraints=rule.get('constraints',{})
        densities=constraints.get('allowed_densities')
        if isinstance(densities,list) and density not in densities:
            continue
        uses=constraints.get('allowed_uses')
        if isinstance(uses,list) and intended_use not in uses:
            continue
        score=40+10*len(overlap)+{'high':3,'medium':2,'low':1}.get(rule.get('confidence'),0)
        candidates.append({'rule_id':rule['rule_id'],'layer':rule['layer'],
                           'score':score,'reason':f'{len(overlap)} content roles match; '
                                f'{rule["confidence"]} evidence; exact document/page family scope',
                           'evidence_ids':list(rule['evidence_ids']),
                           'evidence_refs':list(rule['evidence_refs']),
                           'source_refs':list(rule['evidence_refs']),
                           'element_roles':list(rule.get('element_roles',[])),
                           'relationships':list(rule.get('relationships',[])),
                           'confidence':rule.get('confidence','low'),
                           'variation':list(rule.get('variation',[])),
                           'constraints':dict(constraints),
                           'origin_pack':rule.get('origin_pack',pack.pack_id),
                           'origin_pack_status':rule.get('origin_pack_status',pack.metadata['status'])})
    if not candidates:
        return _fallback('No reviewed grammar fits this page job, content roles and intended use')
    candidates.sort(key=lambda x:(-x['score'],x['rule_id']))
    return {'mode':'approved_grammar','pack_id':pack.pack_id,
            'pack_version':pack.version,'document_family':document_family,
            'page_family':page_family,'rules':candidates,
            'reason':'Reviewed constraints apply; adapt arrangement to actual content'}
