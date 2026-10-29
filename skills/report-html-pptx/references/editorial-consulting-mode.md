# Editorial Consulting Mode — optional, consultant-led planning

This route is **opt-in**. It improves the author's thinking and source-grounded manuscript before the existing Document Studio Design → Export production pipeline. It is not a slower default for one-shot work, a new document family, a new exporter or a parallel content database.

## Activate and resume

Activate only from an actual explicit author request for consultant-led research/critical co-planning. Record the located author response through `scripts/editorial_consulting.py --project <project> begin --origin <user-message-locator>` when a project exists. If no project has been created yet, keep an equivalent compact chat state and bind it to the existing brief once created; never pretend an absent file exists. Reuse existing reader, purpose, genre, source restrictions and prior accepted choices. Treat `intake.fields.mode` and the consultation profile as separate: no expansion of `one_shot|collaborative`, no implicit activation from a routine deliverable request, and no invented user consent.

For editorial-only planning, do not demand final output format, canvas or other production-only selections before substantive research. When the author later requests a laid-out file, preserve the ordinary intake's unresolved required choices and production gate.

## Consultant-first opening

The author should receive a useful **independent first diagnosis**, not an exhaustive survey:

1. Identify the reader's actual decision/use and classify the document family: live narrative, reading report, approval, proposal/plan, SOP, analytical brief or fixed template.
2. Restate the author's provisional thesis as a hypothesis. Identify one to three questions whose evidence could confirm, narrow, contradict or substantially reframe it.
3. Examine supplied evidence first; research consequential public gaps in the relevant original language and geography, subject to explicit source and confidentiality restrictions.
4. Independently investigate **document precedents** of a similar form and purpose, as well as particularly instructive cross-industry editorial/design cases when useful. Do not rely exclusively on the bundled DEMO gallery.
5. Return a professional judgment: what is already strong, what is weak or missing, a supported alternative thesis and why the reader might make a different decision as a result.

Do not require a search count, fixed number of examples or universal deep research. A short internal approval sheet can have one credible pattern; a complex strategy lecture may benefit from multiple genuine options. Stop searching when additional sources would not change the choice. If public search is restricted or evidence cannot be accessed, mark the affected claims and examples unverified.

## Benchmark each inspected reference in three distinct ways

- **Content architecture:** What reader task does the actual source solve? How does it sequence argument, evidence, qualifications, examples, decision and action? What can transfer to this document family?
- **Editorial treatment:** How does it control prose density, terminology, captions, information hierarchy, voice and navigation? Reading reports need complete adjacent explanation; live decks need comprehensible sequence and speaking context.
- **Visual relationship:** What actually inspected imagery, typography, grid, diagrams or pacing helps the argument? Do not infer a visual layout from a source's textual description, inaccessible image or search snippet.

Use original corporate reports, investor publications, official project pages, professional case studies, DEMO reference assets and `external-editorial-references.json` as *discovery candidates*. Open the actual available pages/assets before claiming their properties. Return compact records validated by `validate_reference` with `id, role, title, publisher, url_or_file, checked_scope, access_limit, visual_inspected, transferable_pattern, nontransferable_content, claim_ids, section_ids`. Link factual claims only to content evidence in the existing canonical source record. Editorial/visual precedents are **inspiration, never proof of market or business claims**. Do not copy protected art, logos or wording into the new deliverable.

If an initially inaccessible precedent becomes inspectable, validate the new checked scope and replace its previous compact record under the **same reference ID** (CLI `reference --replace`). Do not keep duplicate references to inflate evidence counts. Reinspection does not by itself validate unrelated claim IDs.

For any consequential fact, preserve definition, jurisdiction, period, population, unit, denominator and limitations. Research outcomes are `confirm|qualify|contradict|reframe`. A contradictory primary source is first marked for argument review; it does not automatically justify a specific replacement thesis. Architecture decides the affected current message and required neighboring transitions, while accepted unaffected sections remain intact.

## Consultant Challenge and meaningful strategy alternatives

For consequential disagreement, show:

1. **Current hypothesis** — the writer's actual claim, not a straw man.
2. **Critical gap/countercase** — relevant checked evidence and strongest reasonable rival interpretation.
3. **Recommended alternative** — precise new thesis, content mechanism or change in order.
4. **Reader impact** — why it better informs, persuades or enables the intended decision.
5. **Tradeoff and decision** — clear recommendation plus one genuinely consequential author choice.

When real alternative structures exist, show two or three distinct approaches, including the recommended one. Compare their reader decision, explanatory order, evidentiary burden and visual communication roles. Do not fabricate three flavors of the same outline or ask the author to choose preferences the assistant can resolve.

The author's response is authoritative: retain accepted/rejected options with an actual origin. An ambiguous `계속`, `알아서`, `続けて`, silence or a suggested default cannot approve a pending direction. Continue independent unaffected investigation while a consequential choice is pending.

## Early visual comparison: a bounded concept spike

Only when visual difference materially helps choose among strategies, create one or two **representative exploratory HTML pages** with distinct meaningful content/visual relationships. Use `planning/previews/`, not the canonical `html/index.html`. Apply actual available prose, verified graphics or explicitly labelled illustrative copy; no fabricated metrics, results, DEMO commitments or unverified reference-image claims. Select medium deliberately (original asset, native diagram, illustrative image or combination). Inspect a real rendered sample at intended presentation/reading size when tools permit and report the actual inspected scope.

This is a direction comparison, **not** final composition, finished image procurement, final-language line-flow QA or PPTX export. Never mark an exploratory sample as a verified Design/Assets/Export stage in `qa/skill-use.json`; a preview record is only metadata. If the concepts differ mainly in wording or argument, show a written comparison and skip the expensive preview.

Once the author chooses, keep a **direction brief** (selected thesis/relationship/visual atmosphere, reference IDs and explicit constraints). Do **not** freeze page geometry or let the preview force the subsequent manuscript.

## Adaptive co-writing after the chosen direction

Return attention to research, outline, arguments, quantitative conditions and final-language manuscript. Maintain one canonical brief, claim ledger, section/page map and copy. Produce a complete through-line, then focus author dialogue on:

- a claim undermined or limited by a new verified source;
- a structural alternative that would materially change reader comprehension or decision;
- a pivotal section with weak causality, missing mechanism or inappropriate evidence;
- a choice between conflicting substantive priorities the author must own.

For routine paragraphs, wording, transitions or small evidence additions, edit autonomously and report the changed scope. Revisit the whole story only if the thesis genuinely changes. Use the document family's actual completion contract; do not impose live-presenter takeaways/bridges on a formal report or template.

Let the author request deeper research, alternatives, local revision, whole-document reframing or reduced involvement at any time. A returned objection triggers focused re-research and re-proposal, not defensive justification of the previous draft.

If the author changes a previously accepted direction, reopen the alternatives stage and invalidate the former manuscript acceptance. If the author requests copy changes after manuscript approval, return to editorial review. Existing production receipts then follow the normal change-impact invalidation rules; an old sample or former approval is not proof for the revised copy.

## Approvals and production handoff

Keep exactly two consequential acceptance events: selected **strategic direction** and accepted **final manuscript**. Review pivotal interim questions adaptively, not through universal per-page sign-offs. Preserve actual response origins. Before manuscript acceptance, verify coherent final-language prose, source-to-claim fidelity, important contrary evidence, status/uncertainty and necessary genre fields. Unresolved decision-critical claims are explicit and cannot be made credible through visual treatment.

After actual manuscript acceptance, hand the supported claim IDs, accepted map, canonical copy, source/asset locators and visual direction brief to the normal owner pipeline. Full Design is free to recompose appropriately around the final content and must perform all existing layout, visual, text-flow and export QA. The ordinary production-intake gate remains in force, and a concept preview cannot waive it.

## Compactness and handoff

Use small phase packets and changed IDs, not copied full transcripts. The optional phase state stores only decisions, source IDs, preview pointers and impact records. If research adds no decision-changing fact, keep the accepted architecture. If a later objection changes one section, edit it and necessary neighbors only. Never make one-shot clients load this guide unless they explicitly request this mode.
