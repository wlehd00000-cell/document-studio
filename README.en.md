# Document Studio

[日本語](README.md) · [한국어](README.ko.md) · [English](README.en.md)

**Package approved company conventions into a reusable document plugin.**

An open-source experiment combining reviewed company rules with document-production skills. It connects employee requests with structure, writing, HTML design, and editable PowerPoint output.

[Open the introduction and examples](https://document-studio-public-experiment.wlehd00000.chatgpt.site/) · [Administrator guide](docs/WORKSPACE_ADMIN_GUIDE.md) · [Documentation map](docs/README.md)

Experimental **alpha.6**. The current public exporter accepts fictional packs and reviewed public sources authorized for distribution. Internal distribution based on private company sources is not supported.

## Choose your next step

| Your goal | Start here |
|---|---|
| See the document examples | [Static showcase, Japanese first with Korean switching](docs/SHOWCASE.md) |
| Evaluate it for a team | [Administrator guide](docs/WORKSPACE_ADMIN_GUIDE.md), or the [Japanese evaluation walkthrough](docs/MANAGER_GUIDE_ja.md) |
| Make your first document | [First-use guide](docs/TRY_FIRST.md) |
| Inspect the implementation and commands | [Technical guide](docs/TECHNICAL_GUIDE.md) |

## Managers prepare conventions; employees request documents

A **Company Pack** records reviewed terminology, writing, design, source rules, and their evidence. The goal is to keep necessary organizational conventions while adapting structure and expression to the reader. A specified fixed layout can also be retained.

| Role | Flow |
|---|---|
| Administrator | Select authorized references → review and approve rules → package the Pack and skills → install and verify in a supported environment |
| After an employee request | Confirm purpose, audience, language, format, and Pack → structure and necessary research → writing and language review → HTML design and QA → requested PPTX and final QA |

Packages include all eight core skills and selected Japanese/Korean language modules. The host AI applies role instructions and scripts; employees need not name each internal skill. Research and visual production are conditional, and manuscript/HTML-only requests can stop earlier. [Illustrated internal flow](https://document-studio-public-experiment.wlehd00000.chatgpt.site/#plugin-flow) · [Skill inventory and contracts](docs/TECHNICAL_GUIDE.md#whats-included-8-core-skills--2-optional-languages)

## Inspect three design choices

| What to inspect | Example |
|---|---|
| Preserve predefined design rules | [Same two pages in monochrome A4, aligned A4, and landscape layouts](https://document-studio-public-experiment.wlehd00000.chatgpt.site/compare) |
| Adapt information to the reader | [Four-page proposal, decision summary, and operations guide](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example?view=all&size=large) |
| Explore a different expression | [One-page creative reinterpretation of the same fictional pilot](https://document-studio-public-experiment.wlehd00000.chatgpt.site/creative) |

[![Japanese preview comparing the same copy under monochrome A4 and aligned A4 rules](docs/assets/showcase/comparison-ja.jpg)](https://document-studio-public-experiment.wlehd00000.chatgpt.site/compare)

The examples are fictional, use an assumed KRW 2.4 million budget, and display pre-authored static HTML. The Site does not run an AI model. Measurements cover these HTML examples, not new generation, business outcomes, print, or PPTX acceptance. [Source and review scope](showcase/README.md)

[Optional editorial consulting](https://document-studio-public-experiment.wlehd00000.chatgpt.site/consulting) begins with research, countercases, and alternatives. It requires explicit selection and is separate from creativity settings.

## From reviewed HTML to editable PowerPoint

The export workflow measures browser geometry and typography, then reconstructs supported text, numbers, and shapes as editable PowerPoint elements. This supports later changes to meeting figures, ownership, or wording.

Photos and complex decoration may remain images. Actual fonts, rendering, and editability must be checked; arbitrary HTML is not guaranteed to reproduce perfectly. The public examples have not been validated as exported PPTX files. [Illustrated output flow](https://document-studio-public-experiment.wlehd00000.chatgpt.site/#pptx-output) · [Exporter contract](skills/html-to-pptx/SKILL.md)

## Try one small task

For individual use, follow the [first-use guide](docs/TRY_FIRST.md). For a company-specific package, use the [fictional administrator evaluation](docs/WORKSPACE_ADMIN_GUIDE.md#evaluate-the-working-export-using-fictional-materials).

| Check | Current status |
|---|---|
| Export approved fictional or distribution-authorized public packs | Implemented evaluation route |
| Installation, Pack selection, a fresh request, HTML/PPTX quality | Verify separately on the target host |
| Private-source internal distribution and one-click corporate setup | Not supported |

The [static HTML viewing ZIP](https://document-studio-public-experiment.wlehd00000.chatgpt.site/downloads/document-studio-demo.zip), [plugin ZIPs](docs/DOWNLOAD_AND_INSTALL.md), and GitHub source ZIP serve different purposes. Downloading an archive does not install a plugin.

This is a personal experiment in applying AI to organizational work. Star the repository to save it, or share what worked and what required revision through [first-run feedback](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md). Japanese, Korean, and English are welcome.

[FAQ — Japanese](docs/FAQ_ja.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Security](SECURITY.md)

Original work is [MIT](LICENSE); bundled fonts and other third-party files retain their [notices](THIRD_PARTY_NOTICES.md). No employer or trademark-owner adoption or endorsement is implied.

## Technical reference

The former detailed README sections are preserved in the [technical guide](docs/TECHNICAL_GUIDE.md). The following legacy fragment targets lead here so older links remain useful.

<a id="start-with-a-small-task"></a>
<a id="codex-install-the-agent-skills"></a>
<a id="chatgpt-use-the-starter-zip"></a>
<a id="first-prompt"></a>
<a id="what-makes-it-useful"></a>
<a id="quick-start--export-a-demo-plugin"></a>
<a id="how-it-works"></a>
<a id="who-is-it-for"></a>
<a id="whats-included-8-core-skills--2-optional-languages"></a>
<a id="what-works-today--and-what-does-not"></a>
<a id="curated-company-packs-phase-a"></a>
<a id="independent-public-source-evaluation-2026-10-29"></a>
<a id="analyze-and-distribute-an-organization-profile-experimental"></a>
<a id="default-visual-grammar-architecture-experimental-implementation"></a>
<a id="approved-layout-grammar--authored-html--browser-qa-experimental-alpha6"></a>
<a id="save-a-private-plugin-in-your-chatgpt-account"></a>
<a id="public-demo-safety"></a>
<a id="get-involved"></a>
<a id="license"></a>
<a id="attribution"></a>
<a id="fixed-rule-document-comparison"></a>
<a id="creative-example-and-optional-editorial-consulting"></a>
<a id="from-reviewed-html-to-editable-powerpoint"></a>
