# Design → visual production → design

This is a file handoff contract, not a remote API or automatic new-chat dispatcher. The skill works in the current authorized workflow. The orchestrator resolves document intake, writing owns labels, research owns evidence acquisition, design owns the page and visual job, and visual production implements the asset.

## Existing record, extended in place

Use `content/visual-assets.json` when the project tracks assets. It may be one record, an array, or an object containing `assets`. Preserve its existing shape and extra fields. The parent architecture's six fields are retained; `contract_version: "visual-assets/1.1"` is optional. Accept its prior `proposed-1` records as the same semantic contract and add only needed information.

| Core field | Required meaning | Useful additions when relevant |
|---|---|---|
| `asset_id` | Stable project identifier | Version/revision in delivery; do not silently reuse an ID for a different subject |
| `section_ids` | Sections/pages using the asset; may be empty for standalone assets | `purpose.claim_ids` links to facts without copying full prose |
| `purpose` | What the visual should explain | `reader_question`, `message`, `visual_job` |
| `semantic_constraints` | Subjects, relationships, confirmed/proposed/concept status and invariants | `subjects`, directed `relationships`, `preserve`, `do_not_invent` |
| `production` | Chosen production approach and necessary placement/style constraints | Fields below; omit irrelevant ones |
| `delivery` | Actual outputs, provenance, revision and review state | Fields below; initialize honestly before production |

A small job may receive equivalent prose instead of structured JSON. The skill should normalize only what makes the handoff clearer. Do not require dozens of optional fields before a simple icon can be copied. Missing factual relationships that affect the scene require resolution; an undecided decorative detail within delegated scope can be chosen.

## Production fields: compatible with the parent design draft

- `preferred_method`: examples include `generated_scene_with_editable_overlays`, `native_svg`, `bitmap_illustration`, `preserve_original`, `targeted_image_edit`. This states intent, not a tool name.
- `style_family_id`, `style_anchor_asset_id`: reuse the designer's IDs. `style_set_id` and a compact `style_spec` may be added for cross-family document traits.
- `composition`: placement, ratio/framing, reader flow and `reserve_text_regions`. Named regions are permissible requests; optional normalized `[x,y,width,height]` regions use 0–1 coordinates in the intrinsic asset frame.
- `text_boundary`: default `embedded_text: "none"`; `editable_overlay_text_owned_by: "writing_and_design"`. Preserve an explicitly requested exception.
- `reference_asset_ids`: resolve from existing inventory. Optional `references` entries can state an actual `file` and role (`style`, `composition`, `subject`, `supporting_insert`, `edit_target`), source ID and availability. A missing file is not a supported tool input.
- `output_constraints`: target dimensions/format, actual minimum placement, transparency and crop restrictions only as needed. Requested dimensions are not actual measured dimensions.
- `revision_scope`: `new_asset` or the precise allowed change. Preserve accepted assets outside that scope.

For DEMO document work, choose the page profile/family and its art direction before production. Extend `production` in place with `design_reference` (selected case IDs and applied composition), `placement_frame` (final page units, width, height/aspect and nearby caption), and `focal_constraints` (must-visible subjects, crop restrictions, required object details). For covers/large scenes, add `art_direction` with `image_role`, `image_area_fraction`, `camera`, `reading_sequence`, `quiet_regions` and `editable_overlay_regions` only when material. The designer may refer to an existing page-map direction instead of duplicating it. `focal_point` is normalized x/y; `crop` is a normalized region or explicitly declared pixels. Fields are planned until delivery inspection records them. These are compact project fields, not new image-tool arguments or a second registry. For a complex scene, use [DEMO image layout](../../report-html-pptx/references/demo-esg-image-layout.md) and actual image inspection to resolve quiet text regions and overlay positions. Delivery can include `effective_ppi_at_placement`, `inspected_crop` and `caption_placement_checked` when actually measured; `not_performed` is valid before page integration.

## Delivery: actual evidence, not inferred completion

- `status`: `not_started`, `produced`, `partial` or `blocked`. `produced` means a real file exists, not that all review or acceptance passed.
- `files`: recommended entries `{path, format, width, height, dimension_units, sha256, transparent_background}`. Relative project paths such as `html/assets/<asset-id>-v1.png` are portable. Existing string file entries can be enriched without replacing the record shape. A source or default tool URL alone is not a saved project asset.
- `intrinsic_dimensions`: optional primary asset dimensions, actually read from output. For vectors, distinguish viewBox units from raster pixels; record unknown dimensions as unknown.
- `provenance_kind`: `generated_concept`, `provided_original`, `sourced_original`, `adapted_vector` or `capture`; retain more specific existing types if meaningful.
- `provenance`: actual source IDs/URLs and usage conditions, reference roles and IDs, generation/edit route, prompt file. For a screenshot, include its page/area and context limitations.
- `request_revision`: identify the request used. Never overwrite another asset's status while registering a new result.
- `review`: retain `visual_inspection`, `source_equivalence`, `unresolved`; optionally add `set_consistency`, `use_size_inspection`, review evidence paths and `layout_review_by_design`. Use `not_performed` / `passed` / `issues_found` / `unavailable`, or `not_applicable` with a reason. A file/hash check is not a visual inspection.
- `user_acceptance`: keep the parent's value; record acceptance only from an actual user response. An approved source/style does not mean a later rendered asset was accepted.
- Optional `content_regions` / `overlay_anchors` / `crop_guidance`: report inspected actual regions and coordinate units. Do not infer exact coordinates from planned placements. Return approximate bounds explicitly as approximate.

Full-image covers may occupy the whole page. A quiet title zone is local and intentional, not a universal empty margin. Do not bake business copy or metadata into the image. Record the source/concept state where it prevents confusion.

For a mixed photo/vector/generated composition, list each component's provenance; one blanket `generated_concept` flag must not conceal an official source. Preserve known relationships and source conditions. Editing a photograph for polish must not create evidence of a nonexistent facility or change a factual subject.

## Project files and comparison

Deliver assets to `html/assets/` or the explicit destination. Keep prompt/reference records in the existing project location, for example `qa/visual-assets/prompts/`. One-off preview files may remain in the preview workspace if they are clearly not delivered assets. Do not introduce a duplicate full-document folder or repeat the report in each asset request.

The optional `scripts/asset_board.py` uses Python's standard library and creates a local HTML contact board from existing delivery files. It accepts the three registry shapes above, keeps links relative, computes file hashes and reads PNG/SVG dimensions where available. It writes no changes to the registry and does not certify visual quality or user acceptance.

```text
python <skill-root>/scripts/asset_board.py --project-root <project> --registry content/visual-assets.json --out qa/visual-assets/asset-board.html --language ko
```

Use `ja` for a Japanese comparison board. Open the HTML in an available browser, panel or viewer and inspect actual assets. No Playwright is required. If Python or a viewer is unavailable, use available native tools to assemble/view a comparison or inspect files individually and record that set comparison was unavailable. Staff never need to set up a runtime to proceed.

The helper only reads/writes within the explicit project root. A standalone asset outside that root can still be produced/inspected with available tools, but is outside this helper's scope. Refer to `request-examples.json` for fictional scene/vector/edit jobs using the parent's field names.

## Optional expression handoff

`production.expression` may contain the existing brief's preset, creativity, visual_intensity and reason, or a reference to `content/brief.json.design_expression`. Use the [canonical expression contract](../../report-html-pptx/system/design-expression.json) and [guidance](../../report-html-pptx/references/design-expression.md). This optional field adds no seventh core request field or acceptance gate. Preserve it during delivery updates. Match semantics and the selected expression in actual scene production and integrated-page review; a quiet palette must not erase a selected inventive metaphor.
