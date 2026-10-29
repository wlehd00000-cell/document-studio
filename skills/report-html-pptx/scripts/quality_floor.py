"""Document Studio Quality Floor P0/P1: minimal strict font policy and independent PPTX audit.

Follow-up checks reuse current ProjectState export reviews and the existing
browser/font/PowerPoint inspectors. They cover this project and host, not approval
or upstream licensing/other-platform certification. Missing tools fail closed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import io
import os
import platform
import struct
import sys
import tempfile
from collections import Counter
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile
from font_policy import evaluate_font_policy as evaluate_company_font_policy

P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
PR = '{http://schemas.openxmlformats.org/package/2006/relationships}'
MODES = {'NEW_DOCUMENT', 'REVISE_ACCEPTED', 'CONVERT_REVIEWED'}
FONT_FILES = {'ja': '_external_PretendardJPVariable.woff2', 'ko': '_external_PretendardVariable.woff2'}
FONT_FAMILY = {'ja': 'Pretendard JP', 'ko': 'Pretendard'}
SHA_PATTERN = re.compile(r'^[a-f0-9]{64}$')
CJK = re.compile(r'[\u3400-\u9fff\uf900-\ufaff]')
KANA = re.compile(r'[\u3040-\u30ff\u31f0-\u31ff]')
HANGUL = re.compile(r'[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]')


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checksum_json(doc: dict) -> str:
    return hashlib.sha256(json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf8')).hexdigest()


def inside(root: Path, rel: str) -> Path:
    # Never allow generated project contracts to read outside their project.
    root = root.resolve()
    if not isinstance(rel, str) or '\\' in rel or not rel or PurePosixPath(rel).is_absolute():
        raise ValueError(f'Invalid project relative path: {rel!r}')
    dst = (root / rel).resolve()
    if not dst.is_relative_to(root):
        raise ValueError(f'Asset outside project: {rel}')
    return dst


def font_metadata(path: Path) -> tuple[set[int], str]:
    from fontTools.ttLib import TTFont
    with TTFont(str(path), lazy=True) as ft:
        cmap = set(ft.getBestCmap() or {})
        name = ft['name']
        fam = (name.getDebugName(16) or name.getDebugName(1) or '').strip()
    if not cmap or not fam:
        raise ValueError(f'Font lacks family name or cmap: {path.name}')
    return cmap, fam


def compatible_family(actual: str, required: str) -> bool:
    a = re.sub(r'\s+', ' ', str(actual or '').strip()).casefold()
    b = re.sub(r'\s+', ' ', required.strip()).casefold()
    # The bundled exporter instantiates the golden fixture's CSS weight 750 exactly.
    return a == b or bool(re.fullmatch(re.escape(b) + r'(?: variable| (?:[1-9]00|750)(?: (?:italic|bold))?)', a))


def resolve_contract(project: Path, brand_assets: Path, tokens_path: Path, *,
                     language: str = 'ja-JP', mode: str = 'NEW_DOCUMENT',
                     profile: str = 'executive_approval', additional_languages=()) -> dict:
    """Resolve source bytes once; project asset must match a known bundled asset.

    This is bundle integrity, not independent upstream/author licensing verification.
    REVISE/CONVERT require an accepted source contract and are intentionally not auto-resolved.
    """
    if mode not in MODES:
        raise ValueError('Unknown mode')
    if mode != 'NEW_DOCUMENT':
        raise ValueError('Revision/conversion require explicit approved source baseline; no DEMO font injection')
    project = Path(project).resolve()
    tokens_path = Path(tokens_path).resolve()
    brand_assets = Path(brand_assets).resolve()
    tokens = json.loads(tokens_path.read_text(encoding='utf-8'))
    if profile not in tokens['profiles']:
        raise ValueError(f'Unknown profile: {profile}')
    if tokens['font']['by_language']['ja']['primary'] != 'Pretendard JP' or tokens['font']['by_language']['ko']['primary'] != 'Pretendard':
        raise ValueError('Unexpected DEMO font policy; review and version policy before changing')
    langs = list(dict.fromkeys([str(language).split('-')[0].lower(), *[str(x).split('-')[0].lower() for x in additional_languages]]))
    if any(x not in FONT_FILES for x in langs):
        raise ValueError('P0/P1 supports Japanese/Korean DEMO fonts only; no implicit fallback')
    sources = {}
    for lang in langs:
        filename = FONT_FILES[lang]
        rel = f'html/assets/{filename}'
        project_font = inside(project, rel)
        bundle_font = brand_assets / filename
        if not project_font.is_file() or not bundle_font.is_file():
            raise ValueError(f'Required bundled {lang} font missing: {filename}')
        actual_sha, trusted_sha = sha(project_font), sha(bundle_font)
        if actual_sha != trusted_sha:
            raise ValueError(f'Required {lang} project font differs from bundled original: {filename}')
        cmap, internal_name = font_metadata(project_font)
        if not compatible_family(internal_name, FONT_FAMILY[lang]):
            raise ValueError(f'Internal font name mismatch: {internal_name!r} vs {FONT_FAMILY[lang]!r}')
        sources[lang] = {'family': FONT_FAMILY[lang], 'asset': rel, 'sha256': actual_sha,
                         'bundled_sha256': trusted_sha, 'internal_family': internal_name,
                         'cmap_count': len(cmap), 'origin_level': 'matched_plugin_bundle_not_upstream_verified'}
    body = {'schema_version':'demo-quality-floor/0.1', 'mode':mode, 'document':{'language':language,'profile':profile},
            'source_tokens_sha256':sha(tokens_path),'font_sources':sources,
            'output_policy':{'font_missing_is_blocking': True,'embed_missing_is_unverified':True,
                             'required_native_renderer':'PowerPoint for Windows', 'editable_text':True},
            'scope':'structural-font-first; visual/font-substitution not certified'}
    body['contract_sha256'] = checksum_json(body)
    return body


def write_contract(contract: dict, path: Path) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError('Never silently replace a project quality contract')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(contract, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')


def _valid_contract(contract: dict) -> bool:
    if contract.get('schema_version') != 'demo-quality-floor/0.1':
        return False
    actual = {k:v for k,v in contract.items() if k != 'contract_sha256'}
    return contract.get('contract_sha256') == checksum_json(actual)


def _languages(text: str, lang_hint: str, default: str) -> set[str]:
    found=set()
    if HANGUL.search(text): found.add('ko')
    if KANA.search(text): found.add('ja')
    if CJK.search(text):
        if lang_hint.startswith('ja'): found.add('ja')
        elif lang_hint.startswith('ko'): found.add('ko')
        else: found.add(default)
    return found


def _rid_links(archive: ZipFile):
    relname='ppt/_rels/presentation.xml.rels'
    if relname not in archive.namelist(): return {}
    rels=ET.fromstring(archive.read(relname))
    return {r.get('Id'):r for r in rels.findall(f'{PR}Relationship')}


def _followup_inputs(contract, root, path, state, target):
    """Locate current files through the existing project, never a claimed status."""
    if not _valid_contract(contract) or json.loads((root/'content/quality-contract.json').read_text('utf8')) != contract:
        raise ValueError('Follow-up contract is not the current project quality contract')
    canonical = state.state['canonical']
    html = state.path(state.state['nodes'][canonical]['path'])
    if not state.freshness(canonical)['fresh'] or not state.freshness(target)['fresh']:
        raise ValueError('Follow-up target or canonical HTML is stale')
    if canonical not in state.walk(target):
        raise ValueError('Export must depend on the canonical HTML')
    audit = path.parent / (path.stem + '_audit')
    outcome = json.loads((audit/'conversion-result.json').read_text('utf8'))
    authored_input = Path(outcome['source']['path']).resolve()
    if (not authored_input.is_relative_to(root) or sha(authored_input) != outcome['source']['sha256']
            or outcome['output_sha256'] != sha(path) or Path(outcome['output']).resolve() != path
            or outcome.get('findings') or outcome.get('status') != 'review_candidate'):
        raise ValueError('Conversion outcome belongs to missing, changed or different files')
    required = [html, path, authored_input, root/'content/quality-contract.json',
                audit/'conversion-result.json', audit/'text-fidelity.json',
                audit/'demo-html-glyph-fonts.json', audit/'_cache/measurements.json',
                audit/'_ppt_renders/render-source.pdf', audit/'_ppt_renders/renderer-profile.json']
    for number in range(1, len(state.state['page_order']) + 1):
        required.append(audit/f'_ppt_renders/slide_{number:02d}.png')
    fonts = {}
    for lang, source in contract['font_sources'].items():
        original = Path(__file__).resolve().parents[1]/'assets/brand'/FONT_FILES[lang]
        local = inside(root, source['asset'])
        if sha(local) != source['sha256'] or sha(original) != source['bundled_sha256'] or sha(local) != sha(original):
            raise ValueError('Original bundle and project font binaries differ: ' + lang)
        if not compatible_family(font_metadata(local)[1], source['family']):
            raise ValueError('Actual font internal family differs: ' + lang)
        required.append(local)
        fonts[lang] = {'asset': source['asset'], 'sha256': sha(local), 'bundle_sha256': sha(original)}
    files = {file.resolve().relative_to(root).as_posix(): sha(file) for file in required}
    exporter = Path(__file__).resolve().parents[2]/'html-to-pptx'
    implementations = [Path(__file__), Path(__file__).with_name('production_contract.py'),
                       Path(__file__).with_name('project_state.py'), exporter/'convert.py',
                       exporter/'text_fidelity.py', *sorted((exporter/'scripts').glob('*.py'))]
    return {'project_root': str(root), 'target': target, 'target_signature': state.signature(target),
            'html_signature': state.signature(canonical), 'html': html.relative_to(root).as_posix(),
            'pptx_sha256': sha(path), 'html_sha256': sha(html), 'contract_sha256': contract['contract_sha256'],
            'fonts': fonts, 'files': files,
            'implementation': {p.relative_to(exporter.parent).as_posix(): sha(p) for p in implementations}}


@lru_cache(maxsize=12)
def _source_static_face(source_bytes, family, weight, slot):
    """Rebuild from source bytes, independent of the exporter's persistent cache."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from font_resolver import _normalize_to_slot
    font = TTFont(io.BytesIO(source_bytes))
    if 'fvar' not in font:
        raise ValueError('Expected the contracted variable font source')
    axis = next(a for a in font['fvar'].axes if a.axisTag == 'wght')
    if not axis.minValue <= weight <= axis.maxValue:
        raise ValueError('Embedded font weight outside the source axis')
    font = instantiateVariableFont(font, {'wght': weight}, inplace=False, optimize=True)
    font.flavor = None
    with tempfile.TemporaryDirectory(prefix='demo-source-font-') as directory:
        generated = Path(directory)/'source.ttf'
        font.save(generated)
        _normalize_to_slot(generated, family, slot, source_weight=weight)
        return generated.read_bytes()


def _check_embedded_origin(contract, root, path, measurement, temporary):
    from fontTools.ttLib import TTFont
    from embed_fonts import chars_from_measurement, subset_ttf, eot_from_ttf
    checked = []
    with ZipFile(path) as archive:
        rels = _rid_links(archive)
        presentation = ET.fromstring(archive.read('ppt/presentation.xml'))
        for entry in presentation.findall(f'{P}embeddedFontLst/{P}embeddedFont'):
            face = entry.find(f'{P}font').get('typeface')
            match = re.fullmatch(r'(Pretendard JP|Pretendard) ([1-9]00|750)', face)
            if not match:
                raise ValueError('Embedded face has no source/weight identity: ' + face)
            family, weight = match.group(1), int(match.group(2))
            source = next((s for s in contract['font_sources'].values() if s['family'] == family), None)
            if not source:
                raise ValueError('Embedded family has no contracted source: ' + face)
            count = 0
            for slot in ('regular', 'bold', 'italic', 'boldItalic'):
                node = entry.find(f'{P}{slot}')
                if node is None:
                    continue
                if slot != ('bold' if weight >= 600 else 'regular'):
                    raise ValueError('Embedded font style slot disagrees with the actual source weight')
                relationship = rels[node.get(f'{R}id')]
                target = relationship.get('Target', '').lstrip('/')
                target = target if target.startswith('ppt/') else 'ppt/' + target
                payload = archive.read(target)
                size = struct.unpack_from('<I', payload, 4)[0]
                if not 0 < size < len(payload):
                    raise ValueError('Invalid EOT font payload size')
                actual_bytes = payload[-size:]
                if eot_from_ttf(actual_bytes) != payload:
                    raise ValueError('Invalid or unsupported EOT wrapper')
                generated = temporary/'expected.ttf'
                generated.write_bytes(_source_static_face(inside(root, source['asset']).read_bytes(), face, weight, slot))
                expected_bytes = subset_ttf(generated, chars_from_measurement(measurement))
                with TTFont(io.BytesIO(actual_bytes)) as actual, TTFont(io.BytesIO(expected_bytes)) as expected:
                    if set(actual.keys()) != set(expected.keys()):
                        raise ValueError('Embedded subset table set differs from the original font')
                    for tag in set(actual.keys()) - {'GlyphOrder'}:
                        left, right = actual.getTableData(tag), expected.getTableData(tag)
                        if tag == 'head':
                            # Only checksumAdjustment and created/modified timestamps vary.
                            left = left[:8] + b'\0'*4 + left[12:20] + b'\0'*16 + left[36:]
                            right = right[:8] + b'\0'*4 + right[12:20] + b'\0'*16 + right[36:]
                        if left != right:
                            raise ValueError(f'Embedded font does not derive from the source: {face}/{tag}')
                count += 1
                checked.append({'typeface': face, 'slot': slot, 'source_sha256': source['sha256'],
                                'embedded_payload_sha256': hashlib.sha256(payload).hexdigest()})
            if not count:
                raise ValueError('Embedded font entry has no payload')
    if not checked:
        raise ValueError('No embedded source font payloads')
    return checked


def _recheck_followup(contract, root, path, inputs):
    """Re-observe real files and native output; success-only JSON cannot pass."""
    exporter = Path(__file__).resolve().parents[2]/'html-to-pptx'
    for directory in (exporter, exporter/'scripts'):
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
    from document_quality_html_gate import audit as glyph_audit
    from measure import open_deck_page, measure
    from dependency_cache import capture
    from text_fidelity import audit as text_audit
    from self_check import _try_powerpoint_com
    from PIL import Image, ImageChops
    import fitz
    html = inside(root, inputs['html'])
    browser_path = os.environ.get('GS_QF_BROWSER_PATH') or None
    glyphs = glyph_audit(html, contract, root, browser_path=browser_path)
    if glyphs.get('blocking') or not glyphs.get('samples'):
        raise ValueError('Actual HTML glyph font check failed: ' + str(glyphs.get('blocking')))
    with tempfile.TemporaryDirectory(prefix='demo-evidence-recheck-') as directory:
        temporary = Path(directory)
        with open_deck_page(html, browser_path=browser_path) as page:
            measurement = measure(html, temporary/'measurements.json', no_screenshots=True, verbose=False, page=page)
            dependencies = capture(html, page)
        resources = {}
        if dependencies.get('unresolved'):
            raise ValueError('Unresolved HTML resources cannot bind follow-up evidence')
        for name, digest in dependencies['files'].items():
            file = Path(name).resolve()
            if not file.is_relative_to(root) or sha(file) != digest:
                raise ValueError('HTML dependency is outside the project or changed')
            resources[file.relative_to(root).as_posix()] = digest
        fidelity = text_audit(path, temporary/'measurements.json', temporary/'text-fidelity.json')
        if fidelity.get('findings'):
            raise ValueError('Actual HTML/native text parity failed: ' + str(fidelity['findings']))
        payloads = _check_embedded_origin(contract, root, path, measurement, temporary)
        renders = temporary/'renders'
        renders.mkdir()
        diagnostics = {}
        count, error = _try_powerpoint_com(path, renders, font_diagnostics=diagnostics)
        expected = {p['typeface'] for p in payloads}
        if (error or count != len(measurement['slides']) or diagnostics.get('status') != 'verified'
                or diagnostics.get('render_method') != 'PowerPoint-PDF/PyMuPDF'
                or not all(diagnostics.get('recognized', {}).get(face) is True for face in expected)):
            raise ValueError('Actual embedded-font PowerPoint PDF rendering unavailable or failed: ' + str(error or diagnostics))
        previous = path.parent/(path.stem+'_audit')/'_ppt_renders'
        with fitz.open(renders/'render-source.pdf') as pdf, fitz.open(previous/'render-source.pdf') as recorded_pdf:
            if len(recorded_pdf) != count:
                raise ValueError('Recorded PowerPoint PDF has a different page count')
            for number, slide in enumerate(measurement['slides'], 1):
                name = f'slide_{number:02d}.png'
                with Image.open(previous/name) as original, Image.open(renders/name) as current:
                    if original.size != current.size or ImageChops.difference(original.convert('RGB'), current.convert('RGB')).getbbox():
                        raise ValueError('Current PowerPoint page differs from the inspected export: ' + str(number))
                    recorded_page = recorded_pdf[number-1]
                    matrix = fitz.Matrix(current.width/recorded_page.rect.width, current.height/recorded_page.rect.height)
                    pixmap = recorded_page.get_pixmap(matrix=matrix, alpha=False, colorspace=fitz.csRGB)
                    if pixmap.width != current.width or pixmap.height != current.height or pixmap.samples != current.convert('RGB').tobytes():
                        raise ValueError('Recorded PDF does not match the actual PowerPoint page: ' + str(number))
                native = pdf[number-1].get_text()
                text = ''.join(r.get('text', '') for r in slide['records'] if r.get('kind') == 'text')
                scripts = lambda s: Counter(c for c in s if CJK.match(c) or KANA.match(c) or HANGUL.match(c))
                if scripts(native) != scripts(text):
                    raise ValueError('PowerPoint PDF omits or changes script glyphs: ' + str(number))
        # Bind the actual Office build/executable and host, not just the label "Windows".
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        owns = False
        try:
            try: office = win32com.client.GetActiveObject('PowerPoint.Application')
            except Exception:
                office = win32com.client.DispatchEx('PowerPoint.Application'); owns = True
            executable = Path(office.Path)/'POWERPNT.EXE'
            office_environment = {'version': str(office.Version), 'build': str(office.Build),
                                  'executable': str(executable), 'executable_sha256': sha(executable)}
        finally:
            if owns and office.Presentations.Count == 0: office.Quit()
            pythoncom.CoUninitialize()
    executable = Path(browser_path) if browser_path else None
    if executable is None:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as runtime: executable = Path(runtime.chromium.executable_path)
    environment = {'host': platform.node(), 'platform': platform.platform(), 'python': platform.python_version(),
                   'browser': {'version': glyphs['browser']['version'], 'executable': str(executable.resolve()), 'sha256': sha(executable)},
                   'office': office_environment,
                   'packages': {name: version(name) for name in ('fonttools', 'playwright', 'python-pptx', 'PyMuPDF', 'pywin32', 'Pillow')}}
    if any(sha(inside(root, name)) != digest for name, digest in resources.items()):
        raise ValueError('HTML resource changed during the evidence check')
    return {'environment': environment, 'resources': resources, 'embedded_payloads': payloads,
            'scope': 'Current project on this Windows PowerPoint host only; no user approval or other-platform claim.'}


def bind_followup_evidence(contract, pptx_path, *, project, review_path):
    """Augment an existing actual export review, then re-import its normal receipt."""
    from project_state import ProjectState
    root, path = Path(project).resolve(), Path(pptx_path).resolve()
    state = ProjectState(root)
    review_file = state.path(review_path)
    report = json.loads(review_file.read_text('utf8'))
    target = report['target']
    if state.path(state.state['nodes'][target]['path']) != path:
        raise ValueError('Review target is a different export')
    if state.layer_status(target, 'export')['state'] not in {'checked', 'checked_with_warnings'}:
        raise ValueError('Existing current per-page export review is required')
    inputs = _followup_inputs(contract, root, path, state, target)
    rechecked = _recheck_followup(contract, root, path, inputs)
    if _followup_inputs(contract, root, path, state, target) != inputs:
        raise ValueError('Inputs changed during the live evidence check')
    report['quality_floor'] = {'inputs': inputs, **rechecked}
    for page in report['pages']:
        refs = {item['path']: item for item in page['evidence']}
        for name, digest in {**inputs['files'], **rechecked['resources']}.items():
            refs[name] = {'path': name, 'sha256': digest}
        page['evidence'] = list(refs.values())
    review_file.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    state.review(target, 'export', review_path)
    return report['quality_floor']


def _accept_followup(contract, root, path):
    from project_state import ProjectState
    state = ProjectState(root)
    targets = [key for key, node in state.state['nodes'].items()
               if node['kind'] == 'artifact' and state.path(node['path'], must_exist=False) == path]
    if len(targets) != 1:
        raise ValueError('Export is not uniquely registered in this project')
    target = targets[0]
    if state.layer_status(target, 'export')['state'] not in {'checked', 'checked_with_warnings'}:
        raise ValueError('Current export review is missing or blocked')
    latest = {}
    for receipt in state.state['receipts']:
        if receipt['target'] == target and receipt['layer'] == 'export' and state.receipt_current(receipt):
            for number in receipt['pages']: latest[number] = receipt
    if set(latest) != set(state.state['page_order']):
        raise ValueError('Missing or stale per-page export review evidence')
    inputs = _followup_inputs(contract, root, path, state, target)
    proofs = [json.loads(state.path(r['evidence']['path']).read_text('utf8')).get('quality_floor') for r in latest.values()]
    if any(not isinstance(p, dict) or p.get('inputs') != inputs for p in proofs):
        raise ValueError('Missing, stale or different-project follow-up binding')
    for proof in proofs:
        environment = proof.get('environment', {})
        if any(environment.get(k) != v for k, v in {'host':platform.node(), 'platform':platform.platform(), 'python':platform.python_version()}.items()):
            raise ValueError('Actual execution environment changed')
    for receipt in latest.values():
        recorded = {ref['path']: ref['sha256'] for ref in receipt['files']}
        if any(recorded.get(name) != digest for name, digest in inputs['files'].items()):
            raise ValueError('Follow-up files are not bound by the ProjectState review receipt')
    checked = _recheck_followup(contract, root, path, inputs)
    if any(any(p.get(k) != v for k, v in checked.items()) for p in proofs):
        raise ValueError('Actual resources, source payloads or execution environment changed')
    if _followup_inputs(contract, root, path, state, target) != inputs:
        raise ValueError('Inputs changed while rechecking follow-up evidence')
    return checked


def verify_artifact(contract: dict, pptx_path: Path, *,project: Path|None=None) -> dict:
    """Fail known font defects; never assert Office native glyph fidelity from OOXML.

    Candidate means not VERIFIED. All results hash-bound to both contract and PPTX.
    """
    path=Path(pptx_path)
    blocking=[]; unresolved=[]; evidence={'runs_checked':0,'script_runs':0,'slides':0, 'script_typefaces':{}, 'embedded_typefaces':[]}
    def block(code,**details):blocking.append({'code':code,**details})
    def unknown(code,**details):unresolved.append({'code':code,**details})
    if not _valid_contract(contract):
        block('INVALID_OR_TAMPERED_CONTRACT')
        return {'status':'BLOCKED','blocking':blocking,'unverified':unresolved,'evidence':evidence}
    if contract['mode']!='NEW_DOCUMENT':
        block('UNSUPPORTED_MODE_NEEDS_ACCEPTED_SOURCE_POLICY')
    primary=contract['document']['language'].split('-')[0].lower()
    if primary not in contract['font_sources']:
        block('PRIMARY_FONT_POLICY_MISSING')
    if project is not None:
        root=Path(project).resolve()
        for lang, src in contract.get('font_sources',{}).items():
            try:
                font=inside(root,src['asset'])
                if not font.is_file() or sha(font)!=src['sha256']:
                    block('FONT_SOURCE_MISSING_OR_CHANGED',language=lang)
            except (OSError,ValueError,KeyError,TypeError):
                block('FONT_SOURCE_NOT_VERIFIABLE',language=lang)
    else:
        unknown('SOURCE_FILES_NOT_RECHECKED')
    if not path.is_file():
        block('PPTX_MISSING')
        return {'status':'BLOCKED','blocking':blocking,'unverified':unresolved,'evidence':evidence}
    try:
        pptx_hash=sha(path)
        with ZipFile(path) as z:
            names=set(z.namelist())
            if 'ppt/presentation.xml' not in names:
                block('PRESENTATION_XML_MISSING')
                raise ValueError('No presentation.xml')
            presentation=ET.fromstring(z.read('ppt/presentation.xml'))
            slides=presentation.find(f'{P}sldIdLst')
            intended_count=len(slides) if slides is not None else 0
            slide_names=sorted([n for n in names if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)], key=lambda n:int(re.search(r'(\d+)\.xml$',n).group(1)))
            evidence['slides']=len(slide_names)
            if intended_count != len(slide_names) or not slide_names:
                block('SLIDE_LIST_COUNT_MISMATCH',declared=intended_count,xml_files=len(slide_names))
            font_refs={}
            embedded=presentation.find(f'{P}embeddedFontLst')
            if embedded is not None:
                for entry in embedded.findall(f'{P}embeddedFont'):
                    el=entry.find(f'{P}font')
                    if el is None: continue
                    name=el.get('typeface')
                    if name:font_refs.setdefault(name,[])
                    for slot in ['regular','bold','italic','boldItalic']:
                        e=entry.find(f'{P}{slot}')
                        if e is not None:
                            rid=e.get(f'{R}id')
                            font_refs.setdefault(name,[]).append(rid)
            evidence['embedded_typefaces']=sorted(font_refs)
            rels=_rid_links(z)
            for face,rids in font_refs.items():
                if not rids: block('EMBEDDED_FONT_WITHOUT_FACE',font=face)
                for rid in rids:
                    rel=rels.get(rid)
                    if rel is None or not str(rel.get('Type','')).endswith('/font'):
                        block('BROKEN_EMBEDDED_FONT_LINK',font=face,id=rid)
                        continue
                    if rel.get('TargetMode')=='External':
                        block('EXTERNAL_EMBEDDED_FONT_REL',font=face);continue
                    target=rel.get('Target','').lstrip('/')
                    target=target if target.startswith('ppt/') else 'ppt/'+target
                    if target not in names:
                        block('FONT_PART_MISSING',font=face,target=target)
            # Every native run containing relevant script must have an explicit EA font.
            for index, name in enumerate(slide_names,1):
                slide=ET.fromstring(z.read(name))
                for run in slide.iter(f'{A}r'):
                    t=run.find(f'{A}t')
                    if t is None or not t.text:continue
                    content=t.text
                    evidence['runs_checked']+=1
                    prop=run.find(f'{A}rPr')
                    hint=prop.get('lang','') if prop is not None else ''
                    langs=_languages(content,hint,primary)
                    if not langs:continue
                    evidence['script_runs']+=1
                    lat=prop.find(f'{A}latin') if prop is not None else None
                    ea=prop.find(f'{A}ea') if prop is not None else None
                    latin_name=lat.get('typeface') if lat is not None else None
                    ea_name=ea.get('typeface') if ea is not None else None
                    for lang in sorted(langs):
                        src=contract['font_sources'].get(lang)
                        if not src:
                            block('LANGUAGE_FONT_POLICY_MISSING',page=index,language=lang);continue
                        required=src['family']
                        key=f'{lang}:{ea_name or "MISSING"}'
                        evidence['script_typefaces'][key]=evidence['script_typefaces'].get(key,0)+1
                        if not ea_name:
                            block('EA_FONT_MISSING',page=index,language=lang,latin=latin_name,text=content[:28])
                        elif not compatible_family(ea_name,required):
                            block('WRONG_CJK_FONT',page=index,language=lang,actual=ea_name,expected=required,text=content[:28])
                        if latin_name and not compatible_family(latin_name,required):
                            # Different Latin typeface is allowed in bilingual runs, if CJK slot is right.
                            # It is not evidence of native CJK family compliance.
                            pass
                        if ea_name and compatible_family(ea_name,required) and ea_name not in font_refs:
                            unknown('FONT_NOT_EMBEDDED',page=index,language=lang,font=ea_name)
            if evidence['script_runs']==0:
                block('NO_JAPANESE_OR_KOREAN_NATIVE_TEXT')
    except (BadZipFile,ET.ParseError,ValueError,KeyError) as exc:
        block('INVALID_PPTX_OR_OOXML',detail=str(exc))
        pptx_hash=sha(path)
    followup = None
    if project is not None and not blocking and not unresolved:
        try:
            followup = _accept_followup(contract, Path(project).resolve(), path.resolve())
            evidence['followup'] = followup
        except Exception as exc:
            # Optional native/browser dependencies and malformed evidence must fail closed.
            block('FOLLOWUP_EVIDENCE_REJECTED', detail=f'{type(exc).__name__}: {exc}')
    if followup is None:
        unknown('ACTUAL_POWERPOINT_FONT_RENDER_NOT_TESTED')
        unknown('HTML_PLATFORM_FONT_AND_TEXT_PARITY_NOT_TESTED')
        unknown('EMBEDDED_BINARY_ORIGIN_NOT_PROVEN')
    # Stable de-dup by issue semantics.
    unique=[];seen=set()
    for item in unresolved:
        key=json.dumps(item,sort_keys=True,ensure_ascii=False)
        if key not in seen:seen.add(key);unique.append(item)
    result={'schema_version':'demo-quality-audit/0.1','status':'BLOCKED' if blocking else 'REVIEW_CANDIDATE',
            'contract_sha256':contract['contract_sha256'],'pptx_sha256':pptx_hash,
            'blocking':blocking,'unverified':unique,'evidence':evidence,
            'claims':{'structural_check_executed':True,'native_powerpoint_verified':bool(followup),
                      'verification_scope': followup['scope'] if followup else None,
                      'other_platforms_verified':False,'user_approval':False,'ready_for_delivery':False}}
    return result


def cli():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    make=sub.add_parser('init-contract');make.add_argument('--project',required=True)
    make.add_argument('--brand-assets',required=True);make.add_argument('--tokens',required=True)
    make.add_argument('--language',default='ja-JP');make.add_argument('--profile',default='executive_approval')
    make.add_argument('--additional-language',action='append',default=[])
    make.add_argument('--out',required=True)
    verify=sub.add_parser('verify');verify.add_argument('--contract',required=True)
    verify.add_argument('--pptx',required=True);verify.add_argument('--project')
    verify.add_argument('--out')
    args=parser.parse_args()
    if args.command=='init-contract':
        contract=resolve_contract(Path(args.project),Path(args.brand_assets),Path(args.tokens),
                                  language=args.language,profile=args.profile,additional_languages=args.additional_language)
        write_contract(contract,Path(args.out))
        print(json.dumps({'status':'contract_created','path':args.out,'contract_sha256':contract['contract_sha256']},ensure_ascii=False))
    else:
        c=json.loads(Path(args.contract).read_text(encoding='utf-8'))
        result=verify_artifact(c,Path(args.pptx),project=Path(args.project) if args.project else None)
        if args.out:
            Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 2 if result['status']=='BLOCKED' else 1 # candidate is NOT success
    return 0

if __name__=='__main__':
    raise SystemExit(cli())
