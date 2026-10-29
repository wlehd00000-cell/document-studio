# Scoped execution and honest readiness (v4)

The orchestrator remains the only request owner. Specialist skills remain the
actual authors and reviewers; the runtime validates local files, choices,
scope and evidence. No host hook can prove that a model performed a skill.

`system/workflow-contract.json` owns stage IDs, owner mapping, change impacts
and readiness terms. Existing project-state v1 files remain readable. Existing
legacy briefs are treated as full production until their actual work scope is
declared; migration does not invent user decisions or reviews.
Execution updates live in `qa/workflow.json`, which overrides legacy
`brief.workflow` without rewriting the content or invalidating its reviews.

Use `scripts/workflow.py --project <project> begin --operation full --origin
<located request>` for new work. A local edit uses `--operation revision
--changed-role copy --pages 2 --origin <located edit>`. Argument, fact,
generated_asset, asset, style, font, canvas and export_fix have separate
impacts. Global changes reopen all affected pages. Declare actual conditional
research/asset jobs with repeated `begin --required-stage research|assets`
(stored in `qa/workflow.json`); otherwise record why
they are unnecessary with `skip research|assets --reason <actual reason>`.
Required work cannot be skipped. Bounded translation uses only its target language owner.

`handoff writing|design|export` returns current choices, actual file paths and
hashes, changed scope and the expected result. Reuse this packet; do not ask
known choices again or rewrite completed analyses. Apply the named owner skill
and update the same map/copy/HTML, without a second manuscript.

v4.2 adds `begin --execution-profile auto|focused|standard|showcase` and repeated
`--risk-signal` (external_presentation, spatial_concept, live_motion,
brand_sensitive, precision_data). The classifier records execution effort but
never removes required owners, factual review, brand checking or first-build
final-size visual inspection. Legacy workflows without profile resolve to
`standard` for new full work. A requested low profile cannot override high-risk
work; explicit upgrade is allowed.

`handoff <stage> --track-metrics` opens an **optional** stage attempt in
`qa/execution-metrics.json`. Plain handoff remains read-only. `complete` and
`skip` close only a real open attempt; repeating them cannot fabricate timing.
The elapsed time is observed wall-clock interval, which may include user idle
time, **not** an isolated model execution duration. `input_tokens`,
`output_tokens`, model/tool/image/export counts and QA reuse remain `null` unless
the runtime actually provided measurable values. Negative elapsed time is
unverified. This log is separate from the production evidence owned by
`qa/skill-use.json` and deliberately contains no manuscript, prompt or business
copy. A metric write failure is reported separately; it does not falsify a
completed product receipt.

After actual work, `complete <stage> --input <project-relative source> --output
<actual result> --pages <checked IDs> --observations <actual checked scope>`
records input/output hashes in the existing `qa/skill-use.json`. Repeat input
and output options as needed. A read, plan, future file or generic checkbox is
not a completed stage. This is a production receipt; it does not pass editorial,
visual, export or user-acceptance QA. New workflow records also bind decisions
and actual page scope. Changed inputs/outputs/decisions invalidate reuse.

`project_state.py --project <project> changes --changed <node>` is a read-only
impact plan. Existing scoped receipts may be reused only after actual current
production is snapshotted and their scope signatures remain current. Export-only
audited HTML must be registered and currently reviewed; a byte-identical work
copy may use the canonical review. Keep the original user file read-only.

For page-local canonical Markdown, place exact `<!-- demo-page:ID -->` markers
in page order, once per page. The prefix before the first marker is global.
Unmarked or ambiguous copy conservatively invalidates all pages. Register that
canonical copy as an actual HTML dependency. Import genuinely inspected reviews
with `review --split-evidence` to bind immutable per-page proof copies under
`qa/receipts/`; otherwise overwriting a working audit can invalidate its receipts.
Global shell, font, style, canvas and shared input changes still reopen their
affected scope. A marker or copied proof does not replace actual review.

`production_contract.py prepare` accepts `--recommendations`, `--hints`,
`--changed-field` and `--blocking-field`. Specific delegation plus a reasoned
selection resolves only that field. An accepted preset or template can supply
located reusable choices through the existing intake records/hints. Do not
convert silence, vague continuation, preselection or a model assumption into
acceptance. No new summary approval or per-image approval is required.

The exporter writes `<output>_audit/conversion-result.json` for every started
conversion, retaining actual stage states and failures. `review_candidate`
means a file exists and the executed checks found no blocking failure; it does
not mean delivery-ready. Missing renderers remain `unverified`; disabled checks
remain `skipped`. A failed check or missing/corrupt media retains a useful
candidate and returns exit 2. Critical pre-generation errors leave an incomplete
attempt. The current project gate plus real export review determines readiness.
Do not delete QA evidence while it is bound to current receipts.

Rootless conversion requires the explicit `--reviewed-html-only` declaration.
That flag cannot downgrade a full DEMO project. A project-scoped bounded conversion
requires `workflow.operation=conversion`, the located request origin, and
`workflow.reviewed_input={path,sha256}` for the unchanged reviewed HTML. A changed
input requires renewed review. This is a scope declaration, not an extra user
confirmation when the request already authorizes conversion.
Use `begin --operation conversion --reviewed-input html/index.html --origin
<located conversion request>` to record that binding. The bounded final gate
retains source review and export checks without requiring new-document intake.

Default raster snapshots use 2x pixels while preserving measured CSS/native
geometry. `--snapshot-scale 1..4` controls the cost; its changes invalidate
incremental reuse. Plain originals remain byte-preserved. SVGs annotated
`data-pptx-native="lines"` with only supported solid line children become editable
connectors. Curves, arbitrary markers, complex effects, canvas charts and other
SVGs retain the snapshot path. Table cells remain editable text/shapes; this is
not a guarantee of native table/chart data objects. Original template masters,
animations and arbitrary theme objects are not lossless round trips through HTML.

Purpose/canvas defaults live in design-tokens.json. Intentional per-element
deviations use `target` matching `data-demo-design-key` for body type, font or grid
gap; page and document-wide deviations remain supported. All marked body samples
are checked. Explicit conditions, expressive/rich defaults, meaningful body
images, varied relationships and the accepted guide baseline remain unchanged.

Use an existing permitted runtime. `H2P_CACHE_DIR` (or converter `--cache-dir`)
keeps generated font caches in a writable task directory. Resolving a cache path
does not write during import or `--help`. No system font installation is implied.
Shared JSON writes retry only brief file locks, then report persistent failure.
Concurrent writers to one project remain unsupported; owners run sequentially.

Language-specific default fonts are bundled: Korean Pretendard, Japanese
Pretendard JP. Official Korean family names are `Pretendard` / `Pretendard Variable`,
not an invented `Pretendard KR` font identity. Use actual `lang=ko|ja` on bilingual
passages. Newly scaffolded contracts use version 2.0; existing version 1.0 projects
retain their prior JP policy until an authorized font change or located template
override. Any font change invalidates affected layout and export review.
The exporter uses an EOT font envelope and records PowerPoint's actual embedded
font recognition. Rejected embedded fonts block verification; other renderers'
font recognition remains unverified. Every final page still requires visual review.
