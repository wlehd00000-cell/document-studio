# Deploy Document Studio in a ChatGPT workspace

This is a practical guide for administrators evaluating **Document Studio v0.1.0-alpha.5**. The project's core task is to turn approved document references into a reviewable Company Pack and an installable document plugin. **It does not yet offer a one-click workspace setup wizard.**

## Why standardize documents separately from the AI model?

AI models, prompt styles, employee teams and document topics evolve. A Company Pack records an approved baseline — writing conventions, brand tokens, allowed layout relationships and documented evidence — outside any one prompt. Managers can review and version this standard, and then use it as an input to their document-production workflow. **This does not guarantee that two models or model versions will behave identically.** After a model or plugin upgrade, recheck compatibility, output quality, font rendering, layout and source rights before broad rollout.

The operating principle is **consistent organizational standards, not frozen templates or identical pixels**. New creative layouts are welcome when they meet the approved grammar and visual QA requirements.

## Important alpha limitation

The present `export_company_plugin.py` is a **public-distribution exporter**. It works with the repository's independent fictional examples and with suitably reviewed **public** sources that explicitly allow distribution. It intentionally **rejects packs derived from private or restricted company files**. Private-source analysis does not imply permission to distribute a derived pack.

Therefore, the full *private corporate references → internal-only plugin* release flow is **not yet shipped**. Do not mark a private file as public, forge approval metadata, or bypass the export guard. A separate private-distribution workflow with explicit organizational authorization and verification is required before production rollout.

## Evaluate the working export using fictional materials

1. Clone the [repository](../README.md#quick-start--export-a-demo-plugin) and use Python 3.12 with the relevant optional dependencies.
2. Run `python scripts/install_local.py --verify-only`.
3. Export the included fictional retail pack:

   ```bash
   python scripts/export_company_plugin.py \
     --company-pack company-packs/demo-retail \
     --language-skills ko,ja \
     --output ./dist/demo-retail-documents.zip
   ```

4. Check the export log and package manifest. The package excludes source PDFs/PPTX files and font binaries; it still needs a human review before being installed anywhere.
5. In an account with the right permissions, follow the [private plugin installation procedure](../skills/company-profile-analyzer/references/account-installation.md) using Plugin Creator. The tool's ZIP export alone does **not** publish the plugin.
6. If you are a workspace admin, use the plugin's **Publish** action in ChatGPT's Plugins directory when your account exposes it. Confirm the published plugin appears to the intended users, then test a harmless fictional report request.

For current platform behavior and permissions, consult OpenAI's official guides:

- [Package a plugin and publish it to a workspace](https://developers.openai.com/plugins/build/plugins)
- [Workspace plugin controls](https://learn.chatgpt.com/docs/enterprise/apps-and-connectors)
- [GitHub marketplace import and sync](https://learn.chatgpt.com/docs/enterprise/plugin-management)

**ChatGPT Business note:** plugin availability is workspace-wide; do not assume Enterprise-style per-role controls are present. Installing a plugin does not automatically grant its connected apps or external data access.

## Optional: maintain workspace plugins from GitHub

Administrators may import a properly configured GitHub plugin marketplace via **Admin → Plugins → Add → Import marketplace**, including from private GitHub repositories. Future syncs can update packages, subject to workspace policies. This is **an alternative deployment mechanism**, not a required step to use Document Studio.

Only import a repository after reviewing its contents. Prefer an approved release/tag or a protected branch for corporate use; automatic sync from an unreviewed development branch is a supply-chain risk. See the official [plugin-management documentation](https://learn.chatgpt.com/docs/enterprise/plugin-management).

## Before enabling an organization-wide rollout

- [ ] Confirm that every input document is authorized for analysis and every *derived rule or excerpt* is authorized for the intended distribution scope.
- [ ] Verify that the Company Pack was reviewed and approved by an accountable human.
- [ ] Check the ZIP and manifest for source data, secrets, licensed fonts, hidden notes, and unwanted dependencies.
- [ ] Validate installation and a **new** report request in a pilot workspace/account.
- [ ] Inspect actual generated pages, Japanese/Korean typography where relevant, and required QA artifacts.
- [ ] Record the plugin version, reviewers, deployment owner, and rollback procedure.

## Roadmap, not current product behavior

- A separately authorized **internal-only export mode** that can enforce organizational scope without weakening the existing public-export guard.
- A guided source-upload → review → package interface for nontechnical admins.
- Verified end-to-end install, HTML render, and PowerPoint output tests on supported hosts.
- Optional workspace sync configuration generated alongside a company plugin.

Security concerns: see [SECURITY.md](../SECURITY.md). Feature ideas and reproducible bugs are welcome through GitHub Issues.
