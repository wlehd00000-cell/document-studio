# Document Studio — public source edition

An independent company-adaptable document-production plugin (experimental v0.1.0-alpha.5), not a 2.0 release of another plugin. It combines eight core skills with optional Korean/Japanese translation modules, resilient PDF/PPTX visual analysis, approved layout relationships, traceable HTML composition plans, explicit profile approval and public-only plugin ZIP exporting. Native visual/font QA remains environment-dependent.

## Try it

1. Clone the repository and inspect `skills/report-html-pptx/SKILL.md`.
2. Run `python scripts/install_local.py --verify-only` to verify the source bundle. Install with `python scripts/install_local.py --language-skills none` for core-only, or select `ko`, `ja`, `ko,ja` after inspecting the destination.
3. Ask for a **fictional** Korean or Japanese business proposal and choose a document audience, purpose and format.

The demos use invented companies and outcomes. Font binaries and private workplace assets are intentionally excluded. See `README.md` for limitations and `THIRD_PARTY_NOTICES.md` for licenses.

## Requirements

Python 3.10+, and optional Node.js plus an HTML/PPTX conversion environment. The README explains external rendering dependencies. Installing skills does not certify output tools or fonts.
