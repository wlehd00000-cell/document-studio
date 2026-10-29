"""Measure actual HTML text lines; render evidence, never infer editorial approval."""
import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname
sys.path.insert(0,str(Path(__file__).resolve().parent))
from document_runtime import atomic_json


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_audit(path, payload):
    """Replace a complete JSON file atomically; readers never see partial JSON."""
    atomic_json(path,payload)


def check_saved(report_path):
    report = json.loads(Path(report_path).read_text(encoding='utf-8'))
    evidence = report.get('source_evidence', {})
    files = evidence.get('local_files', {})
    if (report.get('schema_version') != 1 or report.get('status') != 'measured'
            or not files or evidence.get('input') not in files
            or not {'render_text_flow.py', 'text_flow_measure.js'} <= set(report.get('implementation_hashes', {}))):
        raise ValueError('Audit is incomplete or unsupported; run a fresh measurement')
    changed = []
    for name, expected in files.items():
        path = Path(name)
        if not path.is_file() or file_hash(path) != expected:
            changed.append(name)
    for name, expected in report.get('implementation_hashes', {}).items():
        current = Path(__file__).with_name(name)
        if not current.is_file() or file_hash(current) != expected:
            changed.append('measurement-implementation:' + name)
    audit_root = Path(report_path).resolve().parent
    for screenshot in report.get('screenshots', []):
        image = (audit_root / screenshot['file']).resolve()
        if not image.is_relative_to(audit_root):
            raise ValueError('Screenshot path escapes the audit directory')
        if not image.is_file() or ('sha256' in screenshot and file_hash(image) != screenshot['sha256']):
            changed.append('screenshot:' + screenshot['file'])
    return {'status': 'stale' if changed else 'local_files_unchanged',
            'changed': changed, 'revision': report.get('revision'),
            'scope': 'Saved local files only; verify canvas, runtime/fonts and external assets separately.',
            'editorial_approval': False}


def render(args):
    source = Path(args.input).resolve(strict=True)
    if source.suffix.lower() not in {'.html', '.htm'}:
        raise ValueError('Input must be a local HTML file')
    output = Path(args.output_dir).resolve()
    if output == source.parent or output in source.parents:
        raise ValueError('Choose a separate QA output directory')
    terms = list(args.protected_term)
    if args.terms_json:
        supplied = json.loads(Path(args.terms_json).read_text(encoding='utf-8'))
        if not isinstance(supplied, list) or not all(isinstance(s, str) and s for s in supplied):
            raise ValueError('terms-json must be an array of nonempty strings')
        terms.extend(supplied)
    selected = []
    if args.pages:
        selected = sorted(set(int(n.strip()) for n in args.pages.split(',')))
        if not selected or min(selected) < 1:
            raise ValueError('pages must contain positive page numbers')
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError('Playwright is unavailable in this runtime. Select an existing compatible runtime or permitted renderer; no dependency was installed.') from error
    measure = Path(__file__).with_name('text_flow_measure.js').read_text(encoding='utf-8')
    options = {'pageSelector': args.page_selector, 'blockSelector': args.block_selector,
               'protectedTerms': sorted(set(terms)), 'selectedPages': selected,
               'contentSelector': args.content_selector, 'boundarySelector': args.boundary_selector}
    files = {str(source): file_hash(source)}
    external = set()
    failed = []
    output_started = False
    settle = '''async timeout => {
        let timer;
        try {
            await Promise.race([
                (async () => {
                    await document.fonts.ready;
                    await Promise.all([...document.images].map(i => i.decode().catch(() => null)));
                    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
                })(),
                new Promise((_, reject) => { timer=setTimeout(() => reject(new Error('Asset readiness timed out')), timeout); })
            ]);
        } finally { clearTimeout(timer); }
    }'''

    def on_request(request):
        parsed = urlparse(request.url)
        if parsed.scheme == 'file':
            # url2pathname handles Windows drives as well as POSIX paths.
            name = url2pathname(parsed.path)
            if parsed.netloc:
                name = '//' + parsed.netloc + name
            path = Path(name)
            key = str(path.resolve())
            if key not in files and path.is_file():
                files[key] = file_hash(path)
        elif parsed.scheme in {'http', 'https'}:
            external.add(request.url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=args.browser_path)
        try:
            page = browser.new_page(viewport={'width': args.viewport_width, 'height': args.viewport_height},
                                    device_scale_factor=args.scale)
            page.set_default_timeout(args.timeout_ms)
            page.on('request', on_request)
            page.on('requestfailed', lambda r: failed.append({'url': r.url, 'error': r.failure}))
            page.on('response', lambda r: failed.append({'url': r.url, 'status': r.status}) if r.status >= 400 else None)
            page.goto(source.as_uri(), wait_until='load', timeout=args.timeout_ms)
            page.evaluate(settle, args.timeout_ms)
            screen = page.evaluate(measure, options)
            if selected and max(selected) > screen['total_pages']:
                raise ValueError('Requested page number exceeds document page count')
            if not any(sheet['status'] == 'measured' for sheet in screen['pages']):
                raise ValueError('No visible pages selected; measurement did not run')
            output.mkdir(parents=True, exist_ok=True)
            save_audit(output / 'text-flow-audit.json', {'schema_version': 1, 'status': 'measuring',
                        'revision': args.revision, 'input': str(source)})
            output_started = True
            screenshots = []
            for sheet in screen['pages']:
                if sheet['status'] != 'measured':
                    continue
                name = f"page-{sheet['page']}.png"
                page.locator(screen['page_selector']).nth(sheet['locator_index']).screenshot(path=str(output / name))
                screenshots.append({'page': sheet['page'], 'file': name, 'sha256': file_hash(output / name)})
            page.emulate_media(media='print')
            page.evaluate(settle, args.timeout_ms)
            printed = page.evaluate(measure, options)
            browser_version = browser.version
        except Exception as error:
            if output_started:
                save_audit(output / 'text-flow-audit.json', {'schema_version': 1, 'status': 'failed',
                            'revision': args.revision, 'input': str(source), 'error': str(error)})
            raise
        finally:
            browser.close()
    fingerprint = hashlib.sha256(json.dumps(files, sort_keys=True).encode('utf-8')).hexdigest()
    layout_count = sum(len(pg['layout_findings']) for mode in (screen, printed) for pg in mode['pages'])
    warning_count = sum(len(b['warnings']) for mode in (screen, printed) for pg in mode['pages'] for b in pg['blocks'])
    font_errors = [f for mode in (screen, printed) for f in mode['fonts'] if f['status'] == 'error']
    incomplete = any(pg['status'] == 'hidden' or not pg['blocks'] for mode in (screen, printed) for pg in mode['pages'])
    report = {'schema_version': 1, 'status': 'measured', 'revision': args.revision,
              'implementation_hashes': {name: file_hash(Path(__file__).with_name(name))
                                        for name in ('render_text_flow.py', 'text_flow_measure.js')},
              'measured_at': datetime.now(timezone.utc).isoformat(),
              'source_evidence': {'input': str(source), 'local_files': files, 'fingerprint': fingerprint,
                                  'external_resources_unhashed': sorted(external)},
              'renderer': {'engine': 'Chromium', 'version': browser_version,
                           'viewport': [args.viewport_width, args.viewport_height], 'scale': args.scale},
              'options': options, 'screen': screen, 'print': printed, 'screenshots': screenshots,
              'resource_failures': failed, 'font_errors': font_errors,
              'summary': {'total_pages': screen['total_pages'],
                          'measured_pages': [p['page'] for p in screen['pages'] if p['status'] == 'measured'],
                          'hidden_pages': [p['page'] for p in screen['pages'] if p['status'] == 'hidden'],
                          'layout_findings': layout_count, 'editorial_candidates': warning_count,
                          'coverage_status': 'incomplete' if incomplete else 'selected_pages_measured',
                          'structural_status': 'findings' if layout_count or failed or screen['missing_images'] or printed['missing_images'] or font_errors else ('incomplete' if incomplete else 'no_detected_findings')},
              'visual_review': 'pending', 'editorial_review': 'pending', 'user_acceptance': 'not_assessed'}
    audit = output / 'text-flow-audit.json'
    save_audit(audit, report)
    return {'status': 'measured', 'audit': str(audit), **report['summary'],
            'visual_review': 'pending', 'editorial_review': 'pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?')
    parser.add_argument('--output-dir')
    parser.add_argument('--revision')
    parser.add_argument('--check-against')
    parser.add_argument('--page-selector')
    parser.add_argument('--block-selector', default='h1,h2,h3,p,td,th,li,figcaption,.source,.sources,[data-text-flow]')
    parser.add_argument('--content-selector')
    parser.add_argument('--boundary-selector')
    parser.add_argument('--pages')
    parser.add_argument('--protected-term', action='append', default=[])
    parser.add_argument('--terms-json')
    parser.add_argument('--viewport-width', type=int, default=1280)
    parser.add_argument('--viewport-height', type=int, default=1400)
    parser.add_argument('--scale', type=float, default=1)
    parser.add_argument('--browser-path')
    parser.add_argument('--timeout-ms', type=int, default=30000)
    args = parser.parse_args()
    if args.check_against:
        result = check_saved(args.check_against)
        print(json.dumps(result, ensure_ascii=False))
        return 3 if result['status'] == 'stale' else 0
    if not args.input or not args.output_dir:
        parser.error('input and --output-dir are required for rendering')
    if min(args.viewport_width, args.viewport_height, args.timeout_ms) <= 0 or not math.isfinite(args.scale) or args.scale <= 0:
        parser.error('viewport, timeout and scale must be positive')
    result = render(args)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
