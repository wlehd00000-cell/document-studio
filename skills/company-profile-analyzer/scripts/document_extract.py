"""Extract measured PDF/PPTX geometry and text; never execute document content."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile
import shutil
import subprocess
import tempfile


A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
P='{http://schemas.openxmlformats.org/presentationml/2006/main}'
EMU=914400  # EMU per inch


def _pdf_rgb_hex(value):
    """Convert a PDF device-RGB drawing color to a stable CSS hex value."""
    if (not isinstance(value,(tuple,list)) or len(value)!=3 or
            any(not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in value)):
        return None
    return '#'+''.join(f'{round(v*255):02X}' for v in value)


def _pdf_graphic_colors(page):
    """Summarize visible vector fills/strokes without retaining vector artwork."""
    weights=Counter()
    area=max(1.0,page.rect.get_area())
    for drawing in page.get_drawings():
        bounds=drawing.get('rect')
        coverage=min(8.0,max(1.0,bounds.get_area()/area*70.0)) if bounds else 1.0
        fill=_pdf_rgb_hex(drawing.get('fill'))
        if fill and drawing.get('fill_opacity',1)>0:
            weights[fill]+=coverage
        stroke=_pdf_rgb_hex(drawing.get('color'))
        if stroke and drawing.get('stroke_opacity',1)>0:
            weights[stroke]+=min(3.0,coverage)
    return [[color,round(weight,2)] for color,weight in weights.most_common(60)]


def _pptx_text(sp):
    return '\n'.join(''.join(n.text or '' for n in para.iter(f'{A}t'))
                     for para in sp.iter(f'{A}p')).strip()


def extract_pptx(path: Path) -> dict:
    pages=[]
    with ZipFile(path) as z:
        names=z.namelist()
        if 'ppt/presentation.xml' not in names:
            raise ValueError('PPTX presentation.xml is missing')
        presentation=ET.fromstring(z.read('ppt/presentation.xml'))
        size=presentation.find(f'{P}sldSz')
        dims=[round(int(size.get(k,'0'))/EMU*72,2) for k in ('cx','cy')] if size is not None else None
        slides=sorted((n for n in names if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)),
                      key=lambda n:int(re.search(r'slide(\d+)',n)[1]))
        for idx,name in enumerate(slides,1):
            root=ET.fromstring(z.read(name))
            shapes=[]
            for sp in list(root.iter(f'{P}sp'))+list(root.iter(f'{P}pic'))+list(root.iter(f'{P}graphicFrame')):
                xf=sp.find(f'.//{A}xfrm')
                if xf is None:
                    xf=sp.find(f'{P}xfrm')
                offset=xf.find(f'{A}off') if xf is not None else None
                ext=xf.find(f'{A}ext') if xf is not None else None
                bbox=[round(int(node.get(coord,'0'))/EMU*72,2) for node,coord in
                      ((offset,'x'),(offset,'y'),(ext,'cx'),(ext,'cy'))] if offset is not None and ext is not None else None
                text=_pptx_text(sp)
                fonts=sorted({n.get('typeface') for n in sp.iter() if n.get('typeface')})
                sizes=sorted({int(n.get('sz'))/100 for n in sp.iter() if n.get('sz','').isdigit()})
                colors=sorted({'#'+n.get('val').upper() for n in sp.iter(f'{A}srgbClr') if re.fullmatch(r'[0-9A-Fa-f]{6}',n.get('val',''))})
                kind='text' if sp.tag==f'{P}sp' else ('image' if sp.tag==f'{P}pic' else 'table_or_chart')
                shapes.append({'kind':kind,'bbox_pt':bbox,'text':text,'fonts':fonts,'font_sizes_pt':sizes,
                               'colors':colors,'measurement':'observed_xml'})
            pages.append({'number':idx,'size_pt':dims,'shapes':shapes})
    return {'format':'pptx','pages':pages,'measurement':'observed_xml','rendered_visual_review':'not_performed'}


def extract_pdf(path: Path) -> dict:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError('PDF extraction requires optional PyMuPDF (fitz)') from exc
    pages=[]
    with fitz.open(path) as document:
        for idx,page in enumerate(document,1):
            shapes=[]
            for block in page.get_text('dict')['blocks']:
                if block.get('type')==1:
                    shapes.append({'kind':'image','bbox_pt':list(block['bbox']),'text':'',
                                   'fonts':[],'font_sizes_pt':[],'colors':[],
                                   'measurement':'observed_pdf_geometry'})
                    continue
                if block.get('type')!=0:
                    continue
                spans=[span for line in block.get('lines',[]) for span in line.get('spans',[])]
                if not spans:
                    continue
                colors=sorted({'#'+format(span['color'] & 0xffffff,'06X') for span in spans if 'color' in span})
                shapes.append({'kind':'text','bbox_pt':list(block['bbox']),
                               'text':' '.join(span.get('text','') for span in spans).strip(),
                               'fonts':sorted({span.get('font','') for span in spans if span.get('font')}),
                               'font_sizes_pt':sorted({round(span.get('size',0),2) for span in spans if span.get('size')}),
                               'colors':colors,'measurement':'observed_pdf_extract_font_names_may_be_subsetted'})
            pages.append({'number':idx,'size_pt':[round(page.rect.width,2),round(page.rect.height,2)],
                          'graphic_color_weights':_pdf_graphic_colors(page),'shapes':shapes})
    return {'format':'pdf','pages':pages,'measurement':'observed_pdf_extract','rendered_visual_review':'not_performed'}


def extract_document(path: Path) -> dict:
    path=Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError('Input must be a regular file, not a symlink')
    if path.suffix.lower()=='.pptx':
        return extract_pptx(path)
    if path.suffix.lower()=='.pdf':
        return extract_pdf(path)
    raise ValueError('Supported formats: PDF/PPTX')


def render_preview(path: Path, output_dir: Path, max_pages: int = 6) -> list[str]:
    """Render for subsequent *human/agent* visual review, not visual certification."""
    path=Path(path)
    if max_pages<1 or max_pages>50:
        raise ValueError('max_pages must be 1..50')
    out=Path(output_dir)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Preview output must be new or empty')
    out.mkdir(parents=True,exist_ok=True)
    if path.suffix.lower()=='.pptx':
        office=shutil.which('libreoffice') or shutil.which('soffice')
        if office is None:
            return []
        with tempfile.TemporaryDirectory(prefix='document-preview-') as temp:
            proc=subprocess.run([office,'-env:UserInstallation=file://'+str(Path(temp)/'profile'),
                                 '--headless','--convert-to','pdf','--outdir',temp,str(path)],
                                capture_output=True,timeout=120)
            pdf=Path(temp)/(path.stem+'.pdf')
            if proc.returncode!=0 or not pdf.is_file():
                return []
            import fitz
            with fitz.open(pdf) as doc:
                return _save_preview_pages(doc,out,max_pages)
    if path.suffix.lower()=='.pdf':
        import fitz
        with fitz.open(path) as doc:
            return _save_preview_pages(doc,out,max_pages)
    raise ValueError('Supported formats: PDF/PPTX')


def _save_preview_pages(document, folder, limit):
    import fitz
    files=[]
    for number,page in enumerate(document,1):
        if number>limit:
            break
        target=folder/f'page-{number:02}.png'
        page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(target)
        files.append(str(target))
    return files


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--render-preview-dir',type=Path)
    a=p.parse_args()
    extracted=extract_document(a.source)
    if a.render_preview_dir:
        previews=render_preview(a.source,a.render_preview_dir)
        extracted['preview_pages']=previews
        extracted['rendered_visual_review']='images_created_review_pending' if previews else 'unavailable'
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(extracted,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'format':extracted['format'],'pages':len(extracted['pages']),
                      'visual_review':extracted['rendered_visual_review']}))
