"""Turn extracted geometry into quantitative Design DNA and review candidates."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


def analyze_design(extracted: dict, *, source_id: str, document_family: str) -> dict:
    pages=extracted.get('pages',[])
    if not pages:
        raise ValueError('No extracted pages for design analysis')
    colors=Counter()
    fonts=Counter()
    sizes=Counter()
    margins=[]
    for page in pages:
        width,height=page.get('size_pt') or (0,0)
        for shape in page.get('shapes',[]):
            for color in shape.get('colors',[]):
                if isinstance(color,str) and len(color)==7 and color.startswith('#'):
                    colors[color.upper()]+=1
            for font in shape.get('fonts',[]):
                if isinstance(font,str) and font:
                    fonts[font]+=1
            for size in shape.get('font_sizes_pt',[]):
                if isinstance(size,(int,float)) and size>0:
                    sizes[round(size,1)]+=1
            bbox=shape.get('bbox_pt')
            if bbox and width and height and len(bbox)==4:
                x,y,w,h=bbox
                if x>=0 and y>=0:
                    margins.append([round(x/width,3),round(y/height,3)])
    result={'source_ids':[source_id],'document_family':document_family,
            'page_count':len(pages),'canvas_sizes_pt':[p.get('size_pt') for p in pages],
            'dominant_colors':colors.most_common(8),'frequent_fonts':fonts.most_common(8),
            'frequent_font_sizes_pt':sizes.most_common(12),
            'min_observed_margins_normalized':[
                min((x[0] for x in margins),default=None),
                min((x[1] for x in margins),default=None)],
            'quantitative_status':'observed_measurement',
            'visual_interpretation':{'status':'UNVERIFIED','requires_rendered_page_review':True,
                'questions':['What is the visual center of the cover?',
                             'How do image and heading relate?',
                             'What recurring page compositions and reading paths appear?']},
            'font_name_recovery':'PDF font names may be subsetted or misleading; confirm before official use'}
    return result


def draft_design_profile(analyses: list[dict]) -> tuple[dict,dict,dict]:
    """Create safe proposed overlays; never claim official design approval."""
    colors=Counter()
    fonts=Counter()
    cases=[]
    layouts=[]
    for i,analysis in enumerate(analyses,1):
        colors.update(dict(analysis.get('dominant_colors',[])))
        fonts.update(dict(analysis.get('frequent_fonts',[])))
        cases.append({'case_id':f'analyzed-layout-{i}',
                      'title':'Measured page composition candidate',
                      'source_ids':analysis['source_ids'],'status':'suggested','confidence':'low',
                      'jobs':['layout','evidence'],
                      'page_families':['evidence'],'purpose_profiles':['reading_report'],
                      'observed':'Quantitative bounds extracted; visual composition needs review'})
        layouts.append({'source_ids':analysis['source_ids'],'document_family':analysis['document_family'],
                        'page_count':analysis['page_count'],'canvas_sizes_pt':analysis['canvas_sizes_pt'],
                        'status':'measured_layout_not_render_verified'})
    distinct=[name for name,_ in colors.most_common() if name not in {'#000000','#FFFFFF'}]
    while len(distinct)<4:
        distinct += ['#28506A','#17384F','#5D7E82','#A5BBC1'][len(distinct):len(distinct)+1]
    brand=dict(zip(('blue','deep_blue','green','orange'),distinct[:4]))
    tokens={'palette':{'brand':brand}}
    if fonts:
        tokens['font']={'primary':fonts.most_common(1)[0][0]}
    return tokens,{'cases':cases},{'layouts':layouts,'review_status':'unverified'}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('extraction',type=Path)
    p.add_argument('--source-id',required=True)
    p.add_argument('--document-family',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    extracted=json.loads(a.extraction.read_text(encoding='utf8'))
    result=analyze_design(extracted,source_id=a.source_id,document_family=a.document_family)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'source_ids':result['source_ids'],'pages':result['page_count'],
                      'visual_review':'UNVERIFIED'}))
