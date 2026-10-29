"""Static, private review gallery for evidence-grounded company layout rules."""
from __future__ import annotations

from html import escape
import os
from pathlib import Path

from layout_grammar import validate_grammar


LAYER_LABELS={'brand_dna':'Brand DNA','layout_grammar':'Layout Grammar',
              'creative_vocabulary':'Creative Vocabulary'}


def default_fictional_examples() -> list[dict]:
    """Independently authored text for visibly different layout experiments."""
    return [
        {'id':'study-editorial','layout':'editorial-split','page_job':'evidence',
         'title':'A clearer path to the next decision',
         'body':'An invented organization is testing a lighter review process.',
         'metric':'48 sample teams'},
        {'id':'study-dashboard','layout':'dense-grid','page_job':'data_visualization',
         'title':'Fictional operations at a glance',
         'body':'These indicators are placeholders, not real business results.',
         'metric':'12 pilot workstreams'},
        {'id':'study-story','layout':'image-led','page_job':'image_story',
         'title':'Ideas become visible in context',
         'body':'A wholly invented scenario for exploring visual hierarchy.',
         'metric':'3 design directions'},
    ]


def build_review_board(evidence: dict, grammar: dict, *, private_preview_root: Path,
                       output: Path, fictional_examples: list[dict]) -> Path:
    root=Path(private_preview_root).absolute()
    output=Path(output).absolute()
    if root.is_symlink() or not root.is_dir() or output.is_symlink() or not output.is_relative_to(root):
        raise ValueError('Review board must stay inside an existing private preview workspace')
    if output.exists():
        raise FileExistsError('Review board already exists')
    if not isinstance(fictional_examples,list) or len(fictional_examples) not in {2,3}:
        raise ValueError('Provide two or three fictional layout studies')
    ids=[example.get('id') for example in fictional_examples]
    layouts=[example.get('layout') for example in fictional_examples]
    if len(set(ids))!=len(ids) or len(set(layouts))!=len(layouts) or any(
            layout not in {'editorial-split','dense-grid','image-led'} for layout in layouts):
        raise ValueError('Study IDs and layout strategies must be distinct')
    validate_grammar(grammar,evidence)
    css=(Path(__file__).resolve().parents[1]/'assets/visual-review-board.css').read_text(encoding='utf8')
    panels=[]
    for page in evidence.get('pages',[]):
        filename=f'page-{page["number"]:02}.png'
        image=root/'previews'/filename
        if image.is_symlink() or not image.is_file():
            raise ValueError('Review thumbnail missing; render page first')
        overlays=[]
        for reg in page['regions']:
            left,top,right,bottom=reg['bbox_norm']
            kind=reg.get('kind','text')
            if kind not in {'text','image','table_or_chart','vector'}:
                kind='text'
            overlays.append(f'<span class="region {kind}" title="{escape(reg["region_id"])} · {escape(kind)}" '
                            f'style="left:{left*100:.3f}%;top:{top*100:.3f}%;'
                            f'width:{(right-left)*100:.3f}%;height:{(bottom-top)*100:.3f}%"></span>')
        relative=Path(os.path.relpath(image,output.parent)).as_posix()
        panels.append(f'<figure class="source"><div class="page-image">'
                      f'<img src="{escape(relative)}" alt="Private source page {page["number"]} preview">'
                      f'{"".join(overlays)}</div><figcaption>Page {page["number"]}: '
                      f'{len(page["regions"])} measured regions</figcaption></figure>')
    rules=[]
    for layer,label in LAYER_LABELS.items():
        cards=[]
        for rule in grammar['rules']:
            if rule['layer']!=layer:
                continue
            refs=', '.join(f'{a["source_id"]} p.{a["page"]} {a["region_id"]}' for a in rule['evidence_refs'])
            relationships=''.join(f'<span class="relation">{escape(r)}</span>' for r in rule['relationships'])
            cards.append(f'<article class="rule"><h3>{escape(rule["rule_id"])}</h3>'
                         f'<div class="relations">{relationships}</div>'
                         f'<p>{escape(rule.get("reason","Review the cited evidence"))}</p>'
                         f'<small>{escape(refs)} · {escape(rule["status"])} · {escape(rule["confidence"])}</small></article>')
        rules.append(f'<section aria-label="{label}"><h2>{label}</h2>'
                     f'{"".join(cards) if cards else "<p>No observations yet.</p>"}</section>')
    studies=[]
    for example in fictional_examples:
        for field in ('title','body','metric','page_job'):
            if not isinstance(example.get(field),str) or not example[field].strip():
                raise ValueError('Fictional content must have nonempty study fields')
        studies.append(f'<article class="study {example["layout"]}" aria-label="Fictional layout study">'
                       f'<span class="eyebrow">INDEPENDENT FICTIONAL STUDY · {escape(example["page_job"])}</span>'
                       f'<div class="study-main"><h3>{escape(example["title"])}</h3>'
                       f'<p>{escape(example["body"])}</p></div>'
                       f'<strong class="metric">{escape(example["metric"])}</strong></article>')
    output.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                      '<meta name="viewport" content="width=device-width,initial-scale=1">'
                      '<title>Document Studio · Private visual review</title><style>'+css+'</style></head>'
                      '<body><header><p class="eyebrow">DOCUMENT STUDIO · PRIVATE EVIDENCE</p>'
                      '<h1>Visual grammar review</h1><p>Inspect observations, then record explicit '
                      'review decisions separately. This board never approves a Company Pack.</p></header>'
                      '<main><h2>Source evidence (private thumbnails)</h2>'
                      '<div class="evidence-controls" aria-label="Evidence overlays">'
                      '<label><input type="checkbox" id="show-vectors"> Vector shapes</label>'
                      '<label><input type="checkbox" id="show-text" checked> Text blocks</label>'
                      '<label><input type="checkbox" id="show-images" checked> Images and charts</label>'
                      '</div><div class="gallery">'
                      +''.join(panels)+'</div><div class="grammar">'+''.join(rules)+'</div>'
                      '<h2>Creative studies with fictional content</h2><div class="studies">'
                      +''.join(studies)+'</div></main></body></html>',encoding='utf8')
    return output
