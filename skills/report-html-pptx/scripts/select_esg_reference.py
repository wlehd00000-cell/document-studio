"""Select a small relevant set of observed DEMO report cases; does not certify design."""
import argparse
import json
from pathlib import Path
import sys
from company_pack import load_company_pack

NOTE='Candidates only. Select by actual evidence and page purpose; record applied composition in the existing section map.'

def _summary(case):
    return {key:case[key] for key in ('case_id','title','title_ko','source_id','source_ids','status','confidence','pdf_page','jobs','page_families','purpose_profiles','review_level') if key in case}


def _catalog(company_pack=None):
    if company_pack is None:
        root=Path(__file__).resolve().parents[1]
        return json.loads((root/'references/demo-esg-casebook.json').read_text(encoding='utf-8'))
    pack=load_company_pack(company_pack)
    return {'cases':list(pack.design_cases)}


def select(query=None, source=None, limit=None, family=None, profile=None, summary=False, company_pack=None):
    limit = (3 if summary else 4) if limit is None else limit
    if not 1 <= limit <= (3 if summary else 12):
        raise ValueError('Summary limit must be 1 to 3; full limit must be 1 to 12')
    catalog=_catalog(company_pack)
    terms=[t.casefold() for t in (query or '').split() if t.strip()]
    candidates=[]
    for case in catalog['cases']:
        if source and case['source_id']!=source:
            continue
        if family and family not in case.get('page_families', []):
            continue
        if profile and profile not in case.get('purpose_profiles', []):
            continue
        jobs=case.get('jobs',[])
        hay=' '.join([str(case.get('case_id','')),str(case.get('title_ko',case.get('title',''))),*jobs,str(case.get('observed',''))]).casefold()
        score=sum(4 if term in jobs else 1 for term in terms if term in hay) if terms else 1
        if score:
            candidates.append((score,case))
    candidates.sort(key=lambda item:(-item[0],item[1]['case_id']))
    return {'query':query,'family':family,'profile':profile,'case_count':len(candidates),'cases':[_summary(c) if summary else c for _,c in candidates[:limit]],
            'pack_id':load_company_pack(company_pack).pack_id if company_pack else None,'note':NOTE}

def by_id(case_ids, source=None, summary=False, company_pack=None):
    if summary and not 1<=len(set(case_ids))<=3:
        raise ValueError('Summary limit must be 1 to 3')
    catalog=_catalog(company_pack)
    indexed={c['case_id']:c for c in catalog['cases']}
    wanted=list(dict.fromkeys(case_ids))
    missing=[key for key in wanted if key not in indexed]
    if missing:
        raise ValueError('Unknown case IDs: '+', '.join(missing))
    cases=[indexed[key] for key in wanted]
    if source and any(c['source_id']!=source for c in cases):
        raise ValueError('Selected case does not belong to the requested source')
    return {'query':None,'case_count':len(cases),'cases':[_summary(c) if summary else c for c in cases],
            'pack_id':load_company_pack(company_pack).pack_id if company_pack else None,'note':NOTE}

if __name__=='__main__':
    tokens=json.loads((Path(__file__).resolve().parents[1]/'system/design-tokens.json').read_text(encoding='utf-8'))
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query',nargs='?',help='Jobs/keywords: narrative image scene table factbook process strategy responsibility matrix comparison trend macc')
    parser.add_argument('--case-id',action='append',default=[],help='Exact known case; repeat to reuse accepted cases')
    parser.add_argument('--pretty',action='store_true',help='Indented output; default is compact UTF-8 JSON')
    parser.add_argument('--source',help='Source ID within the selected casebook')
    parser.add_argument('--company-pack',type=Path,help='Isolate search to this Company Pack')
    parser.add_argument('--family',choices=sorted(tokens['page_families']),help='Page role, independent from document purpose')
    parser.add_argument('--profile',choices=sorted(tokens['profiles']),help='Document purpose profile')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--summary',action='store_true',help='Compact case identity and evidence only (1–3 cases)')
    args=parser.parse_args()
    if args.limit is None:
        args.limit=3 if args.summary else 4
    if not 1<=args.limit<=(3 if args.summary else 12):
        parser.error('--limit must be 1 to 3 for --summary, otherwise 1 to 12')
    if not args.query and not args.case_id and not args.family and not args.profile:
        parser.error('Specify a query, --family, --profile or --case-id')
    if args.case_id and (args.query or args.family or args.profile):
        parser.error('Use either query/family/profile filters or exact case IDs')
    try:
        result=by_id(args.case_id,args.source,args.summary,args.company_pack) if args.case_id else select(args.query,args.source,args.limit,args.family,args.profile,args.summary,args.company_pack)
    except ValueError as error:
        parser.error(str(error))
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2 if args.pretty else None,
                     separators=None if args.pretty else (',',':')))
