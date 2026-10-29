# Repeated reports without stale evidence

Create a new period project from the last accepted project when required. Reuse its valid brief, compositions, source bindings and components, not old facts or approval receipts. Weekly/KPI/event reports need only changed inputs, affected analysis/conclusions and current output checks.

Preserve source filename/range or URL, period, unit, denominator, aggregation and status. Refresh volatile evidence before reuse. A missing value is not zero; percentages need a defined denominator. New datasets/periods invalidate charts and conclusions even if the visible page template is unchanged. Complex YoY/cohort/forecast/scenario/survey calculations use an appropriate available analysis workflow, with method/output bound to evidence IDs.

HTML text binding remains compatible: use <span data-report-key="sales.current">old value</span> in html/template.html. Keys use letters/digits/underscore/dot/hyphen, double quotes, no nested markup. content/report-data.json holds formatted strings; values are escaped. Avoid a second manual transcript.

```text
python scripts/refresh_report.py html/template.html content/report-data.json html/index.html --previous ../previous/html/index.html
```

Output differs from template/data/previous. Missing keys fail before writing; unused keys are reported. Row additions, charts, assets and narrative changes need deliberate source edits. Recurring decks use the canonical HTML and default HTML-to-PPTX path. Older native-only projects require the HTML scope needed for the requested output; preserve originals and accepted constraints.

Changed page numbers are a review shortlist, not automatic incremental export authorization. [Project-state](../system/project-state.md) checks actual source/dependency signatures and scoped receipts. External CSS/font/image/geometry changes broaden invalidation. New-period output normally needs full export verification. User acceptance applies to the revision actually reviewed. Do not claim measured time/token savings without a comparable benchmark.
