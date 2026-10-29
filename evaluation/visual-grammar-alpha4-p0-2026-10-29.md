# Layout-grammar evidence P0 regression — Document Studio alpha.4

**Product:** Independent `document-studio`, version `0.1.0-alpha.4` (not another plugin's 2.0).

**Scope:** Geometry robustness, salient PDF vector evidence and conservative spatial relationship hypotheses. This is **not** a successful visual reproduction or production-ready company identity evaluation.

## Real-source evaluation (private files, public provenance)

The same publicly accessible official PDFs and source SHA-256s documented in [the initial source evaluation](public-company-fidelity-2026-10-29.md) were re-extracted. Original PDFs, previews, raw text and draft Company Packs remain outside this repository. Only aggregate results are recorded here.

| Measured result | Suntory fact sheet (4p) | Seven & i corporate outline (31p) |
|---|---:|---:|
| Pages processed successfully | 4 / 4 | 31 / 31 |
| Salient vector bounding-box regions retained | 71 | 601 |
| PDF zero-area image regions quarantined | 0 | 1 |
| Previously visually role-labeled observations reused | 11 | 7 |
| Draft grammar rules after spatial inference | 7 | 8 |
| Spatial relation hypotheses generated | 2 | 1 |

The 3 generated spatial relationships were `heading above section_label`, `section_label above image`, and `heading above subheading`. These are **geometry-based, unapproved suggestions**, not validated corporate design policy. Single-instance observations remain low-confidence; no real-company rule was accepted or exported.

The Seven & i observation originally anchored to an index that omitted the zero-area image. For this *private evaluation only*, the stale region ID was matched to its unique measured bounding box and the observation was revalidated. In production, changing evidence IDs invalidates the prior review until reanchored and reviewed; no automatic approval occurs.

## Implementation and tests

1. Zero-area images tagged as extracted PyMuPDF image geometry are quarantined with a page-level count, without silently accepting arbitrary invalid boxes. Original extractor indices of remaining shapes are stable.
2. PDFs contribute significant vector bounding boxes (not proprietary path geometry), clipped to the page and capped at 80 per page. Dense charts and tiny drawing fragments are intentionally sampled: **no completeness claim**.
3. Given reviewed visual role *labels* as input, the grammar synthesizer proposes nearby same-page, same-family `above` or `left_of` relation rules, each citing **both** observed source regions. Spatial proximity is measured; design rationale is not inferred automatically.
4. The private HTML review board displays relation labels and offers independent text/image/vector overlay controls. Vector overlays start hidden to preserve legibility.

The relevant synthetic regressions first failed against prior code (zero-area PDF image, missing vector regions, empty relationship rules, over-dense vector evidence, missing review controls) and passed after the targeted implementation. The full repository test suite and package integrity are rerun at release packaging time.

## Still open before any visual-fidelity claim

- **Actual output composition:** rules are now derived and selectable, but a freeform design generator does not yet map approved relations into compelling new HTML layouts automatically.
- **Rendered similarity:** no measured pixel/semantic layout alignment between generated and official pages in this stage. Color recurrence in the earlier study must not be misrepresented as fidelity.
- **Human approval:** real source diagrams, role labeling, corporate tone, licensing, and produced-document visual QA require explicit review. Official source availability does not imply asset redistribution rights.
