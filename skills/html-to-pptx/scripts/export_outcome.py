"""Persist conversion attempts separately from delivery readiness. Stdlib only."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
from uuid import uuid4
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'report-html-pptx/scripts'))
from document_runtime import atomic_json


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def media_findings(measurement):
    findings=[]
    for index,slide in enumerate(measurement.get('slides', [measurement]),1):
        for record in slide.get('records',[]):
            if record.get('kind') not in {'img','svg','canvas','deco_snapshot'}:
                continue
            rect=record.get('rect',{})
            if rect.get('w',0)<=0 or rect.get('h',0)<=0: continue
            original=record.get('originalImage')
            image=original.get('path') if original else record.get('screenshot')
            if record.get('captureError') or not image or not Path(image).is_file():
                findings.append({'page':index,'code':'missing_media','kind':record['kind'],
                    'marker':record.get('marker'),'detail':record.get('captureError') or 'No captured image'})
            elif record.get('screenshot_sha256') and sha(image)!=record['screenshot_sha256']:
                findings.append({'page':index,'code':'media_snapshot_changed','marker':record.get('marker')})
            if record.get('kind')=='img' and not record.get('naturalImageSize',{}).get('w',0):
                findings.append({'page':index,'code':'image_not_loaded','src':record.get('src')})
    return findings


class ExportOutcome:
    def __init__(self,source,output):
        self.output=Path(output)
        self.path=self.output.parent/(self.output.stem+'_audit')/'conversion-result.json'
        self.start=time.perf_counter()
        self.record={'schema_version':1,'format':'demo-export-outcome-v1','attempt':uuid4().hex,
            'source':{'path':str(source),'sha256':sha(source)},'output':str(self.output),
            'status':'in_progress','created':False,'delivery_state':'blocked','stages':{},
            'findings':[],'limitations':['Conversion evidence requires subsequent editorial and visual export review.']}
        self.save()

    def save(self):
        atomic_json(self.path,self.record)

    def stage(self,name,status,detail=None):
        if status not in {'succeeded','failed','skipped','unavailable'}:raise ValueError('Unknown stage status')
        self.record['stages'][name]={'status':status,'detail':detail}
        self.save()

    @contextmanager
    def step(self,name):
        start=time.perf_counter()
        try:yield
        except BaseException as error:
            self.stage(name,'failed',str(error))
            self.record['status']='failed';self.record['seconds']=round(time.perf_counter()-self.start,3)
            self.save();raise
        else:
            self.stage(name,'succeeded',{'seconds':round(time.perf_counter()-start,3)})

    def finish(self,measurement,fidelity,self_check=None,audit_package=None):
        self.record['created']=self.output.is_file()
        if self.record['created']:self.record['output_sha256']=sha(self.output)
        findings=media_findings(measurement)+fidelity.get('findings',[])
        # A failed preferred renderer is not a failed check when fallback worked.
        for name,detail in (self_check or {}).get('errors',{}).items():
            if name in {'layout','fullslide_pic'}:
                findings.append({'code':'structural_check_failed','check':name,'detail':detail})
        if audit_package and audit_package.get('failed'):
            findings.append({'code':'comparison_coverage_missing','pages':audit_package['failed']})
        fonts=(self_check or {}).get('font_verification',{'status':'unverified'})
        if fonts.get('status')=='failed':
            findings.append({'code':'embedded_fonts_rejected','fonts':fonts.get('rejected',[])})
        if fonts.get('requires_fixed_layout') and fonts.get('status')=='unverified':
            findings.append({'code':'font_rendering_unverified','detail':fonts.get('reason')})
        self.record['font_verification']=fonts
        self.record['findings']=findings
        renderer=(self_check or {}).get('engine')
        self.record['rendering']={'engine':renderer,'pages':(self_check or {}).get('rendered_total',0),
            'state':'rendered_awaiting_review' if renderer else 'unverified'}
        self.record['structural_warnings']={k:(self_check or {}).get(k,[]) for k in
            ('layout_warnings','fullslide_pic_warnings','preflight_warnings')}
        failures=[name for name,row in self.record['stages'].items() if row['status']=='failed']
        self.record['status']='failed' if not self.record['created'] else 'verification_failed' if findings or failures else 'review_candidate'
        self.record['seconds']=round(time.perf_counter()-self.start,3)
        self.record['editability']={'native_text_records':sum(r.get('kind')=='text' for s in measurement.get('slides',[measurement]) for r in s.get('records',[])),
            'raster_records':sum(r.get('kind') in {'svg','canvas','deco_snapshot'} for s in measurement.get('slides',[measurement]) for r in s.get('records',[]))}
        self.save()
        return self.record
