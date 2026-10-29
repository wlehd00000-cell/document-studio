"""Resolve an evidence-aware document brief; inspect designated inputs without mutation.

This helper never executes source text, reads arbitrary project trees, or edits inputs.
Missing required choices remain pending; suggestions never become user answers.
"""
import argparse
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from authoring_routes import select_route
from design_expression import validate_preferences, resolve_expression

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / 'references/intake-contract.json').read_text(encoding='utf-8'))
FIELDS = tuple(CONTRACT['fields'])
LAYOUT_FIELDS = tuple(CONTRACT['required_layout_fields'])
ALIASES = {'document_type': 'genre', 'purpose': 'reader_action', 'output_format': 'requested_outputs'}
RESOLVED = set(CONTRACT['resolved_statuses'])
MAX_TEXT = 12000


def validate_submission(value):
    if not isinstance(value, dict):
        raise ValueError('Brief submission must be a JSON object')
    unknown = set(value) - set(CONTRACT['submission_keys'])
    if unknown:
        raise ValueError('Unknown submission keys: ' + ', '.join(sorted(unknown)))
    if value.get('schema_version') != CONTRACT['schema_version']:
        raise ValueError('Unsupported intake schema version')
    fields = value.get('fields')
    if not isinstance(fields, dict) or set(fields) - set(FIELDS):
        raise ValueError('Invalid intake field map')
    for key, item in fields.items():
        if not isinstance(item, str) or not item.strip() or len(item) > 1500:
            raise ValueError('Field values must be nonempty text: ' + key)
    if 'mode' in fields and fields['mode'] not in {'one_shot', 'collaborative'}:
        raise ValueError('Mode requires one_shot or collaborative')
    if 'document_type' in fields and fields['document_type'] not in {'report', 'submission', 'proposal', 'plan', 'presentation', 'guide', 'manual'}:
        raise ValueError('Unknown document type')
    if 'final_language' in fields and not all(re.fullmatch(r'[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*', tag) for tag in fields['final_language'].split('+')):
        raise ValueError('Invalid deliverable language tag')
    delegations = value.get('delegated_fields', [])
    if not isinstance(delegations, list) or any(key not in (*FIELDS, *LAYOUT_FIELDS) for key in delegations) or len(delegations)!=len(set(delegations)):
        raise ValueError('Unknown or duplicate delegated field')
    if set(delegations) & set(fields):
        raise ValueError('A field cannot be both explicitly selected and pending recommendation')
    if value.get('use') is not None and value['use'] not in {item['value'] for item in CONTRACT['use_choices']}:
        raise ValueError('Unknown final use')
    if value.get('notes') is not None and (not isinstance(value['notes'], str) or len(value['notes']) > 6000):
        raise ValueError('Invalid brief notes')
    if value.get('source_paths') is not None and (not isinstance(value['source_paths'], list) or any(not isinstance(p, str) for p in value['source_paths'])):
        raise ValueError('Source paths must be text references')
    if value.get('conversation_language') is not None and value['conversation_language'] not in {'ko', 'ja', 'en'}:
        raise ValueError('Invalid conversation language')
    if value.get('canvas') is not None and value['canvas'] not in {item['value'] for item in CONTRACT['canvas_choices']}:
        raise ValueError('Unknown canvas decision')
    if value.get('review_checkpoint') not in {None, 'content', 'design'}:
        raise ValueError('Unknown review checkpoint')
    origins = value.get('choice_origins', {})
    if not isinstance(origins, dict) or any(k not in (*FIELDS, *LAYOUT_FIELDS) or not isinstance(v, str) or not v.strip() for k, v in origins.items()):
        raise ValueError('Choice origins require located nonempty text')
    # Mode governs authorization to complete the work. An attachment or a vague
    # continuation message cannot delegate it; require a location in the user's
    # current chat instruction rather than a default or an inferred source.
    if 'mode' in delegations and not re.match(r'^(?:user_message|user_request|chat_turn):\S+', origins.get('mode', '')):
        raise ValueError('Mode delegation requires a located explicit user message')
    if any(value.get(k) is not None and k in delegations for k in LAYOUT_FIELDS):
        raise ValueError('A layout choice cannot be both selected and delegated')
    if 'design_preferences' in value:
        validate_preferences(value['design_preferences'])
    return copy.deepcopy(value)


def prior_fields(brief):
    """Read legacy and v3 brief shape without upgrading or modifying its source."""
    current = brief.get('intake', {}).get('fields', {})
    if current:
        return copy.deepcopy(current)
    gate = brief.get('intake_gate', {})
    if gate.get('status') != 'complete':
        return {}
    values = {
        'mode': brief.get('interaction', {}).get('mode'),
        'document_type': brief.get('genre'), 'audience': brief.get('audience'),
        'purpose': brief.get('reader_action'),
        'final_language': '+'.join(brief.get('communication', {}).get('deliverable_languages', [])),
        'output_format': ' + '.join(brief.get('requested_outputs', [])),
    }
    return {key: {'value': value, 'status': gate.get('fields', {}).get(key, 'reused'), 'origin': 'prior brief; retain recorded provenance'}
            for key, value in values.items() if value}


def resolve_layout(submission, existing, hints, recommendations, changed, blocking):
    previous = existing.get('intake', {}).get('layout', {}).get('fields', {})
    result = {}
    choices = {'use': {x['value'] for x in CONTRACT['use_choices']},
               'canvas': {x['value'] for x in CONTRACT['canvas_choices']}}
    for key in LAYOUT_FIELDS:
        rec = previous.get(key, {})
        if key not in changed | blocking and rec.get('status') in RESOLVED and rec.get('value') in choices[key] and rec.get('user_confirmed') is not False and rec.get('origin'):
            result[key] = {**copy.deepcopy(rec), 'status': 'reused'}
        else:
            result[key] = {'value': None, 'status': 'unknown', 'origin': None}
        safe = [h for h in hints if h.get('field') == key and h.get('value') in choices[key]
                and h.get('explicit_field') is True and h.get('current') is True
                and h.get('context_matches') is True and h.get('locator')]
        if result[key]['status'] not in RESOLVED:
            values = {h['value'] for h in safe}
            if len(values) == 1:
                result[key] = {'value': next(iter(values)), 'status': 'source_explicit', 'origin': safe[0]['locator']}
            elif len(values) > 1:
                result[key] = {'value': None, 'status': 'conflict', 'origin': 'conflicting designated sources', 'observations': safe}
        if submission.get(key) is not None:
            result[key] = {'value': submission[key], 'status': 'explicit', 'user_confirmed': True,
                           'origin': submission.get('choice_origins', {}).get(key, 'explicit submission.'+key)}
        if key in submission.get('delegated_fields', []):
            rec = recommendations.get(key, {})
            result[key] = {'value': None, 'status': 'unknown', 'origin': 'specific delegation; recommendation pending'}
            if isinstance(rec, dict) and rec.get('value') in choices[key] and rec.get('reason'):
                result[key] = {'value': rec['value'], 'status': 'delegated', 'reason': rec['reason'],
                               'origin': submission.get('choice_origins', {}).get(key, 'specific user delegation')}
        if result[key]['status'] not in RESOLVED:
            result[key]['suggested_value'] = CONTRACT['startup_policy']['default_use' if key == 'use' else 'default_canvas']
            result[key]['suggestion_reason'] = CONTRACT['startup_policy']['reason']
    # Neither a legacy intake.use default nor an AI-authored report-config proves acceptance.
    return {'fields': result, 'missing': [k for k in LAYOUT_FIELDS if result[k]['status'] not in RESOLVED]}


def resolve_intake(submission=None, existing=None, hints=None, changed_fields=None, recommendations=None, blocking_fields=None):
    """Merge user submission, valid brief reuse and located source observations.

    Hints must declare context_matches/current/explicit_field and a real locator to
    resolve a field. Content language, filenames, sample values and ambiguous clues
    remain candidates. Explicit user changes take precedence and retain history.
    """
    submission = validate_submission(submission or {'schema_version': '1.0', 'fields': {}})
    existing = existing or {}
    changed = set(changed_fields or [])
    if not changed.issubset((*FIELDS, *LAYOUT_FIELDS)):
        raise ValueError('Unknown changed intake field')
    blocking = set(blocking_fields or [])
    if not blocking.issubset((*FIELDS, *LAYOUT_FIELDS)):
        raise ValueError('Unknown blocking intake field')
    old = prior_fields(existing)
    result = {key: {'value': None, 'status': 'unknown', 'origin': None} for key in FIELDS}
    for key, record in old.items():
        if key not in result or key in changed or key in blocking:
            continue
        if record.get('status') in RESOLVED and record.get('value') and record.get('user_confirmed') is not False:
            result[key] = {**record, 'status': 'reused', 'origin': record.get('origin', 'accepted prior brief')}
        elif record.get('status') == 'assumed' or record.get('user_confirmed') is False:
            result[key] = {'value': None, 'status': 'candidate', 'origin': 'unconfirmed prior assumption',
                           'previous_assumption': copy.deepcopy(record)}
        elif record.get('status') not in RESOLVED:
            result[key] = copy.deepcopy(record)
    hints = hints or []
    for key in FIELDS:
        if result[key]['status'] in RESOLVED:
            continue
        candidates = [h for h in hints if h.get('field') == key and h.get('value')]
        # Mode can only come from a current user request or accepted prior brief.
        safe = [h for h in candidates if key != 'mode' and h.get('explicit_field') is True
                and h.get('current') is True and h.get('context_matches') is True and h.get('locator')]
        values = {str(h['value']) for h in safe}
        if len(values) == 1:
            result[key] = {'value': next(iter(values)), 'status': 'source_explicit', 'origin': safe[0]['locator'], 'observations': safe}
        elif len(values) > 1:
            result[key] = {'value': None, 'status': 'conflict', 'origin': 'conflicting designated sources', 'observations': safe}
        elif candidates and result[key]['status'] != 'conflict':
            result[key] = {'value': None, 'status': 'candidate', 'origin': 'unconfirmed source clues', 'observations': candidates}
    for key, value in submission['fields'].items():
        previous = result[key]
        result[key] = {'value': value.strip(), 'status': 'explicit', 'origin': submission.get('choice_origins', {}).get(key, 'explicit user submission'), 'user_words': value}
        if previous.get('value') and previous['value'] != value:
            result[key]['supersedes'] = previous
    for key in submission.get('delegated_fields', []):
        if key in LAYOUT_FIELDS: continue
        # A reasoned choice is necessary; delegation is not a value by itself.
        result[key] = {'value': None, 'status': 'unknown', 'origin': 'specific user delegation; recommendation pending'}
        rec = (recommendations or {}).get(key)
        valid = (isinstance(rec, dict) and isinstance(rec.get('value'), str)
                 and isinstance(rec.get('reason'), str) and rec['reason'].strip())
        if key == 'mode':
            valid = valid and rec['value'] in {'one_shot', 'collaborative'}
        if valid:
            result[key] = {'value': rec['value'], 'status': 'delegated',
                           'origin': submission.get('choice_origins', {}).get(key, 'specific user delegation'),
                           'reason': rec['reason']}
    defaults = CONTRACT['startup_policy']['defaults']
    chat_language = submission.get('conversation_language') or existing.get('communication', {}).get('conversation_language') or 'ko'
    for key in FIELDS:
        record = result[key]
        if record['status'] in RESOLVED:
            continue
        rec = (recommendations or {}).get(key)
        valid_rec = isinstance(rec, dict) and rec.get('value') and rec.get('reason')
        value = rec['value'] if valid_rec else defaults[key]
        if value == '$conversation_language':
            value = chat_language
        # Recommendations aid the next question; they cannot close an unanswered field.
        result[key] = {**record, 'suggested_value': value,
                       'suggestion_reason': rec['reason'] if valid_rec else CONTRACT['startup_policy']['reason']}
    missing = [key for key in FIELDS if result[key]['status'] not in RESOLVED]
    # Validate resolved decisions, even when they came from a source or legacy brief.
    resolved_values = {key: record['value'] for key, record in result.items() if record['status'] in RESOLVED}
    validate_submission({'schema_version': '1.0', 'fields': resolved_values})
    layout = resolve_layout(submission, existing, hints, recommendations or {}, changed, blocking)
    missing += layout['missing']
    use = layout['fields']['use']['value']
    canvas = layout['fields']['canvas']['value']
    route_selection = None
    if result['output_format']['status'] in RESOLVED:
        route_selection = select_route({'use':use,'output_format':result['output_format']['value'],'existing_template':use == 'template_edit'})
    return {'schema_version': '1.0', 'fields': result, 'use': use, 'canvas': canvas, 'layout': layout,
            'review_checkpoint': submission.get('review_checkpoint') or existing.get('intake', {}).get('review_checkpoint'),
            'status': 'ready' if not missing else 'needs_decision', 'missing': missing,
            'question_groups': [missing] if missing else [],
            'assumptions': {},
            'suggestions': {key: {'value': record['suggested_value'], 'reason': record['suggestion_reason']}
                            for key, record in result.items() if 'suggested_value' in record},
            'conversation_language': chat_language,
            'route_selection':route_selection,
            'design_expression': resolve_expression(submission.get('design_preferences'), existing),
            'preflight_allowed': True, 'production_allowed': not missing,
            'note': 'Core choices, use and canvas must be resolved. PPTX is not a ratio. All six required core choices must be explicit, validly reused, source-explicit or specifically delegated with a reasoned recommendation. Partial replies and silence keep the remaining questions pending. Independent source review may proceed.'}


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []; self.skipped = 0
    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style'}: self.skipped += 1
    def handle_endtag(self, tag):
        if tag in {'script', 'style'} and self.skipped: self.skipped -= 1
    def handle_data(self, data):
        if not self.skipped: self.parts.append(data)


def inspect_source(path):
    path = Path(path).expanduser().resolve()
    result = {'path': str(path), 'exists': path.is_file(), 'review': 'bounded preflight',
              'decisions_confirmed': False}
    if not path.is_file(): return result
    result.update(bytes=path.stat().st_size, type=path.suffix.lower())
    if path.stat().st_size > 100 * 1024 * 1024:
        result['limitation'] = 'Input over 100 MB; metadata only'; return result
    result['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    text = ''
    try:
        if path.suffix.lower() in {'.txt', '.md', '.csv', '.tsv', '.json', '.html'}:
            with path.open(encoding='utf-8-sig') as source: text = source.read(MAX_TEXT)
            if path.suffix.lower() == '.html':
                parser = TextOnly(); parser.feed(text); text = '\n'.join(parser.parts)
        elif path.suffix.lower() in {'.pptx', '.docx'}:
            with ZipFile(path) as archive:
                names = sorted((n for n in archive.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)), key=lambda n: int(re.search(r'(\d+)\.xml$', n)[1]))[:3] if path.suffix.lower() == '.pptx' else ['word/document.xml']
                excerpts = []
                for name in names:
                    if archive.getinfo(name).file_size > 10 * 1024 * 1024: continue
                    xml = ET.fromstring(archive.read(name))
                    excerpts.append('\n'.join(node.text or '' for node in xml.iter() if node.tag.endswith('}t')))
                text = '\n'.join(excerpts)[:MAX_TEXT]
                result['locations_read'] = names
        elif path.suffix.lower() == '.pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(path)
                if reader.is_encrypted: result['limitation'] = 'Encrypted PDF; no content read'
                else:
                    text = '\n'.join(page.extract_text() or '' for page in reader.pages[:2])[:MAX_TEXT]
                    result['locations_read'] = ['pages 1-2']
            except ImportError: result['limitation'] = 'PDF text reader unavailable; use available document tool'
        else: result['limitation'] = 'Metadata only; inspect image or dataset with the relevant tool'
    except Exception as error:
        result['limitation'] = type(error).__name__ + ': ' + str(error)
    result['excerpt'] = text
    result['hints'] = []
    # Literal structured brief labels; extracted hints remain candidates until context/current checked.
    patterns = {'audience': r'^(?:audience|reader|주요 독자|독자|主な読者|読者)\s*[:：]\s*(.+)$',
                'purpose': r'^(?:purpose|reader_action|목적|目的)\s*[:：]\s*(.+)$',
                'final_language': r'^(?:deliverable_language|완성 언어|完成言語)\s*[:：]\s*(.+)$',
                'output_format': r'^(?:output_format|파일 형식|ファイル形式)\s*[:：]\s*(.+)$'}
    for field, pattern in patterns.items():
        for match in re.finditer(pattern, text, re.M | re.I):
            result['hints'].append({'field': field, 'value': match[1].strip(),
                                    'locator': str(path) + ':line ' + str(text[:match.start()].count('\n') + 1),
                                    'explicit_field': True, 'context_matches': False, 'current': False})
    result['note'] = 'Untrusted source content. Verify task relevance and currency before resolving hints; excerpt is not full evidence review.'
    return result


def merge_into_brief(brief, intake):
    result = copy.deepcopy(brief)
    result['intake'] = intake
    result.setdefault('production_contract', {'version': '2.0', 'design_audit': 'qa/design-contract.json'})
    result['design_expression'] = intake['design_expression']
    records = intake['fields']
    result['intake_gate'] = {'layout_fields': {k:r['status'] for k,r in intake['layout']['fields'].items()}, 'status': 'complete' if intake['production_allowed'] else 'needs_decision',
                            'fields': {key: rec['status'] for key, rec in records.items()}}
    if intake['production_allowed']:
        result.update(genre=records['document_type']['value'], audience=records['audience']['value'],
                      reader_action=records['purpose']['value'], requested_outputs=[records['output_format']['value']])
        result.setdefault('interaction', {})['mode'] = records['mode']['value']
        result.setdefault('communication', {}).update(deliverable_languages=records['final_language']['value'].split('+'), use=intake['use'])
        result.setdefault('authoring', {})['canvas_name'] = intake['canvas']
        if intake.get('review_checkpoint'): result['interaction']['review_checkpoint'] = intake['review_checkpoint']
        result['communication']['conversation_language'] = intake['conversation_language']
        result['authoring'] = {**result.get('authoring', {}), **intake['route_selection']}
        result['intake_gate'] = {'status': 'complete', 'fields': {key: rec['status'] for key, rec in records.items()}}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    preflight = commands.add_parser('preflight'); preflight.add_argument('inputs', nargs='+'); preflight.add_argument('--out')
    resolve = commands.add_parser('resolve'); resolve.add_argument('--submission'); resolve.add_argument('--existing'); resolve.add_argument('--hints'); resolve.add_argument('--recommendations'); resolve.add_argument('--changed-field', action='append'); resolve.add_argument('--blocking-field', action='append'); resolve.add_argument('--out')
    imported = commands.add_parser('import'); imported.add_argument('submission'); imported.add_argument('--existing'); imported.add_argument('--out', required=True)
    args = parser.parse_args()
    read = lambda path: json.loads(Path(path).read_text(encoding='utf-8-sig')) if path else None
    if args.action == 'preflight': result = {'files': [inspect_source(path) for path in args.inputs], 'production_started': False}
    else:
        existing = read(args.existing) or {}
        result = resolve_intake(read(args.submission), existing, read(getattr(args, 'hints', None)), getattr(args, 'changed_field', None), read(getattr(args, 'recommendations', None)), getattr(args, 'blocking_field', None))
        if args.action == 'import': result = merge_into_brief(existing, result)
    if args.out:
        destination = Path(args.out).resolve()
        input_paths = [Path(path).resolve() for path in (getattr(args, 'inputs', None) or [getattr(args, 'submission', None), getattr(args, 'existing', None), getattr(args, 'hints', None), getattr(args, 'recommendations', None)]) if path]
        if destination in input_paths: raise ValueError('Output must not overwrite an input; use a reviewed temporary brief then apply it deliberately')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
