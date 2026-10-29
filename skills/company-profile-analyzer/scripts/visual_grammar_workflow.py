"""CLI stages for private evidence → visual observations → reviewable Company Pack.

Models/humans inspect rendered pages and supply observation JSON. This CLI only
validates and packages that evidence; it never invents visual observations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from visual_evidence import prepare_visual_workspace
from layout_grammar import validate_observations
from grammar_synthesis import propose_grammar
from visual_review_board import build_review_board,default_fictional_examples
from record_visual_review import record_visual_review

REPORT_DIR=Path(__file__).resolve().parents[2]/'report-html-pptx/scripts'
sys.path.insert(0,str(REPORT_DIR))
from company_pack import load_company_pack  # noqa: E402
from select_layout_grammar import select_layout_grammar  # noqa: E402


def _read(path: Path) -> dict:
    data=json.loads(Path(path).read_text(encoding='utf8'))
    if not isinstance(data,dict):
        raise ValueError('Expected a JSON object')
    return data


def _write_new(path: Path, data: dict) -> None:
    path=Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f'Refuse to overwrite {path.name}')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare',help='Render source pages privately')
    prep.add_argument('--source',type=Path,required=True)
    prep.add_argument('--extracted',type=Path,required=True)
    prep.add_argument('--source-id',required=True)
    prep.add_argument('--document-family',required=True)
    prep.add_argument('--private-workspace',type=Path,required=True)
    propose=sub.add_parser('propose',help='Validate observed roles and propose flexible grammar')
    propose.add_argument('--evidence',type=Path,required=True)
    propose.add_argument('--observations',type=Path,required=True)
    propose.add_argument('--grammar-output',type=Path,required=True)
    propose.add_argument('--redacted-evidence-output',type=Path,required=True)
    board=sub.add_parser('board',help='Create private evidence + fictional style review HTML')
    board.add_argument('--evidence',type=Path,required=True)
    board.add_argument('--grammar',type=Path,required=True)
    board.add_argument('--private-workspace',type=Path,required=True)
    board.add_argument('--output',type=Path,required=True)
    record=sub.add_parser('record',help='Record explicit human rule-by-rule decisions')
    record.add_argument('--pack',type=Path,required=True)
    record.add_argument('--decisions',type=Path,required=True)
    record.add_argument('--reviewer',required=True)
    select=sub.add_parser('select',help='Rank reviewed grammar or neutral fallback')
    select.add_argument('--pack',type=Path,required=True)
    select.add_argument('--document-family',required=True)
    select.add_argument('--page-family',required=True)
    select.add_argument('--content-role',action='append',required=True)
    select.add_argument('--density',default='medium')
    select.add_argument('--use',default='reading')
    args=parser.parse_args()
    if args.command=='prepare':
        target=prepare_visual_workspace(args.source,_read(args.extracted),
                  source_id=args.source_id,document_family=args.document_family,
                  workspace=args.private_workspace)
        result={'workspace_index':str(target),'visual_review':'pending'}
    elif args.command=='propose':
        evidence=_read(args.evidence)
        if 'evidence' in evidence:
            evidence=evidence['evidence']
        normalized=validate_observations(_read(args.observations),evidence,{evidence['source_id']})
        combined={**evidence,'observations':normalized['observations']}
        grammar=propose_grammar(normalized['observations'],[],document_family=evidence['document_family'])
        _write_new(args.redacted_evidence_output,combined)
        _write_new(args.grammar_output,grammar)
        result={'proposed_rules':len(grammar['rules']),'review_status':'pending',
                'grammar':str(args.grammar_output),'redacted_evidence':str(args.redacted_evidence_output)}
    elif args.command=='board':
        target=build_review_board(_read(args.evidence),_read(args.grammar),
                    private_preview_root=args.private_workspace,output=args.output,
                    fictional_examples=default_fictional_examples())
        result={'private_review_board':str(target),'human_review':'required'}
    elif args.command=='record':
        result=record_visual_review(pack_dir=args.pack,
            grammar_file=args.pack/'design/layout-grammar.json',
            decision_file=args.decisions,reviewer=args.reviewer)
    else:
        result=select_layout_grammar(load_company_pack(args.pack),
                    document_family=args.document_family,page_family=args.page_family,
                    content_roles=args.content_role,density=args.density,intended_use=args.use)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
