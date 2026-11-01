# Document Studio technical guide

Use this guide after the [first document task](TRY_FIRST.md). Commands run from a full source checkout. The generic skill installation does not include repository-level packaging tools.

[All documentation](README.md) · [Reference-to-plugin walkthrough](DEMO_FLOW.md) · [Administrator guide](WORKSPACE_ADMIN_GUIDE.md)

## Export a fictional demo plugin

Try the packaging step with an approved fictional Company Pack. No real company documents are needed.

```bash
git clone https://github.com/wlehd00000-cell/document-studio.git
cd document-studio
python scripts/install_local.py --verify-only
python scripts/export_company_plugin.py \
  --company-pack company-packs/demo-retail \
  --language-skills ko,ja \
  --output ./dist/demo-retail-documents.zip
```

The result is a plugin ZIP. Register it using the [ChatGPT installation route](TRY_FIRST.md#chatgpt). To package the generic workflow without a company profile, use:

```bash
python scripts/package_account_plugin.py --language-skills ko,ja \
  --output ./dist/document-studio-account.zip
```

## Skill guide

| Skill | Role |
|---|---|
| `report-html-pptx` | Route the brief, coordinate stages, and track checks |
| `document-architecture` | Develop the argument, structure, and page plan |
| `document-research` | Gather evidence and source notes |
| `document-writing` | Write business copy and consult writing references |
| `document-design` | Compose HTML with readable text and visual relationships |
| `visual-assets` | Select or produce explanatory visuals and record provenance |
| `html-to-pptx` | Convert HTML to editable PowerPoint and check the export |
| `company-profile-analyzer` | Extract PDF/PPTX evidence and prepare Company Packs for review |
| `business-korean-translation` | Optional Korean adaptation and proofreading |
| `business-japanese-translation` | Optional Japanese adaptation and proofreading |

For local installation, `--language-skills none` selects the eight core skills. Use `ko`, `ja`, or `ko,ja` for language modules; omitting the flag includes both.

## Scaffold a document with a Company Pack

The fictional [retail](../company-packs/demo-retail/pack.json) and [manufacturing](../company-packs/demo-manufacturing/pack.json) packs demonstrate separate writing and design settings. Validate a pack, scaffold a project, and retrieve a writing reference:

```bash
python skills/report-html-pptx/scripts/validate_company_pack.py company-packs/demo-retail --require-approved
python skills/report-html-pptx/scripts/scaffold_report.py ./output/retail-pilot \
  --company-pack company-packs/demo-retail --language en-US \
  --genre proposal --interaction-mode one_shot \
  --audience 'Team leadership' --reader-action 'Decide on the pilot' \
  --output-format HTML --canvas widescreen --use reading
python skills/document-writing/scripts/find_writing_reference.py \
  --company-pack company-packs/demo-retail --language en-US \
  --document-family business_proposal --writing-function recommendation
```

The scaffold supplies a starting structure and a content-addressed pack snapshot. Write the new document and inspect its rendered output. The generated font-policy review records a pending check; naming a font does not establish its availability or redistribution rights.

## Analyze an organization profile

Follow the [reference-to-plugin walkthrough](DEMO_FLOW.md) for source registration, extraction, design/writing analysis, draft pack creation, review, and eligible export.

The analyzer measures characteristics such as text geometry, font names, colors, and writing patterns. Those observations become proposed conventions. A reviewer decides which rules and assets are suitable before approving the pack.

For visual relationships, the experimental [Visual Grammar onboarding workflow](../skills/company-profile-analyzer/references/visual-grammar-onboarding.md) connects source evidence, proposed rules, fictional style studies, and human review. Changes to source evidence identify rules that need another review. See the [design specification](superpowers/specs/2026-10-29-visual-grammar-onboarding-design.md) and [source regression study](../evaluation/visual-grammar-alpha4-p0-2026-10-29.md) for implementation details.

Keep originals, extracted text, and private registries outside the public checkout. Private-source analysis is available, but the public exporter **rejects packs derived from private/restricted sources**. Public-source packs also need explicit distribution authorization and completed review and approval. See the [source policy](../skills/company-profile-analyzer/references/source-policy.md).

## Apply Layout Grammar to HTML

After the manuscript and page decisions are settled, create `content/page-brief.json` using schema `layout-page-brief/1.0`. Include each page's reader question, semantic roles, element IDs, reading order, density, use, canvas, language, and authorized assets.

```bash
python skills/report-html-pptx/scripts/plan_layout_grammar.py \
  --project ./output/retail-pilot \
  --page-brief content/page-brief.json \
  --company-pack company-packs/demo-retail
```

The planner selects individually accepted rules from the approved pack, binds roles to elements, and reports conflicts. Use the resulting page, element, and rule IDs in the authored `html/index.html` through `data-page-id`, `data-grammar-element-id`, and `data-grammar-rule-ids`.

Then run the audit:

```bash
python skills/report-html-pptx/scripts/audit_layout_grammar.py \
  --project ./output/retail-pilot
```

Static checks verify traceability. With Chromium/Playwright available, the browser checker measures visibility, clipping, bounding boxes, and `above` / `left_of` relationships, recording screenshots and hashes in `qa/layout-grammar-application.json`. An unavailable renderer produces `UNVERIFIED`.

A passing relationship check establishes the measured geometry. Visual judgment, font review, source rights, and final PowerPoint editability still need their own checks. See the [composition specification](superpowers/specs/2026-10-29-approved-layout-grammar-composition-design.md) and [acceptance status](../evaluation/layout-grammar-native-integration-2026-10-29.md).

## Evaluation and limitations

The [2026-10-29 public-company PDF study](../evaluation/public-company-fidelity-2026-10-29.md) tested official Suntory and Seven & i Holdings publications. It inferred style from the first two pages and measured exact color recurrence on the remaining pages: 25% and 75%, respectively. These figures measure color recurrence only. The study did not establish faithful reproduction of layouts, fonts, writing voice, or editable PPTX.

The shipped workflow supports evidence extraction, explicit Company Pack review, and eligible plugin ZIP packaging. Authoring a new document, checking its actual appearance, and installing the plugin in a receiving account remain separate tasks. Automatic workspace publication and private-source pack export are not supported.

Font binaries are excluded from this public source edition. Use appropriately licensed fonts and verify the actual rendered text. The HTML-to-PPTX converter requires its own dependencies and output inspection.

## Source validation

Use the checks in [CONTRIBUTING.md](../CONTRIBUTING.md#local-checks) for regression tests, source verification, and the package inventory. Regenerate the file-hash manifest after changing tracked package content.
