# Office-printer A4 reports

Use this conditional profile when the user requests an office-printer report or A4 printing: “인쇄용 보고서”, “문서용/사무용 프린터”, “A4 인쇄”, “印刷用報告書”, “事務用プリンター”, “A4出力”, “office-printer report”. PDF, reading PPTX or A4 size alone does not select it. An explicit accepted template or a user request to retain color branding can override individual choices. This profile does not impose a two-page limit on every report.

## Reuse the accepted task

An existing document's print adaptation keeps its language, reader, purpose, production mode, requested outputs, required copy, page cap, original assets and factual/approval status. Ask only about a consequential unresolved change. Printer model, monochrome mode and binding are optional context, not a new intake gate. Do not restart a six-field interview for “컬러띠 빼고 A4 인쇄용으로”. In collaborative work, inspect the changed HTML, reuse the user's relevant acceptance/delegation and complete the authorized files.

Record `output_profile=office-print` in the existing configuration/brief, with the user's actual use and any known printer constraints. Record geometry review, PDF review, PPTX review, physical print test and user acceptance separately. Do not treat this package's sample checks as acceptance of a future report.

## Dense printed composition

- Remove the decorative page-top color band from authored HTML and editable exports. Remove its reserved height too; hiding a band only in print media leaves the screen design and PPTX inconsistent. A thin gray heading rule is sufficient.
- Use the neutral `palette.office_print` values in [canonical design-tokens.json](../system/design-tokens.json) for paper, body/headings, secondary text, rules and table headers. Replace large decorative color fills, theme shadows and ornamental cards. Preserve emphasis through headings, weight, spacing, direct labels and table grouping.
- Charts and conditions must remain distinguishable in monochrome. Use explicit labels, line styles or patterns; never rely on blue/green/orange alone for status or category. Keep facts, proposals and agreement-needed items in words.
- Preserve source logos, posters, product packages, photos and factual diagrams, with their original artwork, aspect ratio and color. Do not redraw, generically replace or desaturate official assets because the page is for a printer. Explicit grayscale-file requests may transform an output copy; retain the originals.
- Use canonical `profiles.office_print` typography/leading and font. `office-print-dense` remains a compatibility alias. These preserve the reviewed office-print candidate values; check the actual used Korean/Japanese glyph font. Values are production defaults, not official DEMO CI or a universal accessibility minimum.
- Preserve the user's required information. For a two-page executive brief, combine introduction, plan and goals into those two pages and avoid extra cover/thanks pages. First shorten duplicate wording, tighten title/section gaps, rebalance columns and reduce redundant image area. Keep essential images, conditions, units, sources and footer readable; do not keep shrinking body text to conceal overflow.

## Physical A4 and safe area

A4 portrait is exactly **210 × 297mm**, landscape **297 × 210mm**. At 96 CSS px/in the portrait canvas is approximately **793.700787 × 1122.519685px**, not exactly 794 × 1123px. Use mm or the exact ratio for printed reports. `1pt = 4/3 CSS px` at this scale. An HTML-to-PPTX converter must preserve the same physical page rather than round its canvas silently.

Use `profiles.office_print.print.safe_margin_mm` and its separate content/footer reserves as the starting geometry, including headers, logos, captions, sources, page numbers and footer rules. Reserve additional space above the footer so body/source text cannot overlap it. Known printer, duplex or binding requirements take precedence; unknown-printer geometry does not certify an actual device's printable area.

Use the canonical token-generated shared CSS or scaffold variables first, then [conditional CSS](../assets/demo-esg-design/office-print-report.css) after project styles. Do not copy the print stylesheet alone without its canonical variables. Add `office-print` and `data-output-profile="office-print"` to the body; set exact `--page-width/--page-height` and `@page{size:A4 portrait;margin:0}` (landscape when selected). It covers the starter `.page` and shared `.demo-page` structures. Remove `.top-rule`/`.demo-rule` markup when adapting a source. Custom selectors need deliberate adaptation, not a broad override of every image or graphic.

The scaffold accepts `--output-profile office-print` and defaults to A4 portrait/report density for that profile. It also recognizes explicit print-use language in the resolved `--output-format`. An accepted A4 landscape canvas remains landscape. It rejects widescreen/ESG canvases and live-presentation density combined with office-print; resolve the contradiction before generating. New document decoration follows the canonical purpose/family choice; a decorative band is opt-in outside office print.

For example, after the existing intake is resolved:

```text
python scripts/scaffold_report.py <new-project> --title "印刷用報告書" --language ja --genre report --interaction-mode one_shot --audience "社内責任者" --reader-action "計画と目標を確認する" --output-format "A4印刷用PDFと編集可能PowerPoint" --output-profile office-print
```

The four-page scaffold is a working example, not a finished report or an imposed page count. Replace example copy and compose the actual page cap before review/export.

## HTML review

Wait for local fonts and images, inspect actual used typefaces and render the final physical size. Check dense pages at 100% and close-up, Korean word flow/Japanese kinsoku, image identity/crop, every page edge and the body-to-footer gap. Recheck global changes across their affected pages/exports. The text-flow renderers include `.source` **and `.sources`** by default; for a custom structure select its source/caption blocks explicitly. Use the existing content/boundary selectors to include source notes in footer-clearance measurement.

Measure visible text/image/rule bounds rather than only an outer container, and check print media as well as screen HTML. No overflowing, clipped or omitted content is allowed. A contact sheet alone cannot verify small table/caption text. A neutral authored palette is not evidence that an unlabelled colored chart still explains its data in monochrome.

## PDF and editable PPTX

**PDF:** export exact A4 at 100%, without browser headers/footers or automatic fit-to-page shrinkage. Keep meaningful gray header fills when exporting, remove decorations in the source and avoid rasterizing the full report. Verify the exported page count, MediaBox/CropBox dimensions, native selectable/copyable text, actual glyphs, fonts and original assets, and inspect rendered pages. If a renderer rounds a page box, correct the output copy and recheck it; do not assert exact A4 from an HTML declaration alone. Check Unicode extraction when CJK copies differ from visible glyphs. Type3 fonts with actual glyph programs and ToUnicode can be portable; a FontFile-only test is insufficient.

**PPTX:** preserve native editable paragraphs, labels and individual table cells/simple shapes. A full-slide bitmap does not meet this requirement. A4 portrait is **7560000 × 10692000 EMU** (landscape reversed). Verify source physical fonts, actual typeface names and embedded resources separately. Prefer private font resolution/subsetting/embedding to installing fonts; system/user font installation retains the existing authorization rule.

Inspect the actual PowerPoint/LibreOffice rendering of both small tables and surrounding paragraphs/footers. For a new authoring path or a spacing/border symptom, check these known conversion failure modes:

1. A whole-shape base style applied after rich runs may overwrite their small inline sizes/bold/colors. Apply the base before runs or restore verified per-run styles; preserve visible label spacing.
2. When writing OOXML directly, keep `a:lnSpc`, `a:spcBef`, `a:spcAft` before `a:defRPr` inside `a:pPr`. Use source line height and physical scaling; for exact 96dpi A4, `a:spcPts@val = round(line_height_px × 75)` in hundredths of a point.
3. Native table cell properties require schema order: `a:lnL`, `a:lnR`, `a:lnT`, `a:lnB` before fills. Incorrect order can show heavy/default borders while package checks pass. Preserve intentionally absent borders and gray source widths (1 CSS px = 9525 EMU at this scale).
4. Theme/table styles or shape `p:style` can restore unwanted borders/shadows. Inspect the rendered result and remove an unwanted effect in the affected output component; do not strip intended source styling blindly.

These are symptom-specific checks, not a requirement to replace a working converter. Preserve source HTML; conversion repairs belong in an audited working copy/export stage. A renderer failure leaves PPTX visual QA unverified even when package/editability checks pass.

## Delivery

Deliver the requested files with compact evidence: pages/A4 dimensions, source text/asset preservation, measured margins/footer clearance, PDF checks and PPTX editability/render checks. A self-contained HTML, print PDF and editable PPTX have distinct validation states. State any missing renderer or physical print test accurately. A file passing geometry review is ready for a print check, not evidence that it has already been printed on the user's device.
