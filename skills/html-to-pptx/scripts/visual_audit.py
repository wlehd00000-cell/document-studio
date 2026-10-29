"""visual_audit.py — Stage 5b 视觉审计物料。

产出 `<out>_audit/`：
- `slide_NN_compare.png` × N — HTML | PPT 双栏拼图
- `audit_index.json` — 每页元数据 + 结构化告警
- `audit_prompt.md` — 给上游 VLM agent 的审计指南
"""
import json
import re
from pathlib import Path

from local_config import audit_mode


AUDIT_PROMPT_MD = """# Visual review

Use the current agent for review. Delegate only if separately authorized and useful.
Read audit_index.json for page paths, failed comparisons and structural warnings.
Left is HTML; right is rendered PPTX. The comparison heading is not slide content.

Inspect canvas dimensions, content coverage, text legibility, semantic line breaks,
tables, captions, diagram connections and image crops. Open warned, dense and changed
pages at full size. A contact sheet alone cannot certify small text. In incremental
mode review fresh_indices and retain prior findings for unchanged pages.

Report concrete visual evidence with page number, affected object and consequence.
Separate conversion defects from source design issues; fix source copy/layout in
authored HTML, conversion-only behavior in the audited copy. Ordinary antialiasing
and harmless pixel drift need no repair. Do not dismiss missing conditions, isolated
units, broken names, text overlaps or misleading diagram links as engine differences.
Do not assume an OK result or fabricate findings to meet a quota.

Save compact audit_findings.md with reviewed pages, actual renderer, findings and
remaining limits. Label contact-only and unrendered pages accurately. After two
unsuccessful repairs of the same issue, state the limitation rather than looping.
Missing PPT renders mean visual QA is unverified, not passed.
"""


def build_audit_prompt(mode: str, contact_sheets: list[dict]) -> str:
    contact_lines = "\n".join(
        f"- {item['path']} (pages {item['pages'][0]:02d}-{item['pages'][-1]:02d})"
        for item in contact_sheets
    ) or "- none"
    if mode == "manual":
        instructions = "Saved manual-review mode: provide the review materials and mark visual review pending. Do not claim an agent visual pass."
    elif mode == "page":
        instructions = "Inspect every target page at full size; use contact sheets for navigation."
    else:
        instructions = "Triage: inspect the contact sheet, then full-size warned, dense, changed and representative pages. Missing or legacy ask settings use triage; no preference interview is required."
    return f"{instructions}\n\n## Contact sheets\n\n{contact_lines}\n\n{AUDIT_PROMPT_MD}"


def build_compare_image(html_png: Path, ppt_png: Path, out_path: Path, page_idx: int):
    """生成单页 HTML | PPT 双栏拼图。"""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    # 跨平台 title 字体兜底：arial=Windows、DejaVuSans=Linux/PIL bundled、Helvetica=macOS。
    # 都找不到时 load_default() 是 bitmap，36pt 显示效果差但不阻塞 audit。
    title_font = None
    for name in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
        try:
            title_font = ImageFont.truetype(name, 36)
            break
        except Exception:
            continue
    if title_font is None:
        title_font = ImageFont.load_default()
    try:
        html_img = Image.open(html_png).convert("RGB")
        ppt_img = Image.open(ppt_png).convert("RGB")
    except Exception as e:
        print(f"  [warn] compare build fail page {page_idx}: {e}")
        return None

    width, height = html_img.size
    mismatch = abs(ppt_img.width / ppt_img.height - width / height) > 0.005
    if mismatch:
        print(f"  [warn] page {page_idx}: canvas aspect mismatch HTML {html_img.size}, PPT {ppt_img.size}")
    # Preserve each aspect ratio so a wrong canvas cannot be hidden by stretching.
    ppt_img = ImageOps.contain(ppt_img, (width, height))
    right_x = width + 8
    bar_h = 60
    composite = Image.new("RGB", (width * 2 + 8, height + bar_h), (255, 255, 255))
    d = ImageDraw.Draw(composite)
    # 标题栏
    d.rectangle((0, 0, width, bar_h), fill=(245, 245, 247))
    d.rectangle((right_x, 0, width * 2 + 8, bar_h), fill=(255, 220, 220) if mismatch else (255, 245, 235))
    d.text((16, 12), f"HTML reference  ·  slide {page_idx:02d}", fill=(20, 20, 20), font=title_font)
    d.text((right_x + 16, 12), f"PPT output  ·  slide {page_idx:02d}" + (" [SIZE]" if mismatch else ""), fill=(20, 20, 20), font=title_font)
    # 中间分隔
    d.rectangle((width, 0, right_x, height + bar_h), fill=(200, 200, 200))
    composite.paste(html_img, (0, bar_h))
    composite.paste(ppt_img, (right_x + (width - ppt_img.width) // 2,
                              bar_h + (height - ppt_img.height) // 2))
    composite.save(out_path, optimize=True)
    return out_path


def build_contact_sheets(out_dir: Path, page_indices: list[int], per_sheet: int = 6) -> list[dict]:
    """Build compact overview sheets from compare images for triage/manual audit."""
    from PIL import Image, ImageDraw, ImageFont

    for old in out_dir.glob("audit_contact_*.png"):
        try:
            old.unlink()
        except OSError:
            pass

    title_font = None
    for name in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
        try:
            title_font = ImageFont.truetype(name, 20)
            break
        except Exception:
            continue
    if title_font is None:
        title_font = ImageFont.load_default()

    contact_sheets: list[dict] = []
    # 2 列大 tile：tile 越大 triage 第 1 轮分流越准，假入围页直接浪费 sub-agent 轮次
    cols = 2
    tile_w = 1150
    label_h = 28
    gap = 28
    margin = 18

    for start in range(0, len(page_indices), per_sheet):
        chunk = page_indices[start:start + per_sheet]
        images = []
        for idx in chunk:
            path = out_dir / f"slide_{idx:02d}_compare.png"
            if not path.exists():
                continue
            img = Image.open(path).convert("RGB")
            tile_h = int(round(tile_w * img.height / img.width))
            images.append((idx, img.resize((tile_w, tile_h))))
        if not images:
            continue

        rows = (len(images) + cols - 1) // cols
        tile_h = images[0][1].height
        sheet_w = margin * 2 + cols * tile_w + (cols - 1) * gap
        sheet_h = margin * 2 + rows * (label_h + tile_h) + (rows - 1) * gap
        sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
        draw = ImageDraw.Draw(sheet)

        for pos, (idx, img) in enumerate(images):
            col = pos % cols
            row = pos // cols
            x = margin + col * (tile_w + gap)
            y = margin + row * (label_h + tile_h + gap)
            draw.text((x, y), f"slide_{idx:02d}", fill=(20, 20, 20), font=title_font)
            sheet.paste(img, (x, y + label_h))

        out_path = out_dir / f"audit_contact_{chunk[0]:02d}_{chunk[-1]:02d}.png"
        sheet.save(out_path, optimize=True)
        contact_sheets.append({
            "file": out_path.name,
            "path": str(out_path),
            "pages": chunk,
        })

    return contact_sheets


def build_audit_package(pptx_path: Path, html_screenshots_dir: Path, ppt_screenshots_dir: Path,
                        self_check_result: dict, preflight_result: dict | None,
                        out_dir: Path,
                        only_indices: set[int] | None = None) -> dict:
    """产出 audit 物料包：compare 图 × N + audit_index.json + audit_prompt.md。

    only_indices 给定时走增量：只对列出的页重建 compare 图，其它页保留 out_dir 里上轮的
    slide_NN_compare.png（缓存缺失则兜底重建）。audit_index.json 标记每页 fresh=true/false，
    上游 agent 看 fresh_indices 决定本轮要复审哪些页。

    返回 dict 描述包内容（方便 convert.py 在终端打印）。
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # 按文件名页号配对（不是 sorted 列表位置）：渲染单页空洞时位置配对会让空洞
    # 之后每张 compare 图左右两半错位成不同 slide，VLM 报一串假 finding
    def _pngs_by_no(d: Path) -> dict[int, Path]:
        out = {}
        for p in d.glob("slide_*.png"):
            m = re.fullmatch(r"slide_(\d+)\.png", p.name)
            if m:
                out[int(m.group(1))] = p
        return out

    html_by_no = _pngs_by_no(html_screenshots_dir)
    ppt_by_no = _pngs_by_no(ppt_screenshots_dir)
    # 权威页数：渲染器报告的 pptx 总页数；缺失时退回两侧共同覆盖的最大页号
    n = self_check_result.get("rendered_total") or max(
        set(html_by_no) & set(ppt_by_no), default=0)

    # 清理超过总页数的上轮 compare 残留（deck 缩短后的"幽灵页"）
    for p in out_dir.glob("slide_*_compare.png"):
        m = re.fullmatch(r"slide_(\d+)_compare\.png", p.name)
        if m and int(m.group(1)) > n:
            try:
                p.unlink()
            except OSError:
                pass

    pages_meta = []
    pages_by_idx = {p["idx"]: p for p in self_check_result.get("pages", [])}
    preflight_by_idx = {s["index"]: s for s in (preflight_result or {}).get("slides", [])}

    fresh_set: set[int] = set()
    skipped_set: set[int] = set()
    failed: dict[int, str] = {}
    for idx in range(1, n + 1):
        compare_path = out_dir / f"slide_{idx:02d}_compare.png"
        html_png = html_by_no.get(idx)
        ppt_png = ppt_by_no.get(idx)
        if html_png is None or ppt_png is None:
            failed[idx] = "missing-html-png" if html_png is None else "missing-ppt-png"
        else:
            must_rebuild = (only_indices is None
                            or idx in only_indices
                            or not compare_path.exists())
            if must_rebuild:
                if build_compare_image(html_png, ppt_png, compare_path, idx) is None:
                    failed[idx] = "compare-build-failed"
                else:
                    fresh_set.add(idx)
            else:
                skipped_set.add(idx)
        page_info = pages_by_idx.get(idx, {})
        preflight_info = preflight_by_idx.get(idx, {})
        risks = [r["code"] for r in preflight_info.get("risks", [])]
        pages_meta.append({
            "index": idx,
            "compare_image": None if idx in failed else str(compare_path.name),
            "html_screenshot": html_png.name if html_png else None,
            "ppt_screenshot": ppt_png.name if ppt_png else None,
            "structural_level": page_info.get("level"),
            "preflight_risks": risks,
            "preflight_confidence": preflight_info.get("confidence"),
            "fresh": idx in fresh_set,
            **({"compare_failed": failed[idx]} if idx in failed else {}),
        })

    mode = audit_mode()
    contact_sheets = build_contact_sheets(
        out_dir, [p["index"] for p in pages_meta if not p.get("compare_failed")])

    index_data = {
        "pptx": str(pptx_path.name),
        "pptx_path": str(pptx_path),
        "total_pages": n,
        "audit_mode": mode,
        "contact_sheets": contact_sheets,
        "instructions_file": "audit_prompt.md",
        "findings_output": "audit_findings.md",
        "incremental_mode": only_indices is not None,
        "fresh_indices": sorted(fresh_set),
        "cached_indices": sorted(skipped_set),
        "failed_indices": sorted(failed),
        "pages": pages_meta,
        "self_check_summary": {
            "engine": self_check_result.get("engine"),
            "structural_warnings_count": len(self_check_result.get("warnings", [])),
        },
    }

    (out_dir / "audit_index.json").write_text(
        json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "audit_prompt.md").write_text(build_audit_prompt(mode, contact_sheets), encoding="utf-8")

    return {
        "out_dir": str(out_dir),
        "pages": n,
        "audit_mode": mode,
        "contact_sheets": contact_sheets,
        "fresh": sorted(fresh_set),
        "cached": sorted(skipped_set),
        "failed": sorted(failed),
        "incremental": only_indices is not None,
        "index": str(out_dir / "audit_index.json"),
        "prompt": str(out_dir / "audit_prompt.md"),
    }
