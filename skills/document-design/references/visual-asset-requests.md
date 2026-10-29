# Design requests for visual-asset production

Load only when an asset is useful. Architecture owns the reader question and supported meaning; research owns source evidence/acquisition; writing owns final labels; design owns visual encoding, composition and the request. The separate asset specialist executes it with its own production methods and style references.

The integrated producer is [visual-assets](../../visual-assets/SKILL.md). Its [asset contract](../../visual-assets/references/asset-contract.md) is the detailed field/return authority; read it for integration or complex requests. Its [request examples](../../visual-assets/references/request-examples.json) are fictional patterns, not actual available files or production requests. Reuse that maintained contract rather than introducing another schema or production prompt library.

## Choose whether and how to produce

Apply [visual-medium selection](visual-medium-selection.md) for ambiguous cover/hero/body visuals. HTML is the integration layer, not the default drawing method for realistic scenes. The image job can precede detailed composition once its meaning, frame and text-safe zone are known. Do not wait for a near-finished code-only mock-up to discover that the scene requires real illustration. Preserve native labels, exact diagrams, official originals and factual provenance.

For DEMO reference-led work, first apply [DEMO image layout](../../report-html-pptx/references/demo-esg-image-layout.md). Art direction selects purpose profile/page family, image role/occupancy, camera/view and reading sequence before the asset method. Full-image covers and local quiet title zones are explicitly allowed. Carry selected `case_ids` in `production.design_reference`; set the final frame/aspect, focal subject, caption location, allowed crop and editable-text regions before production. Apply its useful scene/photo relationship under the selected expression; high creativity may reinterpret it through a current-subject metaphor or independent composition. Existing reference-gallery availability does not justify a generic visual when a source-like integrated scene or evidence-photo sequence serves the reader better.

An accurate chart, simple editable diagram or standard geometric icon normally uses HTML/SVG/native elements. A composite spatial scene, illustration or distinctive pictogram series may benefit from image production. Original products, logos, characters and factual location photographs use supplied/official assets. A generated concept must not pretend to be recorded evidence.

Consider meaningful candidates such as annotated original + detail, process/ownership diagram, full-page scene, grouped pictograms, sequence panels or a mixed scene + exact editable overlay. The relevant relationship chooses the form. No fixed camera, central subject, large empty margins or isometric style applies to every scene. Whole-page scenes can fill the frame while preserving intentional text regions.

## One compact request/result record

Use the existing asset record, or content/visual-assets.json when needed. Do not create a second registry. The shared six fields are:

| Field | Meaning |
|---|---|
| asset_id | Stable asset identifier |
| section_ids | Actual sections/pages that use it; do not copy their whole body |
| purpose | Reader question, supported message, visual job and related claim IDs |
| semantic_constraints | Essential entities/relationships/directions, fact/concept/proposal state, protected elements and forbidden inventions |
| production | Suitable method, aspect/crop/composition, style family/reference assets, image/editable-label boundary and relevant output constraints |
| delivery | Actual request/result status, existing files, source kind and verification/remaining limits |

Simple requests need only their useful details. Complex scenes may add camera, materials, lighting, stroke, figure proportion, color roles, pixel dimensions, alpha and text-safe regions. Define relations by the actual subjects and predicate/direction, not vague business vocabulary. A request is not evidence that generation happened.

Major factual labels, numbers, conditions, chart axes and meaningful arrows stay editable where practical. Usually request a text-free background/scene and add final-language overlays in the canonical HTML composition. Exact attachment points are returned only if needed and verified against the actual image; do not invent anchors. Style consistency shares a reference/visual family, not identical composition for every page. Large scenes and tiny icons can use related subfamilies.

Reference files must exist and their roles be explicit: identity, layout, style or editing target. Source assets retain known rights, attribution and edit restrictions. One-shot/scoped delegation executes the recommended request; collaboration follows the accepted core-visual choice and representative HTML checkpoint. The request does not introduce per-image approvals.

## Result and page integration

Return actual project files, format/useful size, source type, image/label boundary, semantic and visual checks, and unresolved items. Hash/alpha/anchor/crop records are included when relevant and actually measured. Document files belong in html/assets/ and are referenced relatively. A proposed file path, remote URL or generated thumbnail alone is not acquired delivery.

Inspect the asset at full size and at document size, then integrate the real composition. Check required subjects/relations, crop, labels, protected identity, consistency and legibility. Produce a series contact sheet when it materially helps consistency review. Separate generation, inspection, user acceptance and current output status. If the request changes after a result, invalidate its affected review rather than keeping an old pass.

Use the producer within the current authorized workflow. This file handoff does not create a new chat/agent or remote API. When actual generation capability or a required original is unavailable, retain honest partial/blocked state and complete unaffected work. Do not duplicate the asset specialist's prompts or style library here.

## Carry optional expression

Pass the resolved `brief.design_expression` as `production.expression` or its brief reference. The [two-axis guidance](../../report-html-pptx/references/design-expression.md) owns presets, defaults and cross-axis behavior. A high-creativity request should specify the original metaphor/spatial idea; intensity should specify contrast, image presence, material/light and the final text region. Reference roles are still explicit. Do not overwrite a user's chosen expression with a conservative observed-case prompt.
