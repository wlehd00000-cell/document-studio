# Security and data-handling policy

Document Studio processes document references that can contain sensitive information. **Never upload confidential company files, credentials, personal data, private source registries, or extracted text to a public GitHub Issue, pull request, or this repository.**

## Report a vulnerability

Please use GitHub's **private vulnerability reporting** for this repository if that option is enabled under **Security → Report a vulnerability**. If it is unavailable, open an Issue requesting a private reporting channel **without posting exploit details or secrets**.

Include the affected version, a minimal non-sensitive reproduction, expected and observed behavior, and the impact. Please allow maintainers time to investigate before public disclosure; no response-time guarantee is currently offered.

## Security boundaries in alpha.5

- Source registration, analysis, and draft pack assembly can operate on local authorized files. Keep private source material and registries outside the public repository.
- The **public** Company Pack exporter is deliberately restricted. Private or otherwise restricted source-derived packs are blocked from distribution; do not spoof their visibility, rights, or review records.
- A plugin ZIP should be reviewed for source excerpts, embedded media, font licenses, hidden notes, credentials, and unexpected dependencies before installation.
- Plugin installation, workspace publication, and service permissions are separate actions controlled by the relevant account administrator.
- Generated documents must undergo factual review, rights review, and applicable visual/browser QA before production use.

The project has **not** undergone an independent security audit. It is an experimental open-source toolkit, not a security-certified enterprise data-processing service. For deployment scope and limitations, see the [workspace admin guide](docs/WORKSPACE_ADMIN_GUIDE.md).
