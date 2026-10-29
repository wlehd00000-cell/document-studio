"""Scoped structural/editorial HTML checks; no renderer, style bans or network.

Exit 0: automated checks passed (warnings may need review).
Exit 1: document findings. Exit 2: invocation/input failure.
"""
from __future__ import annotations

import argparse
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
SKIP = {'script', 'style', 'template', 'noscript'}
PLACEHOLDER = re.compile(r'\{\{[^{}]+\}\}|\bText\s*\d+\b|(?:ラベル|タイトル|텍스트|라벨)\s*\d+|\bYYYY\b|[◯○]{2,}')
COUNT = re.compile(r'([0-9０-９]+)\s*(?:단계|フェーズ|段階|ステップ|단계의)')
DEFAULT_TERMS = [['メモリー', 'メモリ'], ['サーバー', 'サーバ'], ['フォルダー', 'フォルダ']]
SENTENCE_ENDINGS = {
    'ko': re.compile(r'(?:니다|입니까|하십시오|하세요|합시다|필요하다|기대된다|한다|된다|있다|없다)[.!?。？！]*$'),
    'ja': re.compile(r'(?:です|ます|でした|ました|である|となる|になる|できる|する)[.!?。？！]*$'),
}


def inherited_attr(node, name):
    while node is not None:
        if name in node.attrs:
            return node.attrs[name]
        node = node.parent
    return ''


@dataclass(eq=False)
class Node:
    tag: str
    attrs: dict[str, str]
    parent: Node | None = None
    parts: list = field(default_factory=list)
    line: int = 0

    @property
    def classes(self):
        return set(self.attrs.get('class', '').split())

    def hidden(self):
        return (self.tag in SKIP or 'hidden' in self.attrs or self.attrs.get('aria-hidden') == 'true'
                or bool(re.search(r'(?:display\s*:\s*none|visibility\s*:\s*hidden)', self.attrs.get('style', ''), re.I)))

    def text(self):
        if self.hidden():
            return ''
        return re.sub(r'\s+', ' ', ' '.join(p.text() if isinstance(p, Node) else p for p in self.parts)).strip()

    def walk(self):
        if self.hidden():
            return
        yield self
        for p in self.parts:
            if isinstance(p, Node):
                yield from p.walk()


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('document', {})
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict((k, v or '') for k, v in attrs), self.stack[-1], line=self.getpos()[0])
        self.stack[-1].parts.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].parts.append(data)


def page_nodes(root):
    nodes = list(root.walk())
    explicit = [n for n in nodes if 'data-pptx-slide' in n.attrs]
    candidates = explicit or [n for n in nodes if n.classes & {'demo-page', 'page', 'slide'} or (n.tag == 'section' and 's' in n.classes)]
    candidate_set = set(candidates)
    result = []
    for n in candidates:
        ancestor = n.parent
        while ancestor is not None and ancestor not in candidate_set:
            ancestor = ancestor.parent
        if ancestor is None:
            result.append(n)
    return result


def title_node(nodes):
    explicit = next((n for n in nodes if 'data-page-title' in n.attrs), None)
    styled = next((n for n in nodes if n.classes & {'page-title', 'demo-page-title', 'title', 'ttl', 'msg'}), None)
    return explicit or styled or next((n for n in nodes if n.tag in {'h1', 'h2'}), None)


def inspect_html(html, *, template=False, term_groups=None):
    parser = DocumentParser()
    parser.feed(html)
    pages = page_nodes(parser.root)
    findings, titles, body_sequence = [], [], []
    quantities = defaultdict(list)

    def add(severity, code, page, message, node=None):
        findings.append({'severity': severity, 'code': code, 'page': page,
                         'line': node.line if node else None, 'message': message})

    if not pages:
        add('FAIL', 'NO_PAGES', None, 'No recognized document pages; no page checks were performed.')

    for i, page in enumerate(pages, 1):
        nodes = list(page.walk())
        title = title_node(nodes)
        text = page.text()
        title_text = title.text() if title else ''
        titles.append({'page': i, 'title': title_text})
        allowed_blank = bool(page.classes & {'cover', 'outro', 'chap', 'section-divider'}) or page.attrs.get('data-fixed-page') in {'cover', 'outro'}
        if not title_text and not allowed_blank:
            add('FAIL', 'MISSING_TITLE', i, 'A body page has no recognized nonempty title.', page)
        if not template:
            hits = sorted(set(PLACEHOLDER.findall(text)))
            if hits:
                add('FAIL', 'PLACEHOLDER', i, 'Unreplaced content: ' + ', '.join(hits[:8]), page)

            role = page.attrs.get('data-page-role') or page.attrs.get('data-fixed-page', '')
            excluded = role in {'cover', 'outro', 'chapter_opener', 'appendix'} or bool(page.classes & {'cover', 'outro', 'chap', 'section-divider', 'appendix'})
            if not excluded:
                form = page.attrs.get('data-dominant-form', '')
                has_table = any(n.tag == 'table' or n.attrs.get('role') == 'table' for n in nodes)
                body_sequence.append({'page': i, 'node': page, 'form': form,
                                      'move': page.attrs.get('data-narrative-move', ''),
                                      'table_candidate': form == 'table' or (not form and has_table)})
            language = inherited_attr(page, 'lang').split('-')[0]
            endings = SENTENCE_ENDINGS.get(language)
            for heading in nodes:
                if heading is not title and heading.tag not in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'} and not heading.classes & {'subhead', 'section-title'}:
                    continue
                style = inherited_attr(heading, 'data-heading-style')
                genre = inherited_attr(heading, 'data-document-genre')
                nominal = style == 'nominal' or (not style and genre in {'report', 'submission', 'plan', 'guide', 'manual', 'proposal'})
                if nominal and endings and endings.search(heading.text()):
                    add('WARN', 'SENTENCE_HEADING', i,
                        'Report heading may use a sentence ending; rewrite as a concrete noun phrase while preserving proposed/expected/completed status: ' + heading.text(), heading)

        enumerations = [n for n in nodes if 'data-enumeration' in n.attrs]
        scopes = enumerations or [page]
        for scope in scopes:
            labels = [n.attrs['data-step-index'] for n in scope.walk() if 'data-step-index' in n.attrs]
            if 'data-enumeration' in scope.attrs:
                expected_raw = scope.attrs.get('data-count', '')
            else:
                match = COUNT.search(title_text)
                expected_raw = match.group(1) if match else ''
            if not expected_raw:
                continue
            try:
                expected = int(expected_raw)
                indices = [int(label) for label in labels]
                if expected < 1:
                    raise ValueError
            except ValueError:
                add('FAIL', 'BAD_ENUMERATION', i, 'Enumeration count/index is not a positive integer.', scope)
                continue
            if enumerations and not indices:
                add('FAIL', 'EMPTY_ENUMERATION', i, 'An annotated enumeration has no step indices.', scope)
            elif indices and (len(indices) != expected or sorted(indices) != list(range(1, expected + 1))):
                add('FAIL', 'COUNT_MISMATCH', i, f'Expected steps 1..{expected}; found {indices}.', scope)

        for node in nodes:
            attrs = node.attrs
            if 'data-quantity' not in attrs:
                continue
            required = ('data-value', 'data-unit', 'data-period', 'data-scope', 'data-basis')
            if not attrs['data-quantity'].strip() or any(not attrs.get(k, '').strip() for k in required):
                add('WARN', 'INCOMPLETE_QUANTITY', i, 'Repeated-quantity check skipped: value/unit/period/scope/basis is incomplete.', node)
                continue
            try:
                value = Decimal(attrs['data-value'].replace(',', '').strip())
                if not value.is_finite():
                    raise InvalidOperation
            except InvalidOperation:
                add('FAIL', 'INVALID_QUANTITY', i, 'Annotated quantity has a non-finite or non-numeric value.', node)
                continue
            key = tuple(attrs.get(k, '') for k in ('data-quantity', 'data-period', 'data-scope', 'data-basis'))
            quantities[key].append((i, value, attrs['data-unit'], node))

    for key, values in quantities.items():
        if len({(value, unit) for _, value, unit, _ in values}) > 1:
            add('FAIL', 'QUANTITY_MISMATCH', values[-1][0],
                f'Repeated quantity {key[0]} ({key[1:]}) disagrees: ' + '; '.join(f'p{i}={v} {u}' for i, v, u, _ in values), values[-1][-1])

    full_text = '\n'.join(p.text() for p in pages)
    html_node = next((n for n in parser.root.walk() if n.tag == 'html'), None)
    lang = html_node.attrs.get('lang', '') if html_node else ''
    groups = term_groups if term_groups is not None else (DEFAULT_TERMS if lang.startswith('ja') else [])
    for group in groups:
        # Longest spelling first, so a shorter variant is not counted inside it.
        ordered = sorted(set(group), key=len, reverse=True)
        if len(ordered) < 2:
            continue
        pattern = re.compile('|'.join(re.escape(term) for term in ordered))
        hits = set(pattern.findall(full_text))
        if len(hits) > 1:
            add('WARN', 'TERM_VARIANTS', None, 'Potential spelling variation (context review needed): ' + ', '.join(sorted(hits)))

    by_title = defaultdict(list)
    for title in titles:
        if title['title']:
            by_title[title['title']].append(title['page'])
    for title, ids in by_title.items():
        if len(ids) > 1:
            add('WARN', 'REPEATED_TITLE', None, f'Pages {ids} share a title; check for repetition or intentional continuation: {title}')

    if len(body_sequence) >= 3:
        table_pages = [row['page'] for row in body_sequence if row['table_candidate']]
        if len(table_pages) * 2 >= len(body_sequence):
            add('WARN', 'TABLE_HEAVY_CANDIDATE', None,
                f'Body pages {table_pages} use a declared table form or contain an unclassified table. Review images/diagrams/charts/timelines/prose as alternatives; precise comparisons may justify tables. DOM presence does not measure visual dominance.')
        for key, code in [('form', 'REPEATED_BODY_FORM'), ('move', 'REPEATED_NARRATIVE_MOVE')]:
            run = []
            for row in body_sequence:
                if run and (not row[key] or row[key] != run[-1][key] or row['page'] != run[-1]['page'] + 1):
                    run = []
                if row[key]:
                    run.append(row)
                if len(run) == 3:
                    add('WARN', code, row['page'],
                        f'Body pages {[r["page"] for r in run]} repeat {key}={row[key]}. Reconsider the explanation or record a specific comparison/template reason for repetition.', row['node'])

    failures = sum(f['severity'] == 'FAIL' for f in findings)
    return {'status': 'fail' if failures else 'automated_checks_passed', 'page_count': len(pages),
            'titles': titles, 'failures': failures, 'warnings': len(findings) - failures,
            'findings': findings,
            'body_sequence': [{k: v for k, v in row.items() if k != 'node'} for row in body_sequence],
            'coverage': 'HTML structure/visible source text, explicit form/movement and heading annotations, and table-presence candidates. External CSS visibility, visual dominance, disguised cards, actual narrative quality, logical truth, numeric sums, actual line breaks and final PPTX are not verified.'}


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('html', type=Path)
    cli.add_argument('--json', action='store_true')
    cli.add_argument('--template', action='store_true')
    cli.add_argument('--terms', type=Path)
    args = cli.parse_args(argv)
    try:
        terms = None
        if args.terms:
            terms = json.loads(args.terms.read_text(encoding='utf-8-sig'))['groups']
            if not isinstance(terms, list) or not all(isinstance(g, list) and all(isinstance(t, str) and t for t in g) for g in terms):
                raise ValueError('terms.groups must be an array of nonempty-string arrays')
        source_bytes = args.html.read_bytes()
        result = inspect_html(source_bytes.decode('utf-8-sig'), template=args.template, term_groups=terms)
        result['input'] = {'path': str(args.html.resolve()), 'sha256': hashlib.sha256(source_bytes).hexdigest()}
        result['implementation_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        if args.terms:
            result['terms_sha256'] = hashlib.sha256(args.terms.read_bytes()).hexdigest()
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        result = {'status': 'unverified', 'page_count': 0, 'error': str(exc)}
        print(json.dumps(result, ensure_ascii=False))
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for title in result['titles']:
            print(f"p{title['page']}: {title['title']}")
        for f in result['findings']:
            print(f"{f['severity']} {f['code']} p{f['page']}: {f['message']}")
        print(f"{result['page_count']} pages; {result['failures']} FAIL / {result['warnings']} WARN")
        print(result['coverage'])
    return 1 if result['failures'] else 0


if __name__ == '__main__':
    sys.exit(main())
