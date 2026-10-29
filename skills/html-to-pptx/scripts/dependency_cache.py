"""Content fingerprints for safe measured-page reuse; missing evidence means full measure."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

def capture(html_path: Path, page) -> dict:
    observed = page.evaluate("""() => {
      const slides = [...document.querySelectorAll('[data-pptx-slide]')];
      if (!slides.length) return {supported:false};
      const copy = document.documentElement.cloneNode(true);
      copy.querySelectorAll('[data-pptx-slide]').forEach((s,i) => {
        const p=document.createElement('template');p.setAttribute('data-cache-page',String(i+1));s.replaceWith(p);
      });
      return {supported:true,global:copy.outerHTML,
        pages:slides.map(s=>s.outerHTML),
        firstFonts:[...new Set(slides.flatMap(s=>[...s.querySelectorAll('*')].filter(e=>
          [...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())).map(e=>
          getComputedStyle(e).fontFamily.split(',')[0].replace(/["']/g,'').trim().toLowerCase())))],
        loadedFaces:[...document.fonts].filter(f=>f.status==='loaded').map(f=>
          f.family.replace(/["']/g,'').trim().toLowerCase()),
        urls:[...new Set([...performance.getEntriesByType('resource').map(r=>r.name),
          ...[...document.querySelectorAll('[src],link[href]')].map(e=>e.src||e.href)])],
        canvas:slides.map(s=>[s.getBoundingClientRect().width,s.getBoundingClientRect().height]),
        fonts:document.fonts.status,snapshotScale:window.devicePixelRatio};
    }""")
    if not observed.get("supported"):
        return {"version": 1, "reusable": False, "reason": "Explicit page markers missing"}
    files = {}
    unresolved = []
    # File resource timing may omit nested stylesheets/fonts. Reuse the
    # converter's bounded local CSS resolver, not the timing list alone.
    from font_resolver import _local_style_sources, _parse_local_font_faces
    css_dependencies = {}
    css_sources = _local_style_sources(html_path, css_dependencies)
    local_faces = _parse_local_font_faces(html_path)
    unresolved.extend(css_dependencies.get('unresolved', []))
    css_resource_paths = []
    css_urls = re.compile(r'''url\(\s*(?:"([^"]+)"|'([^']+)'|([^\s)]+))\s*\)''', re.I)
    for css, base in css_sources:
        if re.search(r'\bimage-set\s*\(', css, re.I):
            unresolved.append('CSS image-set dependency not certified')
        for groups in css_urls.findall(css):
            url = next(value for value in groups if value)
            parsed = urlparse(url)
            if parsed.scheme == 'data' or url.startswith('#'):
                continue
            if parsed.scheme or parsed.netloc or '\\' in url:
                unresolved.append(url)
                continue
            css_resource_paths.append((base / unquote(parsed.path)).resolve())
    for path in [*css_dependencies.get('files', []), *css_resource_paths, *(f['path'] for f in local_faces.values())]:
        if not path.is_file():
            unresolved.append(str(path))
        else:
            files[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    for url in observed["urls"]:
        parsed = urlparse(url)
        if parsed.scheme == "data" or not url:
            continue
        if parsed.scheme != "file" or parsed.netloc not in {"", "localhost"}:
            unresolved.append(url)
            continue
        path = Path(url2pathname(unquote(parsed.path))).resolve()
        if not path.is_file():
            unresolved.append(url)
        else:
            files[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    implementation = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in Path(__file__).parent.glob("*.py")}
    implementation["convert.py"] = hashlib.sha256(Path(__file__).parents[1].joinpath("convert.py").read_bytes()).hexdigest()
    try:
        engine = page.context.browser.version
    except Exception:
        engine = None
    verified_fonts = set(observed.get("loadedFaces", [])) & set(local_faces)
    font_proof = set(observed.get("firstFonts", [])) <= verified_fonts
    return {"version":5, "reusable":not unresolved and bool(engine) and observed["fonts"]=="loaded" and font_proof,
            "global":digest(observed["global"]), "pages":[digest(p) for p in observed["pages"]],
            "files":files, "canvas":observed["canvas"], "implementation":implementation,
            "engine":engine, "snapshot_scale":observed.get('snapshotScale',1), "font_proof":font_proof, "unverified_fonts":sorted(set(observed.get("firstFonts", []))-verified_fonts), "unresolved":unresolved}

def can_reuse(prior: dict, current: dict, selected: set[int]) -> tuple[bool,str]:
    if not prior.get("reusable") or not current.get("reusable"):
        return False,"Unverified/remote dependencies or missing previous fingerprint"
    for key in ("version","global","files","canvas","implementation","engine","snapshot_scale"):
        if prior.get(key) != current.get(key):
            return False,"Global dependency changed: "+key
    old, new = prior.get("pages",[]), current.get("pages",[])
    if len(old) != len(new) or not new:
        return False,"Page topology changed"
    if any(i<1 or i>len(new) for i in selected):
        return False,"Requested page scope outside current topology"
    changed = {i+1 for i,(a,b) in enumerate(zip(old,new)) if a!=b}
    if not changed <= selected:
        return False,"Changed page outside requested scope"
    return True,"Unselected pages and global dependencies unchanged"
