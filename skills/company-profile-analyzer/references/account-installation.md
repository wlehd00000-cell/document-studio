# Save a company-specific Document Studio plugin to the current account

Use this route **only after** a human has approved the Company Pack and the user explicitly requests saving/installing it as a ChatGPT plugin. A local ZIP is not an installed plugin.

1. Confirm the intended Company Pack, exact company name, selected `ko`/`ja` optional skills and visibility. The Plugin Creator tool saves a **private** plugin in the authenticated user's **active workspace if one exists**, otherwise in the personal account. Do not claim to choose a different account or scope through the ZIP.
2. Run the standard Company Pack validator with `--require-approved`. Preserve source-rights gates. A public-only archive **cannot** package private/unverified rights, company originals, screenshots or fonts; stop if `export_company_plugin.py` rejects it. Do not alter source records to bypass rights.
3. Create the installable archive in a user-selected local output path, outside the Company Pack itself:

   ```bash
   python scripts/export_company_plugin.py \
      --company-pack /path/to/approved-company-pack \
      --language-skills ko,ja \
      --output /path/to/approved-company-documents.zip
   ```

4. Check the ZIP has one plugin root, a portable `plugin.json`, selected `skills/*/SKILL.md`, no source PDF/PPTX, fonts or secrets, and the built-in package manifest passes verification. For a fresh generic Document Studio instead of a company pack, use `python scripts/package_account_plugin.py --language-skills ko,ja --output /path/to/document-studio.zip`.
5. The **Plugin Creator plugin must already be installed and callable on this authenticated account**. If absent, help the user install it through the ChatGPT plugin directory or ask them to select it. Do not invent an installation API, silently open a browser or claim a ZIP was saved. The Plugin Creator tool is external to Document Studio; scripts never store ChatGPT credentials.
6. If creating a new plugin, call Plugin Creator's `create_plugin` **once** with `{ "archive": "/absolute/path/to/archive.zip" }`. Check its actual result, especially `plugin_id`, `plugin_url`, `scope`, `release_id`, and `status`. Return the plugin URL to the user only if the call succeeds. If the backend reports workspace scope, report workspace scope; do not present it as a personal plugin.
7. For a later revision, retrieve the current release ID and eligible plugin source via Plugin Creator first. Use `update_plugin` with the verified backend `plugin_id`, `expected_release_id`, and update archive; **never create a duplicate** and never change visibility or share permissions by inference.
8. Verify the new plugin appears under Created by You, inspect expected skills, and perform a harmless onboarding request if it can be invoked in the current session. Installation may require a new conversation before its tools/skills become discoverable. Do not report operational verification unless actually performed.

**Account installation is optional**: users may keep a private approved Company Pack and HTML/PPTX workflow without giving any data to Plugin Creator. The archive has only the rights-cleared material selected for distribution.
