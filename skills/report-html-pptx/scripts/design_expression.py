"""Resolve optional expression choices without adding an intake gate."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPRESSION = json.loads((ROOT / 'system/design-expression.json').read_text(encoding='utf-8'))
AXES = tuple(EXPRESSION['axes'])


def validate_preferences(value):
    if not isinstance(value, dict) or set(value) - {'preset', *AXES}:
        raise ValueError('Invalid design_preferences keys')
    if 'preset' in value and (not isinstance(value['preset'], str) or value['preset'] not in {*EXPRESSION['presets'], 'auto'}):
        raise ValueError('Unknown expression preset')
    for axis in AXES:
        if axis in value and (not isinstance(value[axis], str) or value[axis] not in {c['value'] for c in EXPRESSION['axes'][axis]['choices']}):
            raise ValueError('Unknown expression value: ' + axis)
    return copy.deepcopy(value)


def resolve_expression(preferences=None, existing=None):
    """An explicit preset resets both axes; partial axis changes reuse other axes."""
    old = (existing or {}).get('design_expression', {})
    default = EXPRESSION['presets'][EXPRESSION['default_preset']]
    values = {axis: default[axis] for axis in AXES}
    reused = {}
    for axis in AXES:
        if old.get(axis) in {c['value'] for c in EXPRESSION['axes'][axis]['choices']}:
            values[axis] = old[axis]
            reused[axis] = old[axis]
    status = 'reused' if reused else 'default_delegated'
    reason = ('Reuse the current expression' if reused else
              'No expression specified; use the configured ' + EXPRESSION['default_preset'] +
              ' (' + '/'.join(default[axis] for axis in AXES) + ') starting point; ' +
              'apply the configured composition reference to actual body pages')
    if preferences is not None:
        preferences = validate_preferences(preferences)
        preset = preferences.get('preset')
        if preset:
            base = EXPRESSION['presets'][EXPRESSION['default_preset'] if preset == 'auto' else preset]
            values = {axis: base[axis] for axis in AXES}
        for axis in AXES:
            if axis in preferences:
                values[axis] = preferences[axis]
        if preferences:
            status = 'delegated' if preset == 'auto' and len(preferences) == 1 else 'explicit'
            reason = 'User requested a recommendation' if status == 'delegated' else 'Submitted expression selection; explicit axes override the selected preset'
    matched = next((key for key, p in EXPRESSION['presets'].items() if all(values[a] == p[a] for a in AXES)), 'custom')
    return {'schema_version': '1.0', 'preset': matched, **values, 'status': status, 'reason': reason}


def expression_prefills(brief):
    old = (brief or {}).get('design_expression', {})
    result = {a: old[a] for a in AXES if old.get(a) in {c['value'] for c in EXPRESSION['axes'][a]['choices']}}
    if old.get('preset') in EXPRESSION['presets']:
        result['preset'] = old['preset']
    return result
