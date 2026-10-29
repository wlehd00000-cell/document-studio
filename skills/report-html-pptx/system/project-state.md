# One project, current inputs, scoped QA

This is the canonical revision and release contract for every authoring route.
The [CLI](../scripts/project_state.py) uses standard-library Python and one
`content/project-state.json` inside the working project. It does not create a
second manuscript, copy evidence into a database, install tools or contact a
service. Keep prose in its existing files and store paths/IDs here.

## Registered sources and generated artifacts

Register the actual brief, canonical copy, data, official assets, fonts, style,
layout and tool/configuration files which influence the requested output.
Sources have no production dependencies. Generated charts, HTML, native decks,
PDF/PPTX and rendering derivatives are artifacts with explicit dependency IDs.
An export depends on the canonical authored artifact; a chart depends on the
data and its calculation/specification. Register changes to the graph rather
than retaining obsolete edges. Missing files, cycles and unsafe paths fail.

Paths are project-relative with forward slashes. Materialize needed approved
assets and fonts inside the project; the state tool rejects absolute paths,
parent traversal, drive/UNC paths, NTFS streams and links escaping the root.
Source acquisition may still read user-designated external files through the
normal source workflow. The manifest records their in-project production copy,
not permission to read arbitrary locations. Do not register a URL as a file.
Remote resources must be acquired/hash-bound before certifying a reusable
render. Keep original source locator/rights/provenance in the evidence record.

`snapshot` is a **production receipt**, recorded after actually producing the
artifact. It hashes artifact bytes, immediate dependencies and their complete
upstream graph, plus page order. It cannot snapshot an artifact whose generated
dependency is stale. It is not a QA approval and must not be used to bless an
unrebuilt export. `register` alone never grants freshness to an artifact.

At every reuse/delivery, `status` reads live bytes. A changed copy invalidates
its layout and export; changed data invalidates its chart; a replaced image or
font invalidates relevant layout/review/export. An updated HTML with an old
PPTX is reported stale even though both files exist. Timestamps and completion
flags are not freshness evidence. A hash confirms sameness, not claim accuracy
or whether old external facts are still current; Research owns that review.

### Approved Layout Grammar dependency

An approved company scaffold registers its immutable policy snapshot, including
reviewed Layout Grammar and human rule decisions, but **does not** register an
invented page-specific grammar plan from placeholder starter content. After the
final manuscript, `plan_layout_grammar.py --project PROJECT --page-brief
content/page-brief.json --company-pack PACK` registers `page_brief` as source,
`layout_plan` as an artifact depending on `page_brief`, canonical `copy` and
company-pack snapshot, and adds `layout_plan` to the canonical `html` artifact's
dependencies. Page IDs follow the approved brief; HTML must be recomposed and
freshly snapshotted after this graph change. The plan retains `pending_render_review`.

Run `audit_layout_grammar.py --project PROJECT` after authoring actual HTML.
Its separate `qa/layout-grammar-application.json` records source/checker hashes,
semantic anchors, browser-measured relationships, page screenshots and
`PASS|FAIL|UNVERIFIED`. On an approved-grammar page, missing, stale, failed or
unverified records block `production_contract.py` delivery even when a
different design measurement passed. A changed pack, manuscript, page plan,
HTML, canvas, font or project asset invalidates the bound receipt. Geometry
PASS is *not* a human/vision review; the independent `visual` layer still needs
actual rendered evidence. No matching accepted grammar gives an explicit neutral
fallback and does not claim an official corporate layout.

## Scoped reuse

Use `--pages all` for fonts, global CSS, global settings and topology. Register
genuinely page-local copy/assets with `--pages 1,2`. All is the safe default.
If the canonical copy is one undivided file, changing it invalidates all its
dependent scope. Do not assign narrow scope to a shared resource for speed.

For valid HTML with `.page` or `data-pptx-slide` roots, the tool fingerprints
exact page source slices and the shared shell. Separate receipts per page let
an unchanged page retain review after another page changes and the artifact
is produced again. Global shell/CSS/font changes invalidate every affected
page. Unknown/malformed markup falls back to the whole-file hash. Native PPTX
currently uses conservative whole-file invalidation; it does not claim safe
page reuse from similar-looking screenshots. Converter cache validity is a
separate implementation check, not a review receipt.

## Five independent review layers

| Layer | Evidence and scope | Release use |
|---|---|---|
| `automated` | Actual text-flow audit or built-in OOXML verification; bound dependencies, implementations and measured pages | Required for canonical artifact and requested export |
| `editorial` | Source equivalence, conditions/status and language, with per-page observations and actual hashed evidence | Required for canonical artifact |
| `visual` | Hierarchy, actual-size readability and assets/crop, with per-page rendered evidence | Required for canonical artifact |
| `export` | Final file integrity, actual rendered comparison and editability expectations | Required for requested export |
| `user_acceptance` | Actual human decision with a preserved user-response locator/file | Required only when the user/task explicitly requires acceptance before delivery |

Automated checks do not approve prose, visual quality or user acceptance.
HTML visual review does not approve the exported PPTX/PDF. Output existence
does not approve its appearance. `ready` means required current checks are
complete with no blocking findings; it never means user-accepted, installed
on an account or deployed across the organization. Preserve acceptance as
pending/not assessed when no human decision exists. Never invent a human ID.

All pages in a target's declared scope need current coverage. Partial review
does not pass a whole document, including after a global font change. Newest
current receipt owns its observed pages; it can resolve an earlier finding on
those pages, but cannot erase findings elsewhere. Old receipts remain history
and are marked stale. Separate receipt files need no parallel stage database.

## Findings and the gate

Use only `blocking` or `warning` severity. Source/data errors, unsupported
critical claims, omitted required conditions/assets, clipped/unreadable text,
failed font/image loading, broken page structure or export corruption block
ready delivery. The rendered text bounds after manual line breaks must fit
the box and avoid neighboring content/footer; unchanged box dimensions do
not prove that an extra line fits. An improved crop, small alignment issue or
optional refinement is a warning when meaning/readability remains intact.
Reviewers must describe the actual problem, not assign severity by a score.

The CLI derives gate results from current artifacts and validated receipts.
It rejects missing evidence/coverage, mismatching hashes, unhashed remote
resources and self-declared `passed` flags. Structured editorial/visual records
remain reviewer attestations: software cannot prove that someone read an
image or independently verify a business interpretation. Do not describe this
as tamper-proof or an independent professional certification. All dependency
completeness is a producer responsibility; undeclared files cannot invalidate
a manifest automatically.

If a renderer is unavailable, deliver the requested artifact as a clearly
marked **review candidate** when useful, state the unverified export scope,
and keep the gate blocked. Do not label it ready. User acceptance need not
block an otherwise ready deliverable unless explicitly requested.

## Actual CLI contract

Staff never run or select these commands; production uses them internally.

```text
project_state.py --project PROJECT init --pages 1,2 --canonical html
project_state.py --project PROJECT register copy content/final.md --role copy
project_state.py --project PROJECT register font html/assets/font.woff2 --role font
project_state.py --project PROJECT register html html/index.html --kind artifact --role html --depends copy,font
project_state.py --project PROJECT snapshot html
project_state.py --project PROJECT review html --layer automated --evidence qa/text-flow/text-flow-audit.json
project_state.py --project PROJECT review html --layer editorial --evidence qa/editorial-review.json
project_state.py --project PROJECT review html --layer visual --evidence qa/visual-review.json
project_state.py --project PROJECT register pptx final/report.pptx --kind artifact --role export --depends html
project_state.py --project PROJECT snapshot pptx
project_state.py --project PROJECT verify pptx --evidence qa/pptx-intrinsic.json
project_state.py --project PROJECT review pptx --layer export --evidence qa/pptx-export-review.json
project_state.py --project PROJECT gate --exports pptx
```

`status` prints live node signatures, reasons for staleness and each layer's
missing pages/findings. `gate` exits 2 when blocked, 0 when ready; malformed
input exits 1. `pages --pages 1,2,3` changes topology and invalidates existing
coverage. Default state path is fixed; callers cannot redirect state writes
outside the project. APIs are the same methods on `ProjectState(project)`.

Existing text-flow audit import checks actual source/local-resource hashes,
the installed measurement implementation, screen/print page coverage and
screenshot hashes. Findings are derived from measured records; a summary flag
cannot override them. The built-in PPTX check reads ZIP/OOXML without extraction,
validates page count, native text and text-box canvas bounds. It does **not**
measure glyph clipping, actual font loading, crop, slide overlap, or final
PowerPoint appearance; export review of actual renders remains required.

## Reviewer evidence format

Use `demo-review-v1` for the four non-automated layers. Obtain `target_signature`
from the current `status`/`snapshot`; a stale signature is rejected on import.
Every page needs observations and real project files with SHA-256 hashes.
For visual/export use actual final-size renders, not only a contact sheet.
For editorial use source/copy records plus the inspected final text/render.
Store only necessary observations in the existing QA directory.

```json
{
  "schema_version": 1,
  "format": "demo-review-v1",
  "target": "html",
  "target_signature": "64-character-current-SHA256-signature",
  "layer": "visual",
  "reviewer": {"kind": "agent", "id": "current-reviewer"},
  "pages": [{
    "page": "1",
    "checked": ["hierarchy", "readability", "assets_crop", "reference_application", "design_tokens_actual"],
    "observations": "Viewed page 1 at final size; title zone and photo subject remain clear.",
    "evidence": [{"path": "qa/page-1.png", "sha256": "64-character-file-hash"}],
    "findings": []
  }]
}
```

Required `checked` values are `source_equivalence,status_conditions,language,copy_clarity,spacing_consistency,rendered_lineflow,semantic_breaks`
for editorial; `hierarchy,readability,assets_crop,reference_application,design_tokens_actual` for visual;
`file_integrity,rendered_comparison,editability,text_fidelity,rendered_lineflow,semantic_breaks` for export; and `acceptance`
for user acceptance. PDF/image export's editability observation states whether
editability was requested, rather than pretending it contains native shapes.
Acceptance additionally needs reviewer kind `human` and `decision`:
`accepted` or `rejected`. A rejection blocks an acceptance-required gate.
Findings use `severity`, `code`, `detail`; page is inferred from its record.

Migration: import actual existing files/QA reports into the manifest, inspect
dependency completeness, and run the gate. Old `passed`, install or stage
flags cannot migrate as current receipts. Preserve useful historical reports
without reclassifying them as current approvals.

## Text-flow warning dispositions (3.5.0)

Automated candidates have stable `finding_id`, page, block and mode coverage. Screen/print duplicates are merged; neither layout blockers nor resource failures can be waived. An editorial page may add `warning_dispositions`: `[{"finding_id":"tf-...","decision":"accepted","reason":"Actual phrase and line were read; why this wrap is acceptable"}]`. The page must bind its actual screenshot evidence. `unresolved` or a missing disposition blocks delivery. A claimed `fixed` item still present in the current measurement blocks delivery: correct it, rerun measurement and register the new audit. Only a current editorial receipt on that same page can accept the candidate. Acceptance remains a documented warning, separate from user acceptance. Updated required editorial/export categories invalidate older incomplete receipts instead of silently upgrading their claims.

Follow [production contract](../references/production-contract.md) for independent use/canvas decisions, compact next-step information, actual design measurement and verified role evidence. Existing editorial/visual/export checks remain required.
