"""Write an approved-source, review-pending grammar plan from a final manuscript brief."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from company_pack import load_company_pack
from layout_plan import build_layout_plan


def write_layout_plan(project: Path, page_brief: str, company_pack: Path | None = None) -> dict:
    project=Path(project).resolve(strict=True)
    if not project.is_dir():raise ValueError('Expected existing document project')
    from project_state import ProjectState
    state=ProjectState(project)
    input_file=state.path(page_brief)
    if input_file.suffix.lower()!='.json':raise ValueError('Page brief must be JSON')
    brief=json.loads(input_file.read_text(encoding='utf-8'))
    pack=load_company_pack(company_pack) if company_pack else None
    config_file=state.path('report-config.json',must_exist=False)
    if config_file.is_file():
        config=json.loads(config_file.read_text(encoding='utf-8'))
        pinned=config.get('company_pack')
        if pinned and (pack is None or pack.pack_id!=pinned['pack_id'] or pack.version!=pinned['version']):
            raise ValueError('Company Pack identity/version differs from project')
        if not pinned and pack is not None:
            raise ValueError('Company Pack must be selected when the project is scaffolded')
    plan=build_layout_plan(pack,brief)
    snapshot_file=state.path('content/company-pack-snapshot.json',must_exist=False)
    if snapshot_file.is_file():
        snapshot=json.loads(snapshot_file.read_text(encoding='utf-8'))
        if snapshot.get('sha256')!=plan['pack_snapshot_sha256']:
            raise ValueError('Company Pack snapshot changed; re-review before production')
    destination=state.path('content/layout-plan.json',must_exist=False)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(plan,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    if state.state is not None:
        page_ids=[page['page_id'] for page in plan['pages']]
        if state.state['page_order']!=page_ids:
            state.set_pages(page_ids)
        state.register('page_brief',page_brief,'source','brief')
        dependencies=['page_brief']
        for source in ('copy','company_pack'):
            if source in state.state['nodes']:dependencies.append(source)
        state.register('layout_plan','content/layout-plan.json','artifact','layout',
                       depends=dependencies)
        state.snapshot('layout_plan')
        if 'html' in state.state['nodes']:
            prior=state.state['nodes']['html']
            dependencies=sorted(set(prior['depends']+['layout_plan']))
            state.register('html','html/index.html','artifact','html',depends=dependencies)
    return {'plan':str(destination),'status':plan['review_status'],
            'pages':len(plan['pages']),'plan_sha256':plan['plan_sha256']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--page-brief',default='content/page-brief.json')
    parser.add_argument('--company-pack',type=Path)
    print(json.dumps(write_layout_plan(**vars(parser.parse_args())),ensure_ascii=False))
