# Document Studio — Approved Layout Grammar → Creative Composition

**Status:** Approved by author on 2026-10-29; implementation pending

**Product:** Independent `document-studio` (successor to alpha.4)

**Chosen approach:** C — hybrid grammar-constrained planning, creative HTML composition, rendered visual QA
**Scope:** Document-generation integration, not a new company-training pipeline.

## 1. Intent and success conditions

Enable Document Studio to **use** a reviewed organization's layout relationships when making a genuinely new document, rather than merely recording rule IDs. Retain Brand DNA and corporate voice while freely adapting hierarchy, size, spacing, number of columns, media and document rhythm to the reader's task. The content and page purpose decide the new form. Approval and rights checks remain distinct from design quality.

Success is demonstrated by one authorized, synthetic, approved Company Pack producing **at least two visibly different HTML compositions of new fictional content**, both satisfying the same selected grammar. An approved pack's exact source elements must not be cloned or embedded. The project must record which rules were selected, why, how each was implemented and what QA was actually performed.

### Non-goals / anti-goals

- No fixed source-page cloning, guaranteed official-brand look, pixel-match percentage or automatic certification of a real company's identity.
- No automatic acceptance of draft/stale/rejected rules, no privilege escalation from a mere public PDF, no silent cross-company style reuse.
- No forced hardcoded layout template or compulsory three-variant ceremony for every page.
- No copying original corporate logos, illustrations, font files or document text into a public plugin.
- No blanket promise that HTML visual QA implies editable PPTX visual QA; export receives its own check.

## 2. Approaches and decision

| Approach | Benefit | Limitation | Decision |
|---|---|---|---|
| A — AI reads rule prose and directly writes HTML | Maximum expressive freedom | No deterministic rule selection or audit trail | Rejected alone |
| B — Deterministic rule-to-template renderer | Testable placement | Tends to repeat rigid forms, weak at image-led narratives | Rejected alone |
| **C — Structured planner + creative HTML + measured QA** | Reviewable source-to-design chain, real stylistic variation | More engineering and QA work | **Selected by author** |

## 3. Existing code and the missing connection

- `skills/company-profile-analyzer/scripts/grammar_synthesis.py` proposes spatial relationships; individual rule acceptance and pack approval occur separately.
- `skills/report-html-pptx/scripts/select_layout_grammar.py` currently selects reviewed rules but **omits their `relationships`** and allows selecting relational rules with only one of the involved content roles.
- `skills/report-html-pptx/scripts/scaffold_report.py` records selected `rule_ids` on the company config, then emits the **same generic starter HTML**. `skills/document-design/SKILL.md` tells the author to select rules but does not yield a mandatory structured composition contract or audit.

The new connection must modify this production path without breaking generic/unbranded documents or existing projects.

## 4. Interfaces and data contracts

### 4.1 Strict rule selection

Extend `select_layout_grammar` outputs additively with `element_roles`, `relationships`, measured `evidence_refs`, `constraints`, `variation` and `origin_pack`. Require **all** roles in a multi-role relationship to appear in the page content inventory; the existing one-role selection behavior remains for non-relational rules. Preserve document/page family, density, intended-use and ancestor-approval gates. A conflict returns a described no-match/fallback, not an invented constraint.

### 4.2 Page input and plan

Introduce a schema-checked page brief consumed **after manuscript completion**. A page includes:

- `page_id`, `page_family`, reader question, intended reading order, content roles and element identifiers;
- content density, actual output use/canvas, language and document-family scope;
- licensed/verified assets with source status and whether labels remain native;
- requested visual expression and selected design direction, when provided.

`plan_layout_grammar.py` accepts an **approved** Company Pack, document/page-family scope and this page brief; emits `content/layout-plan.json` with:

1. exact pack identity/version, snapshot hash and selected accepted rule IDs;
2. each applicable rule's source evidence, `above` / `left_of` (and future permitted) relationship, role anchors, confidence, and allowed variations;
3. an executable page composition contract: protected brand traits, required semantic relationships, intentionally variable geometry and media choice;
4. rule conflicts, missing roles/invalid evidence and neutral fallback reasons;
5. `review_status: pending_render_review` — **never** approval from planning alone.

The plan references roles and evidence, **not copied PDF coordinates**. Plan generation is deterministic and testable; interpretation of meaning and final visual form remains with Document Design.

### 4.3 Actual HTML integration

Document Design consumes `layout-plan.json` as an obligatory stage input when an approved pack is active. It authors **real** `html/index.html` with actual final-language copy and content assets. Every page carries stable `data-page-id`, and every rule implementation links its actual layout elements to `rule_id`/`element_id` via `data-grammar-*` annotations. Generate layout variants freely where the rule permits (e.g. spacing, alignment, scale, crop, image ratio, column count) while preserving selected required relationships and author decisions.

No universal cover/card/table template: a typography-led cover, image narrative, analytical two-column composition and dense operational body may all be correct outputs. A permitted variation is an option, not a command to use it. Source-derived inferred geometry is advisory; source copyrights and brand asset licensing are enforced independently.

For projects with no approved matching rule, the plan records `neutral_fallback` and the existing document-design route operates normally. This is not represented as approved corporate grammar.

### 4.4 Visual and structural QA

Add `audit_layout_grammar.py` to compare the actual rendered DOM geometry to the active plan **without declaring aesthetic taste from geometry alone**:

- verify the target page/element anchors exist exactly once; detect unauthorized rule IDs and missing role evidence;
- for `above` / `left_of`, measure actual DOM rectangles and report ordered positioning, overlap/conflicts and canvas overflow;
- inspect text clipping, font resolution and safety margins through existing production contract browser checks;
- generate per-page screenshots and an `qa/layout-grammar-application.json` receipt that records renderer/tool availability, inspected pages, passed/failed/unverified relationships and review notes.

No available browser ⇒ `UNVERIFIED`, never PASS. Structural audit PASS alone ⇒ not full visual acceptance. A human/vision reviewer must inspect cover, meaningful body pages and all flagged pages; author revisions rerender affected pages. Export then repeats its own HTML/PPTX checks.

## 5. Processing sequence

```text
Approved Company Pack + final-language manuscript/page map
  → select accepted scoped rules (or neutral fallback)
  → plan page relationships + allowed expressive freedom
  → Document Design composes actual HTML and assets
  → render screenshots + measure element geometry
  → visually review; revise the HTML if necessary
  → approved HTML handoff to existing export/ProjectState
```

The project state records the pack snapshot hash, plan hash, HTML hash, QA artifact and actual tool receipt. A changed pack rule, accepted design direction, body copy, font or canvas invalidates affected checks; unchanged pages may reuse valid receipts. The original approved pack stays immutable.

## 6. Explicit permission and security boundaries

- `status=approved` on the pack **and** `status=accepted` plus matching human review for each rule are mandatory for branded production.
- An inherited rule from an unapproved ancestor must never become trusted because the child pack was approved.
- No private filesystem paths, source preview images, source paragraphs, arbitrary CSS/HTML or raw reference drawings enter exported Company Packs, plugin archives or public fixtures.
- HTML content and plan IDs are escaped/validated; untrusted source material is data. Asset URLs require independently verified provenance and project containment.
- No automatic execution of document-embedded scripts/macros or network import of corporate assets.

## 7. Test and evaluation plan

1. **Selection tests (RED→GREEN):** approved multi-role rules require all participating content roles; relationship/variation/source anchors survive selection; proposed/stale and cross-family rules cannot leak.
2. **Plan tests:** deterministic output, conflicting or missing role identification, no fake approval, stable pack snapshot, neutral fallback and prompt-injection-like source text treated only as data.
3. **HTML contract tests:** on a synthetic approved pack, two distinct authored page layouts satisfy the same grammar and receive separate evidence-linked trace IDs; changes to position break the relationship audit.
4. **Render QA:** real browser when available, actual screenshots and DOM rectangle checks for `above` and `left_of`, overflow and text clipping; missing browser yields explicit unverified status.
5. **Integration:** scaffold + Design + Export project state consumes plan and QA; existing unbranded pathway and all prior tests remain intact.
6. **Real public sources:** Suntory and Seven & i continue as **private, unapproved reference evaluations** only. Measure whether observed brand traits can guide novel fictional-content compositions, with honest human observations; no real-company production approval or pixel-fidelity claim.

Release only after a clean full test suite, real rendered sample inspection, rights-safe ZIP inventory, and guarded update of the **existing personal Document Studio plugin** via Plugin Creator. Do not create a second unrelated plugin or change its sharing scope.

## 8. Risks and explicit builder defaults

| Risk | Mitigation |
|---|---|
| Sparse 1-page evidence mistaken for corporate law | Require accepted rule, show confidence and page-family scope, allow omission when sensible |
| Spatial rules conflict with actual content order | Report a conflict and request design replan; don't silently reorder facts |
| Deterministic templates reduce creativity | Contract specifies relationships and constraints; Document Design owns form and media |
| Automated QA passes a bland/ugly layout | Distinguish geometry pass from vision/human aesthetic review |
| No browser/export tool in runtime | Mark unverified, preserve HTML/plan and report limitation truthfully |
| Company assets or fonts redistributed | Pack references and rights approval only; no source file bundling |

**Unsettled implementation details the builder can decide:** exact CLI argument spelling, JSON field names within this contract, choice of HTML/DOM inspection library already supported by the runtime, and internal test fixture organization. These choices must not weaken approval, evidence or visual QA gates.
