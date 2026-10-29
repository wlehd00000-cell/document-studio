"""Company-specific font availability, rights and actual-output checks.

Unlike the legacy strict DEMO quality floor, an unrendered or unlicensed font
can never receive PASS merely because CSS names it.
"""
from __future__ import annotations

import re
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree as ET


def _pptx_faces(path: Path) -> set[str]:
    found = set()
    with ZipFile(path) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r"ppt/slides/slide\d+\.xml", name):
                continue
            tree = ET.fromstring(archive.read(name))
            for node in tree.iter():
                value = node.attrib.get('typeface')
                if value:
                    found.add(value)
    return found


def evaluate_font_policy(pack, language: str, *, html_path: Path | None = None,
                         pptx_path: Path | None = None,
                         rendered_font_families: set[str] | None = None) -> dict:
    """Report PASS/FAIL/UNVERIFIED, preserving independent rights and render checks."""
    lang = language.split('-')[0].lower()
    policy = pack.font_policy.get('by_language', {}).get(lang)
    report = {'pack_id': pack.pack_id, 'pack_version': pack.version, 'language': language,
              'family': None, 'status': 'UNVERIFIED', 'findings': []}
    if not isinstance(policy, dict) or not isinstance(policy.get('family'), str) or not policy['family'].strip():
        report.update(status='FAIL', findings=['Missing official font policy for this language'])
        return report
    family = policy['family'].strip()
    report['family'] = family
    report['license'] = policy.get('license', 'unverified')
    report['redistribution'] = policy.get('redistribution', False) is True
    if not policy.get('license') or 'unverified' in str(policy.get('license','')).lower() or 'not verified' in str(policy.get('license','')).lower():
        report['findings'].append('Font licensing has not been independently verified')
    if not report['redistribution']:
        report['findings'].append('Font redistribution is not authorized by this policy')
    if html_path is not None:
        html = Path(html_path).read_text(encoding='utf8')
        if family.casefold() not in html.casefold():
            report.update(status='FAIL')
            report['findings'].append('Expected font is absent from generated HTML/CSS')
    if pptx_path is not None:
        try:
            faces = _pptx_faces(Path(pptx_path))
        except (BadZipFile, ET.ParseError, OSError) as exc:
            report.update(status='FAIL')
            report['findings'].append(f'PowerPoint font inspection failed: {type(exc).__name__}')
        else:
            if family.casefold() not in {face.casefold() for face in faces}:
                report.update(status='FAIL')
                report['findings'].append('Expected font is absent from editable PPTX runs')
    if rendered_font_families is not None and family.casefold() not in {x.casefold() for x in rendered_font_families}:
        report.update(status='FAIL')
        report['findings'].append('Rendered font differs from the policy family')
    if report['status'] != 'FAIL':
        if rendered_font_families is None:
            report['findings'].append('Actual rendered font usage has not been checked')
        if pptx_path is None:
            report['findings'].append('Editable PowerPoint font usage has not been checked')
        if (not report['findings'] and rendered_font_families is not None and pptx_path is not None):
            report['status'] = 'PASS'
    return report
