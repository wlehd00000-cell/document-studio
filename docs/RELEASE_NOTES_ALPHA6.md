# Document Studio v0.1.0-alpha.6 — Maintenance pre-release

**AI models change. Your company's document standards shouldn't.**

This alpha continues the MIT-licensed, review-first Document Studio toolkit for evidence-backed Company Packs and company-aware document production. It applies relevant *generic* fixes found during a separate plugin audit, without adding corporate-only source documents, branding, fonts, or instructions.

## Download

- `document-studio-starter-v0.1.0-alpha.6.zip`: 8 core skills + Korean/Japanese optional language modules.
- `demo-retail-documents-v0.1.0-alpha.6.zip`: independently fictional retail Company Pack and selected skills.
- `SHA256SUMS.txt`: checksums for both archives; verify before installation.

[Installation guide](https://github.com/wlehd00000-cell/document-studio/blob/main/docs/DOWNLOAD_AND_INSTALL.md) · [Business admin guide](https://github.com/wlehd00000-cell/document-studio/blob/main/docs/WORKSPACE_ADMIN_GUIDE.md)

## Changes since alpha.5

- Fixed incorrect skill counts and stale inherited instructions in entrypoint documentation.
- Unified `plugin.json` and `.codex-plugin/plugin.json` public-facing listing metadata.
- Added **preflight WOFF2 font inspection before scaffold file creation** when authorized font binaries are provided. Missing fontTools/Brotli fails closed; no font-quality bypass or automatic substitution.
- Added read-only audit of 10 skill entrypoints, internal Markdown links, the package manifest's SHA-256 file inventory, and metadata consistency.
- Added regression tests and required the audit in CI and package publishing.

## Important limits

This remains **experimental alpha**, not a production-certified enterprise release. The exporter **rejects Company Packs derived from private/restricted source documents**. Automatic account/plugin installation, consistent *pixel-identical* output across AI model upgrades, and full browser/PPTX visual acceptance are **not** guaranteed. Downloading a ZIP is not the same as installing it. No source company documents or restricted fonts are bundled.

The previous v0.1.0-alpha.5 assets remain untouched. For new evaluations, prefer alpha.6 and submit issues with synthetic examples.
