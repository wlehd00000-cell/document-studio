# Visual-grammar onboarding — evidence-first operating sequence

This is the default for company onboarding when the user needs the **company's visual language**, not just a color-token estimate. The scripts do not have a built-in image-recognition model: an available vision-capable assistant or human must actually inspect the private rendered page previews and describe them in the observation JSON. Never claim visual review when only numbers were parsed.

## 1. Private source and measured geometry

Register authorized PDFs/PPTXs with `source_registry.py`, then extract and analyze them as described in this skill. The private source registry is kept **outside public plugin files**.

```bash
python skills/company-profile-analyzer/scripts/visual_grammar_workflow.py prepare \
  --source /private/authorized.pdf --extracted /private/extracted.json \
  --source-id SRC_FROM_REGISTRY --document-family corporate_profile \
  --private-workspace /private/company-visual-review
```

The private workspace now has `previews/page-01.png`, etc., and `evidence-index.json`. Inspect a contact sheet and at least representative full-size crops; record page roles, title/body hierarchy, reading order, image relationship, decorative elements, whitespace and unknowns. Compare multiple pages and multiple independent documents when available. A PDF parsed successfully is **not** evidence it was visually inspected.

**Vector and PDF anomaly handling:** The evidence index now records significant PDF vector bounds as `kind: "vector"` (no reproducible path data). To keep dense PDFs inspectable, it retains salient shapes and at most 80 vectors per page; it is *not* a lossless vector extraction. Zero-area PyMuPDF image boxes are quarantined with a `quarantined_regions` count and skipped without renumbering later measured regions. Invalid manual geometry remains a hard failure. Inspect any missing visual feature against the actual private page image instead of treating absence from the index as proof of absence.

## 2. Structured visual observations

The assistant or reviewer produces `/private/observations.json` with a separate measured-region link for every claimed visible relationship. These are **suggestions**; the human has not yet approved them:

```json
{
  "schema_version": "visual-observations/1.0",
  "observations": [
    {
      "observation_id": "EV-001",
      "source_id": "SRC_FROM_REGISTRY",
      "page": 1,
      "region_id": "SRC_FROM_REGISTRY-P1-R1",
      "bbox_norm": [0.10, 0.12, 0.80, 0.20],
      "role": "heading",
      "page_family": "cover",
      "observation": "Prominent title on a relatively open upper canvas",
      "evidence_kind": "visually_observed",
      "confidence": "medium",
      "status": "suggested"
    }
  ]
}
```

Use measured coordinates from the evidence index, not invented sample values. Visual role vocabulary and page families are validated by `layout_grammar.py`. Source text may be seen in private inspection, but observations should describe *layout relationships*, not reproduce confidential paragraphs.

```bash
python skills/company-profile-analyzer/scripts/visual_grammar_workflow.py propose \
  --evidence /private/company-visual-review/evidence-index.json \
  --observations /private/observations.json \
  --grammar-output /private/grammar.json \
  --redacted-evidence-output /private/redacted-evidence.json
```

The result separates **Brand DNA**, **Layout Grammar**, and **Creative Vocabulary**. A pattern observed on one cover gets low confidence and cannot be silently declared a universal company-wide rule.

The synthesis also proposes separate **spatial relationship** rules from pairs of role-labeled observations on the same source page and page family. It currently supports nearby measurable `above` and `left_of` relations, recording both evidence anchors. The default one-page relation has `low` confidence and remains a hypothesis. A relation is only proposed after a vision-capable reviewer or human has assigned meaningful region roles; it cannot learn the company's intentions from PDF coordinates alone.

## 3. Visual comparison and human acceptance

```bash
python skills/company-profile-analyzer/scripts/visual_grammar_workflow.py board \
  --evidence /private/redacted-evidence.json --grammar /private/grammar.json \
  --private-workspace /private/company-visual-review \
  --output /private/company-visual-review/review.html
```

The private board shows page thumbnails with togglable **text, image/chart and vector** evidence overlays, explicit spatial relationship labels, rule cards and 2–3 **fictional-content** layout studies. The vector layer starts hidden to avoid obscuring busy source pages. The studies are independent hypotheses and are not official corporate examples. Ask the reviewer to inspect: (1) whether the observation and relationship are true, (2) whether they are recurrent/optional patterns, (3) whether the variant still suits novel content, and (4) whether font/logo/image rights are verified separately.

Build a **new draft pack** via `build_company_pack.py build` with the existing registry/design/writing arguments plus `--grammar-proposal /private/grammar.json --redacted-evidence /private/redacted-evidence.json`. Never alter a previously approved pack in place.

The human review decision file (`/private/decisions.json`) looks like:

```json
{
  "schema_version": "visual-review-decisions/1.0",
  "preview_ids": ["study-editorial"],
  "decisions": [
    {
      "rule_id": "cover-heading",
      "action": "accept",
      "note": "Confirmed in source image and tested with alternative title lengths",
      "evidence_digest": "SHA256_FROM_compute_evidence_digest"
    }
  ]
}
```

The digest must be computed over the exact validated observations cited by each rule; the CLI will reject guessed or stale hashes. Actions: `accept`, `reject`, or `revise` (the latter requires a fully validated revised rule and rationale). Every candidate rule needs a recorded decision.

```bash
python skills/company-profile-analyzer/scripts/visual_grammar_workflow.py record \
  --pack /private/company-pack --decisions /private/decisions.json \
  --reviewer "Actual reviewer name"
python skills/company-profile-analyzer/scripts/build_company_pack.py review \
  /private/company-pack --reviewer "Actual reviewer name" --note "Visual evidence reviewed"
python skills/company-profile-analyzer/scripts/build_company_pack.py approve \
  /private/company-pack --reviewer "Authorized owner" --note "Approved for production"
```

After pack approval, query `visual_grammar_workflow.py select` or `report-html-pptx/scripts/select_layout_grammar.py` by document family/page family/content roles. The selector returns either reviewed rule candidates **with reasons** or an explicit neutral fallback. It does not yet compose finished high-quality HTML automatically; visual composition and HTML→PPTX checking remain the document-design/export stages.

When evidence changes, create a versioned draft from the previous approved pack, re-review only affected rules and preserve the original as a historical approved snapshot. Do not re-train on produced documents without independent review.
