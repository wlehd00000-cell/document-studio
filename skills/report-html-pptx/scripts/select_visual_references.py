"""Retrieve a few suitable local visual references from declared evidence; no network."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LIBRARY=ROOT/'references/visual-reference-library.json'

def select(purpose, evidence, limit=3, language='ko', avoid_kinds=()):
    if not 1<=limit<=5:
        raise ValueError('limit must be between 1 and 5')
    data=json.loads(LIBRARY.read_text(encoding='utf-8'))
    if purpose not in data['families']:
        raise ValueError('Unknown purpose')
    if language not in {'ko','ja'}:
        raise ValueError('language must be ko or ja')
    known={feature for p in data['patterns'] for feature in p['requires']}
    if set(evidence)-known:
        raise ValueError('Unknown evidence features: '+', '.join(sorted(set(evidence)-known)))
    candidates=[p for p in data['patterns'] if p['family']==purpose
                and set(p['requires'])<=set(evidence) and p['kind'] not in avoid_kinds]
    ranked=sorted(candidates,key=lambda p:(-p['priority'],p['id']))
    selected=[]
    if ranked:
        selected.append(ranked.pop(0))
    # Where possible, compare different useful forms rather than three cosmetic variants.
    while ranked and len(selected)<limit:
        used_kinds={p['kind'] for p in selected}
        next_item=next((p for p in ranked if p['kind'] not in used_kinds),ranked[0])
        selected.append(next_item)
        ranked.remove(next_item)
    refs=[]
    for p in selected:
        refs.append({'id':p['id'],'name':p['name'][language],'kind':p['kind'],
            'why':p['why'][language],'caveat':p['caveat'][language],
            'requires':p['requires'],'thumbnail':str(ROOT/p['thumbnail']),
            'references':[data['sources'][s]['url'] for s in p['source_ids']],
            'schematic_only':True})
    return {'status':'candidates' if refs else 'no_supported_candidates',
            'purpose':purpose,'candidates':refs,'evidence_declared':list(evidence),
            'notice':('자료 조건에 따른 후보입니다. 실제 값·출처·독자 적합성은 별도 확인하며 구도 샘플은 실적이 아닙니다.' if language=='ko'
                      else '資料条件に基づく候補です。実際の数値・出典・読者への適合性を確認してください。構図サンプルは実績ではありません。')}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--purpose',required=True,choices=['compare','change','composition','distribution','relationship','process','planning','decision','concept','image','storytelling'])
    parser.add_argument('--evidence',default='',help='Comma-separated available feature names; no source contents are read')
    parser.add_argument('--limit',type=int,default=3)
    parser.add_argument('--language',choices=['ko','ja'],default='ko')
    parser.add_argument('--avoid-kind',action='append',default=[],choices=['chart','table','diagram','image','storyboard'])
    parser.add_argument('--pretty',action='store_true',help='Indented output; default is compact UTF-8 JSON')
    args=parser.parse_args()
    evidence=sorted({value.strip() for value in args.evidence.split(',') if value.strip()})
    import sys
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(select(args.purpose,evidence,args.limit,args.language,args.avoid_kind),
                     ensure_ascii=False,indent=2 if args.pretty else None,
                     separators=None if args.pretty else (',',':')))

if __name__=='__main__':
    try:
        main()
    except (ValueError,OSError,json.JSONDecodeError) as error:
        import sys
        print(json.dumps({'status':'failed','error':str(error)},ensure_ascii=False),file=sys.stderr)
        raise SystemExit(1)
