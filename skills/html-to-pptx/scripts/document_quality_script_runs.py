"""Quality Floor P1.2: script-aware measured-run normalization before font resolution.

Only NEW_DOCUMENT projects with a valid, source-bound quality-contract.json are modified.
This module does not establish a font's glyph fidelity or grant VERIFIED status.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

LANGS = {"ja": ("Pretendard JP", "ja-JP"), "ko": ("Pretendard", "ko-KR")}
KANA = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
HANGUL = re.compile(r"[\u1100-\u11ff\u3130-\u318f\uac00-\ud7af]")
HAN = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")


def _lang(value):
    return str(value or "").lower().replace("_", "-").split("-")[0]


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _checksum(doc):
    return hashlib.sha256(json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def find_contract(html_path):
    path = Path(html_path).resolve()
    for root in list(path.parents)[:5]:
        contract_path = root / "content" / "quality-contract.json"
        if contract_path.exists():
            return root, contract_path
    return None, None


def _valid_contract(contract):
    if contract.get('schema_version') != 'demo-quality-floor/0.1' or contract.get('mode') != 'NEW_DOCUMENT':
        return False
    body = {k:v for k,v in contract.items() if k != 'contract_sha256'}
    return _checksum(body) == contract.get('contract_sha256')


def _assert_sources(root, contract):
    for lang, source in contract.get('font_sources', {}).items():
        if lang not in LANGS or source.get('family') != LANGS[lang][0]:
            raise ValueError('Unrecognized protected font policy for '+str(lang))
        rel = source.get('asset', '')
        if not isinstance(rel, str) or '\\' in rel or not rel.startswith('html/assets/'):
            raise ValueError('Unsafe font source path')
        path = (root / rel).resolve()
        if not path.is_relative_to(root) or not path.is_file() or _sha(path) != source.get('sha256'):
            raise ValueError('Locked font source missing or modified: '+lang)


def _char_script(ch):
    if KANA.fullmatch(ch): return 'ja'
    if HANGUL.fullmatch(ch): return 'ko'
    if HAN.fullmatch(ch): return 'han'
    return None


def _explicit_fonts(text, source_lang):
    scripts = {x for c in text if (x := _char_script(c)) in ('ja','ko')}
    hint = _lang(source_lang)
    if 'han' in [_char_script(c) for c in text]:
        # Han is shared across Japanese/Korean; the explicit language, not the glyph,
        # determines its identity when the run contains no adjacent strong script.
        if hint not in LANGS and not scripts:
            raise ValueError('Ambiguous Han text requires an explicit ja/ko language')
    return scripts


def split_run(run: dict, default_language: str, protected_languages: set[str]) -> tuple[list[dict],bool]:
    """Preserve every text byte and style except fontFamily/lang where script needs correction.

    Not a generic Unicode language detector. Kana -> ja; Hangul -> ko; Han ->
    explicit declared language, or nearest strong script; mixed Han with no
    reliable language origin is rejected rather than silently classified.
    """
    if run.get('linebreak') or not run.get('text'):
        return [run], False
    text = str(run['text'])
    hint = _lang(run.get('lang'))
    default = _lang(default_language)
    if hint not in LANGS and default not in LANGS:
        raise ValueError('NEW_DOCUMENT text requires a ja/ko default language')
    strong = [_char_script(ch) for ch in text]
    present = {x for x in strong if x in LANGS}
    if not present and not any(s == 'han' for s in strong):
        return [run], False
    if hint in LANGS and hint not in protected_languages:
        raise ValueError('Declared language is not in the locked font policy: '+hint)
    if not present:
        selected = hint if hint in LANGS else default
        if selected not in protected_languages:
            raise ValueError('Missing font policy for '+selected)
        target = LANGS[selected]
        family = str(run.get('fontFamily','')).split(',')[0].strip().strip('"\'')
        if re.fullmatch(re.escape(target[0]) + r'(?: [1-9]00)?', family, re.I) and hint == selected:
            return [run], False
        raise ValueError('Font policy drift in unmixed CJK run: '+family+' expected '+target[0])

    # A declared language tag anchors Han. If absent, assign Han to the
    # nearest explicit Kana/Hangul script within the same phrase. Neutral spans
    # (Latin, digits, punctuation) are carried by the preceding script.
    base = hint if hint in LANGS else default
    labels = []
    for idx, (ch, cls) in enumerate(zip(text,strong)):
        if cls in LANGS:
            labels.append(cls)
        elif cls == 'han':
            next_strong = next((strong[j] for j in range(idx+1,len(text)) if strong[j] in LANGS),None)
            prev_strong = next((strong[j] for j in range(idx-1,-1,-1) if strong[j] in LANGS),None)
            # Use preceding real script within a mixed run; leading ideographs
            # use the run's explicit source language, then the nearest script.
            labels.append(prev_strong or (hint if hint in LANGS else next_strong) or next_strong or base)
        else:
            labels.append(None)
    for i in range(len(labels)):
        if labels[i] is None:
            prev = next((labels[j] for j in range(i-1,-1,-1) if labels[j] in LANGS),None)
            nxt = next((labels[j] for j in range(i+1,len(labels)) if labels[j] in LANGS),None)
            labels[i] = prev or nxt or base
    for lang in set(labels):
        if lang not in protected_languages:
            raise ValueError('Text requires font not locked in project policy: '+lang)

    segments=[]
    start=0
    for i in range(1,len(text)+1):
        if i==len(text) or labels[i] != labels[start]:
            lang = labels[start]
            seg_text = text[start:i]
            new = dict(run)
            new['text'] = seg_text
            new['fontFamily'] = f'"{LANGS[lang][0]}"'
            new['lang'] = LANGS[lang][1]
            new['qualityFloorNormalized'] = True
            segments.append(new)
            start=i
    if ''.join(s['text'] for s in segments) != text:
        raise AssertionError('Text changed during language segmentation')
    # For a single, correctly styled run, keep its original metadata.
    if len(segments)==1:
        orig_font = str(run.get('fontFamily','')).split(',')[0].strip().strip('"\'')
        script=labels[0]
        if re.fullmatch(re.escape(LANGS[script][0])+r'(?: [1-9]00)?',orig_font,re.I) and hint==script:
            return [run], False
        raise ValueError('Font policy drift in unmixed CJK run: '+orig_font+' expected '+LANGS[script][0])
    return segments, True


def normalize_measurement_gs_runs(measurement: dict, html_path) -> dict:
    """Apply only in a project with a verified NEW_DOCUMENT quality contract.

    Must run BEFORE collect_requested_fonts, local font registration and PPTX
    assembly. This repairs incorrect measured run family metadata, but the
    HTML browser rendering remains a separate QA responsibility.
    """
    root, path = find_contract(html_path)
    if path is None:
        return {'scope':'not_a_locked_new_gs_project','runs':0,'normalized':0,'mutated':False}
    contract = json.loads(path.read_text(encoding='utf-8'))
    if not _valid_contract(contract):
        raise ValueError('Invalid or tampered DEMO quality contract')
    _assert_sources(root,contract)
    policy = set(contract['font_sources'])
    default=contract['document']['language']
    # Transactional preparation; never partially mutate the measured object if
    # any run needs a missing language/font.
    edits=[]
    affected=0
    checked=0
    for slide in measurement.get('slides',[]):
        for rec in slide.get('records',[]):
            if rec.get('kind') != 'text':
                continue
            original=rec.get('runs') or []
            normalized=[]
            for run in original:
                checked+=1
                parts,changed=split_run(run,default,policy)
                normalized.extend(parts)
                affected+=int(changed)
            edits.append((rec,normalized))
    for rec,parts in edits:rec['runs']=parts
    return {'scope':'NEW_DOCUMENT','runs':checked,'normalized':affected,'mutated':bool(affected),
            'contract_sha256':contract['contract_sha256'],
            'warning':'Measured text and browser glyph/font parity require a separate audit when mutated' if affected else None}
