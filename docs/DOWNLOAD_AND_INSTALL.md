# Download and install Document Studio (v0.1.0-alpha.6)

> **Experimental alpha.** These archives are plugin packages, not a one-click ChatGPT installation or a guarantee of identical output across AI model versions. No private employer/customer documents or licensed font files are included.

## Choose one download

| Package | Intended for | Download |
|---|---|---|
| **Starter plugin** | Anyone who wants the 8 core document skills and optional Korean/Japanese modules | [Download Starter ZIP](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/document-studio-starter-v0.1.0-alpha.6.zip) |
| **Fictional retail demo** | Workspace admins and evaluators who want a ready-approved *fictional* Company Pack | [Download Demo ZIP](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/demo-retail-documents-v0.1.0-alpha.6.zip) |
| **Full source** | Developers who want to inspect or modify the analyzer and packaging tools | [Browse source](https://github.com/wlehd00000-cell/document-studio) |

These are **different from GitHub's Code → Download ZIP**, which downloads the entire source repository.

## In three steps

**1 — Download and verify.** Choose one archive from the [pre-release page](https://github.com/wlehd00000-cell/document-studio/releases/tag/v0.1.0-alpha.6), download `SHA256SUMS.txt`, and compare the archive's SHA-256. The archive contains a single plugin root with a `plugin.json` and `skills/*/SKILL.md`. Inspect the contents before installation.

Windows PowerShell: `Get-FileHash .\document-studio-starter-v0.1.0-alpha.6.zip -Algorithm SHA256`

macOS/Linux: `shasum -a 256 document-studio-starter-v0.1.0-alpha.6.zip`

**2 — Register the plugin.** In an eligible ChatGPT account where **Plugin Creator** is available, upload the ZIP to a conversation using Plugin Creator and explicitly request creation of a **private** plugin from that ZIP. Confirm the returned plugin ID, scope and installed skill list. **Exporting/downloading a ZIP does not install anything.** If the account lacks Plugin Creator or permission to create plugins, follow the available account/workspace plugin setup process or use the source-only skill installation instead. Do not assume that every ChatGPT subscription supports ZIP installation.

**3 — Test with harmless content.** In a new chat, select the installed plugin and try:

> Create a two-page proposal for a *fictional* employee onboarding pilot. Use the approved writing and layout conventions where available. Report anything that was not visually or factually verified.

For the **fictional demo**, ask for the demo-retail Company's approved conventions, not a real employer's brand. Verify output, fonts, charts, and content manually. ChatGPT Business managers can publish the installed company-specific plugin to their workspace **only if the required administrative controls are available**; see the [admin guide](WORKSPACE_ADMIN_GUIDE.md).

## If you prefer local source installation

Clone the repo, run `python scripts/install_local.py --verify-only`, then inspect and run `python scripts/install_local.py --language-skills ko,ja`. This is a *local agent skills* installation, not a ChatGPT account plugin registration.

## Important scope and security boundaries

- The Starter ZIP bundles the generic engine and language modules, **not a company-trained model or an approved employer profile**.
- The retail example is independently fictional; it is **not evidence of fidelity to a real company's style**.
- Private/restricted company-source packs are **rejected by the present public exporter**. Do not relabel confidential material as public. An organization-scoped, explicitly authorized private export path remains future work.
- Output depends on the model and the local rendering environment. **Company Pack is a consistent *standard*, not a promise of identical outputs across models or upgrades.** Browser geometry and editable PowerPoint output require further verification.
- The pre-release is not a security-audited enterprise deployment. Do not upload confidential company files to public issues or unapproved services.

Found a problem? [Open an issue](https://github.com/wlehd00000-cell/document-studio/issues/new/choose) with a fictional/reproducible example.
