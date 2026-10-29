"""Bind explicit human decisions to an evidence digest and approved rule snapshot."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from layout_grammar import compute_evidence_digest,validate_grammar


def rule_digest(rule: dict) -> str:
    return hashlib.sha256(json.dumps(rule,sort_keys=True,ensure_ascii=False,
                       separators=(',',':')).encode('utf8')).hexdigest()


def record_visual_review(*,pack_dir: Path,grammar_file: Path,decision_file: Path,
                         reviewer: str) -> dict:
    pack_dir=Path(pack_dir).absolute()
    grammar_file=Path(grammar_file).absolute()
    decision_file=Path(decision_file).absolute()
    if not isinstance(reviewer,str) or not reviewer.strip():
        raise ValueError('Named human reviewer required')
    if grammar_file!=pack_dir/'design/layout-grammar.json' or any(p.is_symlink() for p in
            (pack_dir,grammar_file,decision_file,pack_dir/'design/visual-evidence.json')):
        raise ValueError('Unsafe visual review paths')
    meta=json.loads((pack_dir/'pack.json').read_text(encoding='utf8'))
    if meta['status']!='draft' or (pack_dir/'design/visual-review.json').exists():
        raise ValueError('Only a new draft pack may receive a one-time visual review')
    evidence=json.loads((pack_dir/'design/visual-evidence.json').read_text(encoding='utf8'))
    grammar=validate_grammar(json.loads(grammar_file.read_text(encoding='utf8')),evidence)
    decisions=json.loads(decision_file.read_text(encoding='utf8'))
    if decisions.get('schema_version')!='visual-review-decisions/1.0' or not isinstance(decisions.get('decisions'),list):
        raise ValueError('Invalid human review decision file')
    by_id={d['rule_id']:d for d in decisions['decisions'] if isinstance(d,dict) and d.get('rule_id')}
    if len(by_id)!=len(decisions['decisions']) or set(by_id)!={r['rule_id'] for r in grammar['rules']}:
        raise ValueError('Human decisions must cover every proposed rule exactly once')
    accepted=[]
    records=[]
    for rule in grammar['rules']:
        decision=by_id[rule['rule_id']]
        if decision.get('action') not in {'accept','reject','revise'} or not isinstance(decision.get('note'),str) or not decision['note'].strip():
            raise ValueError('Each decision needs an action and a reason')
        expected=compute_evidence_digest(rule['evidence_ids'],evidence)
        if decision.get('evidence_digest')!=expected:
            raise ValueError('Evidence digest mismatch: reviewer must reconsider changed sources')
        if rule['status']!='suggested':
            raise ValueError('Unreviewed grammar must contain suggestions only')
        if decision['action']=='revise':
            revision=decision.get('revised_rule')
            if not isinstance(revision,dict) or revision.get('rule_id')!=rule['rule_id'] or not decision['note'].strip():
                raise ValueError('Revision needs a full rule and written rationale')
            revision=validate_grammar({'schema_version':'layout-grammar/1.0','rules':[revision]},evidence)['rules'][0]
            if revision['evidence_ids']!=rule['evidence_ids'] or revision['evidence_refs']!=rule['evidence_refs']:
                raise ValueError('Revision cannot silently replace reviewed evidence')
            rule.clear()
            rule.update(revision)
        rule['status']='rejected' if decision['action']=='reject' else 'accepted'
        if rule['status']=='accepted':
            accepted.append(rule['rule_id'])
        records.append({'rule_id':rule['rule_id'],'action':decision['action'],
                        'note':decision['note'],'evidence_digest':expected,
                        'rule_digest':rule_digest(rule)})
    record={'schema_version':'visual-review/1.0','reviewer':reviewer.strip(),
            'reviewed_at':datetime.now(timezone.utc).isoformat(),
            'preview_ids':decisions.get('preview_ids',[]),'decisions':records,
            'status':'reviewed'}
    grammar_file.write_text(json.dumps(grammar,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (pack_dir/'design/visual-review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return {'accepted':accepted,'rejected':[r['rule_id'] for r in grammar['rules'] if r['status']=='rejected'],
            'reviewer':reviewer.strip()}


def invalidate_affected_rules(previous_pack, new_source_hashes: dict[str,str]) -> dict:
    """Return a proposed new grammar snapshot; never edit an approved pack in place."""
    rules=deepcopy(list(previous_pack.layout_grammar))
    changed=set(new_source_hashes)
    for rule in rules:
        if any(ref['source_id'] in changed for ref in rule['evidence_refs']):
            rule['status']='stale'
    return {'schema_version':'layout-grammar/1.0','rules':rules}
