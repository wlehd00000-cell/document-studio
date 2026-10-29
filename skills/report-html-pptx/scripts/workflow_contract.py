"""One stage registry and scope policy. No host hooks or model execution claims."""
import json
from pathlib import Path
from execution_profile import classify_profile

CONTRACT=json.loads((Path(__file__).resolve().parents[1]/'system/workflow-contract.json').read_text(encoding='utf-8'))
STAGES=CONTRACT['stages']


def load_brief(project):
    root=Path(project).resolve()
    brief=json.loads((root/'content/brief.json').read_text(encoding='utf-8-sig'))
    execution=root/'qa/workflow.json'
    if execution.is_file():
        value=json.loads(execution.read_text(encoding='utf-8-sig'))
        if value.get('schema_version')!=1:raise ValueError('Unsupported execution state')
        brief={**brief,'workflow':value['workflow']}
    return brief


def decision_signature(brief):
    import hashlib
    intake=brief.get('intake',{})
    groups=[intake.get('fields',{}),intake.get('layout',{}).get('fields',{})]
    values={key:{k:row.get(k) for k in ('value','origin','reason','user_confirmed')} for group in groups for key,row in group.items()}
    values['expression']=intake.get('design_expression')
    return hashlib.sha256(json.dumps(values,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def plan(brief, exports=False):
    workflow=brief.get('workflow',{})
    operation=workflow.get('operation','full')
    if operation not in CONTRACT['operations']:raise ValueError('Unknown workflow operation')
    required=set()
    if operation=='full':required.update(CONTRACT['full_required'])
    elif operation=='revision':
        changes=workflow.get('changed_roles',[])
        if not changes or any(role not in CONTRACT['change_impacts'] for role in changes):
            raise ValueError('Revision requires actual changed roles')
        required.update(stage for role in changes for stage in CONTRACT['change_impacts'][role])
    elif operation=='conversion':required.add('export')
    elif operation=='translation':
        language=workflow.get('target_language')
        if language not in {'ko','ja'}:raise ValueError('Translation requires its actual target language')
        required.add('korean' if language=='ko' else 'japanese')
    extra=workflow.get('required_stages',[])
    if not isinstance(extra,list) or any(stage not in STAGES for stage in extra):raise ValueError('Unknown required stage')
    required.update(extra)
    if exports:required.add('export')
    elif operation not in {'conversion'}:required.discard('export')
    scope=workflow.get('pages','all')
    if scope!='all' and (not isinstance(scope,list) or not scope or len(set(scope))!=len(scope) or any(not isinstance(p,str) for p in scope)):
        raise ValueError('Scope must be all or unique page IDs')
    if operation=='revision' and set(workflow['changed_roles']) & set(CONTRACT['global_changes']):scope='all'
    profile=classify_profile(workflow)
    return {'operation':operation,'pages':scope,**profile,'required_stages':[s for s in STAGES if s in required],
        'required_skills':[STAGES[s]['skill'] for s in STAGES if s in required],
        'preserved_stages':[s for s in STAGES if s not in required]}
