"""Small, scoped handoffs and hashed owner results using existing project files."""
import argparse
import json
from pathlib import Path
import sys
from project_state import ProjectState, digest_file, digest_json
from workflow_contract import CONTRACT, STAGES, plan, decision_signature, load_brief
from execution_profile import classify_profile, PROFILES, RISK_SIGNALS
from execution_metrics import start_attempt, finish_attempt, path_of as metric_path


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,value):
    # Same atomic writer as project state; never alter designated source inputs.
    from render_text_flow import save_audit
    path.parent.mkdir(parents=True,exist_ok=True);save_audit(path,value)


def begin(root,operation,changed_roles=(),pages='all',target_language=None,origin=None,required_stages=None,reviewed_input=None,
          execution_profile='auto',risk_signals=()):
    file=Path(root)/'qa/workflow.json';brief=load_brief(root)
    if not origin or not origin.strip():raise ValueError('Preserve located request/accepted scope origin')
    workflow={'operation':operation,'changed_roles':list(changed_roles),'pages':pages,
              'target_language':target_language,'origin':origin}
    if risk_signals:
        workflow['risk_signals']=list(risk_signals)
    previous=read(file) if file.is_file() else {'schema_version':1,'history':[]}
    prior=brief.get('workflow')
    workflow['required_stages']=list(required_stages if required_stages is not None else
        (prior.get('required_stages',[]) if prior and prior.get('operation')==operation=='full' else []))
    if reviewed_input:
        if operation!='conversion':raise ValueError('Reviewed input binding is only for bounded conversion')
        state=ProjectState(root);source=state.path(reviewed_input)
        workflow['reviewed_input']={'path':source.relative_to(state.root).as_posix(),'sha256':digest_file(source)}
    if operation=='conversion' and not reviewed_input:
        raise ValueError('Bounded conversion needs --reviewed-input for the actually reviewed project file')
    # Decide after binding conversion evidence so reviewed conversion can be focused.
    classified=classify_profile(workflow,execution_profile)
    workflow['execution_profile']=classified['execution_profile']
    if prior and prior!=workflow:previous['history'].append(prior)
    brief['workflow']=workflow
    result=plan(brief)
    if (Path(root)/'content/project-state.json').is_file() and result['pages']!='all':
        ProjectState(root).scope(result['pages'])
    save(file,{**previous,'workflow':workflow})
    return result


def handoff(root,stage,track_metrics=False):
    root=Path(root).resolve();brief=load_brief(root);current=plan(brief,stage=='export')
    if stage not in STAGES:raise ValueError('Unknown stage')
    from production_contract import packet
    choices=packet(brief,stage) if current['operation'] in {'full','revision'} else {'production_allowed':True,'scope':current['operation']}
    paths=[]
    if (root/'content/project-state.json').is_file():
        state=ProjectState(root)
        paths=[{'id':key,'path':node['path'],'role':node['role'],'pages':node['pages'],
                'sha256':digest_file(state.path(node['path'])) if state.path(node['path'],must_exist=False).is_file() else None}
               for key,node in state.state['nodes'].items()]
    result={'schema_version':1,'stage':stage,'owner':STAGES[stage]['skill'],'expected_result':STAGES[stage]['result'],
        'required':stage in current['required_stages'],'operation':current['operation'],'pages':current['pages'],
        'choices':choices,'current_files':paths,'brief':'content/brief.json',
        'note':'Apply the actual owner skill. This packet and a skill read are not completion evidence.'}
    if track_metrics:
        start_attempt(root,stage,current['operation'],current['execution_profile'],current['pages'])
    return result


def complete(root,stage,inputs,outputs,pages,observations):
    if stage not in STAGES or not inputs or not outputs or not observations.strip():
        raise ValueError('Stage needs actual inputs, outputs and checked observations')
    root=Path(root).resolve();state=ProjectState(root)
    scope=state.scope(pages)
    def records(names):
        return [{'path':name,'sha256':digest_file(state.path(name))} for name in dict.fromkeys(names)]
    brief=load_brief(root);planned=plan(brief,stage=='export')['pages']
    if stage in {'architecture','writing','design','export'} and brief.get('workflow',{}).get('operation','full') in {'full','revision'}:
        from production_contract import packet
        if not packet(brief,stage)['production_allowed']:raise ValueError('Required choices still pending; retain provisional work without claiming stage completion')
    required=state.scope(planned)
    if not set(required)<=set(scope):raise ValueError('Checked stage scope misses affected pages')
    record={'skill':STAGES[stage]['skill'],'stage':stage,'status':'verified','operation':brief.get('workflow',{}).get('operation','full'),
            'checked_scope':scope,'job':observations,'inputs':records(inputs),'evidence':records(outputs)}
    record['decision_signature']=decision_signature(brief)
    file=root/'qa/skill-use.json';value=read(file) if file.is_file() else {'schema_version':1,'applied':[]}
    value['applied']=[r for r in value.get('applied',[]) if r.get('skill')!=record['skill']]+[record]
    save(file,value)
    if metric_path(root).is_file():
        try:
            finish_attempt(root,stage,'verified',observed={'input_hashes':[r['sha256'] for r in record['inputs']],
                                                       'output_hashes':[r['sha256'] for r in record['evidence']]})
        except (OSError,ValueError,TypeError) as error:
            record['metrics_warning']='Metric capture failed independently: '+type(error).__name__
    return record


def skip(root,stage,reason):
    if stage not in CONTRACT['conditional_stages'] or not reason.strip():raise ValueError('Only an unnecessary conditional stage may be skipped with a reason')
    root=Path(root).resolve();brief=load_brief(root)
    if stage in plan(brief,True)['required_stages']:raise ValueError('Required stage cannot be skipped')
    file=root/'qa/skill-use.json';value=read(file) if file.is_file() else {'schema_version':1,'applied':[]}
    record={'skill':STAGES[stage]['skill'],'stage':stage,'status':'not_needed','reason':reason,
            'decision_signature':decision_signature(brief)}
    value['applied']=[r for r in value.get('applied',[]) if r.get('skill')!=record['skill']]+[record]
    save(file,value)
    if metric_path(root).is_file():
        try:finish_attempt(root,stage,'not_needed')
        except (OSError,ValueError,TypeError) as error:
            record['metrics_warning']='Metric capture failed independently: '+type(error).__name__
    return record


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--project',required=True)
    sub=cli.add_subparsers(dest='command',required=True)
    begin_cli=sub.add_parser('begin');begin_cli.add_argument('--operation',choices=CONTRACT['operations'],required=True)
    begin_cli.add_argument('--changed-role',action='append',default=[]);begin_cli.add_argument('--pages',default='all')
    begin_cli.add_argument('--target-language');begin_cli.add_argument('--origin',required=True)
    begin_cli.add_argument('--required-stage',action='append',choices=STAGES)
    begin_cli.add_argument('--reviewed-input')
    begin_cli.add_argument('--execution-profile',choices=('auto',*PROFILES),default='auto')
    begin_cli.add_argument('--risk-signal',choices=RISK_SIGNALS,action='append',default=[])
    packet_cli=sub.add_parser('handoff');packet_cli.add_argument('stage',choices=STAGES)
    packet_cli.add_argument('--track-metrics',action='store_true')
    done=sub.add_parser('complete');done.add_argument('stage',choices=STAGES)
    done.add_argument('--input',action='append',required=True);done.add_argument('--output',action='append',required=True)
    done.add_argument('--pages',default='all');done.add_argument('--observations',required=True)
    unnecessary=sub.add_parser('skip');unnecessary.add_argument('stage',choices=CONTRACT['conditional_stages']);unnecessary.add_argument('--reason',required=True)
    sub.add_parser('status');args=cli.parse_args()
    scope=lambda value:'all' if value=='all' else value.split(',')
    if args.command=='begin':result=begin(args.project,args.operation,args.changed_role,scope(args.pages),args.target_language,args.origin,args.required_stage,args.reviewed_input,args.execution_profile,args.risk_signal)
    elif args.command=='handoff':result=handoff(args.project,args.stage,args.track_metrics)
    elif args.command=='complete':result=complete(args.project,args.stage,args.input,args.output,scope(args.pages),args.observations)
    elif args.command=='skip':result=skip(args.project,args.stage,args.reason)
    else:
        from production_contract import skill_findings
        brief=load_brief(args.project)
        result={**plan(brief,True),'findings':skill_findings(args.project,True)}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError) as error:
        print(json.dumps({'status':'failed','error':str(error)},ensure_ascii=False),file=sys.stderr);raise SystemExit(1)
