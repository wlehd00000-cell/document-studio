# Visual Grammar Onboarding and Review — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Keep all changes on the Document Studio feature branch; do not mix this experimental plugin with the former company-specific plugin.

**Goal:** Make one-time, evidence-backed human visual inspection the standard Company Pack onboarding path, and let subsequent document jobs automatically retrieve only approved, brand-faithful but flexible layout rules.

**Architecture:** Extend the current source registry and PDF/PPTX extractor with private render evidence, validated machine-readable observations, traceable grammar proposals, a local static review board, explicit rule-level decisions, and an approved-only grammar selector. Preserve the current `company-pack/1.0` approval lifecycle and keep the actual creative layout generator as a subsequent milestone.

**Tech Stack:** Python 3.11+ stdlib, existing PyMuPDF and python-pptx optional dependencies, static HTML/CSS, JSON, pytest; no hosted service or mandatory vision SDK.

**Spec:** `docs/superpowers/specs/2026-10-29-visual-grammar-onboarding-design.md`

## Global Constraints

- This is **Document Studio**, independent version `0.1.0-alpha.1`, not a major-version upgrade of any former employer-specific document plugin. Reuse existing generic extraction and output capabilities, not brand-specific assets or policies.
- Company Packs remain `draft → reviewed → approved`; neither OCR, vision observations nor generated previews can transition a pack to `approved` without a named human review and approval. An approved pack is necessary but not sufficient for public redistribution.
- The source registry, original PDFs/PPTXs, rendered screenshots, full-resolution crops and private paths must remain in an explicitly selected **private working directory outside the public repository**. Redacted evidence, rule definitions and independently authored fictional-content samples alone may enter a pack. Avoid copying corporate marks, screenshots, passages or unlicensed fonts into exports.
- A layout rule must record its scope, provenance, uncertainty and adaptation freedom. Single-page evidence must not silently create a universal company-wide invariant. Unknown evidence remains unknown; false precision is forbidden.
- Layouts express relationships and constraints, **not fixed cloned coordinates**. Brand DNA, Layout Grammar and Creative Vocabulary are separate layers. Korean/Japanese writing modules are optional and irrelevant to visual-rule approval.
- Keep optional resources backward compatible: existing demo packs, `company-pack/1.0` metadata and approved scaffold/export workflows must continue to load without a `design/layout-grammar.json`.
- All JSON paths are fixed by the loader; reject symlinks, path traversal and arbitrary user-supplied paths embedded inside pack JSON. Never execute untrusted PDF/PPTX text, HTML or model observations.
- Use real official-public documents only in a separate private **evaluation workspace**. Analysis permission is not redistribution permission; no raw source screenshots or logos enter git.

## Review Focus

1. Traceability: every proposed rule links to actual registered `source_id`, 1-based page number and validated normalized region IDs; conflicting geometry is rejected, never silently normalized into false evidence.
2. Human boundary: a generated suggestion cannot be marked `accepted` or installed for use by changing pack metadata alone; every selected rule must have an explicit reviewer decision linked to a matching evidence digest.
3. Source updates: changing a source hash invalidates **only rules that cite that source**. Unaffected reviewed rules remain eligible; the new pack stays a separate snapshot and must pass pack-level approval.
4. Transfer: rules from company A never apply to company B, even across sequential jobs or parent-pack inheritance. Scope by document family and page family; report a neutral fallback when no approved rule fits.
5. Quality: styleboard uses distinct independent-content compositions. Tests must check traceability, privacy, layout applicability and rendering, not merely color overlap.
6. Supply chain: no hidden network call, automatic source download, arbitrary file writes or unlicensed font/embed paths. Existing public export audit stays authoritative.

---

### Task 1: Normalize measured visual evidence into a private evidence index

**Files:**
- Create: `skills/company-profile-analyzer/scripts/visual_evidence.py`
- Modify: `skills/company-profile-analyzer/scripts/document_extract.py` only if shared bbox adapters need a pure helper
- Create: `tests/test_visual_evidence.py`

**Interfaces:**
- `build_evidence_index(extracted: dict, *, source_id: str, document_family: str) -> dict`: produce a JSON-ready index with `schema_version: "visual-evidence/1.0"`, 1-based pages, page dimensions, measured region IDs and normalized boxes. It must exclude source text and absolute paths.
- `prepare_visual_workspace(source: Path, extracted: dict, *, source_id: str, document_family: str, workspace: Path, max_pages: int = 50) -> Path`: render previews with existing `render_preview` into an explicitly chosen **empty** private workspace; write a private index mapping regions to those images. Never do this implicitly while building an exportable pack.
- Clarify bounding-box formats: PDF uses `[x0,y0,x1,y1]`, PPTX uses `[x,y,width,height]`; normalize both to `[left,top,right,bottom] / canvas_size`. Preserve original measurement kind.

- [ ] **Step 1: Write RED tests** for a 600×400 synthetic PDF with one text box and image/vector region, and a synthetic PPTX with a 72pt offset: assert normalized bounds and known IDs; no source phrases/private paths in exported index. Add cases for zero canvas, NaN/negative/unbounded coordinates, unsupported shape kinds and source-file symlink.
- [ ] **Step 2: Run** `python -m pytest tests/test_visual_evidence.py -q` and confirm expected missing-import/contract failures.
- [ ] **Step 3: Implement** pure normalization and renderer orchestration; region IDs must be stable for a given source hash/page/shape index. Out-of-page geometry is either rejected or explicitly flagged as clipped, never silently treated as full-page content.
- [ ] **Step 4: Run** `python -m pytest tests/test_visual_evidence.py tests/test_company_analyzer.py -q`; confirm 1-based page anchors and no render assumption for unavailable LibreOffice.
- [ ] **Step 5: Commit** `feat: index private PDF and PPTX visual evidence`.

### Task 2: Define and verify grounded visual observations and flexible grammar contracts

**Files:**
- Create: `skills/company-profile-analyzer/scripts/layout_grammar.py`
- Create: `skills/report-html-pptx/system/layout-grammar.schema.json`
- Create: `tests/test_layout_grammar_contract.py`

**Interfaces:**
- `validate_observations(observations: dict, evidence_index: dict, registered_source_ids: set[str]) -> dict`: return a sanitized `visual-observations/1.0` document with supported region roles, exact source/page/region links, confidence and provenance status; reject invented anchors.
- `validate_grammar(grammar: dict, evidence_index: dict | None = None) -> dict`: enforce grammar format `layout-grammar/1.0`, distinct `rule_id`, `layer` (`brand_dna`, `layout_grammar`, `creative_vocabulary`), declared applicability, evidence, relations, allowed variations, and `suggested|accepted|rejected|stale` statuses. If evidence index absent, allow already-reviewed redacted source/page anchors but still check types and internal consistency.
- `compute_evidence_digest(evidence_ids: list[str], evidence_index: dict) -> str`: deterministic digest used to bind a review decision to a specific evidence set.
- Keep region roles in a documented controlled vocabulary; unmapped roles become `unknown` with a review flag, not guessed labels.

- [ ] **Step 1: Write RED tests** for valid measured/visually observed region annotations, nested source-page-region references and evidence digest stability. Add rejection of unknown source, missing page, out-of-range bbox, duplicate IDs, ungrounded inferred relationship, invalid grammar status and attempted `approved` from model output.
- [ ] **Step 2: Run** `python -m pytest tests/test_layout_grammar_contract.py -q` and see expected failures.
- [ ] **Step 3: Implement** validation with pure stdlib and publish matching JSON Schema; add a JSON Schema fixture test or lightweight structural parity test without adding a mandatory runtime dependency.
- [ ] **Step 4: Re-run** target tests, then `python -m pytest tests/test_visual_evidence.py tests/test_layout_grammar_contract.py -q`.
- [ ] **Step 5: Commit** `feat: validate source-grounded visual layout grammar`.

### Task 3: Synthesize explainable rule candidates without declaring official identity

**Files:**
- Create: `skills/company-profile-analyzer/scripts/grammar_synthesis.py`
- Modify: `skills/company-profile-analyzer/scripts/design_analyzer.py` only to expose existing measured styles through a stable adapter
- Create: `tests/test_grammar_synthesis.py`

**Interfaces:**
- `propose_grammar(observations: list[dict], measured_designs: list[dict], *, document_family: str) -> dict`: yield three separate layers of **suggested** candidate rules with source-anchored reasons, support count, confidence, eligible page families, content-density envelope, optional/required constraints and permitted adaptations.
- Treat visual interpretation as externally supplied structured observations. The local program must not claim that it saw/rendered a page when the visual step was unavailable.
- Rule support is by **independent source/page evidence**, not repetitions of the same shape; do not infer immutable brand constraints from one observed cover.

- [ ] **Step 1: Write RED tests** with synthetic multi-page observations showing one common title rhythm and one optional image treatment; verify distinct layers, duplicate suppression, page-family restrictions and source evidence. Test conflict handling and insufficient-source confidence explicitly.
- [ ] **Step 2: Run** `python -m pytest tests/test_grammar_synthesis.py -q` and confirm missing implementation.
- [ ] **Step 3: Implement** deterministic grouping/synthesis with transparent scoring; keep user-visible explanations free of original document paragraphs. Leave uncertain findings as review questions.
- [ ] **Step 4: Run** synthesis and prior contract tests together. Add a fixture for a revised observation producing a changed evidence digest.
- [ ] **Step 5: Commit** `feat: propose adaptable company layout grammar`.

### Task 4: Create a local evidence gallery, grammar board and fictional-content style studies

**Files:**
- Create: `skills/company-profile-analyzer/scripts/visual_review_board.py`
- Create: `skills/company-profile-analyzer/assets/visual-review-board.css` (original styling only)
- Create: `tests/test_visual_review_board.py`

**Interfaces:**
- `build_review_board(evidence: dict, grammar: dict, *, private_preview_root: Path, output: Path, fictional_examples: list[dict]) -> Path`: create one local, static HTML review board with evidence thumbnail overlays, source/page/region anchors, uncertainty badges and three clearly separated rule layers. No remote URL/API or embedded source artwork in the pack.
- `fictional_examples`: 2–3 independently written sample-content layouts, each with its own candidate ID, page-job declaration and **different** composition strategy (not the same layout with recolored CSS). A missing sample or failed render must be reported, not silently substituted by duplicated samples.
- A separate offline review-decision JSON template is displayed/downloadable; the static board itself does not approve a Company Pack.

- [ ] **Step 1: Write RED tests** for HTML escaping of extracted source labels/model observations (`<script>`, event handlers), valid thumbnail→region anchors, per-source source IDs, 2–3 distinct fictional candidates, accessibility labels, no original page text embedded, no private absolute path in output HTML/pack.
- [ ] **Step 2: Run** `python -m pytest tests/test_visual_review_board.py -q` expecting contract failures.
- [ ] **Step 3: Implement** deterministic HTML, responsive contact sheet and normalized SVG or CSS overlays. Keep screenshots in private workspace; output HTML references local private preview files only, without embedding them as data URIs. Author fictional study content and styles independently.
- [ ] **Step 4: Render locally** using available browser or PNG tool and visually inspect: page sequence, crop legibility, evidence overlays, board hierarchy and sample diversity. Capture reviewer notes privately; do not commit source screenshots.
- [ ] **Step 5: Run** target and prior tests; commit `feat: inspect visual grammar in local review board`.

### Task 5: Record rule-level human decisions and build a versioned pack

**Files:**
- Create: `skills/company-profile-analyzer/scripts/record_visual_review.py`
- Modify: `skills/company-profile-analyzer/scripts/build_company_pack.py`
- Modify: `skills/report-html-pptx/scripts/company_pack.py`
- Modify: `skills/report-html-pptx/scripts/validate_company_pack.py` if a review report needs added diagnostics
- Create: `tests/test_visual_review_approval.py`
- Modify: `tests/test_company_pack.py`

**Interfaces:**
- `record_visual_review(*, pack_dir: Path, grammar_file: Path, decision_file: Path, reviewer: str) -> dict`: read a human-authored decision file, validate its rule IDs and evidence digests, and save `design/visual-review.json`; map accepted/revised/rejected decisions into `design/layout-grammar.json`. `revised` requires a verified revised rule and rationale; no invented or invalid relationship may be approved.
- Extend `build_company_pack(..., grammar_proposal: Path | None = None, redacted_evidence: Path | None = None)` with optional args; default must preserve existing callers. Generated rules enter a new pack as `suggested` only.
- Extend `CompanyPack` with `layout_grammar: tuple[...]` and `visual_review: dict[...]` as **backward-compatible optional resources**; ensure dataclass construction and inheritance remain correct. Explicit `accepted` rules are eligible for later use only if enclosing pack is `approved` and review evidence matches.
- `invalidate_affected_rules(previous_pack: CompanyPack, new_source_hashes: dict[str, str]) -> ...`: design a non-destructive change report and produce new **draft pack version**; only directly dependent rule IDs become `stale`, and unchanged reviewed rules retain their recorded evidence. Never edit a previous approved pack in place.

- [ ] **Step 1: Write RED tests** for no-review/suggested-only pack, valid named reviewer, revision provenance, mismatched/forged digest, rejected rule, changed-source selective invalidation, unchanged-rule preservation, existing demo-pack compatibility and human-only approval.
- [ ] **Step 2: Run** `python -m pytest tests/test_visual_review_approval.py tests/test_company_pack.py -q` to see expected failures.
- [ ] **Step 3: Implement** pack resources and decisions. Make `change_review_status(..., action='review'|'approve')` reject a grammar-bearing pack without a completed rule review; keep legacy grammar-free pack behavior unchanged. Document explicit pack approval as a second, distinct human action.
- [ ] **Step 4: Re-run** focused tests and existing `tests/test_company_analyzer.py` to catch approval-state and dataclass regressions.
- [ ] **Step 5: Commit** `feat: require evidence-bound human visual review for grammar packs`.

### Task 6: Retrieve approved grammar by document purpose and content fit

**Files:**
- Create: `skills/report-html-pptx/scripts/select_layout_grammar.py`
- Modify: `skills/document-design/SKILL.md`
- Modify: `skills/report-html-pptx/scripts/scaffold_report.py` only to add selection metadata to the existing content-addressed pack snapshot; avoid speculative HTML auto-layout changes
- Create: `tests/test_layout_grammar_selection.py`

**Interfaces:**
- `select_layout_grammar(pack: CompanyPack | None, *, document_family: str, page_family: str, content_roles: list[str], density: str, intended_use: str) -> dict`: return a ranked list of **accepted** rules from an **approved** pack with evidence IDs and suitability explanations, or `{mode: 'neutral_fallback', rules: [], reason: ...}`. Unknown page families/content roles cannot silently bypass applicability checks.
- Rank content-fit separately from brand constraints; do not pretend every example can serve every page job. Creativity variants are suggestions, never rigid page templates.
- Pack selection must be explicit per job. A previous project's active pack cannot be inferred from ambient state.

- [ ] **Step 1: Write RED tests** for accepted rule ranking, draft/reviewed pack refusal, missing grammar neutral fallback, unmatched document family, content-density mismatch, company A/B isolation, safely inherited rules, and eligibility disappearing when a source-dependent rule becomes stale.
- [ ] **Step 2: Run** `python -m pytest tests/test_layout_grammar_selection.py -q` to observe expected failures.
- [ ] **Step 3: Implement** deterministic selector with transparent score/reasons; update document-design guidance to retrieve grammar before layout proposals and deliberately adapt within constraints. Add only a metadata hook to scaffold; no unreviewed full-page synthesis.
- [ ] **Step 4: Run** focused selection tests plus `tests/test_company_integration.py`; inspect neutral-fallback behavior manually.
- [ ] **Step 5: Commit** `feat: reuse only reviewed company grammar in document design`.

### Task 7: Enforce public-export privacy and validate two real-company holdouts

**Files:**
- Modify: `scripts/export_company_plugin.py`
- Modify: `tests/test_plugin_export.py`
- Modify: `tests/test_public_company_fidelity.py`
- Modify: `skills/company-profile-analyzer/SKILL.md`
- Modify: `README.md`
- Create: `evaluation/visual-grammar-onboarding-2026-10-29.md`
- Refresh: `package-manifest.json`

**Interfaces:**
- Public export includes only reviewed grammar metadata, evidence IDs, reviewer decision summaries and independently authored fictional HTML; it must exclude private review HTML/images, source originals, raw paragraphs, unlicensed fonts and private paths. Export of a real pack still requires **per-source distribution authorization** and existing reviewer/approver checks.
- Document the onboarding CLI order: register → extract → private render/observe → propose → review board → decisions → pack review → pack approval → selector → editable output.
- The public-company evaluation must use two independent official-public PDFs in private workspace, keep source ID/page evidence, and test **novel-content** style studies rather than literal page reconstruction. Record human ratings of identity retention and content readability separately, and distinguish measured data from subjective judgments.

- [ ] **Step 1: Write RED tests** with a pack containing malicious/private screenshot paths, a source quote and a safe redacted grammar. Assert private resources never appear in ZIP, forged source rights are rejected, and existing fictional demo exports still work.
- [ ] **Step 2: Implement** a strict, allowlisted export of new resources with revalidation of accepted rule provenance/review state. Do not copy the private review board directory into output.
- [ ] **Step 3: Run** `python -m pytest tests/ -q`; resolve regressions without loosening source-rights or review gates.
- [ ] **Step 4: Perform** the two-company evaluation privately: verify extraction/renders, human-inspect multi-page sources, inspect generated style studies, compare brand invariants and new-content suitability; mark untested editable PPTX fidelity honestly.
- [ ] **Step 5: Run** `python scripts/verify_public_release.py` and `python scripts/build_package_manifest.py` followed by `python scripts/build_package_manifest.py --check`; inspect git diff for accidental source/private artifacts.
- [ ] **Step 6: Commit** `test: audit visual grammar privacy and public-company onboarding` and update the existing draft PR only after the full suite and manual review pass.

### Task 8: Save an independently packaged plugin through Plugin Creator

**Files:**
- Create: `scripts/package_account_plugin.py`
- Create: `tests/test_account_plugin_package.py`
- Create: `skills/company-profile-analyzer/references/account-installation.md`
- Modify: `skills/company-profile-analyzer/SKILL.md`
- Modify: `README.md`
- Refresh: `package-manifest.json`

**Interfaces:**
- `build_account_plugin(source_root: Path, output: Path, *, language_skills: str = 'none') -> dict`: build a standalone, private-account-ready ZIP containing the plugin manifest, its selected skills, and only explicitly allowlisted public supporting files. Reject symlinks, packaged sources, unlicensed font binaries and path escapes; do not overwrite output.
- For **company-specific** plugins, reuse `export_company_plugin(approved_pack, ...)`, which enforces explicit source rights and approval; do not bypass it through the generic builder.
- In the installed `company-profile-analyzer` skill, route an explicit **save/install to this account** request to the user-installed Plugin Creator's `create_plugin` tool with the absolute generated archive path. Record returned plugin ID, release ID, URL and actual scope; never infer it is personal when an active workspace is selected. For future updates use `update_plugin` with verified current release ID, never create duplicates. Missing tool/permission is a stop condition with a recoverable ZIP artifact.

- [ ] **Step 1: Write RED tests** for expected skill inventory, portable JSON manifest, archive root, no leaked originals/hidden private sources, optional languages, no overwrite, and a company-pack packaging path that cannot bypass export rights.
- [ ] **Step 2: Run** `python -m pytest tests/test_account_plugin_package.py -q` and confirm missing feature failures.
- [ ] **Step 3: Implement** ZIP builder, CLI, skill instructions and account-installation reference. Keep account API calls in the agent tool layer, not scripts holding credentials.
- [ ] **Step 4: Re-run** tests and archive inspection; create an experimental account ZIP; if creating/saving to the user's account is authorized, call Plugin Creator once, retain returned ID and link, and verify new plugin discoverability when available.
- [ ] **Step 5: Run** complete repo tests and public-release scan, refresh manifest, and commit `feat: hand off approved company plugins to account installer`.

## Definition of Done

- Users can inspect **what was learned, why it was inferred and what remains uncertain** using real rendered pages without leaking those pages into the distributed plugin.
- A named reviewer can accept/correct/reject rule candidates, and a separate human pack-level approval unlocks automatic downstream grammar selection.
- The selector produces brand-faithful but **adaptable** pattern suggestions for novel content, with source evidence and neutral fallback. It does **not** claim high-quality freeform document creation is already solved.
- Changed evidence selectively invalidates rules via a new pack version; old approved versions remain immutable and separately usable/auditable.
- Existing 33-test baseline plus added tests pass; public-release scanning, source-rights export checks and package manifest validation pass.
- A real-company visual evaluation reports human assessment and outstanding gaps; no extrapolation from color recurrence to layout quality.
- User can choose optional language skills, build a compliant standalone ZIP, and save it via the authenticated Plugin Creator integration; actual account release and installation are confirmed only from the tool result.

## Follow-on Milestone (not part of this plan)

Implement a creative composition engine that proposes several genuinely different structures from the approved grammar, then renders and repeatedly checks legibility, spacing, language-specific wrapping, slide-to-slide rhythm, and brand fidelity for HTML/PPTX. This follows only after the onboarding interface and approval gate stabilize.

## Self-Review Checklist

- [x] Design specification is linked; every confirmed product decision maps to an implementation task.
- [x] Tests precede implementation; target files, public function contracts, expected failures and verification commands are specified.
- [x] Human approval and public source rights are separate gates, with privacy by default.
- [x] Real-company evaluation distinguishes provenance, visual fidelity and novel-content usability.
- [x] Deliberate scope boundary prevents claiming that a grammar selector alone creates polished documents.

## Implementation Status (2026-10-29)

- **Implemented and automated-test covered:** measured PDF/PPTX evidence index, source-grounded visual observation/grammar validation, deterministic proposed patterns, private static comparison board, explicit rule-level review, Company Pack approval gate, approved-only retrieval, rights-checked ZIP inclusion, authenticated Plugin Creator create/update handoff, optional Korean/Japanese skill selection, and executable onboarding CLI.
- **Verified:** complete test suite, public-release safety scanner, manifest integrity, and private account plugin create/update with the same plugin identity.
- **Pending visual validation:** manual rendering and inspection of the review-board HTML, human comparison against two independent real-company source corpora, text/logo/font licensing review for real-company publication, and actual high-quality novel-content HTML/PPTX generation with iterative render QA. Quantitative extraction and the generated styleboard **do not yet prove faithful design reproduction**.
- **Deployment boundary:** generic Document Studio is a private experimental account plugin. A specific enterprise pack requires its own authorized source rights, human review, and export before it may be saved as a separate private plugin.
