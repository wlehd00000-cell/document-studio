"""Generate design CSS token blocks from the canonical JSON; independent of layout authoring."""
import argparse,json,sys
from pathlib import Path
BEGIN='/* BEGIN GENERATED DESIGN TOKENS - edit system/design-tokens.json */'
END='/* END GENERATED DESIGN TOKENS */'

def generate(tokens):
    pal=tokens['palette']; brand=pal['brand']; primary=tokens['font']['primary']
    lines=[BEGIN, ':root{'+''.join(f'--{k.replace("_","-")}:{v};' for k,v in {**brand,**{k:pal[k] for k in ['ink','slate','line','paper']}}.items())+f'--accent:var(--blue);--brand-band-height:{tokens["brand_band"]["height_px"]}px;--brand-band-cols:'+ ' '.join(str(x)+'fr' for x in tokens['brand_band']['ratios']) +'}']
    def declarations(p):
        out=[]
        for key,value in p['typography'].items():
            if key.endswith('_pt'):out.append(f'--{key[:-3].replace("_","-")}:{value}pt')
            elif key.endswith('_leading'):out.append(f'--{key.replace("_","-")}:{value}')
        for key,value in p.get('grid',{}).items():
            if key.endswith('_px'):out.append(f'--{key[:-3].replace("_","-")}:{value}px')
        return ';'.join(out)
    default=tokens['profiles']['reading_report']
    lines.append('[data-type-profile],[data-design-profile],.demo-esg-dense{'+declarations(default)+f';font-family:var(--demo-font-family,"{primary}"),sans-serif;font-size:var(--body);line-height:var(--body-leading);color:var(--ink)'+'}')
    for language,font in tokens['font'].get('by_language',{}).items():
        lines.append(f'html:lang({language}),body:lang({language}),[lang|="{language}"]'+'{'+f'--demo-font-family:"{font["primary"]}";font-family:var(--demo-font-family),sans-serif'+'}')
    for name,p in tokens['profiles'].items():
        lines.append(f'[data-design-profile="{name}"]'+'{'+declarations(p)+'}')
    for alias,name in tokens['legacy_aliases'].items():
        target=dict(tokens['profiles'][name]);target['typography']={**target['typography'],**tokens.get('legacy_typography_overrides',{}).get(alias,{})}
        lines.append(f'[data-type-profile="{alias}"]'+'{'+declarations(target)+'}')
    for family,info in tokens['page_families'].items():
        for pname,value in info.get('title_pt_by_profile',{}).items():
            lines.append(f'[data-design-profile="{pname}"][data-page-family="{family}"]'+'{'+f'--title:{value}pt'+'}')
        for pname,value in info.get('metadata_pt_by_profile',{}).items():
            lines.append(f'[data-design-profile="{pname}"][data-page-family="{family}"]'+'{'+f'--metadata:{value}pt'+'}')
    office=tokens['palette']['office_print'];printcfg=tokens['profiles']['office_print']['print'];safe=printcfg['safe_margin_mm']
    officevars={**{k:office['ink'] for k in ['blue','green','orange','accent']},**{k:office[k] for k in ['ink','slate','line']},'muted':office['slate'],'paper':pal['paper'],'print-table-head':office['table_head'],'print-safe-top':str(safe['top'])+'mm','print-safe-right':str(safe['right'])+'mm','print-safe-bottom':str(safe['bottom'])+'mm','print-safe-left':str(safe['left'])+'mm','print-content-bottom':str(printcfg['body_bottom_reserve_mm'])+'mm','print-footer-bottom':str(printcfg['footer_bottom_mm'])+'mm','print-caption-leading':printcfg['caption_leading']}
    lines.append('[data-design-profile="office_print"],.office-print{'+''.join('--'+k+':'+str(v)+';' for k,v in officevars.items())+'}')
    lines.append(END)
    return '\n'.join(lines)+'\n'

def validate(tokens):
    required=['reading_report','office_print','executive_approval','proposal','execution','reading_deck','live_deck']
    for name in required:
        p=tokens['profiles'][name]
        for key in ['body_pt','table_pt','caption_pt','label_pt','subhead_pt','title_pt']:
            value=p['typography'][key]
            if not isinstance(value,(int,float)) or value<=0:raise ValueError(f'{name}.{key} must be a positive physical point size')
    if tokens['profiles']['live_deck']['typography']['body_pt']<=tokens['profiles']['reading_report']['typography']['body_pt']:raise ValueError('Live viewing profile must be independently readable')
    if tokens['brand_band']['default_enabled']:raise ValueError('Decorative band must remain opt-in')
    for alias,target in tokens['legacy_aliases'].items():
        if target not in tokens['profiles']:raise ValueError(f'Unknown alias target {alias}: {target}')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];tokens=json.loads((root/'system/design-tokens.json').read_text(encoding='utf-8-sig'));validate(tokens)
    block=generate(tokens);cssfile=root/'assets/demo-esg-design/demo-esg-report.css';src=cssfile.read_text(encoding='utf-8-sig')
    if BEGIN not in src or END not in src:raise SystemExit('Missing generated token markers; refuse to overwrite layout CSS')
    before,tail=src.split(BEGIN,1);_,after=tail.split(END,1);target=before+block+after.lstrip('\n')
    tokenfile=root/'assets/demo-esg-design/demo-design-tokens.css'
    if args.check:
        ok=src==target and tokenfile.exists() and tokenfile.read_text(encoding='utf-8')==block
        print(json.dumps({'tokens_valid':True,'generated_css_current':ok,'profiles':len(tokens['profiles']),'page_families':len(tokens['page_families'])}))
        sys.exit(0 if ok else 1)
    cssfile.write_text(target,encoding='utf-8');tokenfile.write_text(block,encoding='utf-8');print(json.dumps({'generated_css_current':True,'profiles':len(tokens['profiles'])}))
