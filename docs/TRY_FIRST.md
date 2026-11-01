# Make your first document

Start with the fictional two-page proposal below. You can use the generic workflow before configuring a Company Pack.

[한국어](QUICKSTART_ko.md) · [日本語](QUICKSTART_ja.md) · [All documentation](README.md)

## Choose your route

| Your environment | Start here |
|---|---|
| Codex with Node.js and Git | [Install the agent skills](#fast-agent-skill-install) |
| ChatGPT with Plugin Creator and plugin creation permission | [Register the Starter ZIP](#chatgpt) |
| Local source analysis or Company Pack packaging | [Set up the full source](#local-codex) |

## Fast agent-skill install

With Node.js 22.20+ and Git, run this from **your own project folder**, outside the Document Studio checkout:

```bash
npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y
```

The [skills CLI](https://github.com/vercel-labs/skills/blob/main/docs/commands.md) copies the ten skill folders to the project. This copy-install route was verified in an isolated Codex project on 2026-10-31. To inspect the available skills first, use:

```bash
npx --yes skills add wlehd00000-cell/document-studio --list
```

Start a fresh Codex session and confirm that `report-html-pptx` is available, then use the [first task](#first-task).

This route installs agent skills. Repository-level analyzer/export scripts require the full checkout below. Rendering and PowerPoint conversion need their own dependencies.

## ChatGPT

Your account must have Plugin Creator and permission to save plugins. If those controls are unavailable, use a compatible local agent route.

1. [Download the Starter ZIP for alpha.6](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/document-studio-starter-v0.1.0-alpha.6.zip). Follow the [download guide](DOWNLOAD_AND_INSTALL.md) to inspect the archive and verify its checksum.
2. Open a conversation with Plugin Creator, attach the ZIP, and request:

   > Create a private Document Studio plugin from the attached ZIP. Inspect the manifest and skills, then return the saved plugin URL, ID, and scope. If creation is unavailable, explain the blocker.

3. Open the saved plugin, start a new conversation with it selected, and use the first task below.

The returned plugin URL and ID confirm registration. Account support and workspace publication depend on the receiving environment; see the [administrator guide](WORKSPACE_ADMIN_GUIDE.md).

## Local Codex

For the repository-level tools, use Git and Python 3.12, the project's development version. Inspect the installer and its destination before installing:

```bash
git clone --branch v0.1.0-alpha.6 --depth 1 https://github.com/wlehd00000-cell/document-studio.git
cd document-studio
python scripts/install_local.py --verify-only
python scripts/install_local.py --language-skills ko,ja
```

Use `python3` if that is your Python command. The installer reports the selected skills directory and refuses to overwrite differing skills without an explicit replacement and backup. Choose `--language-skills none`, `ko`, `ja`, or `ko,ja` to select language modules.

Check for `installed` or `already_installed` in the installer output. Start a fresh agent session and confirm that `report-html-pptx` is available. File copying and runtime readiness are separate checks.

## First task

Use the installed plugin or local `report-html-pptx` skill:

> Use Document Studio to create a two-page HTML proposal in English for a fictional employee onboarding pilot. Audience: the operations manager. Decision: approve or decline a four-week pilot for 12 people. Fictional budget: $2,400. Page 1: recommendation, problem, and proposed approach. Page 2: schedule, budget, three success measures, and risks. Label numbers as assumptions. Use the generic workflow and fictional content. Provide the HTML and say which factual and visual checks you completed.

Review the actual artifact: can the manager find the decision, check the budget, and read both pages without clipped text? Compare the reported checks with what was actually performed.

To evaluate the workflow, try the same brief in a separate session using the same model and settings without the skills. Record the difference in structure and revision effort. No time-saving or quality-improvement rate has been established.

## Company demo

After the generic task works, try the [fictional retail demo ZIP](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/demo-retail-documents-v0.1.0-alpha.6.zip) through the account registration route above. Ask for the approved `demo-retail` conventions in a new fictional proposal.

For reference analysis and custom ZIP export, use the [technical guide](TECHNICAL_GUIDE.md) and [review walkthrough](DEMO_FLOW.md). The public exporter currently blocks packs derived from private/restricted sources.

## 한국어

[한국어 시작 안내와 예제 요청문](QUICKSTART_ko.md#첫-문서-요청)을 이용하세요.

## 日本語

[日本語の導入ガイドと依頼例](QUICKSTART_ja.md#最初の依頼)をご覧ください。

## Share what happened

[Send first-run feedback](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md) with your environment, the step that worked or stopped, and the artifact produced. Use fictional or public examples. Your AI account and optional rendering tools may have separate costs or requirements.
