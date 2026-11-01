# Document Studio

**A reusable workflow for your next report, proposal, or presentation.**

Document Studio gives AI agents a shared process for research, structure, writing, design, and review. Keep the working conventions you have already explained, then adapt each new document to its reader and purpose.

[**Get started**](docs/TRY_FIRST.md) · [**Explore the workflow**](docs/SHOWCASE.md) · [한국어](docs/QUICKSTART_ko.md) · [日本語](docs/QUICKSTART_ja.md)

Open source · MIT · Experimental alpha.6 · For Codex and eligible ChatGPT plugin accounts

## Give the next document a better starting point

A useful document needs a clear argument, appropriate language, readable design, and checks that match its purpose. Those decisions are easy to lose between AI conversations.

Document Studio makes them reusable in two ways:

- **Agent skills** describe how to plan, research, write, design, and review a document. Each stage lives in a readable `SKILL.md` file that you can inspect and change.
- **Company Packs** hold reviewed writing and design conventions, such as terminology, colors, and layout relationships. Use the generic workflow first; add a pack when company-specific conventions matter.

The pack supplies conventions. Your new brief supplies the audience, decision, evidence, and content.

## Start with one small document

### Codex

With Node.js 22.20+ and Git, run this from **your own project folder**:

```bash
npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y
```

Start a fresh Codex session and check that `report-html-pptx` is available. This installs the ten agent skills. Company Pack packaging tools use the [full source setup](docs/TRY_FIRST.md#local-codex).

### ChatGPT

If your account supports Plugin Creator and saving plugins, [download and register the Starter ZIP](docs/TRY_FIRST.md#chatgpt). Open the saved plugin to begin.

### Try this brief

> Use Document Studio to create a two-page HTML proposal for a fictional employee onboarding pilot. The reader is an operations manager deciding whether to approve a four-week pilot for 12 people with a $2,400 budget. Include the recommendation, schedule, budget, three success measures, and risks. Label all figures as assumptions. Provide the HTML and say which factual and visual checks you completed.

Read the result for a clear decision, consistent figures, and readable layout. [Full setup and first-task guidance →](docs/TRY_FIRST.md)

## What is inside

| Part | What it contributes |
|---|---|
| Planning and evidence | Document architecture, research, and source notes |
| Writing and design | Business copy, visual assets, and HTML composition |
| Korean and Japanese | Two optional language editing modules |
| PowerPoint export | HTML-to-PPTX conversion with separate rendering and editability checks |
| Company conventions | Reference analysis, human review, and reusable Company Packs |

There are **eight core skills and two optional language skills**. See the [skill guide and technical workflows](docs/TECHNICAL_GUIDE.md).

## Add company conventions when you need them

Start with the fictional [retail](company-packs/demo-retail/pack.json) or [manufacturing](company-packs/demo-manufacturing/pack.json) pack to inspect the format. For your own references, the workflow is:

**Authorized PDF/PPTX references → extracted evidence → human review → approved Company Pack → new document.**

A reviewer decides which proposed rules to keep. An approved pack eligible for public distribution can then be exported with the selected skills as a plugin ZIP. [Reference-to-plugin walkthrough →](docs/DEMO_FLOW.md)

## Current scope

Document Studio is an **experimental toolkit**. Your AI agent and rendering environment perform the authoring; output quality and compatibility need to be checked for the actual task.

- **Available:** PDF/PPTX evidence extraction, Company Pack review, and plugin ZIP export for fictional or appropriately authorized public-distribution packs.
- **Requires separate checks:** rendered HTML, fonts, editable PPTX, and installation in the receiving account or workspace.
- **Not supported:** exporting packs derived from private/restricted sources, or automatically publishing plugins to a workspace.

The included examples demonstrate the workflow and composition choices. Real-company studies have a narrower measured scope; see the [evaluation and current limitations](docs/TECHNICAL_GUIDE.md#evaluation-and-limitations).

## Keep exploring

| I want to… | Read |
|---|---|
| Inspect the workflow before installing | [Workflow overview](docs/SHOWCASE.md) |
| Install and make a first document | [First-use guide](docs/TRY_FIRST.md) |
| Analyze references or export a Company Pack | [Technical guide](docs/TECHNICAL_GUIDE.md) |
| Evaluate the workflow for a team | [Workspace administrator guide](docs/WORKSPACE_ADMIN_GUIDE.md) |
| Find all documentation | [Documentation index](docs/README.md) |

Tried it? [Share your first-run experience](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md), or read [CONTRIBUTING.md](CONTRIBUTING.md) to help improve it. Release history is in the [changelog](CHANGELOG.md).

Original contributions use the [MIT License](LICENSE); see [third-party notices](THIRD_PARTY_NOTICES.md). This is an independent personal project, unaffiliated with any employer or trademark owner.
