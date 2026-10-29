"""Find independent, inspected expression studies; does not certify a new document."""
import argparse
import json
from pathlib import Path
import sys
from design_expression import EXPRESSION

ROOT = Path(__file__).resolve().parents[1]


def _summary(case):
    return {key:case[key] for key in ('case_id','kind','title_ko','title_ja','page_families','purpose_profiles','study_file','gallery','body_only','creativity','visual_intensity') if key in case}


def select(preset=None, creativity=None, intensity=None, family=None, limit=3, body_only=False, summary=False):
    if not isinstance(limit,int) or not 1<=limit<=(3 if summary else 6):
        raise ValueError('Summary limit must be 1 to 3; full limit must be 1 to 6')
    if preset:
        p = EXPRESSION['presets'][preset]
        creativity = creativity or p['creativity']
        intensity = intensity or p['visual_intensity']
    cases = json.loads((ROOT / 'references/creative-reference-casebook.json').read_text(encoding='utf-8'))['cases']
    if body_only:
        cases = [c for c in cases if c.get('body_only') is True]
    if family:
        cases = [c for c in cases if family in c['page_families']]
    ranked = sorted(cases, key=lambda c: (
        -int(c['creativity'] == creativity) - int(c['visual_intensity'] == intensity),
        -int(c['case_id'] in EXPRESSION.get('default_reference_ids', [])
             and c['creativity'] == creativity and c['visual_intensity'] == intensity), c['case_id']))
    return {'cases': [_summary(c) if summary else c for c in ranked[:limit]], 'query': {'preset': preset, 'creativity': creativity, 'visual_intensity': intensity, 'family': family, 'body_only': body_only},
            'note': 'Closest expression candidates, not exact guarantees. Open the linked actual composition; adapt the relationship to current content. Independent studies and user-accepted compositions are not observed official DEMO report pages. Use study_page_ids when a body reference shares a full document.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preset', choices=EXPRESSION['presets'])
    p.add_argument('--creativity', choices=[c['value'] for c in EXPRESSION['axes']['creativity']['choices']])
    p.add_argument('--intensity', choices=[c['value'] for c in EXPRESSION['axes']['visual_intensity']['choices']])
    p.add_argument('--family', choices=['cover', 'chapter_opener', 'evidence', 'editorial', 'process', 'narrative'])
    p.add_argument('--body-only', action='store_true', help='Return dedicated body compositions; cover studies cannot satisfy this query.')
    p.add_argument('--limit', type=int, default=3)
    p.add_argument('--summary',action='store_true',help='Return only 1–3 compact case identities and reference paths')
    args = vars(p.parse_args())
    if not 1 <= args['limit'] <= (3 if args['summary'] else 6):
        p.error('--limit must be 1 to 3 for summary, otherwise 1 to 6')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(select(**args), ensure_ascii=False, indent=2))
