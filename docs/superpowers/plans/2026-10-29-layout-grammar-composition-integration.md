# Approved Layout Grammar Composition Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make accepted, evidence-backed Layout Grammar constrain real new HTML compositions, with auditable per-page trace and rendered verification rather than merely recording rule IDs.

**Architecture:** Extend the existing approved-rule selector; introduce a deterministic manuscript-to-page-plan boundary; let Document Design create expressive HTML with traceable semantic anchors; independently measure those anchors in the existing Playwright/browser QA environment. Bind plan, produced HTML, and QA receipt to ProjectState so changes invalidate evidence. Retain unbranded neutral behavior and existing HTML→PPTX export checks.

**Tech Stack:** Python 3 stdlib and pytest; existing `CompanyPack`/`ProjectState` APIs; Node.js + existing Playwright installation for browser measurement; HTML/CSS and JSON files; current plugin packaging scripts.

**Spec:** `docs/superpowers/specs/2026-10-29-approved-layout-grammar-composition-design.md`

## Global Constraints

- Product: independent `document-studio`; preserve the existing core skill modules and optional Korean/Japanese language skills.
- Only pack `status=approved` **and** individually reviewed rule `status=accepted` can enter corporate-branded production. No inheritance from an unapproved ancestor.
- Source references and brand rights are independent of visual quality. Do not embed source pages, company logos, font binaries or corporate text in public fixtures, artifacts or plugin archives.
- The grammar contract preserves relationships; Document Design owns actual composition. No universal template, source pixel copy or automatically certified aesthetics.
- Planning writes `review_status=pending_render_review`; an absent browser writes `UNVERIFIED`, not PASS. DOM checks cannot replace human/vision review.
- Canonical authoring stays `html/index.html`; PPTX is an independent export target and QA concern. All changes remain additive for unbranded documents.
- Repo work stays on `feat/company-pack-foundation`; prefer narrow commits after each green task. Do not push or update the installed plugin before tests, visual review and publication-rights checks.

## File structure and interfaces

| File | Responsibility |
| --- | --- |
| `skills/report-html-pptx/scripts/select_layout_grammar.py` | Strict reviewed-rule selection and lossless relationship metadata |
| `skills/report-html-pptx/scripts/layout_plan.py` | Pure page-brief validation, selection/relationship parsing, conflict reporting, deterministic plan and hashes |
| `skills/report-html-pptx/scripts/plan_layout_grammar.py` | CLI to read a completed manuscript/page brief, write `content/layout-plan.json`, register plan/HTML dependencies |
| `skills/report-html-pptx/scripts/html_grammar_contract.py` | Static HTML anchor uniqueness and selected-rule trace checks, without pretending to measure geometry |
| `skills/report-html-pptx/scripts/audit_layout_grammar.mjs` | Existing-Playwright DOM bounds, screenshots, overflow/clipping and relationship measurements |
| `skills/report-html-pptx/scripts/audit_layout_grammar.py` | Browser availability wrapper, receipt with real hashes/status, bounded project paths, `UNVERIFIED` fallback |
| `skills/report-html-pptx/scripts/production_contract.py` | Reject missing/stale/failed grammar QA on approved-grammar projects only |
| `skills/report-html-pptx/scripts/scaffold_report.py` | Declare deferred post-manuscript grammar stage; do not apply guessed starter-copy rules |
| `skills/document-design/SKILL.md`, `skills/report-html-pptx/SKILL.md` | Mandatory approved-plan → HTML authoring → visual review procedure |
| `skills/report-html-pptx/system/project-state.md` | State dependency and audit receipt workflow |
| `tests/test_layout_grammar_selection.py`, `tests/test_layout_plan.py`, `tests/test_html_grammar_contract.py`, `tests/test_layout_grammar_audit.py`, `tests/test_layout_grammar_integration.py` | Contract, negative, browser/no-browser, state and creative-variation acceptance tests |

## Review Focus

1. **Ambiguous role occurrences:** Two heading elements on one page must not silently satisfy a one-to-one relationship; require an explicit element ID or report ambiguity (Task 2 and 3).
2. **Invalid/untrusted relationship prose:** Unknown operators, HTML-like strings and contradictory ordering are data or conflicts, never executable instructions (Task 1 and 2).
3. **Orphan/inherited evidence:** Missing source references or ancestor packs without approval cannot enter a page plan even if a child pack is approved (Task 1 and 2).
4. **Stale measurements:** Change any plan, HTML, font, canvas, source asset or referenced policy and previous verification must block delivery (Task 4 and 5).
5. **Browser gaps/layout oddities:** Missing browser, hidden anchor, CSS transform, overlap, off-canvas text and nested elements cannot yield a false PASS (Task 4).

---

### Task 1: Strict selection and complete rule metadata

**Files:** Modify `skills/report-html-pptx/scripts/select_layout_grammar.py`; test `tests/test_layout_grammar_selection.py`.

**Interfaces:** Preserve `select_layout_grammar(pack: CompanyPack | None, *, document_family: str, page_family: str, content_roles: list[str], density: str, intended_use: str) -> dict`. Each selected rule additionally returns `element_roles: list[str]`, `relationships: list[str]`, `confidence: str`, `evidence_refs: list[dict]` (retain `source_refs` alias), and `origin_pack_status`.

- [ ] **Step 1: Write failing tests.** `test_multi_role_requires_all_roles` creates an approved/reviewed `heading above body` rule, requests only `heading`, and expects neutral fallback; with both roles, expects selected rule. `test_relational_metadata_is_lossless` verifies exact `relationships`, roles, refs, constraints and variation. `test_rejects_unapproved_inherited_rule` checks inherited status; `test_stale_or_cross_scope_rule_never_selected` checks stale and mismatched family/use/density.
- [ ] **Step 2: Run red.** `python3 -m pytest -q tests/test_layout_grammar_selection.py` → new tests FAIL for dropped metadata and partial overlap.
- [ ] **Step 3: Implement minimal selector change.** For rules with nonempty `relationships`, require all declared `element_roles` in requested `content_roles`; preserve unchanged nonrelational behavior. Keep source strings as data for the Task 2 parser; reject missing provenance rather than treating string data as instructions.
- [ ] **Step 4: Run green/regression.** `python3 -m pytest -q tests/test_layout_grammar_selection.py tests/test_visual_review_approval.py` → PASS.
- [ ] **Step 5: Commit.** `git add skills/report-html-pptx/scripts/select_layout_grammar.py tests/test_layout_grammar_selection.py && git commit -m "feat: preserve reviewed layout relations in strict selection"`.

### Task 2: Deterministic plan after final manuscript

**Files:** Create `skills/report-html-pptx/scripts/layout_plan.py`, `skills/report-html-pptx/scripts/plan_layout_grammar.py`, `tests/test_layout_plan.py`.

**Interfaces:** `validate_page_brief(brief: dict) -> list[dict]`; `parse_relationship(expression: str, roles: list[str]) -> dict | None`; `build_layout_plan(pack: CompanyPack | None, brief: dict) -> dict`. `plan_layout_grammar.py` CLI: `--project PATH --page-brief content/page-brief.json [--company-pack PATH]` resolves only project-contained input and writes `content/layout-plan.json`; no modification of the approved pack. Brief schema version `layout-page-brief/1.0` with `document_family`, `pages[]` containing `page_id`, `page_family`, `reader_question`, `reading_order`, `elements[]` (`element_id`, `role`), `density`, `intended_use`, `canvas`, `language`, and `assets[]` with rights/status. Plan schema version `layout-plan/1.0`, `pages[]`, `pack_snapshot_sha256`, `plan_sha256` and `review_status`.

- [ ] **Step 1: Write failing tests.** `test_plan_is_deterministic_and_binds_pack_and_elements`; `test_relationship_is_semantic_not_pixel_position`; `test_ambiguous_role_requires_explicit_anchor`; `test_conflicting_orders_report_conflict_not_pass`; `test_neutral_fallback_when_rule_not_applicable`; `test_rejects_unknown_operator_or_html_in_role`; `test_rejects_unverified_asset_and_outside_project_path`; `test_snapshot_changes_when_approved_grammar_changes`; `test_missing_or_wrong_page_brief_is_rejected`.
- [ ] **Step 2: Run red.** `python3 -m pytest -q tests/test_layout_plan.py` → module/expected tests FAIL.
- [ ] **Step 3: Implement pure validation/plan.** Canonical `json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False)` SHA-256; hash source policy, accepted grammar and normalized page content, excluding the self-referential `plan_sha256` field; express each relation as `leader_element_id`, `operator`, `follower_element_id`; detect directed cycles/conflicting reading-order requirements; unrecognized expressions become explained `conflicts` and cannot silently become constraints. `review_status` remains `pending_render_review`.
- [ ] **Step 4: Implement CLI with explicit project containment.** Write deterministic `content/layout-plan.json` and return status/paths; do not auto-author HTML. Use existing `ProjectState` registration only after source existence checks; new plan dependencies are introduced at Task 5.
- [ ] **Step 5: Run green.** `python3 -m pytest -q tests/test_layout_plan.py tests/test_layout_grammar_selection.py` → PASS.
- [ ] **Step 6: Commit.** `git add skills/report-html-pptx/scripts/layout_plan.py skills/report-html-pptx/scripts/plan_layout_grammar.py tests/test_layout_plan.py && git commit -m "feat: plan approved grammar from finished page briefs"`.

### Task 3: Real authored HTML trace and creative variation contract

**Files:** Create `skills/report-html-pptx/scripts/html_grammar_contract.py`, `tests/test_html_grammar_contract.py`; modify `skills/document-design/SKILL.md`, `skills/report-html-pptx/SKILL.md`.

**Interfaces:** `inspect_html_grammar(html_text: str, plan: dict) -> dict` returns `status` (`PASS` / `FAIL` / `NOT_APPLICABLE`), exact per-page/rule/element findings and annotations. Actual page: `data-page-id="P1"`; governed elements: `data-grammar-element-id="title"` and `data-grammar-rule-ids="rule-x"` (space-separated IDs); metadata must match active plan. The validator does not infer spatial PASS.

- [ ] **Step 1: Write failing tests.** `test_valid_authored_html_traces_exact_selected_ids`; `test_missing_or_duplicate_page_or_element_anchor_fails`; `test_unknown_rule_and_cross_page_anchor_fail`; `test_html_attribute_injection_is_not_allowed`; `test_two_different_semantic_html_compositions_are_both_valid`; `test_neutral_html_does_not_require_company_anchors`.
- [ ] **Step 2: Run red.** `python3 -m pytest -q tests/test_html_grammar_contract.py` → FAIL.
- [ ] **Step 3: Implement static contract.** Use Python `html.parser` and escaped/restricted identifier matching; only compare IDs, role mappings and rule assignment; treat unknown and duplicate references as blocking. Never accept aesthetic/spatial verification from static DOM.
- [ ] **Step 4: Make Design consume real plan.** Require page brief only after final manuscript, no layout selection from sample copy; use selected relationships as composition constraints, allow novel text/photo/vector composition and explicit variation notes; require the HTML annotations and per-page screenshots for final visual review; retain the neutral document route.
- [ ] **Step 5: Run green.** `python3 -m pytest -q tests/test_html_grammar_contract.py` → PASS; read both edited SKILL.md files for any contradictory instructions.
- [ ] **Step 6: Commit.** `git add skills/report-html-pptx/scripts/html_grammar_contract.py tests/test_html_grammar_contract.py skills/document-design/SKILL.md skills/report-html-pptx/SKILL.md && git commit -m "feat: bind creative HTML to approved layout plan traces"`.

### Task 4: Browser-measured relationships and honest QA receipt

**Files:** Create `skills/report-html-pptx/scripts/audit_layout_grammar.mjs`, `skills/report-html-pptx/scripts/audit_layout_grammar.py`, `tests/test_layout_grammar_audit.py`.

**Interfaces:** `audit_layout_grammar(project: Path, *, browser_path: Path | None = None) -> dict`; CLI `--project PATH [--browser-path PATH]`; outputs `qa/layout-grammar-application.json` with `schema_version=layout-grammar-audit/1.0`, `status: PASS|FAIL|UNVERIFIED|NOT_APPLICABLE`, `plan_sha256`, `html_sha256`, `inspected_pages`, `relationships[]`, `findings[]`, `screenshots[]`, `tool_receipt` and `requires_visual_review=true` for any applicable rule. Browser creates `qa/layout-grammar-pages/<page_id>.png` only for inspected pages.

- [ ] **Step 1: Write failing tests.** `test_no_browser_returns_unverified_not_pass`; `test_static_anchor_failure_blocks_render_pass`; `test_actual_above_and_left_of_measurements_pass`; `test_reversed_relation_fails`; `test_hidden_transform_overlap_canvas_and_clipping_fail_or_unverified`; `test_page_screenshots_match_inspected_pages`; `test_receipt_includes_tool_and_input_hashes`. Browser tests skip explicitly if no Playwright/browser exists; no-browser negative test never skips.
- [ ] **Step 2: Run red.** `python3 -m pytest -q tests/test_layout_grammar_audit.py` → FAIL for missing implementation.
- [ ] **Step 3: Implement measurement.** Reuse the runtime's existing Playwright location/launch convention; wait for fonts, measure `getBoundingClientRect`, computed visibility/overflow and `scrollWidth/scrollHeight`, compare required `above`/`left_of` by actual page geometry with documented non-overlap tolerance, save page PNGs, forbid unapproved network resources and perform bounded filesystem resolution.
- [ ] **Step 4: Implement wrapper and receipt.** Catch unavailability only as `UNVERIFIED`, geometry failure as `FAIL`; distinguish missing tool from invalid HTML; include direct SHA-256 of HTML, plan, referenced assets, fonts and checker modules so stale receipts fail. Forward existing text-flow/resource findings, rather than replacing production checks.
- [ ] **Step 5: Run green.** `python3 -m pytest -q tests/test_layout_grammar_audit.py`; run browser subset on installed renderer, otherwise report specific browser skips and `UNVERIFIED`.
- [ ] **Step 6: Commit.** `git add skills/report-html-pptx/scripts/audit_layout_grammar.mjs skills/report-html-pptx/scripts/audit_layout_grammar.py tests/test_layout_grammar_audit.py && git commit -m "feat: measure grammar relations on rendered document pages"`.

### Task 5: Scaffold/ProjectState/export delivery integration

**Files:** Modify `skills/report-html-pptx/scripts/scaffold_report.py`, `skills/report-html-pptx/scripts/production_contract.py`, `skills/report-html-pptx/system/project-state.md`; test `tests/test_layout_grammar_integration.py` and existing project/scaffold tests.

**Interfaces:** Branded scaffold records `visual_grammar.stage=pending_final_manuscript` and selected-pack snapshot, not a fake approved page layout; after final copy CLI registers `page_brief` (`source`), `layout_plan` (`artifact`, depends on page brief, final copy and company pack), and `html` (`artifact`, additionally depends on layout plan). `grammar_audit_findings(project: Path, html: Path) -> list[dict]` in `production_contract.py` extends existing `contract_findings()` only when plan contains approved grammar.

- [ ] **Step 1: Write failing tests.** `test_branded_scaffold_does_not_claim_starter_page_approved`; `test_plan_registers_content_addressed_html_dependency`; `test_edited_grammar_plan_html_font_canvas_or_asset_invalidates_receipt`; `test_no_browser_or_failed_relation_blocks_export`; `test_neutral_existing_document_is_backward_compatible`; `test_approved_pack_inherited_rule_denied`.
- [ ] **Step 2: Run red.** `python3 -m pytest -q tests/test_layout_grammar_integration.py` → FAIL.
- [ ] **Step 3: Add deferred-stage registration.** Keep older HTML projects loadable, persist pack **grammar** in the snapshot hash (it is currently omitted), preserve state graph anti-cycle constraints, create new per-page plan dependency after final copy and update HTML's dependency graph before production snapshot.
- [ ] **Step 4: Gate deliveries.** Validate audit receipt hashes/screenshots, current checker/module digests and page scope; any `UNVERIFIED`, stale input, missing visual review or failed constraint blocks only applicable branded production. Do not overwrite existing editorial/visual receipts or treat DOM PASS as human visual approval.
- [ ] **Step 5: Run green.** `python3 -m pytest -q tests/test_layout_grammar_integration.py tests/test_layout_grammar_selection.py`; run existing project-state and scaffold tests by filename discovery.
- [ ] **Step 6: Commit.** `git add skills/report-html-pptx/scripts/scaffold_report.py skills/report-html-pptx/scripts/production_contract.py skills/report-html-pptx/system/project-state.md tests/test_layout_grammar_integration.py && git commit -m "feat: enforce fresh grammar QA in production graph"`.

### Task 6: Two-layout acceptance, regression, safe plugin handoff

**Files:** Add two original synthetic-company HTML samples under `tests/fixtures/layout-grammar/` plus `tests/test_layout_grammar_acceptance.py`; update relevant `README.md`, plugin version metadata and `scripts/build_package_manifest.py` output as required by existing packaging conventions.

**Interfaces:** Both original HTML samples are composed for a **synthetic approved** pack, same rule, different content structure/layout; neither contains real-brand assets or copied paragraphs. Each must pass plan/trace/browser tests; visually review both at target canvas and store truthful screenshots/notes in project QA.

- [ ] **Step 1: Write failing acceptance test.** `test_two_distinct_layouts_obey_same_rule_with_different_dom_geometry` requires distinct actual compositions, same accepted relationship, separate trace evidence and screenshot receipts; `test_private_unapproved_references_not_embedded_in_plugin` rejects corporate PDF/asset/URL leaks.
- [ ] **Step 2: Run red.** `python3 -m pytest -q tests/test_layout_grammar_acceptance.py` → FAIL.
- [ ] **Step 3: Build two authored synthetic samples.** Make one typography-led and one image-led (original placeholder illustration or CSS), vary alignment/scale/crop without violating the same `above`/`left_of` rule. Render actual HTML, compare screenshots and revise violations. Mark visual review honestly if a browser or human inspection cannot run.
- [ ] **Step 4: Full regression and safety audit.** Run `python3 -m pytest -q`, `python3 scripts/build_package_manifest.py` (if needed), manifest/file-list checks, `git diff --check`, source-rights inspection and legacy generic HTML→PPTX path tests. Real company PDFs remain **private unapproved** comparison material, not public fixtures.
- [ ] **Step 5: Commit verified work.** `git add` only changed source/fixtures/docs and commit `test: verify creative grammar compositions end to end`; leave unrelated work untouched.
- [ ] **Step 6: Personal plugin update only after all release gates pass.** Package existing `document-studio` skills with optional `ko,ja`, inspect ZIP inventory, fetch live Plugin Creator metadata and guardedly update **same** private personal plugin using current release ID; verify resulting installed version/readback. If permissions/tool support fail, stop and report plugin installation pending rather than claiming success. Do not push the GitHub branch without a separate explicit publishing decision.

## Plan verification and handoff

- [ ] Cross-check every spec section against Tasks 1–6 and the five Review Focus test cases.
- [ ] Check interface names, statuses, schema versions and file paths across tasks for exact consistency.
- [ ] Review the diff and obtain approval of this implementation plan **before** executing Task 1.

**Recommended execution method:** Native. The parser, plan schema, HTML anchors, state graph and QA receipt form a tightly coupled API; one execution context is likely to preserve consistency while the staged red/green commits provide review checkpoints.
