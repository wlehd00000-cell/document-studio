"""Synthesize a reviewable (never automatically approved) Company Pack."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from design_analyzer import draft_design_profile
from layout_grammar import validate_grammar

REPORT_ROOT=Path(__file__).resolve().parents[2]/'report-html-pptx/scripts'
sys.path.insert(0,str(REPORT_ROOT))
from company_pack import PACK_ID, VERSION, load_company_pack  # noqa: E402


def _read(path: Path) -> dict:
    doc=json.loads(Path(path).read_text(encoding='utf8'))
    if not isinstance(doc,dict):
        raise ValueError('Analysis must be a JSON object')
    return doc


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def build_company_pack(*, registry_file: Path, design_analyses: list[Path],
                       writing_analyses: list[Path], output: Path,
                       pack_id: str, company_name: str, version: str,
                       default_language: str, enabled_languages: list[str],
                       grammar_proposal: Path | None = None,
                       redacted_evidence: Path | None = None) -> Path:
    if not PACK_ID.fullmatch(pack_id) or not VERSION.fullmatch(version):
        raise ValueError('Invalid pack ID or version')
    if not company_name.strip() or default_language not in enabled_languages:
        raise ValueError('Company name/default language is invalid')
    registry=_read(registry_file)
    if registry.get('schema_version')!='source-registry/1.0':
        raise ValueError('Unsupported source registry')
    sources={s['source_id']:s for s in registry.get('sources',[])}
    if not sources:
        raise ValueError('No registered sources')
    design=[_read(p) for p in design_analyses]
    writing=[_read(p) for p in writing_analyses]
    if not design or not writing:
        raise ValueError('Design and writing analyses are both required')
    if (grammar_proposal is None)!=(redacted_evidence is None):
        raise ValueError('Visual grammar and redacted evidence must be supplied together')
    grammar=evidence=None
    if grammar_proposal is not None:
        grammar=_read(grammar_proposal)
        evidence=_read(redacted_evidence)
        if evidence.get('schema_version')!='visual-evidence/1.0' or evidence.get('source_id') not in sources:
            raise ValueError('Visual evidence must cite a registered source')
        forbidden={'text','path','preview_pages','image_base64','source_url','private_path'}
        def check_redacted(value):
            if isinstance(value,dict):
                if any(key in forbidden for key in value):
                    raise ValueError('Visual evidence contains non-redacted source content/path')
                for child in value.values():check_redacted(child)
            elif isinstance(value,list):
                for child in value:check_redacted(child)
        check_redacted(evidence)
        validate_grammar(grammar,evidence)
        if any(rule['status']!='suggested' for rule in grammar['rules']):
            raise ValueError('New Company Pack must contain only proposed visual rules')
    for analysis in [*design,*writing]:
        if not analysis.get('source_ids') or any(sid not in sources for sid in analysis['source_ids']):
            raise ValueError('Analysis source_id is absent from the registry')
    design_tokens,casebook,layouts=draft_design_profile(design)
    approved_refs=[]
    glossary=[]
    for analysis in writing:
        if all(sources[sid]['visibility']=='public' and sources[sid]['allow_excerpt_in_pack']
               for sid in analysis['source_ids']):
            glossary.extend({'term':t['term'],'count':t['count'],
                             'source_ids':analysis['source_ids'],'status':'suggested'}
                            for t in analysis.get('terminology_candidates',[]))
        for ref in analysis.get('references',[]):
            if all(sources[sid]['visibility']=='public' and sources[sid]['allow_excerpt_in_pack']
                   for sid in ref['source_ids']):
                approved_refs.append(ref)
    # Casebook captions are generated analysis labels, never source-page text.
    for case in casebook['cases']:
        if any(sources[sid]['visibility']=='private' for sid in case['source_ids']):
            case['disclosure_scope']='internal_only'
        else:
            case['disclosure_scope']='public_metadata'
    included_ids=sorted({sid for doc in [*design,*writing] for sid in doc['source_ids']})
    public_sources={'sources':[{k:source[k] for k in
                ('source_id','language','document_family','visibility','rights','allow_excerpt_in_pack','distribution_authorized')}
                for sid in included_ids for source in [sources[sid]]]}
    for source in public_sources['sources']:
        if source['visibility']=='private':
            source['rights']='private; distribution not authorized'
    fontname=design_tokens.get('font',{}).get('primary','Unverified font')
    fonts={'by_language':{lang.split('-')[0]:{'family':fontname,'license':'unverified',
                                           'redistribution':False} for lang in enabled_languages}}
    folder=Path(output)
    if folder.exists():
        raise FileExistsError('Output Company Pack already exists; create a new version path')
    if folder.name!=pack_id:
        raise ValueError('Output folder must match pack_id')
    folder.mkdir(parents=True)
    metadata={'schema_version':'company-pack/1.0','pack_id':pack_id,
              'company_name':company_name,'version':version,'status':'draft',
              'default_language':default_language,'enabled_languages':enabled_languages,
              'parent_pack':None}
    _write(folder/'pack.json',metadata)
    _write(folder/'sources.json',public_sources)
    _write(folder/'design/tokens.json',design_tokens)
    _write(folder/'design/design-casebook.json',casebook)
    _write(folder/'design/layout-patterns.json',layouts)
    if grammar is not None:
        _write(folder/'design/layout-grammar.json',grammar)
        _write(folder/'design/visual-evidence.json',evidence)
    _write(folder/'writing/references.json',{'references':approved_refs})
    _write(folder/'writing/rules.json',{'rules':[rule for a in writing for rule in a.get('rules',[])]})
    _write(folder/'writing/glossary.json',{'terms':glossary})
    _write(folder/'fonts/policy.json',fonts)
    _write(folder/'review.json',{'status':'draft','reviewer':None,'notes':[],
                                'unverified':['visual interpretation','official font identity/rights',
                                              'company-wide writing policies']})
    load_company_pack(folder)
    return folder


def change_review_status(folder: Path, *, reviewer: str, note: str, action: str) -> dict:
    if action not in {'review','approve'} or not reviewer.strip() or not note.strip():
        raise ValueError('Explicit review/approval action, reviewer and reason are required')
    folder=Path(folder)
    pack=load_company_pack(folder)
    current=pack.metadata['status']
    if pack.layout_grammar and (not pack.visual_review or pack.visual_review.get('status')!='reviewed'):
        raise ValueError('Visual grammar requires documented human visual review before pack status changes')
    if any(rule['status']=='suggested' for rule in pack.layout_grammar):
        raise ValueError('All visual rules must receive human decisions before pack review')
    if (action=='review' and current!='draft') or (action=='approve' and current!='reviewed'):
        raise ValueError('Approval requires the draft → reviewed → approved sequence')
    review=_read(folder/'review.json')
    if action=='approve' and not review.get('notes'):
        raise ValueError('Approval requires documented review evidence')
    next_status='reviewed' if action=='review' else 'approved'
    metadata=dict(pack.metadata,status=next_status)
    review.update(status=next_status,reviewer=reviewer)
    review['notes'].append({'action':action,'reviewer':reviewer,'note':note})
    _write(folder/'pack.json',metadata)
    _write(folder/'review.json',review)
    return {'pack_id':pack.pack_id,'status':next_status,'version':pack.version}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    subs=p.add_subparsers(dest='command',required=True)
    build=subs.add_parser('build')
    build.add_argument('--registry',type=Path,required=True)
    build.add_argument('--design-analysis',type=Path,action='append',required=True)
    build.add_argument('--writing-analysis',type=Path,action='append',required=True)
    build.add_argument('--output',type=Path,required=True)
    build.add_argument('--pack-id',required=True)
    build.add_argument('--company-name',required=True)
    build.add_argument('--version',default='1.0.0')
    build.add_argument('--default-language',required=True)
    build.add_argument('--enabled-language',action='append',required=True)
    build.add_argument('--grammar-proposal',type=Path)
    build.add_argument('--redacted-evidence',type=Path)
    for action in ['review','approve']:
        command=subs.add_parser(action)
        command.add_argument('pack',type=Path)
        command.add_argument('--reviewer',required=True)
        command.add_argument('--note',required=True)
    a=p.parse_args()
    if a.command=='build':
        folder=build_company_pack(registry_file=a.registry,design_analyses=a.design_analysis,
                    writing_analyses=a.writing_analysis,output=a.output,pack_id=a.pack_id,
                    company_name=a.company_name,version=a.version,
                    default_language=a.default_language,enabled_languages=a.enabled_language,
                    grammar_proposal=a.grammar_proposal,redacted_evidence=a.redacted_evidence)
        print(json.dumps({'pack':str(folder),'status':'draft'}))
    else:
        print(json.dumps(change_review_status(a.pack,reviewer=a.reviewer,note=a.note,action=a.command)))
