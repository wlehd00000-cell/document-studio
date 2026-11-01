# Release packages and installation

The current package release is **v0.1.0-alpha.6**. For the complete setup sequence and a first document request, use the [first-use guide](TRY_FIRST.md).

## Choose a package

| Package | Contents | Link |
|---|---|---|
| Starter plugin | Generic document workflow with Korean/Japanese modules | [Download ZIP](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/document-studio-starter-v0.1.0-alpha.6.zip) |
| Fictional retail demo | Selected skills and an approved fictional Company Pack | [Download ZIP](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/demo-retail-documents-v0.1.0-alpha.6.zip) |
| Full source | Skills, analyzer, packaging tools, tests, and documentation | [Browse repository](https://github.com/wlehd00000-cell/document-studio) |

GitHub's **Code → Download ZIP** retrieves the source repository. Use one of the packaged releases above for the ChatGPT ZIP route.

## Verify the download

Download `SHA256SUMS.txt` from the [release page](https://github.com/wlehd00000-cell/document-studio/releases/tag/v0.1.0-alpha.6) and compare your archive's SHA-256.

Windows PowerShell:

```powershell
Get-FileHash .\document-studio-starter-v0.1.0-alpha.6.zip -Algorithm SHA256
```

macOS/Linux:

```bash
shasum -a 256 document-studio-starter-v0.1.0-alpha.6.zip
```

Inspect the archive. It should contain a plugin root with `plugin.json` and `skills/*/SKILL.md`. The Starter supplies the generic workflow; the retail demo also supplies the fictional profile. Original company files and font binaries are excluded.

## Register and try it

Follow the [ChatGPT registration steps](TRY_FIRST.md#chatgpt), confirm the saved plugin URL and ID, then use the [fictional first task](TRY_FIRST.md#first-task). Installation requires supported account permissions.

For local skills, use the [Codex route](TRY_FIRST.md#fast-agent-skill-install). For company-specific export, use the [technical guide](TECHNICAL_GUIDE.md). Current feature boundaries are summarized in the [project overview](../README.md#current-scope).
