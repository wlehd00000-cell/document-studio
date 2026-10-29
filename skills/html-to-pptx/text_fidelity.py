"""Compare browser-measured text boxes with editable PPTX text, without rendering.

This is a content/order/required-spacing check. It is not linguistic correction,
glyph/line-flow verification, or independent proof that measurements are current.
The converter binds the measurements to its input/cache before calling it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET
import zipfile

NS = {
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}
RELNS = 'http://schemas.openxmlformats.org/package/2006/relationships'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def characters_and_spaces(value):
    """Whitespace collapses, but required word boundaries are retained separately."""
    chars, spaces = [], set()
    for ch in value:
        if ch.isspace():
            if chars:
                spaces.add(len(chars))
        else:
            chars.append(ch)
    spaces.discard(len(chars))
    return ''.join(chars), spaces

def hard_break_positions(value):
    count, positions = 0, set()
    for char in value:
        if char in {'\n', '\r'}:
            positions.add(count)
        elif not char.isspace():
            count += 1
    positions.discard(0)
    positions.discard(count)
    return positions

def body_text(body):
    parts = []
    for paragraph in body.findall('a:p', NS):
        if parts:
            parts.append('\n')
        for item in paragraph.iter():
            if item.tag == '{' + NS['a'] + '}t':
                parts.append(item.text or '')
            elif item.tag == '{' + NS['a'] + '}br':
                parts.append('\n')
    return ''.join(parts)

def measured_display_text(record):
    """Honor the same explicit per-run CSS case transform as the assembler."""
    inherited = record.get('style', {}).get('textTransform', 'none')
    runs = record.get('runs')
    if not runs:
        runs = [{'text': record.get('text', '')}]
    parts = []
    for run in runs:
        if run.get('linebreak'):
            parts.append('\n')
        value = run.get('text', '')
        transform = run.get('textTransform') or inherited
        if transform == 'uppercase':
            value = value.upper()
        elif transform == 'lowercase':
            value = value.lower()
        parts.append(value)
    return ''.join(parts)

def ordered_slides(package):
    manifest = ET.fromstring(package.read('ppt/presentation.xml'))
    relationships = ET.fromstring(package.read('ppt/_rels/presentation.xml.rels'))
    rels = {r.get('Id'): r for r in relationships.findall('{' + RELNS + '}Relationship')}
    for sid in manifest.findall('p:sldIdLst/p:sldId', NS):
        relation = rels.get(sid.get('{' + NS['r'] + '}id'))
        if relation is None or relation.get('TargetMode') == 'External':
            raise ValueError('Invalid slide relationship')
        target = relation.get('Target', '')
        member = target.lstrip('/') if target.startswith('/') else 'ppt/' + target
        if '..' in PurePosixPath(member).parts:
            raise ValueError('Unexpected slide relationship traversal')
        yield ET.fromstring(package.read(member))

def audit(pptx, measurements, output=None):
    pptx, measurements = Path(pptx), Path(measurements)
    expected = json.loads(measurements.read_text(encoding='utf-8'))['slides']
    pages, findings = [], []
    with zipfile.ZipFile(pptx) as package:
        bad = package.testzip()
        if bad:
            raise ValueError('Broken PPTX ZIP member: ' + bad)
        slides = list(ordered_slides(package))
        if len(slides) != len(expected):
            findings.append({'severity': 'blocking', 'code': 'page_count',
                             'detail': 'Measured/PPTX page count differs'})
        for index, (source, slide) in enumerate(zip(expected, slides), 1):
            records = [r for r in source['records'] if r['kind'] == 'text' and measured_display_text(r).strip()]
            bodies = slide.findall('.//p:txBody', NS)
            actual = [value for body in bodies if (value := body_text(body)).strip()]
            local = []
            if len(records) != len(actual):
                local.append({'severity': 'blocking', 'code': 'native_text_coverage',
                              'detail': 'Measured/native text-box count differs'})
            for number, (record, native) in enumerate(zip(records, actual), 1):
                original = measured_display_text(record)
                sc, ss = characters_and_spaces(original)
                nc, ns = characters_and_spaces(native)
                if sc != nc:
                    local.append({'severity': 'blocking', 'code': 'native_text_order_or_content',
                                  'box': number, 'record_id': record.get('id'),
                                  'detail': 'Exact non-whitespace character order differs'})
                elif ss - ns:
                    local.append({'severity': 'blocking', 'code': 'required_space_lost',
                                  'box': number, 'record_id': record.get('id'),
                                  'positions': sorted(ss - ns),
                                  'detail': 'Source word boundaries disappeared in native text'})
                elif hard_break_positions(original) - hard_break_positions(native):
                    local.append({'severity': 'blocking', 'code': 'intended_linebreak_lost',
                                  'box': number, 'record_id': record.get('id'),
                                  'positions': sorted(hard_break_positions(original) - hard_break_positions(native)),
                                  'detail': 'Authored/verified line break became continuous native text'})
            for item in local:
                item['page'] = str(index)
            findings.extend(local)
            pages.append({'page': str(index), 'measured_text_boxes': len(records),
                          'native_text_boxes': len(actual), 'findings': local})
    report = {'schema_version': 1, 'format': 'pptx-text-fidelity-v1',
              'status': 'blocked' if findings else 'checked',
              'pptx': {'path': str(pptx), 'sha256': sha(pptx)},
              'measurements': {'path': str(measurements), 'sha256': sha(measurements)},
              'implementation_sha256': sha(__file__), 'pages': pages, 'findings': findings,
              'limitations': 'Does not certify grammar, optional spacing style, rendered wrapping, glyphs, crop, current HTML measurement or human acceptance.'}
    if output:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pptx', required=True, type=Path)
    parser.add_argument('--measurements', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.pptx, args.measurements, args.out)
    print(json.dumps({'status': report['status'], 'pages': len(report['pages']),
                      'findings': len(report['findings'])}))
    return 2 if report['findings'] else 0

if __name__ == '__main__':
    raise SystemExit(main())
