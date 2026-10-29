"""Audit style-extraction fidelity against an official public PDF without republishing it.

The result contains derived measurements only. It is NOT a pixel-fidelity score,
official brand approval, or evidence of rights to redistribute source material.
"""
from __future__ import annotations

import argparse
from collections import Counter
import colorsys
import hashlib
from html import escape
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit


SKILL_SCRIPTS=Path(__file__).resolve().parents[1]/'skills/company-profile-analyzer/scripts'
sys.path.insert(0,str(SKILL_SCRIPTS))
from design_analyzer import analyze_design,draft_design_profile  # noqa: E402
from document_extract import extract_document  # noqa: E402
from writing_analyzer import analyze_writing  # noqa: E402


def _chromatic(name: str) -> bool:
    try:
        if len(name)!=7 or name[0]!='#':
            return False
        red,green,blue=(int(name[i:i+2],16)/255 for i in (1,3,5))
        return colorsys.rgb_to_hsv(red,green,blue)[1]>=0.22
    except (TypeError,ValueError):
        return False


def evaluate_public_company(path: Path, *, company: str, source_url: str,
                            language: str, training_pages: int = 2,
                            document_family: str = 'corporate_profile') -> dict:
    """Use first N pages as style evidence and remaining pages as color holdout."""
    parsed=urlsplit(source_url)
    if parsed.scheme!='https' or not parsed.hostname:
        raise ValueError('Official source provenance must be an HTTPS URL')
    path=Path(path)
    if not company.strip() or not language.strip():
        raise ValueError('Company and language are required')
    if path.suffix.lower()!='.pdf' or not path.is_file() or path.is_symlink():
        raise ValueError('Evaluation requires a regular local PDF')
    if training_pages<1:
        raise ValueError('training_pages must be positive')

    extracted=extract_document(path)
    pages=extracted['pages']
    if not pages:
        raise ValueError('PDF has no pages')
    training_pages=min(training_pages,len(pages))
    train={'pages':pages[:training_pages]}
    full_design=analyze_design(extracted,source_id='PUBLIC-SOURCE',document_family=document_family)
    train_design=analyze_design(train,source_id='PUBLIC-TRAIN',document_family=document_family)
    tokens,_,_=draft_design_profile([train_design])
    writing=analyze_writing(extracted,source_id='PUBLIC-SOURCE',language=language,
                            document_family=document_family,allow_excerpt=False)

    holdout=pages[training_pages:]
    reference=[]
    if holdout:
        holdout_design=analyze_design({'pages':holdout},source_id='PUBLIC-HOLDOUT',
                                      document_family=document_family)
        reference=[color for color,_ in holdout_design['dominant_graphic_colors']
                   if _chromatic(color)][:8]
    selected=set(tokens['palette']['brand'].values())
    shared=len(selected.intersection(reference))
    sizes={tuple(p['size_pt']) for p in pages}
    orientations={('landscape' if size[0]>size[1] else 'portrait') for size in sizes}

    return {
        'schema_version':'public-company-fidelity/1.0',
        'source':{
            'company':company,'official_url':source_url,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'pages':len(pages),'document_family':document_family,'language':language,
            'page_orientation':next(iter(orientations)) if len(orientations)==1 else 'mixed',
            'page_sizes_pt':[list(size) for size in sorted(sizes)],
            'pages_with_vectors':sum(bool(p.get('graphic_color_weights')) for p in pages),
            'pages_with_raster_images':sum(any(s['kind']=='image' for s in p['shapes']) for p in pages),
            'text_block_count':sum(sum(s['kind']=='text' for s in p['shapes']) for p in pages),
        },
        'design':{
            'source_top_graphic_colors':full_design['dominant_graphic_colors'][:8],
            'source_top_text_colors':full_design['dominant_colors'][:8],
            'frequent_font_names_unverified':full_design['frequent_fonts'][:5],
            'frequent_font_sizes_pt':full_design['frequent_font_sizes_pt'][:8],
            'proposed_brand_colors':tokens['palette']['brand'],
            'palette_status':'draft_only_not_official_brand_guidelines',
            'vector_color_scope':'PDF fill/stroke only; raster artwork colors not measured',
        },
        'color_holdout':{
            'train_pages':training_pages,'holdout_pages':len(holdout),
            'holdout_top_chromatic_vector_colors':reference,
            'shared_train_holdout_colors':shared,
            'exact_color_recall_at_4':round(shared/min(4,len(reference)),3) if reference else None,
            'interpretation':'exact CSS color recurrence only, NOT page reconstruction similarity',
        },
        'writing':{
            'paragraph_count':writing['paragraph_count'],
            'sentence_count':writing['sentence_count'],
            'mean_sentence_chars':writing['average_sentence_chars'],
            'script_detection':writing['observed_scripts'],
            'status':writing['analysis_status'],
            'source_excerpts_included':False,
        },
        'release_gate':{
            'company_pack_status':'draft_only',
            'full_visual_reproduction':'NOT_EVALUATED',
            'actual_font_rendering':'NOT_VERIFIED',
            'html_to_pptx_pixel_fidelity':'NOT_VERIFIED',
            'source_redistribution_allowed':False,
        },
    }


def render_style_hypothesis(report: dict) -> str:
    """Independent-content HTML style probe; intentionally not a source recreation."""
    palette=list(report['design']['proposed_brand_colors'].values())
    width,height=report['source']['page_sizes_pt'][0]
    company=escape(report['source']['company'])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Style hypothesis · {company}</title>
<style>
@page {{ size:{width}pt {height}pt; margin:0 }}
:root {{--brand-primary:{palette[0]};--brand-second:{palette[1]};--brand-third:{palette[2]};--brand-fourth:{palette[3]}}}
* {{box-sizing:border-box}}
html,body {{margin:0;padding:0;background:white;color:#231F20;font-family:Arial,sans-serif}}
.page {{width:{width}pt;min-height:{height}pt;padding:43pt 38pt;position:relative;overflow:hidden}}
.top {{height:7pt;background:var(--brand-primary)}}
.eyebrow {{margin-top:25pt;color:var(--brand-primary);font-size:11pt;letter-spacing:.15em;font-weight:700}}
h1 {{font-size:30pt;line-height:1.12;max-width:85%;margin:12pt 0 7pt}}
.subtitle {{font-size:12pt;color:#666;margin-bottom:25pt}}
.rule {{height:2pt;background:var(--brand-primary);margin-bottom:24pt}}
.cols {{display:grid;grid-template-columns:1fr 1fr;gap:22pt}}
h2 {{font-size:14pt;margin:0 0 11pt}}
p {{font-size:10pt;line-height:1.55;margin:0 0 10pt}}
.banner {{background:var(--brand-primary);height:25pt;margin:16pt 0;color:white;font-weight:700;font-size:12pt;padding:5pt 9pt}}
.metric {{background:#f5f7f7;padding:14pt;border-left:5pt solid var(--brand-second);margin-bottom:11pt}}
.metric b {{font-size:23pt;color:var(--brand-primary)}}
.bars div {{height:16pt;margin:7pt 0;background:var(--brand-primary)}}
.bars div:nth-child(2) {{background:var(--brand-second);width:73%}}
.bars div:nth-child(3) {{background:var(--brand-third);width:52%}}
.bars div:nth-child(4) {{background:var(--brand-fourth);width:37%}}
footer {{border-top:1pt solid #ccd3d5;margin-top:21pt;padding-top:9pt;font-size:8pt;color:#777}}
</style></head><body><div class="page">
<div class="top"></div><div class="eyebrow">EVALUATION ONLY / DRAFT STYLE HYPOTHESIS</div>
<h1>Operational overview</h1><div class="subtitle">{company} · Fictional sample data</div><div class="rule"></div>
<div class="cols"><section><h2>Executive context</h2>
<p>This invented example tests the extracted color candidates on a generic report composition.
It is not a company publication, reproduction, or approved brand template.</p>
<div class="banner">Sample program</div>
<p>A fictional team evaluates three alternative operating models and the evidence needed for a decision.</p>
<div class="metric"><b>42%</b><p>Illustrative metric — not a real result</p></div></section>
<section><h2>Example visual hierarchy</h2><p>Fictional segments, not source figures</p>
<div class="bars"><div></div><div></div><div></div><div></div></div>
<div class="banner">Evaluation summary</div><p>Only proposed color values and page dimensions came from measured source traits. Layout, imagery, font rendering and tone are unverified.</p>
</section></div>
<footer>INDEPENDENT STYLE PROBE · Not affiliated with or endorsed by {company}</footer>
</div></body></html>'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--company',required=True)
    parser.add_argument('--official-url',required=True)
    parser.add_argument('--language',default='en-US')
    parser.add_argument('--training-pages',type=int,default=2)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--preview-html',type=Path,
                        help='Optional synthetic-content HTML style hypothesis; never official')
    args=parser.parse_args()
    report=evaluate_public_company(args.source,company=args.company,
                                   source_url=args.official_url,language=args.language,
                                   training_pages=args.training_pages)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if args.preview_html:
        args.preview_html.parent.mkdir(parents=True,exist_ok=True)
        args.preview_html.write_text(render_style_hypothesis(report),encoding='utf8')
    print(json.dumps({'company':args.company,'pages':report['source']['pages'],
                      'holdout':report['color_holdout']['exact_color_recall_at_4'],
                      'status':report['release_gate']['full_visual_reproduction']}))


if __name__=='__main__':
    main()
