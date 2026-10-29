"""Inventory user-designated source files without executing content or extracting archives."""
import argparse
import json
from pathlib import Path
import re
from zipfile import ZipFile

SUPPORTED = {'.pdf','.pptx','.docx','.xlsx','.csv','.tsv','.txt','.md','.html','.png','.jpg','.jpeg','.webp','.gif','.svg','.tif','.tiff'}
IMAGES = {'.png','.jpg','.jpeg','.webp','.gif','.tif','.tiff'}

def inspect(path):
    record = {'name':path.name, 'path':str(path.resolve()), 'type':path.suffix.lower(), 'bytes':path.stat().st_size, 'content_reviewed':False}
    suffix=path.suffix.lower()
    try:
        if suffix in {'.pptx','.docx','.xlsx'}:
            with ZipFile(path) as z:
                names=z.namelist()
                pattern={'.pptx':r'ppt/slides/slide\d+\.xml$', '.xlsx':r'xl/worksheets/sheet\d+\.xml$'}.get(suffix)
                if pattern:record['parts']=sum(bool(re.fullmatch(pattern,n)) for n in names)
                record['embedded_media']=[n for n in names if re.match(r'^(ppt|word|xl)/media/[^/]+$',n)]
        elif suffix in IMAGES:
            try:
                from PIL import Image
                with Image.open(path) as im:record.update(width=im.width,height=im.height,mode=im.mode)
            except ImportError:record['metadata_note']='Pillow unavailable; dimensions not read'
        elif suffix=='.pdf':
            try:
                from pypdf import PdfReader
                reader=PdfReader(path);record['encrypted']=reader.is_encrypted
                if not reader.is_encrypted:record['pages']=len(reader.pages)
            except ImportError:record['metadata_note']='pypdf unavailable; pages not counted'
    except Exception as exc:record['metadata_error']=f'{type(exc).__name__}: {exc}'
    return record

def inventory(inputs,output,recursive=False):
    output=Path(output).resolve();files={};missing=[]
    for value in inputs:
        p=Path(value).expanduser()
        if not p.exists():missing.append(str(p));continue
        candidates=(p.rglob('*') if recursive else p.iterdir()) if p.is_dir() else [p]
        for candidate in candidates:
            if candidate.is_file() and candidate.suffix.lower() in SUPPORTED and candidate.resolve()!=output:
                files[str(candidate.resolve()).casefold()]=candidate
    records=[inspect(p) for p in sorted(files.values(),key=lambda p:str(p).casefold())]
    result={'files':records,'missing_inputs':missing,'summary':{'files':len(records),'embedded_media':sum(len(x.get('embedded_media',[])) for x in records)},'note':'Metadata inventory only. Read documents and inspect selected visuals before making claims.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('inputs',nargs='+');p.add_argument('--out',required=True);p.add_argument('--recursive',action='store_true');args=p.parse_args()
    result=inventory(args.inputs,args.out,args.recursive)
    print(json.dumps({'output':str(Path(args.out).resolve()),**result['summary'],'missing_inputs':result['missing_inputs']},ensure_ascii=True))
