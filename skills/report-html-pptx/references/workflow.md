# One project and useful skill handoffs

The [orchestrator](../SKILL.md) owns completion. [Routes](../system/authoring-routes.md), [intake](intake-contract.json), [tokens](../system/design-tokens.json) and [state](../system/project-state.md) each own one rule; not every support file is mandatory reading.

New work uses architecture → writing → HTML design → HTML-to-PPTX. Research closes actual evidence/original gaps; visual-assets follows a concrete design job. Accepted evidence/copy/layout skips reconstruction. Translation-only uses the target-language skill; reviewed HTML conversion goes to export. Local changes activate only affected owners and rebuild dependent files.

Load the owner SKILL.md at its stage unless already loaded. Pass current brief/map/copy/evidence paths/IDs, accepted constraints and allowed changes. Return actual changes, scoped checks and remaining gaps. The orchestrator coordinates instead of rewriting finished owner analysis. No mandatory agent or duplicate dossier/manuscript.

## Start before paperwork

Understand the current request and enough designated material. Resolve the six required choices from actual instructions/accepted context and ask only the missing ones. Keep partial replies pending; recommendations never close unanswered fields. Independent source review can proceed while waiting. [Question waiting](question-waiting.md) keeps an open asynchronous question pending: after independent work, use supported waits instead of ending the turn with a final message. A display acknowledgment or elapsed wait interval never counts as the reply; fall back to ordinary chat with preserved choices only when the host cannot retain the control. Available sections need not wait for optional research or decorations. A useful draft/composition precedes exhaustive runtime discovery and the complete QA graph.

One-shot finishes files and QA. Explicit collaboration uses a concrete combined content/design proof when practical, including dense body detail, then finishes the agreed scope.

## Canonical files and optional helpers

Use content/brief.json, existing copy/evidence, html/index.html, html/assets, qa and final. brief.sections holds questions/messages/claim IDs/conditions/visual purpose. Inventory is metadata; asset records carry files/provenance/crop review; quantitative conclusions retain validated analysis inputs/method/output.

intake.py preflight is optional bounded reading; resolve/import preserves explicit/reused/specific delegated answers and unresolved fields; old assumptions are not answers. First-use help stays in chat; render_intake.py is retained only for legacy compatibility and is not a startup step. scaffold_report.py requires resolved core choices before creating HTML; its four replaceable starter pages are not a required sequence. authoring_routes.py returns HTML and requested exporters; legacy native arguments cannot switch the route.

run_report.ps1 remains compatible for scaffold/refresh/inventory/convert/render and reuses action-specific runtimes. inventory_sources.py reads designated trees only; refresh_report.py updates its bound text keys, while other changes need actual source edits.

Check only the exporter once when needed. [Runtime compatibility](runtime-compatibility.md) forbids automatic native rewriting/unrequested installation. Bind state as the artifact stabilizes and before reuse/export; snapshot only produced files. Global font/CSS/canvas/order changes reopen affected coverage. Matching names or remembered flags do not establish freshness.

Final delivery needs current automated/editorial/visual and actual export checks. Keep acceptance separate. A useful file with unverified visuals is a review candidate with a precise boundary. This final QA process is not a startup gate.

Follow [production contract](production-contract.md) for independent use/canvas decisions, compact next-step information, actual design measurement and verified role evidence. Existing editorial/visual/export checks remain required.
