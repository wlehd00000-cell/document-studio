"""Find source-backed DEMO Korean writing examples and page subjects."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'report-html-pptx/scripts'))
from company_pack import CompanyPack, load_company_pack

ALIASES={'retail':'demo-a','logistics':'demo-b','circular':'demo-c','가상기업 A':'demo-a','가상기업 B':'demo-b','가상기업 C':'demo-c'}


def find_writing_references(pack: CompanyPack, language: str, document_family: str,
                            writing_function: str, limit: int = 3) -> list[dict]:
    """Return only source-tracked references from the selected pack/lineage."""
    if not 1 <= limit <= 100:
        raise ValueError('limit must be between 1 and 100')
    if language not in pack.metadata['enabled_languages']:
        raise ValueError('Requested language is not enabled by the Company Pack')
    matches=[dict(ref) for ref in pack.writing_references
             if ref['language']==language
             and ref['document_family']==document_family
             and ref['writing_function']==writing_function]
    return matches[:limit]

def query(library,company=None,topic=None,function=None,limit=5,section='both',excerpt_ids=None):
    if section not in {'both','excerpts','pages'}:
        raise ValueError('Unknown reference section')
    if not 1<=limit<=100:
        raise ValueError('limit must be between 1 and 100')
    wanted=list(dict.fromkeys(excerpt_ids or []))
    missing=set(wanted)-{e['id'] for e in library['excerpts']}
    if missing:
        raise ValueError('Unknown excerpt IDs: '+', '.join(sorted(missing)))
    if wanted and section=='pages':
        raise ValueError('Excerpt IDs require excerpts or both')
    ids={s['id'] for s in library['sources']}
    sid=ALIASES.get(company,company) if company else None
    if sid and sid not in ids:
        raise ValueError('Unknown company. Use retail, logistics, circular or a demo ID.')
    term=(topic or '').casefold()
    def contains(row):
        if sid and row['report_id']!=sid:return False
        if function and function not in row.get('writing_functions',[row.get('function')]):return False
        return not term or term in json.dumps(row,ensure_ascii=False).casefold()
    examples=[e for e in library['excerpts'] if contains(e) and (not wanted or e['id'] in wanted)] if section!='pages' else []
    if wanted:
        order={key:i for i,key in enumerate(wanted)}
        examples.sort(key=lambda e:order[e['id']])
    pages=[p for p in library['pages'] if contains(p)] if section!='excerpts' else []
    report_ids={x['report_id'] for x in examples+pages}
    return {'note':library['purpose'],'page_numbering':library['page_numbering'],
            'sources':[s for s in library['sources'] if s['id'] in report_ids],
            'total_excerpts':len(examples) if section!='pages' else None,
            'total_pages':len(pages) if section!='excerpts' else None,
            'excerpts':examples[:limit],'pages':pages[:limit]}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--company',choices=list(ALIASES)+['demo-a','demo-b','demo-c'])
    parser.add_argument('--topic')
    parser.add_argument('--function')
    parser.add_argument('--limit',type=int,default=5)
    parser.add_argument('--list-functions',action='store_true')
    parser.add_argument('--section',choices=['both','excerpts','pages'],help='Return only needed records; excluded totals are null')
    parser.add_argument('--id',action='append',default=[],help='Exact excerpt ID; repeat to reuse accepted models')
    parser.add_argument('--pretty',action='store_true',help='Indented output; default is compact UTF-8 JSON')
    parser.add_argument('--company-pack',type=Path,help='Use company-specific writing cases, never shared DEMO examples')
    parser.add_argument('--language',help='BCP-47 language tag, e.g. ja-JP')
    parser.add_argument('--document-family',help='Document family, e.g. executive_report')
    parser.add_argument('--writing-function',help='Writing function, e.g. risk_explanation')
    args=parser.parse_args()
    if not 1<=args.limit<=100:parser.error('limit must be between 1 and 100')
    if args.company_pack:
        if args.company or args.id or args.topic or args.section or args.list_functions:
            parser.error('Company Pack search cannot be combined with legacy DEMO library filters')
        if not all([args.language,args.document_family,args.writing_function]):
            parser.error('Company Pack search requires --language, --document-family and --writing-function')
        try:
            pack=load_company_pack(args.company_pack)
            examples=find_writing_references(pack,args.language,args.document_family,args.writing_function,args.limit)
            result={'pack_id':pack.pack_id,'version':pack.version,'references':examples,
                    'note':'Source-tracked company examples; empty means use general writing guidance, never another company library.'}
        except ValueError as error:
            parser.error(str(error))
    else:
        path=Path(__file__).resolve().parent.parent/'references/demo-report-library.json'
        library=json.loads(path.read_text(encoding='utf-8'))
        if args.list_functions:
            result=sorted({e['function'] for e in library['excerpts']}|{f for p in library['pages'] for f in p['writing_functions']})
        else:
            try:
                result=query(library,args.company,args.topic,args.function,args.limit,
                             args.section or ('excerpts' if args.id else 'both'),args.id)
            except ValueError as error:
                parser.error(str(error))
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2 if args.pretty else None,
                     separators=None if args.pretty else (',',':')))

if __name__=='__main__':main()
