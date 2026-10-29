"""The installed skill exposes a repeatable, local-only onboarding command route."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/company-profile-analyzer/scripts/visual_grammar_workflow.py'


def test_cli_propose_combines_evidence_and_validated_visual_classification(tmp_path):
    source={'schema_version':'visual-evidence/1.0','format':'pdf','source_id':'SRC-A',
            'document_family':'profile','pages':[{'number':1,'size_pt':[100,100],
            'regions':[{'region_id':'SRC-A-P1-R1','kind':'text','bbox_norm':[0.1,0.1,0.9,0.3]}]}]}
    observed={'schema_version':'visual-observations/1.0','observations':[{
        'observation_id':'EV-001','source_id':'SRC-A','page':1,'region_id':'SRC-A-P1-R1',
        'bbox_norm':[0.1,0.1,0.9,0.3],'role':'heading','page_family':'cover',
        'observation':'Wide title region','evidence_kind':'visually_observed',
        'confidence':'medium','status':'suggested'}]}
    evidence_file=tmp_path/'evidence.json'
    obs_file=tmp_path/'observed.json'
    evidence_file.write_text(json.dumps(source))
    obs_file.write_text(json.dumps(observed))
    cmd=[sys.executable,str(SCRIPT),'propose','--evidence',str(evidence_file),
         '--observations',str(obs_file),'--grammar-output',str(tmp_path/'grammar.json'),
         '--redacted-evidence-output',str(tmp_path/'redacted.json')]
    result=subprocess.run(cmd,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    grammar=json.loads((tmp_path/'grammar.json').read_text())
    assert grammar['rules'][0]['page_families']==['cover']
    redacted=json.loads((tmp_path/'redacted.json').read_text())
    assert redacted['observations'][0]['page_family']=='cover'
    assert 'Wide title region' in str(redacted)
