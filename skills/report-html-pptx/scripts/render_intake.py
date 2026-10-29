"""Build a real local wizard or inline fragment; no server or hidden state bridge."""
import argparse
import base64
import json
from pathlib import Path
import re
from intake import CONTRACT, prior_fields, validate_submission
from design_expression import EXPRESSION, expression_prefills

ROOT = Path(__file__).resolve().parents[1]


def render(destination, language='ko', brief=None, formats=None, fragment=False):
    if language not in {'ko', 'ja'}: raise ValueError('UI language must be ko or ja')
    formats = formats or []
    if any(value not in {'PPTX', 'PDF', 'HTML', 'DOCX'} for value in formats): raise ValueError('Unknown verified format capability')
    existing = prior_fields(brief or {})
    prefills = {key: rec['value'] for key, rec in existing.items()
                if rec.get('status') in CONTRACT['resolved_statuses']
                and rec.get('status') != 'assumed' and rec.get('user_confirmed') is not False}
    validate_submission({'schema_version': '1.0', 'fields': prefills})
    config = {'contract': CONTRACT, 'language': language, 'prefills': prefills,
              'expression': EXPRESSION, 'design_preferences': expression_prefills(brief),
              'use': (brief or {}).get('intake', {}).get('layout', {}).get('fields', {}).get('use', {}).get('value'),
              'canvas': (brief or {}).get('intake', {}).get('layout', {}).get('fields', {}).get('canvas', {}).get('value'), 'verified_formats': formats}
    # Escaping < prevents a source field from terminating the data-only script block.
    payload = json.dumps(config, ensure_ascii=False).replace('<', '\\u003c')
    template = (ROOT / 'assets/onboarding/template.fragment.html').read_text(encoding='utf-8')
    css = (ROOT / 'assets/onboarding/intake.css').read_text(encoding='utf-8')
    tokens = json.loads((ROOT/'system/design-tokens.json').read_text(encoding='utf-8'))
    colors = {'blue':tokens['palette']['brand']['blue'], 'teal':tokens['palette']['brand']['green'],
              'text':tokens['palette']['ink'], 'line':tokens['palette']['line']}
    for name, value in colors.items():
        css = re.sub(r'--demo-'+name+r':#[0-9a-fA-F]{6}', '--demo-'+name+':'+value, css)
    script = (ROOT / 'assets/onboarding/intake.js').read_text(encoding='utf-8')
    logo = base64.b64encode((ROOT / 'assets/brand/demo-mark.svg').read_bytes()).decode('ascii')
    result = template.replace('%%STYLE%%', css).replace('%%CONFIG%%', payload).replace('%%SCRIPT%%', script).replace('%%LOGO%%', logo)
    if not fragment: result = '<!doctype html>\n<html lang="' + language + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Document Studio 문서 제작 · 資料作成</title></head><body>\n' + result + '\n</body></html>\n'
    destination = Path(destination).expanduser().resolve()
    source_dir = ROOT / 'assets/onboarding'
    if destination in {source_dir / 'template.fragment.html', source_dir / 'intake.css', source_dir / 'intake.js'}:
        raise ValueError('Output may not overwrite UI source')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(result, encoding='utf-8')
    return {'path': str(destination), 'mode': 'inline' if fragment else 'standalone', 'verified_formats': formats,
            'callback': 'runtime feature detection; actual returned chat submission required', 'prefilled_fields': list(prefills)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination'); parser.add_argument('--language', choices=['ko', 'ja'], default='ko')
    parser.add_argument('--brief'); parser.add_argument('--format', action='append', dest='formats')
    parser.add_argument('--fragment', action='store_true')
    args = vars(parser.parse_args())
    args['brief'] = json.loads(Path(args['brief']).read_text(encoding='utf-8-sig')) if args['brief'] else None
    print(json.dumps(render(**args), ensure_ascii=False))
