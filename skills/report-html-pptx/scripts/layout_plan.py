"""Turn a finished page manuscript into a deterministic, review-pending layout contract."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import PurePosixPath
import re

from select_layout_grammar import PAGE_FAMILIES, select_layout_grammar


IDENTIFIER=re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,79}$')
ROLE=re.compile(r'^[a-z][a-z0-9_]{0,63}$')
LANGUAGE=re.compile(r'^[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*$')
CANVASES={'widescreen','esg-landscape','a4-portrait','a4-landscape'}
DENSITIES={'low','medium','high','report','presentation'}
USES={'reading','live','office_print','template_edit'}
RIGHTS={'original','licensed','public_domain'}
RELATIONS={'above','left_of'}


def _digest(value: dict | list) -> str:
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _identifier(value, label, *, role=False):
    if not isinstance(value,str) or not (ROLE if role else IDENTIFIER).fullmatch(value):
        raise ValueError(f'Invalid {label}')
    return value


def _project_relative(value: str) -> str:
    if not isinstance(value,str) or not value or '\\' in value or ':' in value or '\x00' in value:
        raise ValueError('Asset must be project-relative')
    path=PurePosixPath(value)
    if path.is_absolute() or any(part in {'.','..',''} for part in value.split('/')):
        raise ValueError('Asset cannot escape project')
    if path.parts[0]!='html' or len(path.parts)<3 or path.parts[1]!='assets':
        raise ValueError('Asset must be in html/assets')
    return value


def validate_page_brief(brief: dict) -> list[dict]:
    """Return a detached canonical page list or reject ambiguous/untrusted input."""
    if not isinstance(brief,dict) or brief.get('schema_version')!='layout-page-brief/1.0':
        raise ValueError('Unsupported layout page-brief schema')
    _identifier(brief.get('document_family'),'document_family',role=True)
    pages=brief.get('pages')
    if not isinstance(pages,list) or not pages:
        raise ValueError('Page brief requires nonempty pages')
    seen_pages=set()
    for page in pages:
        if not isinstance(page,dict):
            raise ValueError('Invalid page brief')
        page_id=_identifier(page.get('page_id'),'page_id')
        if page_id in seen_pages:
            raise ValueError('Duplicate page_id')
        seen_pages.add(page_id)
        if page.get('page_family') not in PAGE_FAMILIES:
            raise ValueError('Unknown page_family')
        if not isinstance(page.get('reader_question'),str) or not page['reader_question'].strip():
            raise ValueError('Missing reader question')
        if page.get('density') not in DENSITIES or page.get('intended_use') not in USES:
            raise ValueError('Unknown density or intended use')
        if page.get('canvas') not in CANVASES or not isinstance(page.get('language'),str) or not LANGUAGE.fullmatch(page['language']):
            raise ValueError('Invalid canvas or language')
        elements=page.get('elements')
        if not isinstance(elements,list) or not elements:
            raise ValueError('Page needs content element inventory')
        ids=set()
        for element in elements:
            if not isinstance(element,dict):
                raise ValueError('Invalid element entry')
            ident=_identifier(element.get('element_id'),'element_id')
            _identifier(element.get('role'),'content role',role=True)
            if ident in ids:
                raise ValueError('Duplicate element ID')
            ids.add(ident)
        order=page.get('reading_order')
        if not isinstance(order,list) or len(order)!=len(ids) or set(order)!=ids or len(set(order))!=len(order):
            raise ValueError('Reading order must enumerate every element exactly once')
        anchors=page.get('role_anchors',{})
        if not isinstance(anchors,dict):
            raise ValueError('Invalid role_anchors')
        for role,ident in anchors.items():
            _identifier(role,'anchor role',role=True)
            if not any(e['element_id']==ident and e['role']==role for e in elements):
                raise ValueError('Anchor must reference an element of the matching role')
        assets=page.get('assets',[])
        if not isinstance(assets,list):
            raise ValueError('Invalid assets list')
        for asset in assets:
            if (not isinstance(asset,dict) or asset.get('status')!='verified'
                    or asset.get('rights') not in RIGHTS):
                raise ValueError('Only verified, rights-cleared assets may be used')
            _project_relative(asset.get('path'))
        direction=page.get('design_direction')
        if direction is not None and (not isinstance(direction,str) or len(direction)>250):
            raise ValueError('Invalid design direction')
    return copy.deepcopy(pages)


def parse_relationship(expression: str, roles: list[str]) -> dict | None:
    """Only interpret explicitly supported three-token spatial relationships."""
    if not isinstance(expression,str):
        return None
    parts=expression.strip().split()
    if (len(parts)!=3 or parts[1] not in RELATIONS or parts[0]==parts[2]
            or parts[0] not in roles or parts[2] not in roles):
        return None
    return {'leader_role':parts[0],'operator':parts[1],'follower_role':parts[2]}


def _has_cycle(edges: list[tuple[str,str]]) -> bool:
    graph={}
    for left,right in edges:
        graph.setdefault(left,set()).add(right)
    visiting,visited=set(),set()
    def visit(node):
        if node in visiting:return True
        if node in visited:return False
        visiting.add(node)
        if any(visit(child) for child in graph.get(node,())):return True
        visiting.remove(node)
        visited.add(node)
        return False
    return any(visit(node) for node in graph)


def _safe_constraints(constraints):
    # Observed source envelopes are not an executable pixel/coordinate template.
    return {key:copy.deepcopy(value) for key,value in constraints.items()
            if key not in {'observed_envelope','bbox_norm','coordinates','source_bbox'}}


def company_pack_snapshot(pack) -> dict:
    """Same policy-and-grammar snapshot used by scaffold and production planning."""
    return {'pack':{key:pack.metadata[key] for key in
                    ('schema_version','pack_id','company_name','version','status',
                     'default_language','enabled_languages','parent_pack')},
            'lineage':list(pack.lineage),'design':pack.design,
            'design_cases':list(pack.design_cases),
            'writing_references':list(pack.writing_references),
            'font_policy':pack.font_policy,
            'layout_grammar':list(pack.layout_grammar),
            'visual_review':pack.visual_review}


def build_layout_plan(pack, brief: dict) -> dict:
    """Pure output: no file writes, no source-PDF coordinates, no visual approval."""
    pages=validate_page_brief(brief)
    if pack is not None:
        pack_hash=_digest(company_pack_snapshot(pack))
    else:
        pack_hash=None
    result={'schema_version':'layout-plan/1.0',
            'document_family':brief['document_family'],
            'pack_id':pack.pack_id if pack else None,
            'pack_version':pack.version if pack else None,
            'pack_snapshot_sha256':pack_hash,
            'review_status':'pending_render_review','pages':[]}
    for page in pages:
        elements=page['elements']; roles=[e['role'] for e in elements]
        choice=select_layout_grammar(pack,document_family=brief['document_family'],
                                     page_family=page['page_family'],content_roles=roles,
                                     density=page['density'],intended_use=page['intended_use'])
        rules,conflicts,edges=[],[],[]
        by_role={}
        for element in elements:by_role.setdefault(element['role'],[]).append(element['element_id'])
        role_anchors=page.get('role_anchors',{})
        order={value:index for index,value in enumerate(page['reading_order'])}
        for selected in choice['rules']:
            resolved=[]
            for expression in selected['relationships']:
                parsed=parse_relationship(expression,selected['element_roles'])
                if parsed is None:
                    conflicts.append(f'unsupported relationship expression in {selected["rule_id"]}')
                    continue
                resolved_ids=[]
                for role in (parsed['leader_role'],parsed['follower_role']):
                    matches=by_role.get(role,[])
                    ident=role_anchors.get(role) or (matches[0] if len(matches)==1 else None)
                    if ident is None:
                        conflicts.append(f'ambiguous role {role} in {selected["rule_id"]}')
                    resolved_ids.append(ident)
                if None in resolved_ids:continue
                left,right=resolved_ids
                if order[left]>=order[right]:
                    conflicts.append(f'reading_order conflicts with {selected["rule_id"]}: {expression}')
                edges.append((left,right))
                resolved.append({**parsed,'leader_element_id':left,'follower_element_id':right})
            rules.append({'rule_id':selected['rule_id'],'layer':selected['layer'],
                          'element_roles':selected['element_roles'],'relationships':resolved,
                          'evidence_ids':selected['evidence_ids'],'evidence_refs':selected['evidence_refs'],
                          'confidence':selected['confidence'],
                          'variation':selected['variation'],'constraints':_safe_constraints(selected['constraints']),
                          'origin_pack':selected['origin_pack'],
                          'origin_pack_status':selected['origin_pack_status']})
        if _has_cycle(edges):conflicts.append('cyclic relationship constraints')
        mode=('needs_revision' if conflicts else choice['mode'])
        result['pages'].append({'page_id':page['page_id'],'page_family':page['page_family'],
                                'reader_question':page['reader_question'],
                                'reading_order':page['reading_order'],'elements':elements,
                                'role_anchors':role_anchors,'canvas':page['canvas'],
                                'language':page['language'],'density':page['density'],
                                'intended_use':page['intended_use'],
                                'design_direction':page.get('design_direction'),
                                'assets':page.get('assets',[]),'mode':mode,
                                'rules':rules,'conflicts':conflicts,
                                'fallback_reason':choice.get('reason') if choice['mode']=='neutral_fallback' else None})
    result['plan_sha256']=_digest(result)
    return result
