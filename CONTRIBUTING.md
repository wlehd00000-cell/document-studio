# Contributing to Document Studio

Thanks for helping build a practical, reviewable document workflow for teams. We welcome bug reports, reproducible examples, documentation fixes, and small, independently testable improvements.

## Before you contribute

1. Read the [README](README.md) and [workspace admin guide](docs/WORKSPACE_ADMIN_GUIDE.md), especially the **alpha limitations**.
2. Open a GitHub Issue for substantial changes. Explain the real problem, a minimal reproduction, and your proposed acceptance criteria before implementing a large feature.
3. Use **only materials you own, created independently, or are authorized to share publicly**. Do not commit employer documents, client data, internal screenshots, credentials, proprietary fonts, or derivative extracts with unclear rights.
4. Do not bypass the exporter’s source-rights or review controls. A private-source deployment mode requires a separately designed authorization boundary and tests.

## Local checks

Use Python 3.12; development dependencies are in `requirements-dev.txt`.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python scripts/verify_public_release.py
python scripts/install_local.py --verify-only
python scripts/build_package_manifest.py --check
python skills/report-html-pptx/scripts/build_design_css.py --check
```

When you change tracked package content, **regenerate and include** `package-manifest.json`:

```bash
python scripts/build_package_manifest.py
python scripts/build_package_manifest.py --check
```

Run a new plugin ZIP export against the fictional `company-packs/demo-retail` fixture when touching packaging, and inspect the produced archive. Browser layout checks require a working Chromium/Playwright environment; tests that skip without it are **not** evidence that browser rendering passed.

## Pull request checklist

- [ ] The issue and user-facing behavior are clearly described.
- [ ] No non-public company material or prohibited font binary is included.
- [ ] New behavior has tests, including failure/denial cases where relevant.
- [ ] Metadata, examples, and documentation do not overstate current capabilities.
- [ ] The file-hash manifest is current and CI checks pass.
- [ ] Visual behavior was checked with a browser when the change affects rendering.

We use [MIT](LICENSE) for original contributions; see [third-party notices](THIRD_PARTY_NOTICES.md). By contributing, you confirm you have the rights to submit your work under the repository's license.
