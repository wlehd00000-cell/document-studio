"""Refresh plain-text bindings without regenerating report layout. Stdlib only."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import re

BINDING = re.compile(r'(<span\b[^>]*\bdata-report-key="([\w.-]+)"[^>]*>)([^<]*)(</span>)')
PAGE = re.compile(r'<section\b[^>]*\bclass="[^"]*\bpage\b[^"]*"[^>]*>.*?</section>', re.S)

def refresh(template, data, output, previous=None):
    template, data, output = map(Path, (template, data, output))
    if output.resolve() in {template.resolve(), data.resolve()} or (previous and output.resolve()==Path(previous).resolve()):
        raise ValueError('Output must not overwrite template, input data or previous report')
    source = template.read_text(encoding='utf-8')
    values = json.loads(data.read_text(encoding='utf-8'))
    if not isinstance(values, dict):
        raise ValueError('JSON must be an object mapping keys to display strings')
    matches = list(BINDING.finditer(source))
    if not matches or source.count('data-report-key=') != len(matches):
        raise ValueError('Bindings must be plain-text spans with double-quoted keys; no nested markup')
    keys = {m[2] for m in matches}
    missing = sorted(keys-values.keys())
    if missing:
        raise ValueError(f'Missing bindings: {missing}')
    if any(not isinstance(values[k], str) for k in keys):
        raise ValueError('Bound values must be formatted strings; use explicit missing-value labels')
    result = BINDING.sub(lambda m:m[1]+escape(values[m[2]], quote=True)+m[4], source)
    current_pages = PAGE.findall(result)
    old = Path(previous).read_text(encoding='utf-8') if previous else ''
    old_pages = PAGE.findall(old)
    same_shell = bool(old) and PAGE.sub('', old)==PAGE.sub('',result) and len(old_pages)==len(current_pages)
    changed = [i+1 for i,page in enumerate(current_pages) if i>=len(old_pages) or old_pages[i]!=page]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding='utf-8')
    return {'output':str(output), 'pages':len(current_pages), 'changed_pages':changed,
            'global_or_topology_change':not same_shell, 'unused_keys':sorted(values.keys()-keys),
            'sha256':hashlib.sha256(result.encode()).hexdigest(),
            'note':'Review shortlist only; verify external assets/styles and converter cache before incremental conversion.'}

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('template'); p.add_argument('data'); p.add_argument('output')
    p.add_argument('--previous')
    print(json.dumps(refresh(**vars(p.parse_args())), ensure_ascii=True, indent=2))
