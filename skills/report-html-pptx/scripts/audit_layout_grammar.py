"""Persist honest browser geometry QA for an approved HTML grammar plan."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from html_grammar_contract import inspect_html_grammar
from layout_plan import _digest
from project_state import ProjectState


SCRIPT=Path(__file__).with_suffix('.mjs')
CHECKER=Path(__file__).with_name('html_grammar_contract.py')
PLANNER=Path(__file__).with_name('layout_plan.py')
LOADER=Path(__file__).with_name('check_layout.mjs')


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_files(state: ProjectState) -> dict[str,str]:
    root=state.root
    candidates=['content/layout-plan.json','html/index.html','report-config.json',
                'content/page-brief.json','content/final.md',
                'content/company-pack-snapshot.json','content/font-policy-review.json']
    assets=root/'html/assets'
    if assets.is_dir():
        candidates += [(f.relative_to(root)).as_posix() for f in assets.rglob('*') if f.is_file()]
    result={}
    for rel in sorted(set(candidates)):
        file=state.path(rel,must_exist=False)
        if file.is_file():result[rel]=_sha(file)
    return result


def audit_layout_grammar(project: Path, *, browser_path: Path | None = None) -> dict:
    state=ProjectState(project)
    plan_file=state.path('content/layout-plan.json')
    html_file=state.path('html/index.html')
    plan=json.loads(plan_file.read_text(encoding='utf-8'))
    static=inspect_html_grammar(html_file.read_text(encoding='utf-8'),plan)
    relevant=any(page['mode'] in {'approved_grammar','needs_revision'} for page in plan['pages'])
    result={'schema_version':'layout-grammar-audit/1.0',
            'plan_sha256':plan.get('plan_sha256'),'html_sha256':_sha(html_file),
            'input_hashes':_source_files(state),
            'tool_receipt':{'checker':_sha(Path(__file__)), 'renderer_script':_sha(SCRIPT),
                            'html_contract':_sha(CHECKER),'planner':_sha(PLANNER),
                            'browser_loader':_sha(LOADER)},
            'requires_visual_review':relevant,'visual_review':'pending' if relevant else 'not_applicable',
            'inspected_pages':[],'relationships':[], 'screenshots':[],
            'findings':static['findings'][:],
            'status':static['status']}
    if result['status']=='PASS':
        command=['node',str(SCRIPT),str(state.root),str(plan_file)]
        if browser_path:command.append(str(browser_path))
        try:
            run=subprocess.run(command,capture_output=True,text=True,timeout=90,check=False)
            if run.returncode:
                raise RuntimeError(f'Browser checker exited {run.returncode}: {run.stderr[-500:]}')
            rendered=json.loads(run.stdout)
            if rendered.get('status') not in {'PASS','FAIL','UNVERIFIED'}:
                raise ValueError('Unexpected rendering tool status')
            result.update({key:rendered.get(key,[]) for key in ('inspected_pages','relationships','screenshots')})
            result['findings']+=rendered.get('findings',[])
            result['status']=rendered['status']
            result['tool_receipt'].update(rendered.get('tool',{}))
            if result['status']=='UNVERIFIED':result['reason']=rendered.get('reason','Renderer unavailable')
        except (FileNotFoundError,subprocess.TimeoutExpired,ValueError,RuntimeError) as error:
            result['status']='UNVERIFIED'
            result['reason']=str(error)
    out=state.path('qa/layout-grammar-application.json',must_exist=False)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--browser-path',type=Path)
    result=audit_layout_grammar(**vars(parser.parse_args()))
    print(json.dumps({'status':result['status'],'findings':len(result['findings']),
                      'inspected_pages':result['inspected_pages']},ensure_ascii=False))
