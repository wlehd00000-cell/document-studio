# Approved Layout Grammar → Native HTML integration: acceptance status

**Date:** 2026-10-29

**Implementation branch:** `feat/company-pack-foundation`

**Scope:** Work in progress, independent Document Studio. A private `0.1.0-alpha.5` experimental plugin update was made at the user's explicit request while browser-based visual acceptance remains **UNVERIFIED**.

## Implemented

1. A rule is eligible only when both its Company Pack and its own evidence-based visual review are approved. Multi-role relationships require all roles, with the original source references and permitted variations retained.
2. A final-language page brief deterministically generates `content/layout-plan.json` after the manuscript, including role-to-element bindings, ordered spatial relationships, provenance, conflicts and SHA-256 trace. A generic starter page does not falsely claim corporate approval.
3. Two independently authored HTML fixture designs, a bold editorial cover and an original abstract illustration cover, use the **same** approved fictional `heading above body` rule while varying scale, spacing, alignment, typography and visuals. Each embeds explicit page, element and rule trace IDs. Static contract tests PASS both.
4. A Playwright/Chromium auditor checks actual DOM geometry, overflow, hidden/clipped elements, page coverage and screenshots. Its Python wrapper binds the receipt to the HTML, plan, checker, source assets and relevant project inputs. Without a working renderer, it records `UNVERIFIED`.
5. ProjectState and the production path reject stale/absent/unverified reports for applicable approved grammar, including stale page briefs, HTML, font policies or source assets. A source-code review found and corrected an extra gate issue: a claimed `PASS` receipt with missing measured relationships was previously accepted; the gate now requires exact relation identities, count, results and Chromium tool metadata.
6. An account-scoped 10-skill ZIP was built with English core and both optional Korean/Japanese skills; it excludes company source PDFs, restricted file types and private folder names. Plugin Creator updated the same private personal plugin to `0.1.0-alpha.5`, preserving its identity and existing prompts.

## Verification carried out

| Check | Result |
| --- | --- |
| Contract tests for the two authored HTML samples | **PASS** (static trace only) |
| Synthetic Company Pack review/approval persistence | **PASS** |
| Relationship/receipt gate negative regression | **PASS** after fail-first test |
| Existing + new Python suite | **123 passed, 6 skipped** (`python3 -m pytest -q -rs`, after final code change) |
| Browser-run relationship measurements and page screenshots | **UNVERIFIED** — Chromium executable unavailable |
| Visual judgment on actual rendered HTML pages | **NOT COMPLETED** — no render screenshots available |
| Real-company publication reconstruction | **NOT CLAIMED** — independently evaluated public sources remain unapproved and outside the plugin ZIP |
| Personal plugin installed/updated via Plugin Creator | **UPDATED** — private experimental `0.1.0-alpha.5`; readback confirmed both manifests and five added native scripts |

## Blocker and next verification

The installed Playwright JavaScript package cannot launch Chromium because the required `chromium_headless_shell` executable is missing. An attempted official browser download failed with invalid/empty archive data. This is an environment/tooling blocker, not an acceptable visual QA pass.

On a machine with working Playwright Chromium:

1. Run `python3 -m pytest -q -rs` and confirm that the browser-specific tests **execute and pass**, with no renderer skips.
2. Run the browser auditor on both fictional HTML fixtures, compare their generated screenshots at their actual canvas, and record an explicit human or vision-capable visual review. Resolve any clipping, font or composition defect found by actual rendering.
3. Recheck source rights, manifest and ZIP inventory; after actual rendered visual acceptance, publish a **follow-up verified release** to the same private Document Studio plugin through Plugin Creator. Do not create a duplicate plugin.

## Scope of evidence

The above checks establish implemented *programmatic constraints and negative-path behavior*, not a visual fidelity score or proof of professionally reviewed layouts. No employer-owned logos, PDFs, fonts or proprietary report passages are used in the acceptance fixtures. The new private plugin release is real and confirmed, but **its browser-dependent quality and actual host document-production behavior remain unverified**.
