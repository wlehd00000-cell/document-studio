# One workflow: reference documents → tailored plugin → new document

This is the **v0.1.0-alpha.5 demo script**, not a claim of one-click automation. Use only fictional or otherwise authorized reference files. Keep originals, extracted text, and the source registry **outside this public repository**.

The five scenes below are intended to appear consecutively in a recorded walkthrough. An actual screen recording and verified end-to-end rendered output are pending; do not substitute generated mockups for those results.

| Scene | Screen to record | Proof point |
|---|---|---|
| **1. Bring references** | A user selects two or three authorized PDF/PPTX reports or brand-guide pages in a private working directory. | The tool is based on *their* examples, not a universal fixed slide theme. |
| **2. Learn their style** | Run extraction and inspect the writing/design evidence, including page geometry and candidate rules. | The model has measurable evidence; it has not declared the rules official. |
| **3. Review and approve** | Show a draft Company Pack and record human decisions on suggested rules and permitted assets. | Company-specific behavior is an explicit review decision. |
| **4. Build their plugin** | Export the approved pack with the selected skills and verify the ZIP manifest. | A reusable, distributable custom plugin is produced without bundling the original reference files. |
| **5. Write something new** | Install the custom plugin via Plugin Creator or the receiving workspace's supported workflow, request an unrelated report, and show its HTML/PPTX output and QA state. | The generated artifact is *new content* guided by the approved pack. |

## Reproducible CLI path

Start with the repository's [installation instructions](../INSTALL_INSTRUCTIONS.md). The commands below are **illustrative** and require you to replace the paths, source IDs, and review notes with real approved inputs. They are not an unattended one-command demonstration.

### 1. Register and extract authorized references

```bash
python skills/company-profile-analyzer/scripts/source_registry.py \
  ../document-studio-private/registry.json ../my-authorized-reference.pptx \
  --title 'Authorized reference deck' --language en-US \
  --document-family executive_report --visibility private \
  --rights 'authorized for internal analysis only'

python skills/company-profile-analyzer/scripts/document_extract.py \
  ../my-authorized-reference.pptx \
  --output ../document-studio-private/extraction.json
```

Keep the `source_id` printed by the registration command. Additional references may be registered and analyzed separately; pass each analysis file to the Company Pack builder.

### 2. Inspect design and writing evidence

```bash
python skills/company-profile-analyzer/scripts/design_analyzer.py \
  ../document-studio-private/extraction.json \
  --source-id REPLACE_WITH_SOURCE_ID \
  --document-family executive_report \
  --output ../document-studio-private/design.json

python skills/company-profile-analyzer/scripts/writing_analyzer.py \
  ../document-studio-private/extraction.json \
  --source-id REPLACE_WITH_SOURCE_ID --language en-US \
  --document-family executive_report \
  --output ../document-studio-private/writing.json
```

For the optional image-based Layout Grammar route, use the [visual-grammar onboarding guide](../skills/company-profile-analyzer/references/visual-grammar-onboarding.md). Extracted metrics alone cannot establish faithful visual similarity.

### 3. Create and approve the Company Pack

```bash
python skills/company-profile-analyzer/scripts/build_company_pack.py build \
  --registry ../document-studio-private/registry.json \
  --design-analysis ../document-studio-private/design.json \
  --writing-analysis ../document-studio-private/writing.json \
  --output ../document-studio-private/my-company \
  --pack-id my-company --company-name 'My Company' \
  --default-language en-US --enabled-language en-US
```

The result is deliberately **draft**, never auto-approved. Inspect the output and resolve any source-rights, font, visual-evidence, and proposed-rule decisions before running the documented `review` and `approve` stages. A real pack with private references may be refused by the public-only exporter unless distribution authorization and approvals are present. Do not modify checks or mark a source as publicly distributable merely to force export.

### 4. Export the custom plugin

For a fully reproducible **fictional** export that does not depend on private materials, use the bundled approved demonstration pack:

```bash
python scripts/export_company_plugin.py \
  --company-pack company-packs/demo-retail \
  --language-skills ko,ja \
  --output ./dist/demo-retail-documents.zip
```

The exporter checks the review and rights contract. It produces a package, **not an installed plugin**. For account installation, see [Plugin Creator instructions](../skills/company-profile-analyzer/references/account-installation.md). Publishing to a Business workspace is a separate admin-controlled action.

### 5. Produce a new document and verify it

After installing the generated plugin in an eligible account, start a **new** chat and ask for a fresh report, for example:

> Using our approved company style, create a three-page proposal for a fictional customer-service pilot. Make the recommendation evidence-aware and preserve the approved writing and layout conventions. Show the HTML output and the QA result.

Alternatively, use the HTML scaffold and [Layout Grammar planning/audit commands](../README.md#approved-layout-grammar--authored-html--browser-qa-experimental-alpha5) to test the accepted fictional pack locally. A new document still requires its own content planning and authoring. Browser layout acceptance depends on Chromium/Playwright and must say `UNVERIFIED` if unavailable; neither HTML validation nor successful ZIP export certifies a pixel-faithful PowerPoint.

## What to show in the GitHub launch video

1. **00–08s:** two or three source documents arrive in a private folder (fictional, independently authored visuals).
2. **08–20s:** extraction evidence and suggested voice/layout tokens appear.
3. **20–30s:** a reviewer accepts/rejects the rules; the pack becomes approved.
4. **30–40s:** a company-specific plugin ZIP is generated and installed.
5. **40–60s:** a *new* request produces a document; the resulting page and its QA status are displayed.

Only record scenes that have actually been executed. Clearly label any illustrative transitions as a **storyboard**, not as an automated feature demo.
