# Document Studio — start here

Version **0.1.0-alpha.6** · experimental public-source edition.

Document Studio keeps document-writing and review conventions in reusable agent skills and reviewed Company Packs. It can analyze authorized references, but the generated output still needs human review.

## Included

- **Eight core skills:** company-profile-analyzer, report-html-pptx, document-research, document-architecture, document-writing, document-design, visual-assets, html-to-pptx.
- **Two optional language skills:** business-korean-translation, business-japanese-translation.

## First experience

1. [Download the Starter or fictional Company Pack ZIP](docs/DOWNLOAD_AND_INSTALL.md). The GitHub source ZIP is not an installable ChatGPT plugin archive.
2. Inspect the downloaded files, verify SHA256, and register through available Plugin Creator or workspace admin controls. Downloading does not itself install anything.
3. Ask for a new *fictional* report; inspect evidence, font policy and actual rendered output.

For local skills installation and source workflows, start with [README](README.md) and `python scripts/install_local.py --verify-only`.

**Required decisions:** reuse explicit user choices. Conversation language does not automatically approve final document language; keep missing production fields pending rather than guessing. A short edit or research-only task does not require the full new-file questionnaire.

**Boundaries:** the public exporter blocks private/restricted source-derived Company Packs; no licensed font binaries or employer materials are bundled; HTML/PPTX quality checks need their own runtime verification. Installation and workspace rollout require supported permissions.

[Workspace administrator guide](docs/WORKSPACE_ADMIN_GUIDE.md) · [한국어](docs/QUICKSTART_ko.md) · [日本語](docs/QUICKSTART_ja.md)
