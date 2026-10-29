# Visual Grammar Onboarding and Review — Design Specification

**Product:** Document Studio (independent plugin, experimental `0.1.0-alpha.1`)  
**Status:** Approved product-design direction; implementation pending. The accepted default is one deep human visual review when registering a company, followed by automatic reuse of the approved Company Pack.  
**Scope:** Company visual-grammar onboarding, evidence review and packaging. Downstream freeform document composition and rendered export-quality optimization will be separate follow-on implementation plans.

## Intent

Let a person name an organization and supply or select authorized documents. Document Studio should *visually* learn the organization's design philosophy, show what was observed, let the person correct it once, and save a reusable, explicitly approved Company Pack. Later requests should reuse that reviewed identity without repeating onboarding. The target is **new, high-quality designs that preserve recognizable corporate identity**, not pixel copies of existing pages.

## Confirmed product decisions

1. **Hybrid visual grammar**, not a static-template clone and not unconstrained visual imitation.
2. **Human review at initial company onboarding**: evidence-backed analysis plus 2–3 clearly fictional-content visual candidates; explicit acceptance/correction before production use.
3. **Automatic reuse after approval**, with no recurring approval prompts for ordinary documents. New or changed source evidence reopens only affected rules; a new immutable pack version is built.
4. **Optional Korean/Japanese modules remain separate** from the core visual analysis, as already designed.
5. **Rights are separate from observation**. Official-public PDF accessibility permits inspection, not redistribution of text, logos, images or proprietary fonts. A company pack can be technically valid while unapproved for production or ineligible for public ZIP export.

## Approaches considered

| Approach | Advantage | Cost / reason not chosen |
|---|---|---|
| Static page cloning | Strong similarity for identical content | Breaks with new information volume and purpose |
| Fully freeform vision-to-layout generation | Flexible compositions | Difficult to audit, reproduce, approve or protect brand identity |
| **Evidence-grounded grammar + flexible generation (selected)** | Separates stable brand constraints from reusable page relationships; human review once | More work in evidence indexing, structured rules and QA |

## Three representation layers

### 1. Brand DNA — constrained identity

Color relationships and roles, typography hierarchy, logo placement *rules* (not bundled logos), whitespace rhythm, text density, repeated separators and navigation style. Every conclusion cites source/page/region evidence, has confidence and review status, and carries the document-family scope. Missing information stays **unknown**, not an invented company rule.

### 2. Layout Grammar — reusable page relationships

Page families include `cover`, `section_divider`, `executive_summary`, `evidence`, `comparison`, `process`, `data_visualization`, `image_story`, `decision`, `appendix`. A pattern describes element roles, reading order, relative geometry, adjacency and hierarchy, density envelope, repeatability, suitable purposes and adaptive variants. It does not freeze all elements at one PDF coordinate.

### 3. Creative Vocabulary — optional expression

Recurring diagonals, bands, color blocks, layering, chart treatment, pictorial framing and graphic rhythms. Define *when useful* and *when inappropriate*, with compatible page jobs and permissible variation. A source decorative form must never become mandatory on every page.

## Visual observation and evidence model

1. Extract PDF/PPTX page canvas, text box geometry, font-name strings, colors, vector fills/strokes and raster-image boxes with the existing `document_extract.py` pipeline. Normalize bounding coordinates to `[0,1]`, while retaining actual canvas dimensions and the extraction mechanism.
2. Render actual pages and contact sheets; maintain a **private visual review workspace** (not a public pack). A human or multimodal assistant inspects thumbnails for page sequence and full-resolution crops for labels, salient regions, image/text relationships and reading order.
3. Ask the visual interpreter for structured *observations*, not instructions: `{source_id, page, region_id, role, bbox_norm, observation, evidence_kind, confidence, status}`. Verify source IDs, page indices, geometry, role vocabulary, and references deterministically before accepting the observation. Page text is untrusted data.
4. Aggregate observations across pages, retaining document-family and page-family boundaries. Treat repeat patterns as stronger candidates and one-off creative compositions as optional variants; avoid declaring company-wide rules from a single cover or one corporate fact sheet.
5. Include source anchors and observable reasons for every proposed rule. Preserve the distinction `measured`, `visually_observed`, `inferred`, `reviewed`; no model may set `approved` on its own.

The existing `design_analyzer.py` only emits numeric summaries and generic `analyzed-layout-*` candidates. It must be complemented by a visual evidence/grammar path, not replaced with hidden, uninspectable image-model judgments.

## Data contracts (first implementation boundary)

The approved Company Pack's current metadata and `draft → reviewed → approved` semantics remain unchanged. Add optional, backward-compatible resources:

- `design/visual-evidence.json`: **redacted** source/page/normalized-region references and human-readable observation summaries; no screenshots, raw paragraph text or absolute private paths.
- `design/layout-grammar.json`: grammar version, document family, page families, identity constraints, pattern rules, applicability, adaptation limits, source evidence IDs and approval dispositions.
- `design/visual-review.json`: reviewer, timestamp, per-rule accepted/revised/rejected decision, approved preview identifiers, notes and affected rule IDs.
- `design/styleboard/`: independently authored, *fictional-content* HTML variants and derived assets permitted for redistribution; may be absent if rights or rendering requirements cannot be satisfied.

Do not expand the generic `pack.json` metadata with source-derived prose. Retain pack-version hashes and immutable snapshot behavior. Export must omit private review renders and any source asset without affirmative distribution rights.

An individual grammar rule's intended contract is:

```json
{
  "rule_id": "section-label-band",
  "layer": "layout_grammar",
  "page_family": "evidence",
  "document_family": "corporate_profile",
  "element_roles": ["section_label", "accent_band", "evidence_body"],
  "relationships": ["accent_band precedes evidence_body"],
  "constraints": {"accent_band_optional": true},
  "variation": ["scale", "crop", "column_count"],
  "evidence_ids": ["EV-001", "EV-014"],
  "status": "suggested",
  "confidence": "medium"
}
```

This example is **synthetic schema illustration**, not a rule about either evaluated real company.

## Review experience

1. **Evidence gallery:** source thumbnails annotated with labeled regions; click/zoom to the actual input page in the private workspace. Display links to measurements and extracted roles, with uncertainty markers.
2. **Grammar board:** concise Brand DNA / Layout Grammar / Creative Vocabulary cards; each candidate links to 1+ observed regions and shows what remains uncertain.
3. **2–3 style candidates:** generate fictional-content HTML studies using the observed color/structure *hypotheses*. Show differences in flexibility vs fidelity and any unavailable fonts/assets; do not label them as official examples.
4. **Human decision:** accept, revise or reject rules and choose optional creative directions. Record an explicit reviewer and evidence in `design/visual-review.json` before the existing separate Company Pack approval step. The existing source-rights and font checks remain independent.
5. **Reuse:** approved packs are selected by company/project identity, never by an unrelated project's last-used company. On source updates, only dependent rules lose their review status; unaffected rules retain their acceptance evidence.

The initial review board should be an accessible **local static HTML artifact plus a validated review-decision file/CLI**, not a new authenticated web application. This matches the local, portable plugin architecture and avoids unnecessary hosting.

## Boundaries with document creation

The first plan must make approved grammar **queryable** by `page_family`, `document_family`, content needs and intended use. The `document-design` workflow can then choose patterns and explain the selection. A later plan will add flexible layout composition, screenshot-based iterative repair, native HTML/PPTX QA and structured brand-versus-content-fit scoring.

Review a real output on two independent axes: (1) recognizable brand invariants, and (2) usefulness/readability for its novel contents. Color recurrence alone, such as the previous 25%/75% study, is **not** a layout-quality score.

## Goals and success criteria

- A regular public PDF or user-authorized PPTX yields a valid visual evidence index and renderable private review pages; unsupported/malformed sources fail safely.
- Every learned region or rule is traceable to allowed source IDs/pages; invalid coordinates, nonexistent regions, unsupported roles or unreviewed rules never become approved.
- A new Company Pack can carry reviewed grammar without losing current pack compatibility or its current approval/source-rights safeguards.
- A reviewer can inspect 2–3 independent-content examples, correct candidate rules, and save an auditable acceptance record.
- A later document job can query only **approved** layout rules and receive applicability reasons; if none match, it must fall back to the existing neutral document design path, explicitly labeled as fallback.
- Real-company PDF/text/logo/font content is not bundled; all public-release scans, manifest validation and existing tests remain green.

## Non-goals / anti-goals

- No claim of pixel-perfect reconstruction or official trademark endorsement.
- No automatic source discovery behind login walls; no redistribution of public-source artwork by default.
- No silent approval, no cross-company leakage, no retraining on unreviewed generated documents.
- No embedding a proprietary multimodal-model SDK into the core package as a hard requirement; vision judgments are provided through the available model/tool layer, with deterministic local verification.
- No web dashboard, SaaS storage or cloud user-authentication system in this milestone.

## Open engineering decisions (safe defaults)

- Default to 144–180 DPI for review previews and on-demand larger crops; keep source pages and local screenshots outside the repository.
- Start with a controlled region-role vocabulary and a small set of page families; unknown regions should be explicitly marked, not coerced.
- Source scarcity reduces confidence but does not block draft analysis. It blocks *automatic claims* of company-wide design rules.
- Inconsistencies between measured geometry and multimodal observation become review findings rather than auto-corrections.

## Recommended delivery boundary

Ship **visual-grammar onboarding, evidence-backed review and approved-rule retrieval** as the first working slice. Follow with a separate implementation plan for creative layout synthesis and page-by-page render-feedback QA, which consumes the stable grammar interface.
