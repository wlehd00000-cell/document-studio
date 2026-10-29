# Public-source fidelity study — 2026-10-29

**Product:** Document Studio `0.1.0-alpha.1` (new independent plugin, not another plugin's v2).
**Scope:** Two official, publicly reachable corporate PDFs. **This is a source-to-style-hypothesis test, not a claim of authentic or pixel-identical company document reproduction.** The named companies do not endorse this study.

## Source evidence and provenance

| Dataset | Official URL | Original pages and canvas | Source SHA-256 |
|---|---|---|---|
| Suntory Group, *Corporate Overview Fact Sheet 2025* | [Official PDF](https://www.suntory.com/about-us/pdf/corporate_overview_fact_sheet_2025.pdf) | 4 pages, A4 portrait (595.28 × 841.89 pt) | `0a112b83349d67bd148989f54e5e2b67ad869eaa62ff9ec513377d90d92a664b` |
| Seven & i Holdings, *Corporate Outline FY2025* | [Official PDF](https://www.7andi.com/en/ir/file/library/co/pdf/2026_all_b_en.pdf) | 31 pages, A4 landscape (841.88 × 595.28 pt) | `9da00576d63716235be408b40a68b1f4fd30a56c8e20866ec309f86c3d6eedc7` |

All PDF originals, rendered source pages, full extracted text, source registries and draft real-company Company Packs were kept in a **temporary evaluation workspace outside the repository**. The repo contains only measurements and independently authored style probes; no original pages, corporate logos, fonts, product images or text excerpts are redistributed.

## Test protocol

1. Register the public PDF with a source URL and SHA-256; set `distribution_authorized=false` and `allow_excerpt_in_pack=false`.
2. Extract all PDF pages' text bounds, font-name strings, page dimensions, images and measured vector fill/stroke color weights. Render and visually inspect representative original pages locally.
3. Infer **draft** styling from only the **first two pages** of each document. Reserve the remaining 2 / 29 pages as holdout.
4. Measure `exact_color_recall_at_4`: intersection of the four proposed colors with the top eight chromatic vector colors in holdout, divided by up to four observable holdout colors. This is **exact color recurrence**, **not** full visual fidelity, and does not evaluate semantics, visual prominence, photographic colors, or output licensing.
5. Generate a company-specific draft Company Pack and a one-page **independently written fictional-content HTML style hypothesis**, render the hypothesis to PDF, and visually compare it with the official PDF. No original source wording or artwork is inserted into the preview.
6. Test validation and export gates. A draft Company Pack may be inspected but must be rejected for approved production and public ZIP export.

## Measured results

| Metric | Suntory | Seven & i |
|---|---:|---:|
| Pages extracted | 4 / 4 | 31 / 31 |
| Pages with observed vector colors | 4 / 4 | 31 / 31 |
| Pages containing raster imagery | 2 / 4 | 31 / 31 |
| Extracted text blocks | 155 | 1,585 |
| First two-page dominant proposed colors | `#50C6DB`, `#BEE5EF`, `#C5E8F1` | `#00A650`, `#F5821F`, `#ED1C24` |
| Exact chromatic holdout recurrence @ 4 | **1 / 4 (25%)** | **3 / 4 (75%)** |
| Draft Company Pack creation | PASS | PASS |
| Real-company pack marked approved | **No** | **No** |
| Actual company font installation/rights | UNVERIFIED | UNVERIFIED |
| Editable PPTX rendering fidelity | NOT TESTED | NOT TESTED |

The full metric inventories, including exact source hashes, can be inspected in [Suntory metrics](suntory-metrics.json) and [Seven & i metrics](seven-i-metrics.json). Values may change as the extraction and color ranking methods are improved; this report describes one controlled run.

### Defect discovered and fixed

The initial PDF parser read only **text-span colors**. Its first Suntory palette was therefore headed by the near-black text color `#231F20`, and its generated palette used generic fallback colors unrelated to the document. The original pages clearly use cyan rules, section strips and diagram strokes. The extraction code now records PDF vector fill/stroke colors with bounded spatial weighting; the draft palette ranks chromatic graphics and reuses source pastels where available. If the input has only one chromatic hue, remaining candidate colors are **provisional tints/shades** of that hue rather than unrelated default corporate colors. Tests cover both PDF vector colors and one-hue source behavior.

This remains imperfect: Seven & i's 31-page report contains thousands of small map/chart primitives, many neutral dots and significant raster content, so graphic counts are **not** a statistically calibrated proxy for brand prominence.

## Manual image comparison — official pages vs independent style probes

The generated one-page probes are [Suntory HTML](suntory-style-hypothesis.html) and [Seven & i HTML](seven-i-style-hypothesis.html). Both visibly label their figures as fictional and disclaim official status.

| Fidelity dimension | Suntory observation | Seven & i observation | Status |
|---|---|---|---|
| Page orientation | Portrait matched | Landscape matched | **PASS** |
| Main color family | Cyan and pale-cyan clearly transfer | Green, orange and red transfer | **PARTIAL** — exact hues transfer, role ranking needs review |
| Typography | PDF names `SUNTORYSyntax-*` / `SuntoryGothic*`, but preview substitutes system sans | PDF names `Gotham-*` / Japanese fonts, but preview substitutes system sans | **NOT VERIFIED** — names are not font licenses |
| Cover hierarchy and composition | Original centers an oversized year/title between cyan rules and places dense tables / organization graphics beneath; probe uses a generic upper-left heading and two columns | Original uses sweeping diagonal multicolor bands, large empty space and a lower-right title; probe uses a horizontal strip and generic two columns | **DOES NOT REPRODUCE** |
| Inner-page layout patterns | Original uses cyan sectional headers and product-photo grids beside company lists | Original uses orange chapter navigation, flow illustrations, complex map/charts | **DOES NOT REPRODUCE** |
| Writing register | Text-block/sentence-length aggregates captured; source-specific terminology and rhetorical patterns not validated | Same, despite a much larger corpus | **NOT VERIFIED** |

**Interpretation:** The current pipeline can extract useful starting evidence and create **visually recognizable color hypotheses**. It **cannot yet faithfully recreate the two companies' document composition, typography, graphics, image treatment or writing voice** from these PDFs. The `25%`/`75%` values above must never be marketed as document-recreation accuracy.

## Release and privacy gates

- Two real-company draft packs were created outside the repository and validated structurally.
- `--require-approved` intentionally rejected the draft Seven & i pack with `Pack is not approved for production`.
- The public ZIP exporter intentionally rejected the draft Suntory pack with `Only explicitly approved Company Packs may be exported`.
- The previews contain **fictional sample data**, no source text or logos. Actual company usage requires visual human review and authorization; public availability of a PDF is **not** permission to redistribute its artwork or font files.

## What needs to improve before claiming high fidelity

1. **Layout grammar per document family:** identify cover/header/navigation/grid/chart/image patterns; promote reviewed page-family templates instead of applying one generic layout. Use visual evidence, not only PDF vector counts.
2. **Typography and rendering:** separate observed font-name strings from licensed available fonts, measure actual text-width/linebreak similarity, and run visual HTML/PPTX render gates.
3. **Asset-aware analysis:** distinguish logo, reusable licensed imagery, diagrams and photo grids. Record observed image placement without copying assets into public packages.
4. **Writing DNA:** sample multiple official documents and genres per company, distinguish editorial voice from a fact-sheet's short labels, and have an expert review actual style examples where permitted.
5. **Evaluation v2:** compare equivalent content and matched page families using rendered-image layout metrics (bounding-box alignment, perceived hierarchy and color-distance metrics), plus human review. Do not collapse them into one uncalibrated percentage.

## Repeat locally

Download each official PDF from the URLs above to a **separate private or temporary directory**, then run:

```bash
python scripts/evaluate_public_company.py /path/to/official.pdf \
  --company 'Company Name' --official-url https://official.example.com/corporate.pdf \
  --language en-US --training-pages 2 \
  --output /private/evaluation.json \
  --preview-html /private/independent-style-hypothesis.html
```

The CLI never quotes original paragraphs or embeds PDF images in its JSON or preview. Its output is a **measurement and draft hypothesis**, not an approved corporate identity system.
