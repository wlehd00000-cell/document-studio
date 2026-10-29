"""DEMO Quality Floor P1.3: rendered glyph-font gate for NEW_DOCUMENT HTML.

This is a separate browser proof, not a PowerPoint/native-rendering certificate.
Only NEW_DOCUMENT contracts created by P0/P1 are in scope; no fonts are installed.
"""
from __future__ import annotations
import argparse
import base64
import re
from lxml import html as LH, etree
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse, unquote

FAMILIES = {'ja': 'Pretendard JP', 'ko': 'Pretendard'}
JS = r'''() => {
  const KANA=/[\u3040-\u30ff\u31f0-\u31ff]/u;
  const HANGUL=/[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]/u;
  const HAN=/[\u3400-\u9fff\uf900-\ufaff]/u;
  const pages=[...document.querySelectorAll('[data-pptx-slide]')];
  const failures=[], samples=[], cssFaces=[];
  const rootLang=(document.documentElement.lang||'').toLowerCase().split('-')[0];
  function isVisible(el) {
    const s=getComputedStyle(el);
    if(s.display==='none'||s.visibility==='hidden')return false;
    if(el.closest('[aria-hidden="true"],script,noscript,style,svg,template'))return false;
    return !!el.getClientRects().length;
  }
  for(const sheet of [...document.styleSheets]){
    let rules=[];
    try{rules=[...sheet.cssRules]}catch(e){failures.push({code:'STYLESHEET_UNREADABLE',detail:String(e)});continue;}
    for(const rule of rules){
      if(rule.type!==CSSRule.FONT_FACE_RULE)continue;
      const fam=rule.style.getPropertyValue('font-family').replace(/["']/g,'').trim();
      const src=rule.style.getPropertyValue('src');
      const urls=[];const pat=/url\(\s*["']?([^"')]+)["']?\s*\)/g; let m;
      while((m=pat.exec(src))!==null){
        try{urls.push(new URL(m[1],sheet.href||document.baseURI).href)}catch(e){urls.push('UNRESOLVED:'+m[1])}
      }
      cssFaces.push({family:fam,urls});
    }
  }
  const probeHolder=document.createElement('div');
  probeHolder.id='demo-quality-font-probes';
  probeHolder.style.cssText='position:absolute;top:-100000px;left:0;white-space:pre;z-index:-9999;pointer-events:none;';
  document.body.appendChild(probeHolder);
  let seq=0;
  for(let pageNo=0;pageNo<pages.length;pageNo++){
    const w=document.createTreeWalker(pages[pageNo],NodeFilter.SHOW_TEXT);
    let n;
    while((n=w.nextNode())){
      const value=n.nodeValue||'';
      if(!KANA.test(value)&&!HANGUL.test(value)&&!HAN.test(value))continue;
      const parent=n.parentElement;
      if(!parent||!isVisible(parent))continue;
      if(samples.length>=2500){failures.push({code:'TEXT_PROBE_LIMIT_EXCEEDED'});break;}
      const ka=[...value].filter(x=>KANA.test(x));
      const ko=[...value].filter(x=>HANGUL.test(x));
      const han=[...value].filter(x=>HAN.test(x));
      const localLang=(parent.closest('[lang]')?.getAttribute('lang')||rootLang||'').toLowerCase().split('-')[0];
      if((ka.length&&ko.length)||(ko.length&&han.length&&localLang==='ja')){
        failures.push({code:'MIXED_SCRIPT_TEXT_NODE',page:pageNo+1,text:value.slice(0,90)});
        continue;
      }
      const lang=ka.length?'ja':ko.length?'ko':localLang;
      if(!['ja','ko'].includes(lang)){
        failures.push({code:'HAN_LANGUAGE_UNDETERMINED',page:pageNo+1,text:value.slice(0,90)});continue;
      }
      if((ko.length||ka.length)&&localLang!==lang){
        failures.push({code:'SCRIPT_LANGUAGE_SCOPE_MISMATCH',page:pageNo+1,script:lang,declared:localLang,text:value.slice(0,90)});
      }
      const s=getComputedStyle(parent);
      const probe=document.createElement('span');
      const identifier='gsfont-'+(++seq);
      probe.dataset.gsQualityFontProbe=identifier;
      probe.lang=lang;
      probe.textContent=[...value].filter(x=>ka.length?KANA.test(x)||HAN.test(x):ko.length?HANGUL.test(x)||HAN.test(x):HAN.test(x)).join('');
      probe.style.cssText=`font-family:${s.fontFamily};font-size:${s.fontSize};font-weight:${s.fontWeight};font-style:${s.fontStyle};font-stretch:${s.fontStretch};letter-spacing:${s.letterSpacing};white-space:pre;`;
      probeHolder.appendChild(probe);
      samples.push({id:identifier,page:pageNo+1,lang,declaredLang:localLang,
        text:probe.textContent.slice(0,90),computedFamily:s.fontFamily,weight:s.fontWeight,
        sourceText:value.slice(0,90)});
    }
  }
  return {pageCount:pages.length,cssFaces,failures,samples};
}'''


FONT_FACE_CSS = re.compile(r'@font-face\s*\{[^{}]*\}', re.I | re.S)
FONT_NAME_CSS = re.compile(r'font-family\s*:\s*[\"\']?([^;\"\']+)[\"\']?\s*;', re.I)
CSS_URL = re.compile(r'url\(\s*([\"\']?)([^)\"\']+)\1\s*\)', re.I)


def _prepare_font_probe_html(html, project, contract):
    """Rehydrate exact local CSS and pinned font bytes for sandboxed set_content.

    This is NOT a faithful full-page export render: only glyph choice and author CSS
    cascade are probed. Every accepted data URI is derived from a locked local file.
    """
    doc=LH.fromstring(Path(html).read_text(encoding='utf-8'))
    failures=[];seen=[]
    # The audit should not execute authored scripts or event attributes.
    if doc.xpath('//script|//iframe|//object|//embed|//meta[translate(@http-equiv,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="refresh"]'):
        failures.append({'code':'EXECUTABLE_HTML_NOT_SUPPORTED_FOR_FONT_PROOF'})
    for node in doc.iter():
        if any(key.lower().startswith('on') for key in node.attrib):
            failures.append({'code':'HTML_EVENT_HANDLER_NOT_ALLOWED','tag':node.tag})
    protected={str((project/src['asset']).resolve()):lang for lang,src in contract['font_sources'].items()}
    def decorate_css(css,base):
        def on_font_face(m):
            face=m.group(0);fm=FONT_NAME_CSS.search(face)
            if not fm:return face
            family=fm.group(1).strip().strip('\"\'')
            def on_url(um):
                url=um.group(2).strip()
                u=urlparse(url)
                if u.scheme or url.startswith('//'):
                    failures.append({'code':'NONLOCAL_FONT_CSS_URL', 'font':family});return um.group(0)
                source=(base/unquote(u.path)).resolve()
                seen.append({'family':family,'source':str(source)})
                lang=protected.get(str(source))
                if lang is None or contract['font_sources'][lang]['family'].lower()!=family.lower():
                    return um.group(0)
                if source.stat().st_size > 24*1024*1024:
                    failures.append({'code':'FONT_SOURCE_TOO_LARGE', 'font':family});return um.group(0)
                blob=source.read_bytes()
                # Recheck bytes at use time: no mutable file swap between admission and render.
                if hashlib.sha256(blob).hexdigest()!=contract['font_sources'][lang]['sha256']:
                    failures.append({'code':'FONT_CHANGED_DURING_PROBE', 'font':family})
                    return um.group(0)
                # Only byte-identical pinned assets were admitted above.
                return 'url("data:font/woff2;base64,'+base64.b64encode(blob).decode('ascii')+'")'
            return CSS_URL.sub(on_url,face)
        return FONT_FACE_CSS.sub(on_font_face,css)

    for link in list(doc.xpath('//link')):
        if 'stylesheet' not in link.get('rel','').lower().split():continue
        href=(link.get('href') or '').strip()
        parsed=urlparse(href)
        if parsed.scheme or href.startswith('//'):
            failures.append({'code':'REMOTE_OR_UNSUPPORTED_STYLESHEET', 'href':href});continue
        path=(html.parent/unquote(parsed.path)).resolve()
        if not path.is_relative_to(project) or not path.is_file():
            failures.append({'code':'STYLESHEET_MISSING_OR_OUTSIDE_PROJECT', 'href':href});continue
        css=path.read_text(encoding='utf-8')
        if '@import' in css.lower():failures.append({'code':'CSS_IMPORT_NEEDS_EXPLICIT_RESOLUTION','href':href})
        style=etree.Element('style');style.set('data-quality-compiled','1');style.text=decorate_css(css,path.parent)
        link.addprevious(style);link.getparent().remove(link)
    for style in doc.xpath('//style'):
        # Newly generated style from a linked file is already compiled.
        if style.text and style.get('data-quality-compiled')!='1':
            if '@import' in style.text.lower():failures.append({'code':'CSS_IMPORT_NEEDS_EXPLICIT_RESOLUTION','href':'inline'})
            style.text=decorate_css(style.text,html.parent)
    return LH.tostring(doc,encoding='unicode',method='html'), seen, failures


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def first_family(css):
    return (str(css).split(',')[0].strip().strip('"\'').replace(' Variable','')).lower()


def physical_family_match(name, lang):
    normalized=' '.join(str(name or '').lower().split())
    if not normalized.startswith('pretendard'):
        return False
    if lang=='ja':
        return 'jp' in normalized.split() or 'japanese' in normalized
    return 'jp' not in normalized.split() and 'japanese' not in normalized


def audit(html, contract, project, *, browser_path=None):
    """Inspect every visible CJK text node; deliberately never return VERIFIED."""
    from playwright.sync_api import sync_playwright
    html=Path(html).resolve();project=Path(project).resolve()
    issues=[];unknown=[];examples=[];faces=[];browser_version=None
    def issue(code,**kv):issues.append(dict(code=code,**kv))
    if not html.is_file() or not html.is_relative_to(project):
        issue('HTML_OUTSIDE_PROJECT_OR_MISSING')
        return {'status':'BLOCKED','blocking':issues,'unverified':unknown}
    if contract.get('mode')!='NEW_DOCUMENT' or not contract.get('font_sources'):
        issue('INVALID_NEW_DOCUMENT_CONTRACT')
        return {'status':'BLOCKED','blocking':issues,'unverified':unknown}
    from quality_floor import _valid_contract
    if not _valid_contract(contract):
        issue('CONTRACT_CHECKSUM_INVALID')
        return {'status':'BLOCKED','blocking':issues,'unverified':unknown}
    for lang,src in contract['font_sources'].items():
        if lang not in FAMILIES or src.get('family')!=FAMILIES[lang]:issue('UNSUPPORTED_FONT_POLICY',language=lang);continue
        path=(project/src.get('asset','')).resolve()
        if not path.is_relative_to(project) or not path.is_file() or sha(path)!=src.get('sha256'):
            issue('LOCKED_FONT_SOURCE_CHANGED',language=lang)
    if issues:
        return {'status':'BLOCKED','blocking':issues,'unverified':unknown}
    rendered_html, font_sources_in_css, preparation_failures = _prepare_font_probe_html(html, project, contract)
    for item in preparation_failures:issue(**item)
    for lang,src in contract['font_sources'].items():
        expected=(project/src['asset']).resolve()
        matching=[x for x in font_sources_in_css if x['family'].lower()==src['family'].lower()]
        if not matching:
            issue('FONT_FACE_DECLARATION_MISSING', language=lang)
        elif any(x['source']!=str(expected) for x in matching):
            issue('FONT_FACE_SOURCE_NOT_LOCKED_ASSET', language=lang)
    if issues:
        return {'status':'BLOCKED','blocking':issues,'unverified':unknown,'font_face_sources':font_sources_in_css}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=browser_path or None,args=['--no-sandbox'])
        try:
            browser_version=browser.version
            page=browser.new_page()
            # No arbitrary network or local file navigation in this verifier.
            page.route('**/*', lambda route: route.abort())
            failures=[]
            page.on('requestfailed',lambda req:failures.append(req.url) if req.resource_type in ('font','stylesheet') else None)
            page.set_content(rendered_html,wait_until='load')
            page.evaluate('document.fonts.ready')
            manifest=page.evaluate(JS)
            # Cloned glyph probes can trigger font loads beyond initial document.fonts.ready.
            try:
                page.wait_for_function('document.fonts.status === "loaded"', timeout=1500)
            except Exception:
                issue('FONT_LOADING_NEVER_SETTLED')
            # CDP font usage is populated after layout/paint, not merely font loading.
            page.evaluate('''async () => {
                document.body.getBoundingClientRect();
                await document.fonts.ready;
                await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            }''')
            if not manifest['pageCount']:issue('NO_PPTX_PAGE_ROOTS')
            for row in manifest['failures']:issue(**row)
            for u in failures:issue('BROWSER_RESOURCE_FAILED',url=u[:300])
            faces=font_sources_in_css
            client=page.context.new_cdp_session(page)
            client.send('DOM.enable');client.send('CSS.enable')
            root_id=client.send('DOM.getDocument',{'depth':-1})['root']['nodeId']
            if not manifest['samples']:issue('NO_VISIBLE_CJK_TEXT')
            for sample in manifest['samples']:
                lang=sample['lang'];expected=FAMILIES.get(lang)
                if not expected or lang not in contract['font_sources']:
                    issue('TEXT_LANGUAGE_NOT_LOCKED',page=sample['page'],lang=lang);continue
                if first_family(sample['computedFamily']) != expected.lower():
                    issue('COMPUTED_FONT_FAMILY_DRIFT',page=sample['page'],lang=lang,actual=sample['computedFamily'],expected=expected,text=sample['text'])
                selector=f'[data-demo-quality-font-probe="{sample["id"]}"]'
                node=client.send('DOM.querySelector',{'nodeId':root_id,'selector':selector})['nodeId']
                if not node:issue('FONT_PROBE_UNRESOLVED',page=sample['page']);continue
                used=client.send('CSS.getPlatformFontsForNode',{'nodeId':node})['fonts']
                evidence=[{'family':item['familyName'],'custom':item['isCustomFont'],'glyphCount':item['glyphCount']} for item in used if item['glyphCount']>0]
                examples.append({**sample,'platformFonts':evidence})
                # Pure CJK text isolated in a fresh DOM node: a fallback glyph is visible here.
                if not evidence or not all(item['custom'] and physical_family_match(item['family'],lang) for item in evidence):
                    issue('ACTUAL_GLYPH_FONT_SUBSTITUTED',page=sample['page'],lang=lang,text=sample['text'],platformFonts=evidence)
        finally:
            browser.close()
    unknown=['NATIVE_POWERPOINT_RENDER_NOT_CHECKED','PPTX_EMBEDDED_FONT_NOT_CHECKED','VISUAL_LAYOUT_NOT_CERTIFIED']
    return {'schema_version':'demo-html-font-audit/0.1','status':'BLOCKED' if issues else 'REVIEW_CANDIDATE',
            'blocking':issues,'unverified':unknown,'html_sha256':sha(html),
            'contract_sha256':contract['contract_sha256'],
            'browser':{'name':'Chromium','version':browser_version,'executable':str(browser_path or 'playwright-default')},
            'pages':manifest['pageCount'],'font_face_rules':faces,'samples':examples,
            'claims':{'html_cjk_actual_font_observed':True,'ready_for_delivery':False,'native_powerpoint_verified':False}}


def inspect_html(html_path, browser_path=None):
    """Return None outside a locked DEMO project, preventing brand bleed into generic HTML."""
    from document_quality_script_runs import find_contract
    root,path=find_contract(html_path)
    if path is None:
        return None
    c=json.loads(path.read_text(encoding='utf-8'))
    return audit(html_path,c,root,browser_path=browser_path)


def cli():
    p=argparse.ArgumentParser()
    p.add_argument('--project',type=Path,required=True)
    p.add_argument('--html',type=Path,required=True)
    p.add_argument('--browser-path')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    from document_quality_script_runs import find_contract
    root,contract_path=find_contract(a.html)
    if not contract_path or root.resolve()!=a.project.resolve():
        result={'status':'BLOCKED','blocking':[{'code':'CONTRACT_MISSING_OR_WRONG_PROJECT'}]}
    else:
        result=audit(a.html,json.loads(contract_path.read_text()),root,browser_path=a.browser_path)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in ('status','blocking','unverified','pages')},ensure_ascii=False))
    return 2 if result['status']=='BLOCKED' else 1

if __name__=='__main__':raise SystemExit(cli())
