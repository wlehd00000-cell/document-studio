# Changelog

Document Studio uses pre-1.0 experimental releases. Features and package contracts may change; administrators should pin reviewed versions before workspace deployment.

## [0.1.0-alpha.6] — 2026-10-30

### Source correctness and compatibility fixes
- Corrected the installed skill count (8 core + 2 optional language modules) and removed stale inherited documentation.
- Synchronized the plugin listing information in both standard and Codex manifests.
- Added pre-scaffold inspection of an optional, authorized WOFF2 font bundle. Missing fontTools/Brotli blocks before writing a partial project; the quality floor remains strict.
- Added a read-only release audit for file SHA-256 hashes, version identity, skill routing and local Markdown links, with regression tests and CI enforcement.
- Preserved Company Pack rights/approval safeguards and existing document QA; no real-company originals or font binaries are added.

### Limitations
Private/restricted Company Packs cannot be distributed by the public-only exporter. Actual browser/PPTX visual fidelity and portability across AI models have not been certified.

## [0.1.0-alpha.5] — 2026-10-29

### Included

- Company Pack analysis, evidence capture, explicit review/approval, and two independently authored fictional example profiles.
- Approved Layout Grammar planning, authored-HTML traceability, and browser-geometry acceptance gates.
- Public-authorized Company Pack ZIP exporter, deterministic file inventory, and selectable Korean/Japanese skill modules.
- Eight core document workflow skills, local installation scripts, and experimental HTML/PPTX production tooling.
- Reproducible fictional-package quick start, workspace administration guidance, public safety checks, and a five-scene demo storyboard.

### Known limitations

- **Private/restricted source-derived Company Packs cannot be exported** by the current public exporter.
- ChatGPT personal/workspace installation requires additional manual steps and sufficient administrative permissions.
- New-document authoring and end-to-end editable PPTX output are **not** automatically completed by the ZIP exporter.
- Browser-dependent rendering validation requires installed Chromium/Playwright and must not be claimed passed when skipped.

See [README](README.md), [release evaluation](evaluation/layout-grammar-native-integration-2026-10-29.md), and [workspace admin guide](docs/WORKSPACE_ADMIN_GUIDE.md) for details.
