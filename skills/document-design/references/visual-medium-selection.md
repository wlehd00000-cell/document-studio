# Visual-medium selection before composition

Choose the medium for each meaningful visual job **before** polishing the HTML. HTML remains the canonical page/layout source; it can contain sourced photos, generated raster art and native components. It is not a requirement to construct every depicted object with CSS or SVG.

## Fast decision (no new gate or questionnaire)

| Visual job | Preferred medium | Avoid |
|---|---|---|
| Exact text, numbers, charts, comparison, connectors, labels or interactive controls | HTML/SVG/native editable elements | Generating inaccurate chart/diagram text as pixels |
| Real company logo, product package, factual location, identifiable person or required character | Supplied or verified original, preserving identity | Generating approximations of an official identity |
| Spatial concept, architecture, organic objects, human activity, material, realistic perspective, cinematic light/texture or distinctive illustration | Actual image-generation asset or suitable licensed/source image | Fake realism made from rectangles, gradients, circles, cards or generic icons |
| Scene with essential labels, evidence, motion or transitions | Hybrid: image/illustration as one or more layers, native text/data/lines and HTML-driven animation | Baking small Korean/Japanese copy, numbers or meaningful arrows into artwork |
| Typography-led, abstract geometry or a simple precise mechanism | Native type, CSS/SVG and purposeful whitespace | Unnecessary image calls or generic decoration |

Treat the visual *element*, not the whole page, as the unit of choice. Reuse suitable existing project assets first. Use an available native image-generation tool when the scene genuinely benefits from rendering; do not manufacture an image quota or extra approval. Official originals and data accuracy always outrank atmospheric polish.

## v4.2 per-element decision note (existing page map only)

For each high-impact element, add one compact entry **inside the existing** `brief.sections`/page map; do not establish a second registry:

```json
{"intent":"Explain who does what in the AI office",
 "medium":"hybrid",
 "reason":"perspective and material need an image; roles and arrows must be exact and editable",
 "source_or_provenance":"generated_concept; official logos absent until verified",
 "native_overlays":["role labels","direction arrows","limitations"],
 "motion_dependency":"three role highlights; static diagram remains readable",
 "reviewed_scope":"unverified until full-size screenshot inspection"}
```

Choose from `native`, `verified_original`, `generated_image`, and `hybrid` for **each element**, not for the document or profile. Before production ask two questions in order:

1. Does the reader need a convincing *appearance* (depth, place, material, person, spatial metaphor), an exact *relationship/data encoding*, or both?
2. Which parts need original identity, exact source numbers, editable language, motion and later revision?

An explanatory building is primarily a pictorial spatial subject, so a photograph/illustration plus native labels will usually outperform CSS cuboids. A numeric KPI plot is primarily exact encoding, so use native data and chart geometry. An actual product hero pairs a **verified** product packshot with native copy. If multiple answers apply, split into layers instead of forcing one medium.

The choice is a **reasoned default, not an irreversible rule**. If actual image output is incoherent, return to the medium decision and revise that element, not merely its padding. No placeholder success: a planned/generated path, unverified brand lookalike, frozen number label or screenshot-only animation does not pass QA. For a new entire deck, every page gets final-size review; for a scoped revision, only unchanged pages with verified dependency signatures can reuse QA.

## Cover and hero scene

Identify the cover's visual thesis, subject, mood, dominant region and readable title zone. A complex building, shop, group activity, 3D material or character-based scene should receive a concrete art-directed image job before detailed HTML styling. Full-bleed or asymmetric imagery is legitimate; a typography-only cover is also legitimate. Keep crucial title/date/brand labels editable and visually anchored. For an original logo/character, composite the verified original; never ask generation to reproduce it inaccurately.

Do not call a stack of CSS cards, primitive boxes or ornamental gradients an architectural illustration merely because it passes geometry checks. A code-built interpretation is suitable only when abstraction itself explains the subject and reads as intentional at final size.

## Body and motion

Use editable native diagrams for precise logic, data and explanation arrows; use real or concept imagery for appearance, place, experience and pictorial analogy. For an HTML motion presentation, animate native text/lines, masks, transforms and separately composed visual layers. Do not flatten interactive content into one bitmap. For exported PPTX, review the actual static/export behavior independently; browser animation is not guaranteed to survive conversion.

## Small decision and repair loop

For a new/changed high-impact visual, record a short medium choice and reason in the existing page map or asset request; create no second registry. A representative visual must actually be produced and inspected, not only proposed. At final size ask: does this scene convincingly depict its intended subject? Are labels tied to the correct object? Is the composition coherent and crop-safe? If a code-only object looks like an awkward imitation, switch the medium before adjusting margins and typography. If image generation is unavailable, preserve an honest conceptual/diagrammatic alternative or report the limitation instead of claiming photorealistic completion.

Examples: a KPI trend → native chart; a DEMO SHOP product hero → verified package image plus native headline; an AI-agent office building → generated environment plus verified marks, native labels and optional motion; a short approval sheet → native typography/table without a forced hero image.
