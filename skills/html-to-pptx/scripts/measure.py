"""measure.py — 用浏览器实测 HTML 中所有 slide 的可见元素，输出 measurement JSON。

Usage:
    python measure.py <html_path> <out_json> [slide_index]
    - 不传 slide_index：抽取全部 slide，输出 { "slides": [ {slide:..., records:[...]}, ... ] }
    - 传 slide_index：抽取单页，输出 { "slide":..., "records":[...] }（兼容旧 API）

约定：
- 视口跟随 HTML 页尺寸；没有尺寸信息时回退 A4 794x1123
- slide 元素由 adapters.DISCOVER_JS 启发式发现（用户显式 `[data-pptx-slide]` 优先，
  否则按"同 tag 兄弟 + 至少一个 ≥50% viewport"启发），slide_index 从 0 开始对应该数组
"""
import contextlib
import hashlib
import io
import json
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

from PIL import Image

from playwright.sync_api import sync_playwright

from _js_snippets import DECO_HELPERS
from canvas_geometry import checked_canvas, uniform_canvas

VIEWPORT = {"width": 794, "height": 1123}

# 在浏览器上下文里执行：抽取当前被 adapter 标记的 slide 的所有可视绘制单元
# 约定：adapter 的 activate_js 必须给目标 slide 设置 data-pptx-target 属性
# DECO_HELPERS 注入 isNonTranslateTransform / isClippingContainerWithTransformedChildren /
# hasPseudoDecoration / hasComplexDecoration 四个工具；measure 与 preflight 共享，
# 避免两边漂移（修在 _js_snippets.py 单点）。
EXTRACT_JS = r"""
(slideIndex) => {
  const slide = document.querySelector('[data-pptx-target]');
  if (!slide) return { error: 'no slide tagged with data-pptx-target' };

  // 把目标 slide 滚动到视口内（容器使用 scroll-snap）
  slide.scrollIntoView({block:'start', inline:'start', behavior:'instant'});

  // 强制等一帧让 layout 稳定（同步：DOM 读取已经触发回流）
  const slideRect = slide.getBoundingClientRect();

  // 我们要抽：
  // 1) text leaves（含 textContent 的最深节点，且没有可见子文本节点冲突）
  // 2) <img>
  // 3) <svg>（整体序列化）
  // 4) 装饰节点（有 border / 非透明背景 / 非默认）

  const css = (el, prop) => getComputedStyle(el).getPropertyValue(prop);
  // Preserve the source's actual language, including a nearer lang="" which
  // intentionally clears inheritance. Script/CJK detection is font selection,
  // not evidence that Japanese or Korean copy is Chinese.
  const sourceLanguage = (el) => el?.closest('[lang]')?.getAttribute('lang') ?? null;
  const rasterVisibleRect = (el) => {
    const original=el.getBoundingClientRect();
    let left=original.left,top=original.top,right=original.right,bottom=original.bottom;
    for(let owner=el.parentElement;owner;owner=owner.parentElement){
      const s=getComputedStyle(owner),r=owner.getBoundingClientRect();
      if(['hidden','clip','scroll','auto'].includes(s.overflowX)){
        left=Math.max(left,r.left+parseFloat(s.borderLeftWidth||0));
        right=Math.min(right,r.right-parseFloat(s.borderRightWidth||0));
      }
      if(['hidden','clip','scroll','auto'].includes(s.overflowY)){
        top=Math.max(top,r.top+parseFloat(s.borderTopWidth||0));
        bottom=Math.min(bottom,r.bottom-parseFloat(s.borderBottomWidth||0));
      }
      // The adapter fixes the slide as its own viewport. Ancestors above it
      // are reader/scroll UI, not clipping parents of its painted contents.
      if(owner===slide)break;
    }
    return {left,top,width:Math.max(0,right-left),height:Math.max(0,bottom-top)};
  };
  const plainImageOriginal = (el) => {
    const s=getComputedStyle(el), r=el.getBoundingClientRect();
    const reject=reason=>({eligible:false,reason});
    if (!el.complete || !el.naturalWidth || !el.naturalHeight) return reject('image_not_ready');
    // Cropped/full-scene art keeps the rendered snapshot path. A plain image
    // must display its complete original at an unchanged aspect ratio.
    if (!['fill','contain'].includes(s.objectFit)) return reject('object_fit_requires_render');
    if (Math.abs(r.height-r.width*el.naturalHeight/el.naturalWidth)>0.5) return reject('aspect_or_letterbox');
    if (['Top','Right','Bottom','Left'].some(side=>parseFloat(s['padding'+side])>0 || parseFloat(s['border'+side+'Width'])>0)) return reject('padding_or_border');
    if (s.backgroundImage!=='none' || !['rgba(0, 0, 0, 0)','transparent'].includes(s.backgroundColor) || s.boxShadow!=='none') return reject('painted_decoration');
    if (s.borderRadius.split(/[ /]+/).some(v=>parseFloat(v)>0)) return reject('rounded_image');
    for(let owner=el;owner;owner=owner.parentElement){
      const cs=getComputedStyle(owner);
      if(cs.transform!=='none' || cs.rotate!=='none' || cs.scale!=='none' || cs.translate!=='none' || Math.abs(parseFloat(cs.zoom||'1')-1)>1e-6) return reject('transformed');
      if(parseFloat(cs.opacity)<1 || cs.filter!=='none' || cs.backdropFilter!=='none' || cs.mixBlendMode!=='normal') return reject('composited');
      if(cs.clipPath!=='none' || !['auto','none'].includes(cs.clip) || cs.maskImage!=='none') return reject('masked');
      const clippedX=['hidden','clip','scroll','auto'].includes(cs.overflowX), clippedY=['hidden','clip','scroll','auto'].includes(cs.overflowY);
      if(owner!==el && (clippedX || clippedY)){
        if(cs.borderRadius.split(/[ /]+/).some(v=>parseFloat(v)>0)) return reject('rounded_clip_ancestor');
        const ar=owner.getBoundingClientRect();
        const left=ar.left+parseFloat(cs.borderLeftWidth||'0'),top=ar.top+parseFloat(cs.borderTopWidth||'0');
        const right=ar.right-parseFloat(cs.borderRightWidth||'0'),bottom=ar.bottom-parseFloat(cs.borderBottomWidth||'0');
        if((clippedX && (r.left<left-.25 || r.right>right+.25)) || (clippedY && (r.top<top-.25 || r.bottom>bottom+.25))) return reject('ancestor_crop');
      }
    }
    return {eligible:true,reason:'plain_complete_local_raster_candidate'};
  };
  const isHidden = (el) => {
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || parseFloat(s.opacity) === 0) return true;
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return true;
    return false;
  };

""" + DECO_HELPERS + r"""

  // 累计 transform 旋转角度（度数；含祖先节点的 rotate）
  // 用 matrix(a, b, ...) 反解 atan2(b, a)。仅处理纯旋转分量；
  // skew / 非均匀 scale 暂不还原（影响极少数模板）
  const cumulativeRotation = (el) => {
    let total = 0;
    let cur = el;
    while (cur && cur !== document.body) {
      const t = getComputedStyle(cur).transform;
      if (t && t !== 'none') {
        // matrix(a, b, c, d, e, f) 或 matrix3d(...)
        const m = t.match(/matrix(?:3d)?\(([^)]+)\)/);
        if (m) {
          const v = m[1].split(',').map(parseFloat);
          // 取 a, b（2D 矩阵） 或 m11, m12（3D 矩阵）
          const a = v[0], b = v[1];
          total += Math.atan2(b, a) * 180 / Math.PI;
        }
      }
      cur = cur.parentElement;
    }
    return total;
  };

  const records = [];

  // Mark calendar descendants at runtime so the assembler can use flat,
  // pixel-aligned border strips instead of PowerPoint connector lines. This
  // does not alter the source HTML or its Chromium rendering.
  slide.querySelectorAll('.calendar-code, .calendar-code *').forEach((el) => {
    el.classList.add('__pptx_calendar_item');
  });
  const calendarSnapshotRoot = slide.querySelector('.calendar-code');
  if (calendarSnapshotRoot) calendarSnapshotRoot.classList.add('__pptx_calendar_snapshot');
  let nodeId = 0;

  // 标记一个节点是否为 "text leaf"：包含 textContent 但所有子节点要么是文本节点，要么是 inline 装饰（em/span 等没有进一步分割结构的）
  // 简化：只要这个元素的 children 中没有任何 block 级元素，就算 text leaf。
  // 漏 ASIDE 这类块元素会让父容器的 inline-group 误把整个 <aside>...</aside> 当 inline 吞掉，
  // 父 walk 末的 block-recursion 也不会下钻 aside，aside 子树全部不发独立 record。
  // HTML5 sectioning + grouping content 全列：ASIDE / BLOCKQUOTE / DL / DT / DD / FORM / ADDRESS / HR / DETAILS / SUMMARY。
  const BLOCK_TAGS = new Set(['DIV','SECTION','ARTICLE','ASIDE','HEADER','FOOTER','MAIN','NAV',
                              'P','H1','H2','H3','H4','H5','H6','UL','OL','LI',
                              'FIGURE','FIGCAPTION','TABLE','THEAD','TBODY','TFOOT',
                              'TR','TH','TD','CAPTION','COLGROUP','COL','PRE','BLOCKQUOTE',
                              'DL','DT','DD','FORM','ADDRESS','HR','DETAILS','SUMMARY',
                              'SVG','IMG','CANVAS','VIDEO']);
  const isLayoutBlock = node => node && node.nodeType === 1 &&
    (BLOCK_TAGS.has(node.tagName.toUpperCase()) ||
     ['block','flow-root','flex','grid','list-item','table','table-row','table-cell'].includes(getComputedStyle(node).display));
  const isAtomicInline = (node) => {
    if (!node || node.nodeType !== 1) return false;
    if (isLayoutBlock(node)) return false;
    const s = getComputedStyle(node);
    const bg = s.backgroundColor;
    const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
    const hasBorder = parseFloat(s.borderTopWidth) > 0 || parseFloat(s.borderBottomWidth) > 0 ||
                      parseFloat(s.borderLeftWidth) > 0 || parseFloat(s.borderRightWidth) > 0;
    const plainProtectedPhrase=node.tagName==='SPAN' && s.display==='inline-block' &&
      s.whiteSpace==='nowrap' && s.position==='static' && !hasBg && !hasBorder &&
      s.boxShadow==='none' && s.transform==='none' &&
      ['paddingTop','paddingRight','paddingBottom','paddingLeft','marginTop','marginRight','marginBottom','marginLeft'].every(k=>(parseFloat(s[k])||0)===0);
    if (plainProtectedPhrase && node.closest('[data-pptx-text-flow]')?.getAttribute('data-pptx-text-flow')==='natural')return false;
    return s.position === 'absolute' || s.position === 'fixed' ||
           s.display === 'inline-block' || s.display === 'inline-flex' ||
           hasBg || hasBorder;
  };

  const decoFromStyle = (s, hasBg, bg, borderTop, borderBottom, borderLeft, borderRight) => ({
    hasBg, bg, borderTop, borderBottom, borderLeft, borderRight,
    borderColor: s.borderTopColor,
    borderTopColor: s.borderTopColor,
    borderBottomColor: s.borderBottomColor,
    borderLeftColor: s.borderLeftColor,
    borderRightColor: s.borderRightColor,
    borderTopWidth: parseFloat(s.borderTopWidth) || 0,
    borderBottomWidth: parseFloat(s.borderBottomWidth) || 0,
    borderLeftWidth: parseFloat(s.borderLeftWidth) || 0,
    borderRightWidth: parseFloat(s.borderRightWidth) || 0,
    borderRadius: s.borderTopLeftRadius,
  });
  // svg / img 等元素即便不是 HTML 块级，也要阻断 text-leaf 判定，
  // 否则容器里同时存在 <svg> 与 <span> 文本时,会被错误地当作纯文本叶子整体吞掉。
  // flex/grid 容器 + spacing 类 justify-content + 2+ 子 = "布局拉开"模式：
  // 子节点在容器内被推到两端 / 等距分布，单 leaf BCR 会跨整个空白区，
  // OOXML 单 textbox 表达不了"AGENDA 左对齐 + 时间 右对齐"。
  // 必须每个子节点独立 record 各带自己 BCR。
  const SPACING_JUSTIFY = new Set(['space-between','space-around','space-evenly',
                                    'end','flex-end','right']);
  const isFlexSpacingContainer = (el) => {
    if (!el || el.nodeType !== 1 || el.children.length < 2) return false;
    const s = getComputedStyle(el);
    const isFG = s.display === 'flex' || s.display === 'inline-flex' ||
                 s.display === 'grid' || s.display === 'inline-grid';
    return isFG && (SPACING_JUSTIFY.has(s.justifyContent) || s.display.includes('grid') ||
      s.flexDirection.startsWith('column') || parseFloat(s.columnGap)>0 || parseFloat(s.rowGap)>0);
  };
  const isTextLeaf = (el) => {
    if (!el.textContent || !el.textContent.trim()) return false;
    if (isFlexSpacingContainer(el)) return false;
    for (const ch of el.children) {
      if (isLayoutBlock(ch)) return false;
      if (isAtomicInline(ch)) return false;
    }
    return true;
  };

  // ::before / ::after 伪元素的 string content 抽取。
  // 伪元素不在 DOM 里（childNodes 找不到），但 getComputedStyle(el, '::before').content
  // 能拿到。只收 string literal（最常见：装饰前缀 ↑↓、列表 marker、徽章"NEW"、引号）。
  // 跳过 url() / attr() / counter() / open-quote 等复杂值——它们极少作为"该可编辑的文字"使用。
  // 几何不用调整：浏览器把伪元素文字算在父 BCR 里，textbox 已经包了那段宽度。
  const extractPseudoRun = (el, pseudo) => {
    const s = getComputedStyle(el, pseudo);
    const c = s.content;
    if (!c || c === 'none' || c === 'normal') return null;
    const m = c.match(/^["'](.*)["']$/);
    if (!m || !m[1]) return null;
    return {
      text: m[1],
      lang: sourceLanguage(el),
      fontFamily: s.fontFamily,
      fontSize: parseFloat(s.fontSize),
      fontWeight: s.fontWeight,
      fontStyle: s.fontStyle,
      color: s.color,
      letterSpacing: s.letterSpacing,
      textDecoration: s.textDecorationLine,
      textShadow: s.textShadow,
      textTransform: s.textTransform,
    };
  };

  const isTextOnlyPseudoMarker = (el, pseudo) => {
    if (!extractPseudoRun(el, pseudo)) return false;
    const ps = getComputedStyle(el, pseudo);
    if (ps.display === 'none' || ps.visibility === 'hidden') return false;
    if (parseFloat(ps.opacity || '1') < 0.999) return false;
    if (ps.position === 'absolute' || ps.position === 'fixed') return false;
    if (ps.backgroundImage && ps.backgroundImage !== 'none') return false;
    const bg = ps.backgroundColor;
    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return false;
    if (parseFloat(ps.borderTopWidth) > 0 || parseFloat(ps.borderBottomWidth) > 0 ||
        parseFloat(ps.borderLeftWidth) > 0 || parseFloat(ps.borderRightWidth) > 0) return false;
    if (ps.outlineStyle && ps.outlineStyle !== 'none' && parseFloat(ps.outlineWidth) > 0) return false;
    if (ps.boxShadow && ps.boxShadow !== 'none') return false;
    if (ps.filter && ps.filter !== 'none') return false;
    if (ps.mixBlendMode && ps.mixBlendMode !== 'normal') return false;
    if (ps.transform && ps.transform !== 'none') return false;
    if (ps.textShadow && ps.textShadow !== 'none') return false;
    return true;
  };

  const hasNonPseudoComplexDecoration = (s, el) => {
    if (s.backgroundImage && s.backgroundImage !== 'none') return true;
    if (s.boxShadow && s.boxShadow !== 'none') return true;
    if (s.outlineStyle && s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0) return true;
    if (isClippingContainerWithTransformedChildren(s, el)) return true;
    if (s.backdropFilter && s.backdropFilter !== 'none') return true;
    if (hasNontrivialFilter(s.filter)) return true;
    if (s.mixBlendMode && s.mixBlendMode !== 'normal') return true;
    if (isUnrepresentableTransform(s.transform)) return true;
    const rounded = [s.borderTopLeftRadius, s.borderTopRightRadius,
                     s.borderBottomRightRadius, s.borderBottomLeftRadius]
      .some(v => parseFloat(v) > 0);
    const borderColors = [s.borderTopColor, s.borderRightColor,
                          s.borderBottomColor, s.borderLeftColor];
    const hasTransparentBorder = borderColors.some(v =>
      v === 'transparent' || v === 'rgba(0, 0, 0, 0)');
    const hasVisibleBorder = borderColors.some(v =>
      v !== 'transparent' && v !== 'rgba(0, 0, 0, 0)');
    if (rounded && hasTransparentBorder && hasVisibleBorder) return true;
    return false;
  };

  const textStyleFromComputed = (s) => ({
    color: s.color,
    fontFamily: s.fontFamily,
    fontSize: parseFloat(s.fontSize),
    fontWeight: s.fontWeight,
    fontStyle: s.fontStyle,
    lineHeight: s.lineHeight,
    letterSpacing: s.letterSpacing,
    textAlign: s.textAlign,
    textTransform: s.textTransform,
    opacity: s.opacity,
    paddingTop: parseFloat(s.paddingTop) || 0,
    paddingRight: parseFloat(s.paddingRight) || 0,
    paddingBottom: parseFloat(s.paddingBottom) || 0,
    paddingLeft: parseFloat(s.paddingLeft) || 0,
    display: s.display,
    alignItems: s.alignItems,
    justifyContent: s.justifyContent,
    writingMode: s.writingMode,
  });

  // 富文本 runs：把一个 text leaf 拆成多个 run，每个 run 携带自己的 computed style
  // 这样 <em> 等内嵌强调可以保留独立字体
  const extractRuns = (el, includePseudo = true) => {
    const runs = [];
    const walk = (n) => {
      if (n.nodeType === 3) {
        const text = n.nodeValue;
        if (!text) return;
        const parent = n.parentElement;
        const s = getComputedStyle(parent);
        // 行内上下标（<sup>/<sub>/vertical-align）：记录墨迹底边，
        // assemble 据此换算 OOXML baseline 偏移（否则上标掉回基线）
        const rng = document.createRange();
        rng.selectNodeContents(n);
        const rr = rng.getBoundingClientRect();
        runs.push({
          text,
          lang: sourceLanguage(parent),
          fontFamily: s.fontFamily,
          fontSize: parseFloat(s.fontSize),
          fontWeight: s.fontWeight,
          fontStyle: s.fontStyle,
          color: s.color,
          letterSpacing: s.letterSpacing,
          textDecoration: s.textDecorationLine,
          textShadow: s.textShadow,
          lineHeight: s.lineHeight,
          textTransform: s.textTransform,
          verticalAlign: s.verticalAlign,
          inkBottom: rr.height > 0 ? rr.bottom : null,
        });
      } else if (n.nodeType === 1) {
        // skip <br>: emit a soft break marker
        if (n.tagName === 'BR') {
          runs.push({ text: '\n', linebreak: true, breakSource: 'explicit' });
          return;
        }
        // display:none / visibility:hidden 的 inline 子树 HTML 里不可见，不进 runs
        if (isHidden(n)) return;
        const before = includePseudo ? extractPseudoRun(n, '::before') : null;
        if (before) runs.push(before);
        for (const ch of n.childNodes) walk(ch);
        const after = includePseudo ? extractPseudoRun(n, '::after') : null;
        if (after) runs.push(after);
      }
    };
    walk(el);
    return applyNaturalLineBreaks(el, runs, !includePseudo);
  };

  const sameRunStyle = (a, b) => {
    return a.lang === b.lang
      && a.fontFamily === b.fontFamily
      && a.fontSize === b.fontSize
      && a.fontWeight === b.fontWeight
      && a.fontStyle === b.fontStyle
      && a.color === b.color
      && a.letterSpacing === b.letterSpacing
      && a.textDecoration === b.textDecoration
      && a.textShadow === b.textShadow
      && a.textTransform === b.textTransform;
  };

  const pushStyledText = (runs, text, style) => {
    if (!text) return;
    const last = runs[runs.length - 1];
    if (last && !last.linebreak && sameRunStyle(last, style)) {
      last.text += text;
    } else {
      runs.push({ ...style, text });
    }
  };

  const applyNaturalLineBreaks = (el, originalRuns, ignorePseudo = false) => {
    // Preserve source paragraph semantics for new DEMO documents. Explicit BR
    // remains a soft break; legacy HTML retains measured-row compatibility.
    const policy = el.closest('[data-pptx-text-flow]')?.getAttribute('data-pptx-text-flow');
    if (policy === 'natural') return originalRuns.map(r => ({...r, naturalWrap: true}));
    if (!originalRuns.length || originalRuns.some(r => r.linebreak)) return originalRuns;
    // Pseudo text (common for list markers) is already folded into the parent
    // BCR, but has no DOM Range. Keep those records on the old path.
    if (!ignorePseudo && (extractPseudoRun(el, '::before') || extractPseudoRun(el, '::after'))) return originalRuns;

    const tokens = [];
    let splitTokenAcrossLines = false;
    const range = document.createRange();
    const collect = (n) => {
      if (n.nodeType === 3) {
        const raw = n.nodeValue || '';
        const parent = n.parentElement;
        if (!parent) return;
        const s = getComputedStyle(parent);
        const style = {
          lang: sourceLanguage(parent),
          fontFamily: s.fontFamily,
          fontSize: parseFloat(s.fontSize),
          fontWeight: s.fontWeight,
          fontStyle: s.fontStyle,
          color: s.color,
          letterSpacing: s.letterSpacing,
          textDecoration: s.textDecorationLine,
          textShadow: s.textShadow,
          lineHeight: s.lineHeight,
          textTransform: s.textTransform,
          verticalAlign: s.verticalAlign,
        };
        for (const m of raw.matchAll(/\S+/g)) {
          range.setStart(n, m.index);
          range.setEnd(n, m.index + m[0].length);
          const rects = Array.from(range.getClientRects())
            .filter(r => r.width > 0 && r.height > 0);
          if (!rects.length) continue;
          if (rects.length > 1) splitTokenAcrossLines = true;
          const r = rects[0];
          tokens.push({ text: m[0], top: r.top, bottom: r.bottom,
                        left: r.left, right: r.right, node: n, style });
        }
      } else if (n.nodeType === 1) {
        if (n.tagName === 'BR') return;
        // visibility:hidden 的文本仍有 client rects，必须显式过滤
        if (isHidden(n)) return;
        for (const ch of n.childNodes) collect(ch);
      }
    };
    collect(el);
    range.detach();
    if (splitTokenAcrossLines || tokens.length < 2) return originalRuns;

    const lines = [];
    const tolerance = Math.max(2, parseFloat(getComputedStyle(el).fontSize || '16') * 0.35);
    // 两 token 同一行的判定有两条任一成立即可：
    //   a) top 接近（同字号常规多行 case，top 差异 ≈ 渲染漂移）
    //   b) 垂直区间重叠达到较小元素高度的 50% 以上（同 baseline 但字号不同的 inline，
    //      例 $29 + <span>/mo</span>：baseline 对齐时小号 top 比大号低 ~ ascender 差，
    //      单看 top 会误判换行；但小号几乎完全落在大号区间内，重叠占比近 100%）
    // 行高 < 1 的栈式相邻行：rect 包含 ascender/descender，相邻行视觉 rect 会有少量
    // 重叠（如 144px 字号 line-height:1 → rect 173px 高 / 行距 144px → 重叠 29px）
    // 比例阈值（50%）能把这种"接缝处少量重叠"和"真正同行的小元素套进大元素"区分开
    const sameLine = (tok, line) => {
      if (Math.abs(tok.top - line.top) <= tolerance) return true;
      const overlap = Math.min(tok.bottom, line.bottom) - Math.max(tok.top, line.top);
      if (overlap <= tolerance) return false;
      const minHeight = Math.min(tok.bottom - tok.top, line.bottom - line.top);
      return overlap >= minHeight * 0.5;
    };
    for (const tok of tokens) {
      const last = lines[lines.length - 1];
      if (last && sameLine(tok, last)) {
        last.tokens.push(tok);
        last.top = Math.min(last.top, tok.top);
        last.bottom = Math.max(last.bottom, tok.bottom);
      } else {
        lines.push({ top: tok.top, bottom: tok.bottom, tokens: [tok] });
      }
    }
    if (lines.length <= 1) return originalRuns;

    const out = [];
    lines.forEach((line, lineIdx) => {
      line.tokens.sort((a, b) => a.left - b.left);
      let prev = null;
      for (const tok of line.tokens) {
        let sep = '';
        if (prev) {
          if (prev.node === tok.node) {
            // 同一文本节点内相邻 \S+ token 之间必然隔着字面空白 → 还原为空格
            sep = ' ';
          } else {
            // 跨节点边界按几何间隙判断：Ship<span>Fast</span> 这类零间隙样式
            // 边界不能插空格（会改写文字内容）；真实空格 / gap 的间隙 ≥ ~0.2em
            const ls = parseFloat(tok.style.letterSpacing) || 0;
            sep = (tok.left - prev.right) > ls + tok.style.fontSize * 0.12 ? ' ' : '';
          }
        }
        pushStyledText(out, sep + tok.text, { ...tok.style, inkBottom: tok.bottom });
        prev = tok;
      }
      if (lineIdx !== lines.length - 1) out.push({ text: '\n', linebreak: true, breakSource: 'automatic' });
    });
    return out.length ? out : originalRuns;
  };

  const textContentDomRect = (el) => {
    const nodes = [];
    const collect = (n) => {
      if (n.nodeType === 3 && n.nodeValue && /\S/.test(n.nodeValue)) {
        nodes.push(n);
      } else if (n.nodeType === 1) {
        if (n.tagName === 'BR') return;
        for (const ch of n.childNodes) collect(ch);
      }
    };
    collect(el);
    if (!nodes.length) return null;

    const first = nodes[0];
    const last = nodes[nodes.length - 1];
    const firstIndex = first.nodeValue.search(/\S/);
    const lastMatch = [...last.nodeValue.matchAll(/\S/g)].pop();
    if (firstIndex < 0 || !lastMatch) return null;

    const range = document.createRange();
    range.setStart(first, firstIndex);
    range.setEnd(last, lastMatch.index + lastMatch[0].length);
    const rects = Array.from(range.getClientRects()).filter(r => r.width > 0 && r.height > 0);
    range.detach();
    if (!rects.length) return null;

    const left = Math.min(...rects.map(r => r.left));
    const top = Math.min(...rects.map(r => r.top));
    const right = Math.max(...rects.map(r => r.right));
    const bottom = Math.max(...rects.map(r => r.bottom));
    return { left, top, right, bottom, width: right - left, height: bottom - top };
  };

  // 选择需要导出的节点
  const walk = (el) => {
    if (!el || el.nodeType !== 1) return;
    if (isHidden(el)) return;
    const calendarSnapshotAncestor = el.closest('.__pptx_calendar_snapshot');
    const suppressCalendarDecoration = !!calendarSnapshotAncestor && el !== calendarSnapshotAncestor;
    const isCalendarEvent = el.classList.contains('event');

    // SVG 整体作为一个节点导出
    if (el.tagName.toLowerCase() === 'svg') {
      const r = el.getBoundingClientRect();
      // Opt-in bounded vector subset. Unsupported SVG remains a faithful image.
      if (el.getAttribute('data-pptx-native') === 'lines') {
        const children = [...el.querySelectorAll('*')];
        let compositingSafe=true;
        for (let n=el;n && n!==slide;n=n.parentElement) {
          const s=getComputedStyle(n);
          if (parseFloat(s.opacity)!==1 || s.filter!=='none' || s.backdropFilter!=='none' ||
              s.clipPath!=='none' || s.maskImage!=='none' || s.mixBlendMode!=='normal') compositingSafe=false;
        }
        const safe = compositingSafe && children.length && children.every(n => n.tagName.toLowerCase() === 'line');
        const native = [];
        if (safe) for (const line of children) {
          const s = getComputedStyle(line), m = line.getScreenCTM();
          if (!m || s.stroke === 'none' || s.filter !== 'none' || s.clipPath !== 'none' ||
              s.strokeDasharray !== 'none' || s.markerStart !== 'none' || s.markerEnd !== 'none' ||
              parseFloat(s.opacity) !== 1 || getComputedStyle(el).opacity !== '1') break;
          const scaleX = Math.hypot(m.a,m.b), scaleY = Math.hypot(m.c,m.d);
          if (Math.abs(scaleX-scaleY) > .001 || Math.abs(m.a*m.c+m.b*m.d) > .001) break;
          const p1 = new DOMPoint(line.x1.baseVal.value,line.y1.baseVal.value).matrixTransform(m);
          const p2 = new DOMPoint(line.x2.baseVal.value,line.y2.baseVal.value).matrixTransform(m);
          if ([p1,p2].some(p => p.x<r.left || p.x>r.right || p.y<r.top || p.y>r.bottom)) break;
          native.push({kind:'connector',x1:p1.x-slideRect.left,y1:p1.y-slideRect.top,
            x2:p2.x-slideRect.left,y2:p2.y-slideRect.top,color:s.stroke,
            width:parseFloat(s.strokeWidth)*scaleX,alpha:parseFloat(s.strokeOpacity),source:'svg-line-v1'});
        }
        if (safe && native.length === children.length) {
          for (const record of native) records.push({...record,id:nodeId++});
          return;
        }
      }
      // 给元素打 marker，便于 Playwright 后续按 marker 截图
      const svgIndex = records.filter(x => x.kind === 'svg').length;
      el.setAttribute('data-pptx-svg-id', `slide${slideIndex+1}-svg${svgIndex+1}`);
      records.push({
        id: nodeId++,
        kind: 'svg',
        tag: 'svg',
        rect: rectRel(r),
        marker: `slide${slideIndex+1}-svg${svgIndex+1}`,
        outerHTML: el.outerHTML,
        color: css(el, 'color'),
      });
      return; // SVG 整体当一张图，不下钻子节点
    }

    if (el.tagName.toLowerCase() === 'img') {
      const r = rasterVisibleRect(el);
      if(r.width<=0 || r.height<=0)return;
      const imgIndex = records.filter(x => x.kind === 'img').length;
      el.setAttribute('data-pptx-img-id', `slide${slideIndex+1}-img${imgIndex+1}`);
      records.push({
        id: nodeId++,
        kind: 'img',
        tag: 'img',
        rect: rectRel(r),
        marker: `slide${slideIndex+1}-img${imgIndex+1}`,
        screenshotClip: {x:r.left,y:r.top,w:r.width,h:r.height},
        src: el.currentSrc || el.src,
        naturalImageSize: {w:el.naturalWidth,h:el.naturalHeight},
        originalImageEligibility: plainImageOriginal(el),
      });
      return;
    }

    // canvas / video — 整体作为 picture 截图嵌入
    // - canvas（Chart.js / WebGL / 自绘图）：像素无法用 OOXML 表达；measure 已等过动画稳定，截首帧足以还原静态呈现
    // - video：OOXML 无原生播放表达，落盘 PPT 里就是首帧图片（多数演示场景可接受）
    // 两者复用同一 kind='canvas' + 同一 marker attr，命中 _MARKER_SHOOT_SPECS / assemble.py 已有 picture 分支；
    // tag 字段保留原始 'canvas' / 'video'，audit / lessons-learned 端能识别来源。
    const tagLow = el.tagName.toLowerCase();
    if (tagLow === 'canvas' || tagLow === 'video') {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) {
        const canvasIndex = records.filter(x => x.kind === 'canvas').length;
        const marker = `slide${slideIndex+1}-canvas${canvasIndex+1}`;
        el.setAttribute('data-pptx-canvas-id', marker);
        records.push({
          id: nodeId++,
          kind: 'canvas',
          tag: tagLow,
          rect: rectRel(r),
          naturalSize: { w: el.offsetWidth, h: el.offsetHeight },
          rotation: cumulativeRotation(el),
          marker,
        });
      }
      return;
    }

    const s = getComputedStyle(el);

    // 装饰：边框或非透明背景色（且不是默认透明）
    const bg = s.backgroundColor;
    const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
    const borderTop = parseFloat(s.borderTopWidth) > 0;
    const borderBottom = parseFloat(s.borderBottomWidth) > 0;
    const borderLeft = parseFloat(s.borderLeftWidth) > 0;
    const borderRight = parseFloat(s.borderRightWidth) > 0;
    const hasBorder = borderTop || borderBottom || borderLeft || borderRight;

    const textLeaf = isTextLeaf(el);
    const pseudoNeedsSnapshot = (pseudo) =>
      hasRasterPseudoDecoration(el, pseudo) && !(textLeaf && isTextOnlyPseudoMarker(el, pseudo));
    const complexDecoration = hasNonPseudoComplexDecoration(s, el) ||
      pseudoNeedsSnapshot('::before') || pseudoNeedsSnapshot('::after');
    const pseudoVectorShapes = complexDecoration ? { before: [], after: [] } : simplePseudoLineShapeRecords(el);
    for (const rec of pseudoVectorShapes.before) records.push(rec);

    // Vector-first rule:
    // - plain background / border / simple pseudo-element lines stay as PPT shapes
    // - rasterize only decorations OOXML cannot express reliably
    //   (image/shadow/filter/blend/skew/complex pseudo shapes)
    //
    // 通用装饰捕获：任何元素只要有 background-image / box-shadow / 复杂伪元素装饰
    // → 整块截图嵌入作为底层；子节点（文字 / 子装饰）按原流程继续处理画在之上
    // 这套机制覆盖所有 PPT 几何原语无法表达的 CSS 装饰，无需为每种新增加 patch
    if (complexDecoration) {
      const r = decorationCaptureRect(el);
      if (r.width > 0 && r.height > 0) {
        const decoIndex = records.filter(x => x.kind === 'deco_snapshot').length;
        const marker = `slide${slideIndex+1}-deco${decoIndex+1}`;
        el.setAttribute('data-pptx-deco-id', marker);
        records.push({
          id: nodeId++,
          kind: 'deco_snapshot',
          tag: el.tagName.toLowerCase(),
          rect: rectRel(r),
          naturalSize: { w: el.offsetWidth, h: el.offsetHeight },
          rotation: cumulativeRotation(el),
          marker,
          screenshotClip: {
            x: r.left,
            y: r.top,
            w: r.width,
            h: r.height,
          },
        });
        // overflow:hidden 裁切容器：容器 PNG 已经包含被裁后的子装饰，跳过子的单独处理
        // （旋转子的 AABB 远大于裁切框，单独画会变成超大色块覆盖周围）
        // 例外：slide 根节点。slide 根的 overflow:hidden 是布局结构（裁视口），
        // 不是"装饰裁切意图"。若 slide 根本身命中此分支会吞掉所有 text/svg 子记录。
        if (el !== slide && isClippingContainerWithTransformedChildren(s, el)) {
          return;
        }
        // 其他情况（背景图 / box-shadow / 伪元素装饰 / filter / mix-blend-mode /
        // backdrop-filter / 不可表达 transform）：截图天然只截装饰（_DECO_HIDE_FOREGROUND_JS
        // 在截图前会 hide 带文字的子元素 + 把 deco 自身的 color 设透明），文字另发
        // 矢量记录画在截图之上，保持可编辑。代价：filter/blend/skew 等视觉效果不会
        // 应用到文字本身（文字 crisp）；客户绝大多数场景偏好可编辑文字。
      }
    }

    // text leaf：直接导出文本节点
    if (textLeaf) {
      const r = el.getBoundingClientRect();
      const runs = extractRuns(el);
      const rotDeg = cumulativeRotation(el);
      const decoForText = (suppressCalendarDecoration && !isCalendarEvent) || complexDecoration
        ? { hasBg: false, bg: 'rgba(0, 0, 0, 0)', borderTop: false, borderBottom: false,
            borderLeft: false, borderRight: false, borderColor: s.borderTopColor,
            borderTopColor: s.borderTopColor, borderBottomColor: s.borderBottomColor,
            borderLeftColor: s.borderLeftColor, borderRightColor: s.borderRightColor,
            borderTopWidth: 0, borderBottomWidth: 0, borderLeftWidth: 0, borderRightWidth: 0,
            borderRadius: s.borderTopLeftRadius }
        : decoFromStyle(s, hasBg, bg, borderTop, borderBottom, borderLeft, borderRight);
      const baseStyle = textStyleFromComputed(s);
      const beforeMarker = isTextOnlyPseudoMarker(el, '::before') ? extractPseudoRun(el, '::before') : null;
      const afterMarker = isTextOnlyPseudoMarker(el, '::after') ? extractPseudoRun(el, '::after') : null;
      const contentRect = beforeMarker && !afterMarker ? textContentDomRect(el) : null;
      if (contentRect) {
        const bodyLeft = Math.min(Math.max(contentRect.left, r.left), r.right);
        const markerRect = { left: r.left, top: r.top, width: Math.max(1, bodyLeft - r.left), height: r.height };
        const bodyRect = { left: bodyLeft, top: r.top, width: Math.max(1, r.right - bodyLeft), height: r.height };
        const ps = getComputedStyle(el, '::before');
        for (const rec of pseudoVectorShapes.after) records.push(rec);
        records.push({
          id: nodeId++,
          kind: 'text',
          tag: el.tagName.toLowerCase() + '::before',
          className: el.className || '',
          rect: rectRel(markerRect),
          naturalSize: { w: markerRect.width, h: markerRect.height },
          rotation: rotDeg,
          runs: [beforeMarker],
          style: textStyleFromComputed(ps),
          deco: { hasBg: false, bg: 'rgba(0, 0, 0, 0)', borderTop: false, borderBottom: false,
                  borderLeft: false, borderRight: false, borderColor: ps.color,
                  borderTopColor: ps.color, borderBottomColor: ps.color,
                  borderLeftColor: ps.color, borderRightColor: ps.color,
                  borderTopWidth: 0, borderBottomWidth: 0, borderLeftWidth: 0, borderRightWidth: 0,
                  borderRadius: ps.borderTopLeftRadius },
          text: beforeMarker.text,
        });
        records.push({
          id: nodeId++,
          kind: 'text',
          tag: el.tagName.toLowerCase(),
          className: el.className || '',
          rect: rectRel(bodyRect),
          naturalSize: { w: bodyRect.width, h: bodyRect.height },
          rotation: rotDeg,
          runs: extractRuns(el, false),
          style: baseStyle,
          deco: decoForText,
          text: el.innerText,
        });
        return;
      }
      for (const rec of pseudoVectorShapes.after) records.push(rec);
      records.push({
        id: nodeId++,
        kind: 'text',
        tag: el.tagName.toLowerCase(),
        className: el.className || '',
        rect: rectRel(r),
        // 元素未旋转的尺寸（不含 transform 效果），用于旋转还原
        naturalSize: { w: el.offsetWidth, h: el.offsetHeight },
        rotation: rotDeg,
        runs,
        style: baseStyle,
        deco: decoForText,
        text: el.innerText,
      });
      return;
    }

    // 非 text leaf 但有装饰 → 单独导出形状（不带文本，文本由子节点输出）
    if (!complexDecoration && (hasBg || hasBorder) && !(suppressCalendarDecoration && !isCalendarEvent)) {
      const r = el.getBoundingClientRect();
      const rotDeg = cumulativeRotation(el);
      records.push({
        id: nodeId++,
        kind: 'shape',
        tag: el.tagName.toLowerCase(),
        className: el.className || '',
        rect: rectRel(r),
        // 元素未旋转的尺寸（不含 transform 效果），用于旋转还原
        naturalSize: { w: el.offsetWidth, h: el.offsetHeight },
        rotation: rotDeg,
        deco: decoFromStyle(s, hasBg, bg, borderTop, borderBottom, borderLeft, borderRight),
      });
    }
    for (const rec of pseudoVectorShapes.after) records.push(rec);

    // flex/grid + spacing 容器：每个直接子（element 或非空 text node）作为独立 flex item 单独 emit。
    // - 不能合并多 item 进同一 group：合并 = 再把容器拉开的间距吞回去
    // - 不能只走 el.children：会丢直接 text node 这种 anonymous flex item
    //   （如 `<div display:flex justify-between>AGENDA<span>09:00</span></div>` 的"AGENDA"）
    // - 跳过 block-only 过滤（要带上 <span> 之类 inline 子项）
    if (isFlexSpacingContainer(el)) {
      for (const ch of el.childNodes) {
        if (ch.nodeType === 1) {
          walk(ch);
        } else if (ch.nodeType === 3 && ch.nodeValue && ch.nodeValue.trim()) {
          emitInlineGroup([ch], el);
        }
      }
      return;
    }

    // 处理"混合容器"：当 el 既有 block 子，又有直接挂着的 text node / inline 元素，
    // 直接文本节点不会进入 el.children 遍历也不属于 isTextLeaf 分支，
    // 必须单独抓取为 inline-group text 记录，否则会丢字（典型：callout）
    emitInlineGroupsAround(el);

    // 继续下钻 block 子
    for (const ch of el.children) {
      // Atomic calendar events were already emitted by emitInlineGroup; walking
      // them again creates two coincident rounded rectangles whose PowerPoint
      // anti-aliasing reads as a drop shadow.
      if (ch.closest('.__pptx_calendar_snapshot') && isAtomicInline(ch)) continue;
      const cs = getComputedStyle(ch);
      const childBg = cs.backgroundColor && cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent';
      const childBorder = parseFloat(cs.borderTopWidth) > 0 || parseFloat(cs.borderBottomWidth) > 0 ||
                          parseFloat(cs.borderLeftWidth) > 0 || parseFloat(cs.borderRightWidth) > 0;
      const childComplex = hasNonPseudoComplexDecoration(cs, ch) ||
                           hasRasterPseudoDecoration(ch, '::before') ||
                           hasRasterPseudoDecoration(ch, '::after');
      if (isLayoutBlock(ch) || childBg || childBorder || childComplex) walk(ch);
    }
  };

  // emit 单个 inline group（trim 过 <br> 的节点列表）→ 一条 text 记录。
  // 抽出公用 helper：emitInlineGroupsAround（常规混合容器）与 flex-spacing 容器分支共享。
  const emitInlineGroup = (trimmed, hostEl) => {
    if (!trimmed.length) return;
    const range = document.createRange();
    range.setStartBefore(trimmed[0]);
    range.setEndAfter(trimmed[trimmed.length - 1]);
    const rects = range.getClientRects();
    if (!rects.length) return;
    // 取整组并集 rect（多行时 getBoundingClientRect 会给到完整范围）
    const atomicEl = trimmed.length === 1 && isAtomicInline(trimmed[0]) ? trimmed[0] : null;
    let r = atomicEl ? atomicEl.getBoundingClientRect() : range.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    // 跳过纯空白（trim 后没文本）
    const txt = (atomicEl ? atomicEl.textContent : range.toString()).replace(/\s+/g, ' ').trim();
    if (!txt) return;

    // 用 trimmed 组的代表元素取样式：第一个 element 节点；找不到就用 hostEl
    // （用 trimmed 而非原 group：原 group 里如果首节点是 <br> 会把 styleHost 错设成 br）
    let styleHost = hostEl;
    for (const n of trimmed) { if (n.nodeType === 1 && n.tagName !== 'BR') { styleHost = n; break; } }
    const natural = hostEl.closest('[data-pptx-text-flow]')?.getAttribute('data-pptx-text-flow') === 'natural';
    // Mixed paragraphs must retain the same natural-flow policy as text leaves.
    // Ink bounds are narrower than the available paragraph width; using them
    // as a new frame changes wrapping and can turn a BR into wrap=none overflow.
    if (natural && !atomicEl && getComputedStyle(hostEl).display === 'block') {
      const hs=getComputedStyle(hostEl), hr=hostEl.getBoundingClientRect();
      const right=hr.right-(parseFloat(hs.paddingRight)||0)-(parseFloat(hs.borderRightWidth)||0);
      r={left:r.left,top:r.top,width:Math.max(r.width,right-r.left),height:r.height};
      styleHost=hostEl;
    }
    const demo = getComputedStyle(styleHost);
    const bg = demo.backgroundColor;
    const hasBg = bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent';
    const borderTop = parseFloat(demo.borderTopWidth) > 0;
    const borderBottom = parseFloat(demo.borderBottomWidth) > 0;
    const borderLeft = parseFloat(demo.borderLeftWidth) > 0;
    const borderRight = parseFloat(demo.borderRightWidth) > 0;

    // 抽取 runs（遍历每个 group 成员）。
    // 用 trimmed 抽 runs：首尾 br 不进 runs（避免 OOXML 多出空行把单行文本撑高错位）。
    const runs = [];
    const walkInline = (n) => {
      if (n.nodeType === 3) {
        if (!n.nodeValue) return;
        // 直接文本节点（如 flex-spacing 容器的 anonymous flex item）parentElement 就是 hostEl
        const p = n.parentElement || hostEl;
        const ps = getComputedStyle(p);
        const irng = document.createRange();
        irng.selectNodeContents(n);
        const irr = irng.getBoundingClientRect();
        runs.push({
          text: n.nodeValue,
          lang: sourceLanguage(p),
          fontFamily: ps.fontFamily,
          fontSize: parseFloat(ps.fontSize),
          fontWeight: ps.fontWeight,
          fontStyle: ps.fontStyle,
          color: ps.color,
          letterSpacing: ps.letterSpacing,
          textDecoration: ps.textDecorationLine,
          textShadow: ps.textShadow,
          lineHeight: ps.lineHeight,
          textTransform: ps.textTransform,
          verticalAlign: ps.verticalAlign,
          inkBottom: irr.height > 0 ? irr.bottom : null,
        });
      } else if (n.nodeType === 1) {
        if (n.tagName === 'BR') { runs.push({ text: '\n', linebreak: true }); return; }
        // 隐藏的 inline 子树不进 runs（与 extractRuns.walk 同规则）
        if (isHidden(n)) return;
        const before = extractPseudoRun(n, '::before');
        if (before) runs.push(before);
        for (const c of n.childNodes) walkInline(c);
        const after = extractPseudoRun(n, '::after');
        if (after) runs.push(after);
      }
    };
    for (const n of trimmed) walkInline(n);
    if (natural) for (const run of runs) run.naturalWrap=true;

    // atomic-inline 元素（display:inline-block / inline-flex 的 <button> 等）
    // 走 emitInlineGroup 而不进 walk()，所以 complexDecoration 路径会被跳过。
    // 这里补一道：若它有 box-shadow / background-image / 复杂伪元素装饰，
    // 也截一张 deco_snapshot 嵌底，下方 text 记录把 bg/border 清掉避免双绘
    let inlineDecoCleared = false;
    if (atomicEl) {
      const aS = getComputedStyle(atomicEl);
      const aTextLeaf = isTextLeaf(atomicEl);
      const aPseudoNeedsSnap = (pseudo) =>
        hasRasterPseudoDecoration(atomicEl, pseudo) && !(aTextLeaf && isTextOnlyPseudoMarker(atomicEl, pseudo));
      const aComplex = hasNonPseudoComplexDecoration(aS, atomicEl) ||
        aPseudoNeedsSnap('::before') || aPseudoNeedsSnap('::after');
      if (aComplex) {
        const aR = decorationCaptureRect(atomicEl);
        if (aR.width > 0 && aR.height > 0) {
          const decoIndex = records.filter(x => x.kind === 'deco_snapshot').length;
          const marker = `slide${slideIndex+1}-deco${decoIndex+1}`;
          atomicEl.setAttribute('data-pptx-deco-id', marker);
          records.push({
            id: nodeId++,
            kind: 'deco_snapshot',
            tag: atomicEl.tagName.toLowerCase(),
            rect: rectRel(aR),
            naturalSize: { w: atomicEl.offsetWidth, h: atomicEl.offsetHeight },
            rotation: cumulativeRotation(atomicEl),
            marker,
            screenshotClip: { x: aR.left, y: aR.top, w: aR.width, h: aR.height },
          });
          inlineDecoCleared = true;
        }
      }
    }
    const inlineInCalendarSnapshot = !!styleHost.closest('.__pptx_calendar_snapshot');
    const inlineIsCalendarEvent = styleHost.classList.contains('event');
    const decoForInline = (inlineInCalendarSnapshot && !inlineIsCalendarEvent) || inlineDecoCleared
      ? { hasBg: false, bg: 'rgba(0, 0, 0, 0)', borderTop: false, borderBottom: false,
          borderLeft: false, borderRight: false, borderColor: demo.borderTopColor,
          borderTopColor: demo.borderTopColor, borderBottomColor: demo.borderBottomColor,
          borderLeftColor: demo.borderLeftColor, borderRightColor: demo.borderRightColor,
          borderTopWidth: 0, borderBottomWidth: 0, borderLeftWidth: 0, borderRightWidth: 0,
          borderRadius: demo.borderTopLeftRadius }
      : decoFromStyle(demo, hasBg, bg, borderTop, borderBottom, borderLeft, borderRight);

    records.push({
      id: nodeId++,
      kind: 'text',
      tag: styleHost.tagName.toLowerCase() + '#inline',
      className: styleHost.className || '',
      rect: rectRel(r),
      runs,
      style: {
        color: demo.color,
        fontFamily: demo.fontFamily,
        fontSize: parseFloat(demo.fontSize),
        fontWeight: demo.fontWeight,
        fontStyle: demo.fontStyle,
        lineHeight: demo.lineHeight,
        letterSpacing: demo.letterSpacing,
        textAlign: demo.textAlign,
        textTransform: demo.textTransform,
        opacity: demo.opacity,
        paddingTop: parseFloat(demo.paddingTop) || 0,
        paddingRight: parseFloat(demo.paddingRight) || 0,
        paddingBottom: parseFloat(demo.paddingBottom) || 0,
        paddingLeft: parseFloat(demo.paddingLeft) || 0,
        display: demo.display,
        alignItems: demo.alignItems,
        justifyContent: demo.justifyContent,
        writingMode: demo.writingMode,
      },
      deco: decoForInline,
      text: txt,
    });
  };

  // 把 el 的子节点按 block 边界切成若干 inline group；每个 group 单独发一个 text 记录
  const emitInlineGroupsAround = (el) => {
    const groups = [];
    let cur = null;
    for (const ch of el.childNodes) {
      const isElem = ch.nodeType === 1;
      const isBlock = isElem && isLayoutBlock(ch);
      const atomic = isAtomicInline(ch);
      if (isBlock || atomic) {
        if (cur) { groups.push(cur); cur = null; }
        if (atomic) groups.push([ch]);
        continue;
      }
      // text node 或 inline element
      if (ch.nodeType === 3 && (!ch.nodeValue || !ch.nodeValue.trim())) {
        // 单独空白文本节点：若已有 cur，把它纳入；否则忽略
        if (cur) cur.push(ch);
        continue;
      }
      if (!cur) cur = [];
      cur.push(ch);
    }
    if (cur) groups.push(cur);

    for (const group of groups) {
      if (!group.length) continue;
      // 剥掉 group 首尾的 <br>：它们没几何意义（零宽软换行），
      // 留着会让 range BCR 跨进上一行/下一行 → record h 翻倍 → 后续 textbox 撞下方相邻段
      let trimmed = group;
      while (trimmed.length && trimmed[0].nodeType === 1 && trimmed[0].tagName === 'BR') {
        trimmed = trimmed.slice(1);
      }
      while (trimmed.length && trimmed[trimmed.length - 1].nodeType === 1 && trimmed[trimmed.length - 1].tagName === 'BR') {
        trimmed = trimmed.slice(0, -1);
      }
      emitInlineGroup(trimmed, el);
    }
  };

  const rectRel = (r) => ({
    x: r.left - slideRect.left,
    y: r.top - slideRect.top,
    w: r.width,
    h: r.height,
  });

  const unionRect = (a, b) => {
    if (!b || b.width <= 0 || b.height <= 0) return a;
    const left = Math.min(a.left, b.left);
    const top = Math.min(a.top, b.top);
    const right = Math.max(a.left + a.width, b.left + b.width);
    const bottom = Math.max(a.top + a.height, b.top + b.height);
    return { left, top, width: right - left, height: bottom - top };
  };

  const pxOrNull = (v) => {
    const n = parseFloat(v);
    return Number.isFinite(n) ? n : null;
  };

  const pseudoAbsRect = (el, pseudo, base) => {
    if (!hasPseudoDecoration(el, pseudo)) return null;
    const ps = getComputedStyle(el, pseudo);
    if (ps.display === 'none' || ps.visibility === 'hidden') return null;
    if (ps.position !== 'absolute' && ps.position !== 'fixed') return null;

    const left = pxOrNull(ps.left);
    const right = pxOrNull(ps.right);
    const top = pxOrNull(ps.top);
    const bottom = pxOrNull(ps.bottom);
    let w = pxOrNull(ps.width) || 0;
    let h = pxOrNull(ps.height) || 0;
    if (ps.boxSizing !== 'border-box') {
      w += (pxOrNull(ps.paddingLeft) || 0) + (pxOrNull(ps.paddingRight) || 0)
           + (pxOrNull(ps.borderLeftWidth) || 0) + (pxOrNull(ps.borderRightWidth) || 0);
      h += (pxOrNull(ps.paddingTop) || 0) + (pxOrNull(ps.paddingBottom) || 0)
           + (pxOrNull(ps.borderTopWidth) || 0) + (pxOrNull(ps.borderBottomWidth) || 0);
    }

    let x1 = left !== null ? base.left + left
             : (right !== null ? base.left + base.width - right - w : base.left);
    let x2 = right !== null ? base.left + base.width - right : x1 + w;
    let y1 = top !== null ? base.top + top
             : (bottom !== null ? base.top + base.height - bottom - h : base.top);
    let y2 = bottom !== null ? base.top + base.height - bottom : y1 + h;
    const l = Math.min(x1, x2);
    const t = Math.min(y1, y2);
    return { left: l, top: t, width: Math.abs(x2 - x1), height: Math.abs(y2 - y1) };
  };

  // box-shadow（含多层）向外延展量。inset shadow 不算（不影响外部 AABB）
  // 输入：computed boxShadow 值，例 "rgb(244, 208, 63) 8px 8px 0px"
  //                            或 "rgb(15, 27, 61) 4px 0px 0px 0px, rgba(244,208,63,1) 8px 8px 0px 0px"
  // 输出：{top, right, bottom, left} 像素延展，全 0 表示无延展
  const parseBoxShadowExtent = (value) => {
    const zero = { top: 0, right: 0, bottom: 0, left: 0 };
    if (!value || value === 'none') return zero;
    // 顶层逗号切分（跳过括号内逗号）；color 是 rgb()/rgba() 直接 split(',') 会切坏
    const parts = [];
    let depth = 0, cur = '';
    for (const ch of value) {
      if (ch === '(') { depth++; cur += ch; }
      else if (ch === ')') { depth--; cur += ch; }
      else if (ch === ',' && depth === 0) { parts.push(cur.trim()); cur = ''; }
      else cur += ch;
    }
    if (cur.trim()) parts.push(cur.trim());
    const ext = { top: 0, right: 0, bottom: 0, left: 0 };
    for (const part of parts) {
      if (/\binset\b/i.test(part)) continue;
      // 去掉 color token，剩下数值
      const numsOnly = part.replace(/rgba?\([^)]+\)/g, '').replace(/#[\dA-Fa-f]+/g, '');
      const nums = (numsOnly.match(/-?\d+\.?\d*(?=px)/g) || []).map(parseFloat);
      if (nums.length < 2) continue;
      const dx = nums[0], dy = nums[1];
      const blur = nums.length >= 3 ? nums[2] : 0;
      const spread = nums.length >= 4 ? nums[3] : 0;
      const r = blur + spread;
      ext.right = Math.max(ext.right, dx + r);
      ext.left = Math.max(ext.left, -dx + r);
      ext.bottom = Math.max(ext.bottom, dy + r);
      ext.top = Math.max(ext.top, -dy + r);
    }
    for (const k of Object.keys(ext)) ext[k] = Math.max(0, ext[k]);
    return ext;
  };

  const decorationCaptureRect = (el) => {
    const baseDom = el.getBoundingClientRect();
    const base = { left: baseDom.left, top: baseDom.top, width: baseDom.width, height: baseDom.height };
    let r = base;
    r = unionRect(r, pseudoAbsRect(el, '::before', base));
    r = unionRect(r, pseudoAbsRect(el, '::after', base));
    const s = getComputedStyle(el);
    const outline = (s.outlineStyle && s.outlineStyle !== 'none') ? (pxOrNull(s.outlineWidth) || 0) : 0;
    if (outline > 0) {
      r = { left: r.left - outline, top: r.top - outline,
            width: r.width + outline * 2, height: r.height + outline * 2 };
    }
    // box-shadow 向外延展：偏移 + blur + spread，不带就是 0
    // 不延展 → 截图框裁掉 shadow，PPT 里整圈"硬阴影"丢失（8-bit 风模板会丢黄色 step shadow）
    const shx = parseBoxShadowExtent(s.boxShadow);
    if (shx.top || shx.right || shx.bottom || shx.left) {
      r = { left: r.left - shx.left, top: r.top - shx.top,
            width: r.width + shx.left + shx.right,
            height: r.height + shx.top + shx.bottom };
    }
    return r;
  };

  const pseudoLineShapeRecord = (el, pseudo) => {
    if (!isSimplePseudoLineDecoration(el, pseudo)) return null;
    const baseDom = el.getBoundingClientRect();
    const base = { left: baseDom.left, top: baseDom.top, width: baseDom.width, height: baseDom.height };
    const r = pseudoAbsRect(el, pseudo, base);
    if (!r || r.width <= 0 || r.height <= 0) return null;
    const ps = getComputedStyle(el, pseudo);
    const z = parseInt(ps.zIndex, 10);
    const deco = {
      hasBg: false,
      bg: ps.backgroundColor,
      borderTop: parseFloat(ps.borderTopWidth) > 0,
      borderBottom: parseFloat(ps.borderBottomWidth) > 0,
      borderLeft: parseFloat(ps.borderLeftWidth) > 0,
      borderRight: parseFloat(ps.borderRightWidth) > 0,
      borderColor: ps.borderTopColor,
      borderTopColor: ps.borderTopColor,
      borderBottomColor: ps.borderBottomColor,
      borderLeftColor: ps.borderLeftColor,
      borderRightColor: ps.borderRightColor,
      borderTopWidth: parseFloat(ps.borderTopWidth) || 0,
      borderBottomWidth: parseFloat(ps.borderBottomWidth) || 0,
      borderLeftWidth: parseFloat(ps.borderLeftWidth) || 0,
      borderRightWidth: parseFloat(ps.borderRightWidth) || 0,
      borderRadius: ps.borderTopLeftRadius,
    };
    return {
      id: nodeId++,
      kind: 'shape',
      tag: el.tagName.toLowerCase() + pseudo,
      className: el.className || '',
      rect: rectRel(r),
      naturalSize: { w: r.width, h: r.height },
      rotation: cumulativeRotation(el),
      deco,
      paintBeforeHost: Number.isFinite(z) && z < 0,
    };
  };

  const simplePseudoLineShapeRecords = (el) => {
    const out = { before: [], after: [] };
    for (const pseudo of ['::before', '::after']) {
      const rec = pseudoLineShapeRecord(el, pseudo);
      if (!rec) continue;
      const target = rec.paintBeforeHost ? out.before : out.after;
      delete rec.paintBeforeHost;
      target.push(rec);
    }
    return out;
  };

  walk(slide);

  // 找一个有"实际"背景色的祖先：slide 自己若 transparent，向上回退到 body
  const opaqueBg = (el) => {
    let cur = el;
    while (cur) {
      const bg = getComputedStyle(cur).backgroundColor;
      if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
      cur = cur.parentElement;
    }
    return 'rgb(255, 255, 255)';
  };

  return {
    slide: {
      width: slideRect.width,
      height: slideRect.height,
      theme: slide.className,  // hero dark / light 等
      background: opaqueBg(slide),
      color: getComputedStyle(slide).color,
    },
    records,
  };
}
"""


_DECO_HIDE_FOREGROUND_JS = r"""(marker) => {
    const deco = document.querySelector(`[data-pptx-deco-id='${marker}']`);
    if (!deco) return;
    const slide = deco.closest('[data-pptx-target]') || document.querySelector('[data-pptx-target]');
    if (!slide) return;
    // Capture this decoration's alpha, not the already separately exported
    // ancestor background. Otherwise a transparent gradient becomes an opaque
    // rectangle and hides its underlying editable image in PowerPoint.
    window.__pptx_deco_ancestors=[];
    for (let parent=deco.parentElement;parent;parent=parent.parentElement) {
        window.__pptx_deco_ancestors.push([parent,parent.getAttribute('style')]);
        parent.style.setProperty('background','transparent','important');
        parent.style.setProperty('border-color','transparent','important');
        parent.style.setProperty('box-shadow','none','important');
    }
    const isAncestor = (el) => {
        let cur = deco.parentElement;
        while (cur) { if (cur === el) return true; cur = cur.parentElement; }
        return false;
    };
    const hasDirectText = (el) => {
        for (const ch of el.childNodes) {
            if (ch.nodeType === 3 && ch.nodeValue && ch.nodeValue.trim()) return true;
        }
        return false;
    };
    const isTransparentColor = (value) => {
        return !value || value === 'transparent' || value === 'rgba(0, 0, 0, 0)';
    };
    const px = (value) => {
        const n = parseFloat(value || '0');
        return Number.isFinite(n) ? n : 0;
    };
    const hasVisibleBoxDecoration = (el) => {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || px(cs.opacity || '1') <= 0) return false;
        const rect = el.getBoundingClientRect();
        if (rect.width < 0.5 || rect.height < 0.5) return false;
        const borderVisible = (side) => {
            return px(cs[`border${side}Width`]) > 0
                && cs[`border${side}Style`] !== 'none'
                && !isTransparentColor(cs[`border${side}Color`]);
        };
        const outlineVisible = px(cs.outlineWidth) > 0
            && cs.outlineStyle !== 'none'
            && !isTransparentColor(cs.outlineColor);
        const shadowVisible = cs.boxShadow && cs.boxShadow !== 'none';
        return !isTransparentColor(cs.backgroundColor)
            || borderVisible('Top')
            || borderVisible('Right')
            || borderVisible('Bottom')
            || borderVisible('Left')
            || outlineVisible
            || shadowVisible;
    };
    const MEDIA = new Set(['SVG','IMG','CANVAS','VIDEO']);
    const isSlideRootDeco = deco === slide;
    const isCalendarSnapshot = deco.classList.contains('calendar-code');
    const hidden = [];
    const transparent = [];
    // Other page roots can sit below the fixed active page. Transparent
    // capture must isolate every outside branch, including nested wrappers.
    for (let branch=deco;branch?.parentElement;branch=branch.parentElement) {
        for (const sibling of branch.parentElement.children) {
            if (sibling===branch) continue;
            for (const el of [sibling,...sibling.querySelectorAll('*')]) {
                hidden.push([el,el.style.visibility,el.style.getPropertyPriority('visibility')]);
                el.style.setProperty('visibility','hidden','important');
            }
        }
    }
    for (const el of slide.querySelectorAll('*')) {
        if (el === deco) continue;
        if (isAncestor(el)) continue;
        const otherDeco = el.hasAttribute('data-pptx-deco-id');
        const media = MEDIA.has(el.tagName.toUpperCase());
        const directText = hasDirectText(el);
        const shapeLike = hasVisibleBoxDecoration(el);
        const insideDeco = deco.contains(el);
        if (otherDeco || media || directText || (shapeLike && (isSlideRootDeco || !insideDeco))) {
            // Keep calendar cell/event backgrounds and borders in the single
            // Chromium snapshot, but remove their text pixels before native
            // editable text is added on top.
            if (isCalendarSnapshot && directText && shapeLike) {
                transparent.push([
                    el,
                    el.style.color,
                    el.style.getPropertyPriority('color'),
                    el.style.textShadow,
                    el.style.getPropertyPriority('text-shadow'),
                ]);
                el.style.setProperty('color', 'transparent', 'important');
                el.style.setProperty('text-shadow', 'none', 'important');
                continue;
            }
            hidden.push([el, el.style.visibility, el.style.getPropertyPriority('visibility')]);
            // inline !important 才能 beat adapters 注入的 [data-anim]{visibility:visible!important}
            el.style.setProperty('visibility', 'hidden', 'important');
        }
    }
    window.__pptx_deco_hidden = hidden;
    window.__pptx_deco_transparent = transparent;
    // deco 自身含直接文本时，临时清 color/text-shadow 避免烘进 PNG
    window.__pptx_deco_self = null;
    if (hasDirectText(deco)) {
        window.__pptx_deco_self = {
            el: deco,
            color: deco.style.color,
            shadow: deco.style.textShadow
        };
        deco.style.setProperty('color', 'transparent', 'important');
        deco.style.setProperty('text-shadow', 'none', 'important');
    }
}"""

_DECO_RESTORE_FOREGROUND_JS = r"""() => {
    for (const [el,style] of (window.__pptx_deco_ancestors || [])) {
        if (style === null) el.removeAttribute('style'); else el.setAttribute('style',style);
    }
    window.__pptx_deco_ancestors=null;
    for (const item of [...(window.__pptx_deco_hidden || [])].reverse()) {
        const [el, v, prio] = item;
        el.style.removeProperty('visibility');
        if (v) el.style.setProperty('visibility', v, prio || '');
    }
    window.__pptx_deco_hidden = null;
    for (const item of (window.__pptx_deco_transparent || [])) {
        const [el, color, colorPrio, shadow, shadowPrio] = item;
        el.style.removeProperty('color');
        el.style.removeProperty('text-shadow');
        if (color) el.style.setProperty('color', color, colorPrio || '');
        if (shadow) el.style.setProperty('text-shadow', shadow, shadowPrio || '');
    }
    window.__pptx_deco_transparent = null;
    const s = window.__pptx_deco_self;
    if (s) {
        s.el.style.removeProperty('color');
        s.el.style.removeProperty('text-shadow');
        if (s.color) s.el.style.color = s.color;
        if (s.shadow) s.el.style.textShadow = s.shadow;
    }
    window.__pptx_deco_self = null;
}"""

_SVG_HIDE_SIBLINGS_JS = r"""(marker) => {
    const svg = document.querySelector(`[data-pptx-svg-id='${marker}']`);
    if (!svg) return;
    const parent = svg.parentElement;
    if (!parent) return;
    window.__pptx_hidden = [];
    for (const ch of parent.children) {
        if (ch === svg) continue;
        window.__pptx_hidden.push([ch, ch.style.visibility]);
        ch.style.visibility = 'hidden';
    }
}"""

_SVG_RESTORE_SIBLINGS_JS = r"""() => {
    for (const [ch, v] of (window.__pptx_hidden || [])) ch.style.visibility = v;
    window.__pptx_hidden = [];
}"""


_IMG_HIDE_OVERLAYS_JS = r"""(marker) => {
    const image = document.querySelector(`[data-pptx-img-id='${marker}']`);
    const slide = image && image.closest('[data-pptx-target]');
    window.__pptx_image_hidden = [];
    if (!image || !slide) return;
    const limitations = new Set();
    // Keep the image's ancestor geometry, clipping and appearance. Hide only
    // other branches at every level, so nested cover wrappers cannot capture
    // separately editable title/logo/footer overlays in the image snapshot.
    for (let branch = image; branch && branch !== slide; branch = branch.parentElement) {
        const parent = branch.parentElement;
        if (!parent) break;
        if ([...parent.childNodes].some(node => node.nodeType === 3 && node.nodeValue.trim())) {
            limitations.add('ancestor_direct_text_not_isolated');
        }
        for (const pseudo of ['::before', '::after']) {
            const content = getComputedStyle(parent, pseudo).content;
            if (content && !['none', 'normal', '""', "''"].includes(content)) {
                limitations.add('ancestor_pseudo_content_not_isolated');
            }
        }
        for (const sibling of parent.children) {
            if (sibling === branch) continue;
            // Descendants can override inherited visibility (including
            // adapter !important styles), so preserve and hide each one.
            for (const element of [sibling, ...sibling.querySelectorAll('*')]) {
                window.__pptx_image_hidden.push([
                    element,
                    element.style.getPropertyValue('visibility'),
                    element.style.getPropertyPriority('visibility'),
                ]);
                element.style.setProperty('visibility', 'hidden', 'important');
            }
        }
    }
    return {policy: 'image-path-sibling-isolation-v1',
            scope: 'separate-branches-through-slide', limitations: [...limitations]};
}"""

_IMG_RESTORE_OVERLAYS_JS = r"""() => {
    for (const [element, value, priority] of [...(window.__pptx_image_hidden || [])].reverse()) {
        element.style.removeProperty('visibility');
        if (value) element.style.setProperty('visibility', value, priority || '');
    }
    window.__pptx_image_hidden = null;
}"""


# (kind, attr, omit_bg, pre_js, post_js)
_MARKER_SHOOT_SPECS = {
    "deco_snapshot": ("data-pptx-deco-id", True, _DECO_HIDE_FOREGROUND_JS, _DECO_RESTORE_FOREGROUND_JS),
    "svg":           ("data-pptx-svg-id",  True,  _SVG_HIDE_SIBLINGS_JS,    _SVG_RESTORE_SIBLINGS_JS),
    "canvas":        ("data-pptx-canvas-id", False, None, None),
    "img":           ("data-pptx-img-id",  True,  _IMG_HIDE_OVERLAYS_JS, _IMG_RESTORE_OVERLAYS_JS),
}


def _resolve_original_image(rec):
    """Hash-bind a complete plain local PNG/JPEG; never fetch or resample it."""
    if rec.get('kind') != 'img' or not rec.get('originalImageEligibility', {}).get('eligible'):
        return None
    parsed=urlparse(rec.get('src',''))
    if parsed.scheme != 'file' or parsed.netloc not in {'','localhost'}:
        rec['originalImageFallback']='not_local_file'; return None
    path=Path(url2pathname(parsed.path)).resolve()
    if path.suffix.lower() not in {'.png','.jpg','.jpeg'} or not path.is_file():
        rec['originalImageFallback']='unsupported_or_missing_original'; return None
    if path.stat().st_size > 128*1024*1024:
        rec['originalImageFallback']='original_exceeds_bounded_read'; return None
    try:
        original_bytes=path.read_bytes()
        if len(original_bytes)>128*1024*1024:
            rec['originalImageFallback']='original_exceeds_bounded_read'; return None
        with Image.open(io.BytesIO(original_bytes)) as source:
            expected=rec.get('naturalImageSize',{})
            if source.format not in {'PNG','JPEG'} or list(source.size) != [expected.get('w'),expected.get('h')] or source.getexif().get(274,1) != 1:
                rec['originalImageFallback']='decoded_size_or_orientation'; return None
        with Image.open(io.BytesIO(original_bytes)) as source:
            source.verify()
        return {'path':str(path),'sha256':hashlib.sha256(original_bytes).hexdigest(),
                'policy':'plain-local-original-v1','pixel_dimensions':[expected['w'],expected['h']]}
    except (OSError,ValueError,KeyError):
        rec['originalImageFallback']='original_decode_failed'; return None


def _shoot_marker_records(page, records, out_dir: Path):
    """统一处理 deco_snapshot / svg / canvas / img 四类 marker 截图。

    各类型差异封装在 _MARKER_SHOOT_SPECS：
    - deco/svg/img 截图前后需要 JS 隐藏 / 恢复前景或兄弟节点
    - canvas 直接截图，无前后处理
    截图成功的 record 写入 rec["screenshot"]；失败的 print warning，rec 不变。
    """
    for rec in records:
        kind = rec.get("kind")
        spec = _MARKER_SHOOT_SPECS.get(kind)
        if spec is None or not rec.get("marker"):
            continue
        attr, omit_bg, pre_js, post_js = spec
        marker = rec["marker"]
        sel = f"[{attr}='{marker}']"
        out_png = out_dir / f"{marker}.png"
        original=_resolve_original_image(rec)
        if original:
            rec['originalImage']=original
            continue
        try:
            if pre_js is not None:
                isolation = page.evaluate(pre_js, marker)
                if kind == 'img' and isolation:
                    rec['imageSnapshotIsolation'] = isolation
            clip = rec.get("screenshotClip")
            if clip:
                viewport = page.viewport_size or VIEWPORT
                x0, y0 = float(clip.get("x", 0)), float(clip.get("y", 0))
                w0, h0 = float(clip.get("w", 1)), float(clip.get("h", 1))
                x, y = max(0.0, x0), max(0.0, y0)
                dx, dy = x - x0, y - y0  # 左/上超出视口被 clamp 掉的量
                w = max(1, min(w0 - dx, max(1, viewport["width"] - x)))
                h = max(1, min(h0 - dy, max(1, viewport["height"] - y)))
                page.screenshot(path=str(out_png),
                                clip={"x": x, "y": y, "width": w, "height": h},
                                omit_background=omit_bg)
                # rect 与 screenshotClip 是同一捕获框的两套坐标（slide 相对 / viewport 绝对）。
                # clip 被视口 clamp 后同步写回 rect，让 assemble 按"实际截到的区域"摆放，
                # 否则贴图相对真实位置偏移 |dx|/|dy| 像素（宽高同理被拉伸）
                if dx or dy or w != w0 or h != h0:
                    rec["rect"]["x"] += dx
                    rec["rect"]["y"] += dy
                    rec["rect"]["w"] = w
                    rec["rect"]["h"] = h
            else:
                page.locator(sel).screenshot(path=str(out_png), omit_background=omit_bg)
            rec["screenshot"] = str(out_png)
            rec['screenshot_sha256'] = hashlib.sha256(out_png.read_bytes()).hexdigest()
        except Exception as e:
            rec['captureError'] = str(e)
            print(f"    [warn] {kind} shoot fail {marker}: {e}")
        finally:
            # 截图成败都必须恢复被 pre_js 隐藏的前景，否则该页后续 deco 截图
            # 和参考页截图会缺前景（隐藏列表还会被下一个 deco 的 pre_js 覆写而永久丢失）
            if post_js is not None:
                try:
                    page.evaluate(post_js)
                except Exception as e:
                    print(f"    [warn] {kind} restore fail {marker}: {e}")


@contextlib.contextmanager
def open_deck_page(html_path: Path, browser_path: str | None = None, snapshot_scale: float = 2):
    """打开 deck 的共享 Playwright 会话。

    preflight 与 measure 传同一个 page 复用会话，省一次 Chromium 冷启动 +
    整页 networkidle 渲染（字体 / 图片 / canvas 全部重载）。"""
    if not isinstance(snapshot_scale, (int, float)) or not 1 <= snapshot_scale <= 4:
        raise ValueError('Snapshot scale must be between 1 and 4')
    url = Path(html_path).resolve().as_uri()
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=browser_path) if browser_path else p.chromium.launch()
        except Exception as primary_error:
            try:
                browser = p.chromium.launch(channel="chrome")
                print("[browser] Bundled Chromium unavailable; using installed Chrome")
            except Exception as chrome_error:
                raise RuntimeError("Neither bundled Chromium nor installed Chrome could launch") from primary_error
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=snapshot_scale)
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="networkidle")
            configure_canvas(page)
            yield page
        finally:
            browser.close()


def configure_canvas(page):
    """Read natural geometry before the adapter forces slides to the viewport."""
    from adapters import DISCOVER_JS

    settle = "async () => { await document.fonts.ready; await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); }"
    sizes_js = """() => (window.__pptxSlides || []).map(el => {
        const r = el.getBoundingClientRect();
        return [el.offsetWidth || r.width, el.offsetHeight || r.height];
    }).filter(([w,h]) => w > 0 && h > 0)"""
    page.evaluate(settle)
    explicit = page.evaluate("""() => ['pptx-width', 'pptx-height'].map(name =>
        document.querySelector(`meta[name="${name}"]`)?.content ?? null)""")
    if any(v is not None for v in explicit) and not all(v is not None for v in explicit):
        raise ValueError('Set both pptx-width and pptx-height metadata')
    page.evaluate(DISCOVER_JS)
    natural = page.evaluate(sizes_js)
    size = checked_canvas(*explicit) if explicit[0] is not None else uniform_canvas(natural)
    page.set_viewport_size(dict(zip(('width', 'height'), size)))
    page.evaluate(settle)
    page.evaluate(DISCOVER_JS)
    after = uniform_canvas(page.evaluate(sizes_js), fallback=size)
    if after != size:
        raise ValueError(f'HTML canvas changed after viewport resize: {size} → {after}; use fixed page dimensions and matching pptx metadata')
    return size


def measure(html_path: Path, out_json: Path | None = None, *,
            single_index: int | None = None,
            only_indices: set[int] | None = None,
            no_screenshots: bool = True,
            verbose: bool = True,
            page=None) -> dict:
    """实测 HTML 中所有 slide。返回 measurement dict。
    out_json 不为 None 时同步写盘；svg 截图始终落盘到 out_json 旁的 _svg_assets/。

    only_indices（1-based set）= 增量模式：只 activate + 抓取这些页，HTML 参考截图也只
    写这些页（其它页保留 anchor 旁的上轮 PNG）。返回 payload 含 _partial_indices / _total
    元数据，调用方据此与上轮 cached measurement 合并。

    single_index（0-based int，CLI 兼容）= 单页模式，互斥于 only_indices。
    """
    if single_index is not None and only_indices is not None:
        raise ValueError("measure: single_index 与 only_indices 互斥，只能给一个")
    html_path = Path(html_path).resolve()

    with contextlib.ExitStack() as _stack:
        # page 传入时复用调用方（preflight 同会话）的浏览器；否则自开自关
        if page is None:
            page = _stack.enter_context(open_deck_page(html_path))

        # canvas 内容（Chart.js / WebGL / 自绘图）的入场动画用 JS rAF 驱动，
        # 不受 CSS animation kill 影响。用通用稳定性检测，不依赖具体库名：
        # 1. 对所有 canvas 取像素 hash，等到连续两次 hash 一致即认为稳定
        # 2. 最多等 2.0s（覆盖 Chart.js 默认 1000ms + 安全余量）
        has_canvas = page.evaluate("() => document.querySelectorAll('canvas').length > 0")
        if has_canvas:
            try:
                page.wait_for_function(r"""
                () => {
                    const cans = document.querySelectorAll('canvas');
                    if (!cans.length) return true;
                    const sample = (cv) => {
                        // 抽样像素 hash，避免 readback 大数据
                        try {
                            const ctx = cv.getContext('2d', { willReadFrequently: true });
                            if (!ctx) return cv.width + 'x' + cv.height;
                            const w = Math.max(1, Math.min(cv.width, 32));
                            const h = Math.max(1, Math.min(cv.height, 32));
                            const data = ctx.getImageData(0, 0, w, h).data;
                            let acc = 0;
                            for (let i = 0; i < data.length; i += 16) acc = (acc * 31 + data[i]) | 0;
                            return acc.toString();
                        } catch (e) {
                            // WebGL canvas getContext('2d') 会 fail；用 toDataURL 短前缀
                            try { return cv.toDataURL().slice(0, 64); } catch (_) { return ''; }
                        }
                    };
                    const snap = Array.from(cans).map(sample).join('|');
                    window.__pptxCanvasSnap = window.__pptxCanvasSnap || '';
                    const prev = window.__pptxCanvasSnap;
                    window.__pptxCanvasSnap = snap;
                    return prev === snap && snap !== '';
                }
                """, timeout=2000)
            except Exception:
                # 持续循环动画的 canvas（WebGL 背景等）两帧 hash 永不一致——
                # 超时不是错误，按当前帧继续测量
                print("  [canvas] 2s 内未稳定（可能是持续动画），按当前帧继续")

        # 一次性准备：disable 动画 / 注入 force-position CSS / 跑 slide 发现
        from adapters import PREPARE_JS, ENUMERATE_JS, ACTIVATE_JS
        page.evaluate(PREPARE_JS)
        page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")

        total = page.evaluate(ENUMERATE_JS)
        if verbose:
            print(f"[measure] 共 {total} 张 slide")

        # svg / 参考截图的落盘位置：依附于 out_json；无 out_json 时落到临时目录
        if out_json is not None:
            anchor = Path(out_json)
            anchor.parent.mkdir(parents=True, exist_ok=True)
        else:
            anchor = Path(tempfile.mkdtemp(prefix="h2p_meas_")) / "measurements.json"

        screenshots_dir = Path(str(anchor.with_suffix("")) + "_screenshots")
        if not no_screenshots:
            screenshots_dir.mkdir(exist_ok=True, parents=True)

        svg_dir = anchor.parent / (anchor.stem + "_svg_assets")
        svg_dir.mkdir(parents=True, exist_ok=True)

        if single_index is not None:
            indices = [single_index]
        elif only_indices is not None:
            # 1-based 入参 → 0-based 内部循环
            indices = sorted(i - 1 for i in only_indices)
            out_of_range = [i + 1 for i in indices if i < 0 or i >= total]
            if out_of_range:
                raise ValueError(f"measure: only_indices {out_of_range} 超出 HTML 实际页数 {total}")
        else:
            indices = list(range(total))

        slides_data = []
        for i in indices:
            page.evaluate(ACTIVATE_JS, i)
            # 等一帧让 .active 类等切换后的 computed style / transform 生效
            page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")

            # counter 动画稳定性等待：识别 3 种常见 counter 约定（不是全部，足以覆盖绝大多数手写 JS counter）：
            #   `data-target` / `data-count-to` / `data-counter`
            # 等到 textContent 包含 dataset 里对应的目标值再抓；超时强制 set 终值。
            # 不等的话会拿到动画中段帧（如 "1+ 0+ 0+ 3" 而非终值 "42+ 20+ 7+ 100"）。
            # 注：用了其它 attr 名的 deck（罕见）会被跳过；agent 可在 audit 阶段发现数字错位
            # 并把对应 HTML 改成上述任一约定，下次 convert 即修复。这是 script 兜底 + agent 兜底的分工。
            page.evaluate(r"""() => {
                // 把多约定 counter 统一暴露给后续 wait / fallback
                const SELECTOR = '[data-target], [data-count-to], [data-counter]';
                window.__pptxCounters = Array.from(document.querySelectorAll(SELECTOR));
                window.__pptxCounterTarget = (el) =>
                    el.dataset.target || el.dataset.countTo || el.dataset.counter || '';
            }""")
            has_counter = page.evaluate("() => (window.__pptxCounters || []).length > 0")
            if has_counter:
                try:
                    page.wait_for_function(
                        """() => (window.__pptxCounters || []).every(c => {
                            const t = window.__pptxCounterTarget(c);
                            return t && c.textContent.includes(t);
                        })""",
                        timeout=2500,
                    )
                except Exception:
                    # IntersectionObserver 没触发或别的原因没跑完——强制设终值兜底
                    page.evaluate("""() => {
                        for (const c of (window.__pptxCounters || [])) {
                            const t = window.__pptxCounterTarget(c);
                            if (t) c.textContent = t;
                        }
                    }""")
            data = page.evaluate(EXTRACT_JS, i)

            # 统一截图四类 marker 元素：deco_snapshot / svg / canvas / img
            # 类型差异封装在 _MARKER_SHOOT_SPECS（pre/post JS、omit_background）
            _shoot_marker_records(page, data.get("records", []), svg_dir)

            slides_data.append(data)
            if no_screenshots:
                if verbose:
                    print(f"  slide {i+1:02d}: {len(data.get('records', []))} records")
            else:
                # 参考截图是数据产物，不能挂在 verbose 日志开关下
                ss = screenshots_dir / f"slide_{i+1:02d}.png"
                # 当前 active slide 总是带 data-pptx-target；不依赖 adapter selector
                page.locator("[data-pptx-target]").first.screenshot(path=str(ss))
                if verbose:
                    print(f"  slide {i+1:02d}: {len(data.get('records', []))} records → {ss.name}")

        # 清理页号超过当前总页数的上轮参考图残留（deck 缩短后的"幽灵页"），
        # 否则 Stage 5b 会把它们当真实页配对进 compare 图
        if not no_screenshots:
            for p in screenshots_dir.glob("slide_*.png"):
                m = re.fullmatch(r"slide_(\d+)\.png", p.name)
                if m and int(m.group(1)) > total:
                    try:
                        p.unlink()
                    except OSError:
                        pass

        if single_index is not None:
            payload = slides_data[0]
        elif only_indices is not None:
            payload = {
                "slides": slides_data,
                "_partial_indices": sorted(only_indices),
                "_total": total,
            }
        else:
            payload = {"slides": slides_data}

        if out_json is not None:
            Path(out_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            if verbose:
                print(f"wrote {out_json}")

    return payload


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    no_screenshots = "--no-screenshots" in flags
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    html_path = Path(args[0]).resolve()
    out_json = Path(args[1]).resolve()
    single_index = int(args[2]) if len(args) >= 3 else None
    measure(html_path, out_json, single_index=single_index, no_screenshots=no_screenshots)


if __name__ == "__main__":
    main()
