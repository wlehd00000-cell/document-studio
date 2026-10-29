# Document Studio

**Open-source bilingual document-production toolkit** · 한국어 / 日本語

A reusable nine-skill workflow for turning a brief into researched, structured, visually explained HTML documents and editable PowerPoint deliverables. The code and working contracts are adapted from a personal implementation; the public examples, fictional organizations and artwork are independent, newly authored materials.

## Skills (9)

| Skill | Role |
|---|---|
| `report-html-pptx` | Intake, one-shot/collaborative routing, orchestration, QA |
| `document-research` | Evidence gathering and source notes |
| `document-architecture` | Argument, document structure and page plan |
| `document-writing` | Korean/Japanese business prose and synthetic style library |
| `document-design` | Editorial design and text/visual contracts |
| `visual-assets` | Diagram/image asset selection and provenance |
| `business-korean-translation` | Professional Korean adaptation |
| `business-japanese-translation` | Professional Japanese adaptation |
| `html-to-pptx` | Editable HTML → PowerPoint conversion and checks |

## Start

```bash
python scripts/install_local.py --verify-only
python scripts/install_local.py
```

See [START_HERE.md](START_HERE.md). To inspect independently authored examples, open `skills/report-html-pptx/assets/accepted-staff-guide/index.html` in a browser.

## Public-demo safety

- Fictional organizations A/B/C, fictional metrics and original SVG visuals only.
- No employer marks, internal documents, source-report text/excerpts, private project history or old validation evidence.
- No claims that synthetic casebook examples were measured from real publications.
- When generating real deliverables, independently verify evidence, sources and use rights.
- **Font binaries are not bundled** in this source-only edition. Install appropriately licensed Korean/Japanese fonts for precise visual QA; fallback typography may vary. Original strict font-embedding checks may require user-provided font assets.
- Editable PowerPoint output requires the optional converter's dependencies; merely cloning/installing skills does not install those dependencies or certify export.

## License

Original contributions in this repository are released under the [MIT License](LICENSE). Existing third-party files retain their own notices; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Attribution

Independent open-source techniques and their license notices are retained where applicable. This is a personal open-source project, **not affiliated with or endorsed by any employer or trademark owner**.
