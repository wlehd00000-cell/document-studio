"""Resolved decisions, measured design and current evidence for DEMO production.

The host still owns skill execution and visual judgment. This module checks the
packaged production/export paths; it is not a host hook or model benchmark.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / 'system/design-tokens.json'
JS = Path(__file__).with_name('measure_design_contract.js')
from design_registry import CANVASES, select_profile,font_for

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def profile_for(brief):
    use = brief['intake']['layout']['fields']['use']['value']
    selected = brief.get('authoring', {}).get('design_profile')
    return select_profile(brief.get('genre'),use,selected)

def packet(brief, stage='design'):
    from intake import resolve_intake
    current = resolve_intake(existing=brief)
    missing = current['missing']
    groups = [{ 'field':k, 'suggestion': (current['fields'].get(k) or current['layout']['fields'].get(k))['suggested_value']}
              for k in missing]
    result = {'status':current['status'], 'missing':missing, 'questions':groups,
              'next_action':'ask_missing_choices' if missing else stage,
              'preflight_allowed':True, 'production_allowed':not missing,
              'use':current['use'], 'canvas':current['canvas'],
              'mode':current['fields']['mode']['value'],
              'review_checkpoint':current.get('review_checkpoint'),
              'scope':'Current project decisions; suggestions are not answers'}
    if not missing:
        normalized = {**brief, 'intake':current}
        profile = profile_for(normalized)
        tokens = read(TOKENS)
        language=None if brief.get('production_contract',{}).get('version')=='1.0' else current['fields']['final_language']['value']
        result['design'] = {'profile':profile, 'canvas_px':CANVASES[current['canvas']],
            'font':font_for(language,tokens)['primary'],'font_by_language':tokens['font']['by_language'] if language else {}, 'paper':tokens['palette']['paper'],
            'typography':tokens['profiles'][profile]['typography'], 'grid':tokens['profiles'][profile]['grid'],
            'expression':current['design_expression']}
    return result

def deviation(brief, page, prop, default, target=None):
    rows = brief.get('design',{}).get('deviations',[])
    matching = [r for r in rows if str(r.get('page')) in {'*',str(page)} and r.get('property') == prop
                and (not r.get('target') or r['target']==target)]
    if matching:
        specificity=lambda r:int(str(r.get('page'))==str(page))+2*int(bool(r.get('target')))
        highest=max(map(specificity,matching));matching=[r for r in matching if specificity(r)==highest]
    if len(matching)>1: raise ValueError('Conflicting design deviations')
    if not matching: return default
    record=matching[0]
    if record.get('status') not in {'intentional','user_accepted','template_preserved'} or not record.get('reason') or not record.get('origin') or 'value' not in record:
        raise ValueError('Design deviation needs a value, scope, reason and origin')
    return record['value']

def evaluate_pages(brief, pages):
    setup=packet(brief); findings=[]
    def fail(page,code,detail): findings.append({'page':page,'code':code,'detail':detail})
    if setup['missing']:
        fail(None,'UNRESOLVED_CHOICES',', '.join(setup['missing'])); return findings
    tokens=read(TOKENS); expected=setup['design']; profile=expected['profile']
    if not pages: fail(None,'NO_MEASURED_PAGES','No actual pages were measured')
    for row in pages:
        page=row['page']; family=row.get('family','')
        if not isinstance(row.get('canvas'),list) or len(row['canvas'])!=2:
            fail(page,'INVALID_MEASUREMENT','Canvas requires two measured dimensions');continue
        numeric=list(row.get('canvas',[]))+[s.get('font_size_px') for s in row.get('samples',[])]+list((row.get('frame') or {}).values())+[g.get('gap') for g in row.get('grids',[])]
        if any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in numeric):
            fail(page,'INVALID_MEASUREMENT','Nonfinite or missing numeric measurement'); continue
        if any(abs(row['canvas'][i]-expected['canvas_px'][i])>1 for i in (0,1)):
            fail(page,'CANVAS_MISMATCH',f"{row['canvas']} vs accepted {expected['canvas_px']}")
        if row.get('profile')!=profile:
            fail(page,'PROFILE_MISMATCH',f"{row.get('profile')} vs {profile}")
        samples=row.get('samples',[])
        if not samples: fail(page,'NO_FONT_SAMPLE','No visible business text')
        for sample in samples:
            language=str(sample.get('language','')).lower().split('-')[0]
            base=expected['font_by_language'].get(language,{}).get('primary',expected['font'])
            font=deviation(brief,page,'font',base,sample.get('key'))
            actual=sample.get('platform_fonts',[])
            expected_name=re.sub(r'\s|Variable','',font,flags=re.I).lower()
            permitted={expected_name}
            if font==base:
                permitted.update(re.sub(r'\s|Variable','',expected['font_by_language'][lang]['primary'],flags=re.I).lower() for lang in sample.get('languages',[]) if lang in expected['font_by_language'])
            bad=[f for f in actual if f.get('glyphCount',0)>0 and re.sub(r'\s|Variable','',f.get('familyName',''),flags=re.I).lower() not in permitted]
            if not any(f.get('glyphCount',0)>0 for f in actual) or bad:
                fail(page,'ACTUAL_FONT_MISMATCH',str(actual))
        # Full-image covers may use intentional imagery rather than paper white.
        if family not in {'cover','chapter_opener'}:
            paper=deviation(brief,page,'paper',expected['paper']).lower()
            if row.get('paper','').lower()!=paper:
                fail(page,'PAPER_MISMATCH',f"{row.get('paper')} vs {paper}")
            if not row.get('frame'):
                fail(page,'UNMEASURED_CONTENT_FRAME','Use data-demo-content-frame on the actual content wrapper')
            else:
                margin=float(deviation(brief,page,'margin_x_px',expected['grid']['margin_x_px']))
                if any(abs(row['frame'][k]-margin)>1 for k in ('left','right')):
                    fail(page,'ACTUAL_MARGIN_MISMATCH',f"{row['frame']} vs {margin}px")
            body=[s for s in samples if s.get('role')=='body']
            if not body: fail(page,'UNMEASURED_BODY_TYPE','Mark actual body prose with data-demo-role=body')
            else:
                for sample in body:
                    size=float(deviation(brief,page,'body_pt',expected['typography']['body_pt'],sample.get('key')))*96/72
                    if abs(sample['font_size_px']-size)>.2:
                        fail(page,'ACTUAL_BODY_SIZE_MISMATCH',f"{sample.get('key')}: {sample['font_size_px']} vs {size}px")
            for grid in row.get('grids',[]):
                gap=float(deviation(brief,page,'grid_gap_px',expected['grid']['column_gap_px'],grid.get('key')))
                if abs(grid['gap']-gap)>1:
                    fail(page,'ACTUAL_GRID_GAP_MISMATCH',f"{grid['gap']} vs {gap}px")
    return findings

def measure(brief_path, html_path, out_path, browser_path=None):
    from playwright.sync_api import sync_playwright
    brief_path=Path(brief_path).resolve(); html_path=Path(html_path).resolve(); out_path=Path(out_path).resolve()
    brief=read(brief_path); setup=packet(brief)
    if setup['missing']: raise ValueError('Unresolved choices: '+', '.join(setup['missing']))
    resources={str(html_path):digest(html_path),str(brief_path):digest(brief_path)}; failures=[]; remote=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=browser_path or None)
        try:
            page=browser.new_page(viewport={'width':setup['design']['canvas_px'][0], 'height':setup['design']['canvas_px'][1]})
            def collect(response):
                parsed=urlparse(response.url)
                if parsed.scheme=='file':
                    name=unquote(parsed.path)
                    if re.match(r'^/[A-Za-z]:/',name):name=name[1:]
                    path=Path(name)
                    if path.is_file():resources[str(path.resolve())]=digest(path)
                elif parsed.scheme in {'http','https'}:remote.append(response.url)
            page.on('response',collect)
            page.on('requestfailed',lambda request:failures.append(request.url) if request.resource_type in {'stylesheet','image','font','script'} else None)
            page.goto(html_path.as_uri(),wait_until='networkidle'); page.evaluate('document.fonts.ready')
            rows=page.evaluate(JS.read_text(encoding='utf-8'))
            cdp=page.context.new_cdp_session(page); cdp.send('DOM.enable');cdp.send('CSS.enable')
            document=cdp.send('DOM.getDocument',{'depth':-1})['root']['nodeId']
            for row in rows:
                for sample in row['samples']:
                    node=cdp.send('DOM.querySelector',{'nodeId':document,'selector':sample.pop('selector')})['nodeId']
                    sample['platform_fonts']=cdp.send('CSS.getPlatformFontsForNode',{'nodeId':node})['fonts'] if node else []
        finally: browser.close()
    findings=evaluate_pages(brief,rows)
    if failures or remote:findings.append({'page':None,'code':'UNVERIFIED_RESOURCE','detail':{'failed':failures,'remote':remote}})
    record={'schema_version':1,'format':'demo-design-contract-v1','status':'measured',
            'implementation_hashes':{str(Path(__file__).resolve()):digest(__file__),str(JS):digest(JS),str(TOKENS):digest(TOKENS)},
            'source_evidence':{'local_files':resources,'external_resources_unhashed':sorted(set(remote))},
            'pages':rows,'findings':findings,'passed':not findings,
            'coverage':'Actual canvas, profile, platform fonts, page paper, body type, content margins and available grid gaps. Spatial reference adaptation and full visual/editorial quality need separate review.'}
    out_path.parent.mkdir(parents=True,exist_ok=True)
    out_path.write_bytes((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode())
    return record

def audit_findings(project, brief, html=None):
    project=Path(project).resolve()
    relative=brief.get('production_contract',{}).get('design_audit','qa/design-contract.json')
    audit=(project/relative).resolve()
    if not audit.is_relative_to(project) or not audit.is_file():return [{'reason':'missing_design_measurement'}]
    try:
        report=read(audit)
        if report.get('format')!='demo-design-contract-v1' or report.get('status')!='measured':raise ValueError('Not a measured design report')
        required={str(Path(__file__).resolve()),str(JS),str(TOKENS)}
        if set(report['implementation_hashes'])!=required:raise ValueError('Unexpected implementation evidence')
        for filename,hashvalue in report['implementation_hashes'].items():
            if digest(filename)!=hashvalue:raise ValueError('Design checker or tokens changed')
        if not required <= set(report['implementation_hashes']):raise ValueError('Missing implementation evidence')
        sources=report['source_evidence']['local_files']
        source=Path(html).resolve() if html else project/'html/index.html'
        bound = str(source) in sources
        if not bound and source.name.endswith('.audited.html'):
            original=source.with_name(source.name.replace('.audited.html','.html'))
            bound=str(original) in sources and digest(source)==sources[str(original)]
        if not bound or str(project/'content/brief.json') not in sources:raise ValueError('Different canonical HTML or brief')
        for filename,hashvalue in sources.items():
            if not Path(filename).resolve().is_relative_to(project):raise ValueError('Rendering resource outside project')
            if digest(filename)!=hashvalue:raise ValueError('Design source/resource changed')
        if report['source_evidence'].get('external_resources_unhashed'):raise ValueError('Unhashed remote resources')
        result=evaluate_pages(brief,report['pages'])
        # Missing/failing resource observations cannot be cleared by editing passed=true.
        result += [x for x in report.get('findings',[]) if x.get('code')=='UNVERIFIED_RESOURCE']
        return [{'reason':'design_contract_finding',**r} for r in result]
    except (ValueError,KeyError,OSError,TypeError) as error:
        return [{'reason':'stale_or_invalid_design_measurement','detail':str(error)}]

def skill_findings(project, exports=False):
    path=Path(project)/'qa/skill-use.json'
    if not path.is_file(): return [{'reason':'missing_skill_application_record'}]
    try:
        from workflow_contract import plan, decision_signature, CONTRACT, STAGES, load_brief
        project=Path(project).resolve()
        brief=load_brief(project) if (project/'content/brief.json').is_file() else {}
        planned=plan(brief,exports)
        active=set(planned['required_skills'])
        if planned['operation']=='full':
            active.update(STAGES[s]['skill'] for s in CONTRACT['conditional_stages'])
        records=read(path).get('applied',[]); done=set(); findings=[]; seen=set(); statuses={}
        if not isinstance(records,list):raise ValueError('applied must be a list')
        for record in records:
            skill=record.get('skill')
            if skill in seen:raise ValueError('Duplicate owner result: '+str(skill))
            seen.add(skill)
            # Retained history from an unaffected owner or previous export is
            # not a prerequisite of this operation. Required owners still
            # hash-check below; project dependencies/QA separately stay bound.
            if 'workflow' in brief and skill not in active:continue
            status=record.get('status')
            statuses[skill]=status
            if status not in {'planned','in_progress','verified','not_needed'}:
                findings.append({'reason':'unresolved_skill_status','skill':record.get('skill')});continue
            if status=='not_needed' and (not isinstance(record.get('reason'),str) or not record['reason'].strip()):
                findings.append({'reason':'missing_not_needed_reason','skill':skill})
            if status=='not_needed' and 'workflow' in brief and record.get('decision_signature')!=decision_signature(brief):
                findings.append({'reason':'stage_decisions_changed','skill':skill})
            if status!='verified': continue
            evidence=record.get('evidence',[])
            if not isinstance(evidence,list) or not evidence:
                findings.append({'reason':'missing_skill_evidence','skill':record.get('skill')});continue
            for item in evidence+record.get('inputs',[]):
                source=(Path(project)/item['path']).resolve()
                if not source.is_relative_to(Path(project).resolve()) or digest(source)!=item['sha256']:
                    raise ValueError('Missing, stale or outside-project skill evidence')
            if 'workflow' in brief:
                if not record.get('inputs') or not record.get('job') or not record.get('checked_scope'):
                    findings.append({'reason':'missing_stage_contract','skill':skill});continue
                if record.get('decision_signature')!=decision_signature(brief):
                    findings.append({'reason':'stage_decisions_changed','skill':skill});continue
                from project_state import ProjectState
                state=ProjectState(project)
                scope=state.scope(record['checked_scope'])
                if not set(state.scope(planned['pages']))<=set(scope):
                    findings.append({'reason':'stage_scope_incomplete','skill':skill});continue
            done.add(record.get('skill'))
        required=set(planned['required_skills'])
        if 'workflow' in brief and planned['operation']=='full':
            for stage in CONTRACT['conditional_stages']:
                skill=STAGES[stage]['skill']
                if statuses.get(skill) not in {'verified','not_needed'}:
                    findings.append({'reason':'unresolved_conditional_owner','skill':skill})
        for skill in sorted(required-done): findings.append({'reason':'unverified_required_owner','skill':skill})
        return findings
    except (ValueError,KeyError,TypeError,OSError) as error:return [{'reason':'invalid_skill_evidence','detail':str(error)}]

def contract_findings(project, html=None, exports=()):
    project=Path(project).resolve(); file=project/'content/brief.json'
    if not file.is_file():return [{'reason':'missing_structured_brief'}]
    try:
        from workflow_contract import load_brief
        brief=load_brief(project); bounded=brief.get('workflow',{}).get('operation')=='conversion'
        if bounded:
            validate_reviewed_input(project,brief,html)
            state=None
        else:
            state=packet(brief)
            if state['missing']:return [{'reason':'unresolved_required_choices','missing':state['missing']}]
        if brief.get('interaction',{}).get('pending_user_review'):
            return [{'reason':'awaiting_requested_user_review'}]
        findings=[] if bounded else audit_findings(project,brief,html)
        findings+=skill_findings(project,bool(exports))
        for filename in exports:
            path=Path(filename)
            if path.suffix.lower()!='.pptx':continue
            # [quality-floor-p0] Independent font gate; no declared-only READY.
            quality_file=project/'content/quality-contract.json'
            if quality_file.is_file():
                from quality_floor import verify_artifact
                proof=verify_artifact(read(quality_file),path,project=project)
                if proof['status']=='BLOCKED':
                    findings.append({'reason':'quality_floor_blocked',
                                     'blocking':proof.get('blocking',[])})
                elif proof.get('unverified'):
                    findings.append({'reason':'quality_floor_render_and_portability_unverified',
                                     'unverified':proof.get('unverified',[])})
            outcome=path.parent/(path.stem+'_audit')/'conversion-result.json'
            if 'workflow' in brief:
                if not outcome.is_file():findings.append({'reason':'missing_conversion_outcome'} )
                else:
                    result=read(outcome)
                    if (result.get('format')!='demo-export-outcome-v1' or result.get('output_sha256')!=digest(path)
                            or result.get('status')!='review_candidate' or result.get('findings')
                            or any(r.get('status')=='failed' for r in result.get('stages',{}).values())
                            or any(result.get('stages',{}).get(k,{}).get('status')!='succeeded'
                                   for k in ('measurement','assembly','text_fidelity'))):
                        findings.append({'reason':'failed_or_stale_conversion_outcome'})
                    source=result.get('source',{})
                    if (not source.get('path') or not Path(source['path']).resolve().is_relative_to(project)
                            or digest(source['path'])!=source.get('sha256')):
                        findings.append({'reason':'conversion_input_changed'})
            with ZipFile(path) as archive:
                xml=ET.fromstring(archive.read('ppt/presentation.xml'))
                size=xml.find('{http://schemas.openxmlformats.org/presentationml/2006/main}sldSz')
                emu=tuple(int(size.get(k)) for k in ('cx','cy'))
            if bounded:continue # Retain measured source canvas; no new-document layout choice.
            selected=state['canvas']; expected={'a4-portrait':(7560000,10692000),'a4-landscape':(10692000,7560000)}.get(selected)
            expected=expected or tuple(round(v*9525) for v in CANVASES[selected])
            if emu!=expected:findings.append({'reason':'pptx_canvas_mismatch','actual':emu,'expected':expected})
        return findings
    except (ValueError,KeyError,TypeError,OSError,ET.ParseError,BadZipFile) as error:
        return [{'reason':'invalid_production_contract','detail':str(error)}]

def find_project(html):
    path=Path(html).resolve()
    for parent in list(path.parents)[:4]:
        if (parent/'content/brief.json').is_file() or (parent/'content/brief.md').is_file():return parent
    return None


def validate_reviewed_input(root,brief,html=None):
    root=Path(root).resolve();workflow=brief['workflow'];binding=workflow.get('reviewed_input',{})
    bound=(root/binding.get('path','')).resolve()
    source=Path(html).resolve() if html else bound
    original=source.with_name(source.name.replace('.audited.html','.html'))
    if (not isinstance(workflow.get('origin'),str) or not workflow['origin'].strip()
            or not bound.is_relative_to(root) or bound not in {source,original}
            or digest(source)!=binding.get('sha256') or digest(bound)!=binding.get('sha256')):
        raise ValueError('Bounded conversion needs an unchanged reviewed input and located scope origin')
    return bound

def require_conversion_ready(html, project=None, reviewed_html_only=False):
    root=Path(project).resolve() if project else find_project(html)
    if root is None:
        if not reviewed_html_only:
            raise ValueError('No DEMO project found. Explicit bounded conversion requires --reviewed-html-only; full production requires --project-root.')
        return {'scope':'Bounded conversion of explicitly reviewed HTML; retain source canvas and design; no new-document intake'}
    brief_path=root/'content/brief.json'
    from workflow_contract import load_brief
    brief=load_brief(root) if brief_path.is_file() else {}
    if reviewed_html_only and brief.get('workflow',{}).get('operation')=='conversion':
        validate_reviewed_input(root,brief,html)
        return {'scope':'Bounded conversion of project-bound reviewed HTML','project':str(root)}
    # The flag cannot downgrade an identified full production project.
    findings=contract_findings(root,html)
    if findings:raise ValueError('DEMO production choices/design/evidence unresolved: '+json.dumps(findings,ensure_ascii=False))
    from project_state import ProjectState
    state=ProjectState(root)
    source=Path(html).resolve()
    registered=next((key for key,node in state.state['nodes'].items()
                     if node['kind']=='artifact' and state.path(node['path'])==source),None)
    if registered is None and source.name.endswith('.audited.html'):
        original=source.with_name(source.name.replace('.audited.html','.html'))
        registered=next((key for key,node in state.state['nodes'].items()
                         if node['kind']=='artifact' and state.path(node['path'])==original
                         and digest(source)==digest(original)),None)
    if registered is None:raise ValueError('Actual conversion input must be a registered, currently reviewed artifact')
    gate=state.gate(canonical=registered,exports=[])
    if gate['delivery_state']=='blocked':raise ValueError('Current HTML editorial/visual QA is incomplete: '+json.dumps(gate['blocking'],ensure_ascii=False))
    return {'scope':'Resolved full-document production with current HTML checks','project':str(root)}

def main():
    cli=argparse.ArgumentParser(description=__doc__); sub=cli.add_subparsers(dest='command',required=True)
    prepare=sub.add_parser('prepare');prepare.add_argument('--submission',required=True);prepare.add_argument('--brief',required=True)
    prepare.add_argument('--recommendations');prepare.add_argument('--hints')
    prepare.add_argument('--changed-field',action='append');prepare.add_argument('--blocking-field',action='append')
    status=sub.add_parser('status');status.add_argument('--brief',required=True);status.add_argument('--stage',default='design')
    audit=sub.add_parser('audit');audit.add_argument('--brief',required=True);audit.add_argument('--html',required=True);audit.add_argument('--out',required=True);audit.add_argument('--browser-path')
    check=sub.add_parser('check');check.add_argument('project');check.add_argument('--html');check.add_argument('--export',action='append',default=[])
    args=cli.parse_args()
    if args.command=='prepare':
        from intake import resolve_intake,merge_into_brief
        target=Path(args.brief).resolve(); old=read(target) if target.is_file() else {}
        input_paths=[Path(p).resolve() for p in (args.submission,args.recommendations,args.hints) if p]
        if target in input_paths:raise ValueError('Brief output must not overwrite a submission or source observation')
        result=merge_into_brief(old,resolve_intake(read(args.submission),existing=old,
            hints=read(args.hints) if args.hints else None,
            recommendations=read(args.recommendations) if args.recommendations else None,
            changed_fields=args.changed_field,blocking_fields=args.blocking_field))
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
        result=packet(result)
    elif args.command=='status':result=packet(read(args.brief),args.stage)
    elif args.command=='audit':
        r=measure(args.brief,args.html,args.out,args.browser_path);result={'passed':r['passed'],'findings':r['findings'],'pages':len(r['pages']),'audit':args.out}
    else:
        findings=contract_findings(args.project,args.html,args.export);result={'passed':not findings,'findings':findings}
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result.get('passed',result.get('production_allowed',False)) else 1

if __name__=='__main__':raise SystemExit(main())
