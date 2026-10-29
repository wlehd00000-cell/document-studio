"""Measured, redacted page evidence and private rendered-page review workspace.

Never copy source text, images, or local paths into the exportable index.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from document_extract import render_preview


KINDS = {'text','image','table_or_chart','vector'}


def _finite_positive(value: object) -> bool:
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>0


def _normalize_bbox(box: list, canvas: list, fmt: str) -> list[float]:
    if not isinstance(box,(list,tuple)) or len(box)!=4 or any(
            not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in box):
        raise ValueError('Invalid bounding box')
    if fmt=='pptx':
        left,top,width,height=box
        right,bottom=left+width,top+height
    else:
        left,top,right,bottom=box
    if left<0 or top<0 or right<=left or bottom<=top or right>canvas[0]+0.01 or bottom>canvas[1]+0.01:
        raise ValueError('Bounding box extends outside canvas or has no area')
    return [round(left/canvas[0],6),round(top/canvas[1],6),
            round(right/canvas[0],6),round(bottom/canvas[1],6)]


def build_evidence_index(extracted: dict, *, source_id: str, document_family: str) -> dict:
    """Return source-grounded geometry while dropping raw text and private paths."""
    fmt=extracted.get('format')
    if fmt not in {'pdf','pptx'} or not source_id or not document_family:
        raise ValueError('PDF/PPTX, source_id, and document_family are required')
    pages=[]
    for page in extracted.get('pages',[]):
        canvas=page.get('size_pt')
        number=page.get('number')
        if not isinstance(canvas,(list,tuple)) or len(canvas)!=2 or not all(map(_finite_positive,canvas)):
            raise ValueError('Invalid page canvas')
        if not isinstance(number,int) or number<1 or number!=len(pages)+1:
            raise ValueError('Pages must be sequential and 1-based')
        regions=[]
        quarantined=0
        for idx,shape in enumerate(page.get('shapes',[]),1):
            if shape.get('kind') not in KINDS:
                continue
            if shape.get('bbox_pt') is None:
                continue
            # Real PDFs can expose an image object with an empty page-space box.
            # Quarantine only this known extractor artifact, not malformed user data.
            box=shape['bbox_pt']
            if (fmt=='pdf' and shape['kind']=='image' and
                    shape.get('measurement')=='observed_pdf_geometry' and
                    isinstance(box,(list,tuple)) and len(box)==4 and
                    all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in box) and
                    0<=box[0]<=box[2]<=canvas[0] and 0<=box[1]<=box[3]<=canvas[1] and
                    (box[0]==box[2] or box[1]==box[3])):
                quarantined+=1
                continue
            regions.append({'region_id':f'{source_id}-P{number}-R{idx}',
                            'kind':shape['kind'],
                            'bbox_norm':_normalize_bbox(shape['bbox_pt'],canvas,fmt),
                            'measurement':str(shape.get('measurement','unknown'))[:80]})
        pages.append({'number':number,'size_pt':list(canvas),'regions':regions,
                      'quarantined_regions':quarantined})
    return {'schema_version':'visual-evidence/1.0','source_id':source_id,
            'document_family':document_family,'format':fmt,'pages':pages}


def prepare_visual_workspace(source: Path, extracted: dict, *, source_id: str,
                             document_family: str, workspace: Path, max_pages: int = 50) -> Path:
    """Generate local PNGs for human inspection outside an exportable Company Pack."""
    source,workspace=Path(source),Path(workspace)
    if source.is_symlink() or not source.is_file() or workspace.is_symlink():
        raise ValueError('Only regular source files and workspace directories allowed')
    if workspace.exists() and (not workspace.is_dir() or any(workspace.iterdir())):
        raise FileExistsError('Private workspace must be new or empty')
    workspace.mkdir(parents=True,exist_ok=True)
    index=build_evidence_index(extracted,source_id=source_id,document_family=document_family)
    preview_paths=render_preview(source,workspace/'previews',max_pages=max_pages)
    private_index={'evidence':index,
                   'previews':[{'page':i+1,'path':str(Path('previews')/Path(path).name)}
                               for i,path in enumerate(preview_paths)],
                   'review_status':'images_created_review_pending' if preview_paths else 'render_unavailable'}
    target=workspace/'evidence-index.json'
    target.write_text(json.dumps(private_index,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return target
