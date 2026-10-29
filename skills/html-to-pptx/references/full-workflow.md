# Conversion troubleshooting

Pipeline: preflight → DOM measure → native shape/text assembly → font embedding → structural self-check → rendered PPTX visual audit. Read the failed stage's script or error only. The entrypoint defines current preferences; older lessons are technical examples, not mandatory approvals or delegation rules.

## Environment
Python 3.11+ and the packaged requirements/Playwright browser must already be available. Check the selected exporter when needed, reuse a known runtime, and preserve HTML plus the exact missing-delivery boundary if unavailable. New installation or access is a concrete final user decision after authorized unaffected work; it is not an automatic prerequisite to start composing. Pillow/fonttools may need Brotli for the bundled WOFF2 font. PowerPoint COM or LibreOffice provides PPTX rendering; absence means visual QA is unverified. Do not install fonts automatically by default.

## Useful CLI
`python convert.py input.html --out final/report.pptx`
`python convert.py input.audited.html --out final/report.pptx --only-slides 2,4`
`python convert.py final/report.pptx --cleanup`
Use `--help` for flags; skipping checks does not establish a pass.

## Cache correctness
HTML source changes reset the audited copy via SHA256. Preserve any desired conversion correction by deliberately reapplying it to the fresh copy. Missing fingerprint resets a legacy audited copy conservatively. External assets/global CSS/font changes need full measurement and rendering. Incremental mode is only for local page edits with unchanged topology; keep the same output location to reuse caches. A clean removes those caches.

## Triage
Read structured self-check/preflight warnings and one contact sheet. Inspect warned/dense/changed pages directly. Inspect full-resolution text before deciding it fits. Batch local repairs; full rerun for global changes. If a page/element still fails after two repairs, record the remaining mismatch and stop speculative edits. Do not require subagents or a specific host's Agent API.

## Fonts and editability
Keep actual characters in native text. Font installation requires prior user authorization; embedding is preferred. Use supported-css.md for raster fallback boundaries. Never flatten the entire report to satisfy similarity checks.

## Office-print reports

Use [office-print](../../report-html-pptx/references/office-print-reports.md#pdf-and-editable-pptx) for exact physical A4, source-to-PPTX line spacing/rich runs/table borders, embedded fonts and actual renderer review. An XML/self-check pass alone can miss spacing and theme-border changes.

## Delivery status
Keep compact QA evidence with the editable PPTX and portable HTML. If renderer access fails, deliver completed authorized artifacts as drafts with the missing verification stated, and request a decision only if more installation/access is required. Preserve sources and useful caches until accepted.
