"""Check semantic HTML↔approved-rule anchors without pretending to verify geometry."""
from __future__ import annotations

from collections import Counter,defaultdict
from html.parser import HTMLParser

from layout_plan import IDENTIFIER, _digest


VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}


class _AnchorCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]
        self.pages=[]
        self.elements=[]
        self.findings=[]

    def handle_starttag(self,tag,attrs):
        row=dict(attrs)
        owner=self.stack[-1][1] if self.stack else None
        if 'data-page-id' in row:
            owner=row['data-page-id']
            self.pages.append(owner)
        if 'data-grammar-element-id' in row or 'data-grammar-rule-ids' in row:
            self.elements.append({'page_id':owner,
                                  'element_id':row.get('data-grammar-element-id'),
                                  'rule_ids':(row.get('data-grammar-rule-ids') or '').split()})
        if tag not in VOID:self.stack.append((tag,owner))

    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID:self.handle_endtag(tag)

    def handle_endtag(self,tag):
        if not self.stack or self.stack[-1][0]!=tag:
            self.findings.append('Malformed HTML nesting at '+tag)
        else:
            self.stack.pop()


def inspect_html_grammar(html_text: str, plan: dict) -> dict:
    """Only semantic trace and pack-scope validation; no spatial approval implied."""
    findings=[]
    if not isinstance(plan,dict) or plan.get('schema_version')!='layout-plan/1.0':
        return {'status':'FAIL','inspected_pages':[],'findings':['Invalid layout plan schema']}
    expected_hash=plan.get('plan_sha256')
    if _digest({key:value for key,value in plan.items() if key!='plan_sha256'})!=expected_hash:
        findings.append('Layout plan hash does not match current content')
    if plan.get('review_status')!='pending_render_review':
        findings.append('Unverified plan claims unsupported review status')
    parser=_AnchorCollector()
    parser.feed(html_text)
    parser.close()
    findings+=parser.findings
    expected_pages={page['page_id']:page for page in plan.get('pages',[])}
    seen=Counter(parser.pages)
    for page_id in expected_pages:
        if seen[page_id]!=1:
            findings.append(f'Expected one data-page-id={page_id}; found {seen[page_id]}')
    for page_id in seen:
        if page_id not in expected_pages:
            findings.append('Unauthorized HTML page ID '+str(page_id))

    located=defaultdict(dict)
    for element in parser.elements:
        page_id,ident=element['page_id'],element['element_id']
        if page_id not in expected_pages or not isinstance(ident,str) or not IDENTIFIER.fullmatch(ident):
            findings.append('Invalid grammar anchor or owner page')
            continue
        expected_ids={entry['element_id'] for entry in expected_pages[page_id]['elements']}
        if ident not in expected_ids:
            findings.append(f'Unknown element anchor {ident} on {page_id}')
            continue
        if ident in located[page_id]:
            findings.append(f'Duplicate element anchor {ident} on {page_id}')
        if not element['rule_ids']:
            findings.append(f'Element {ident} missing rule trace')
        located[page_id][ident]=set(element['rule_ids'])
    any_approved=False
    for page_id,page in expected_pages.items():
        if page['mode']=='needs_revision':
            findings.append(f'Unresolved layout plan conflicts on {page_id}')
            continue
        rules=page['rules'] if page['mode']=='approved_grammar' else []
        if rules:any_approved=True
        valid_ids={rule['rule_id'] for rule in rules}
        for ident,ids in located[page_id].items():
            for rule_id in ids:
                if rule_id not in valid_ids:
                    findings.append(f'Unauthorized rule ID {rule_id} on {page_id}/{ident}')
        by_role=defaultdict(list)
        for entry in page['elements']:
            by_role[entry['role']].append(entry['element_id'])
        for rule in rules:
            required=set()
            for relation in rule['relationships']:
                required.update([relation['leader_element_id'],relation['follower_element_id']])
            if not rule['relationships']:
                for role in rule['element_roles']:
                    ids=by_role.get(role,[])
                    anchor=page.get('role_anchors',{}).get(role) or (ids[0] if len(ids)==1 else None)
                    if anchor is None:
                        findings.append(f'Ambiguous unanchored role {role} on {page_id}')
                        continue
                    required.add(anchor)
            for ident in required:
                if rule['rule_id'] not in located[page_id].get(ident,set()):
                    findings.append(f'Missing rule {rule["rule_id"]} trace on {page_id}/{ident}')
    return {'status':'FAIL' if findings else 'PASS' if any_approved else 'NOT_APPLICABLE',
            'inspected_pages':[p for p in expected_pages if seen[p]==1],
            'findings':findings,
            'note':'Semantic anchors only; browser geometry and visual judgment remain unverified.'}
