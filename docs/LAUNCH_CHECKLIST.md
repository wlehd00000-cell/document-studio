# Document Studio: responsible GitHub launch kit

This project is **v0.1.0-alpha.5**, not a stable v1 release. Promote the reproducible fictional demo and the human-reviewed architecture, not enterprise capabilities that have not shipped.

## Repository presentation

Suggested GitHub About description (fits the short-description field):

> Open-source, review-first toolkit to turn document references into approved company-aware AI document plugins. Built for ChatGPT teams.

Suggested GitHub Topics:

`document-automation` · `ai-agents` · `chatgpt` · `business-workflow` · `powerpoint` · `python` · `prompt-engineering` · `open-source`

Use the included `docs/assets/social-preview.png` as the repository's **Social preview** in **Settings → General → Social preview**. The source graphic is `docs/assets/workflow-hero.svg`. This is an illustrated sequence, not a screenshot or a benchmark result.

## The actual 60-second demonstration

Show one uninterrupted narrative with a real screen capture: a few **fictional reference documents** → evidence and proposed rules → human approval → generated ZIP/manifest → installed demo plugin → a **new**, unrelated report. Use the [scene-by-scene checklist](DEMO_FLOW.md).

Do not release an edited montage as an automated end-to-end proof unless each demonstrated operation actually ran. Clearly label any storytelling or simulated transition; show the reviewer actions and the QA state. A real browser/PPTX verification capture is still pending.

## Share copy — English

> **Your company's document style shouldn't live in one employee's prompt history.**
>
> I'm open-sourcing **Document Studio**, a review-first toolkit that analyzes authorized PDF/PPTX references, proposes a Company Pack and layout rules, and exports a customized document plugin from an approved, publicly distributable example.
>
> The idea: bring references → approve what the system learned → reuse those rules when creating something new.
>
> It's an early alpha, **not** a one-click enterprise installer. Private-source internal distribution and fully verified output are still roadmap items. There is a reproducible fictional-company demo, code, tests, and a manager-oriented deployment guide.
>
> Code + demo: https://github.com/wlehd00000-cell/document-studio
>
> I would love feedback from teams who struggle to keep AI-generated reports consistent.

## Share copy — Japanese

> **AIで作った資料が、毎回「自社らしくない」と感じたことはありませんか？**
>
> 企業の PDF・PowerPoint を参考に、文体やレイアウトの根拠を抽出し、人が確認・承認したルールを再利用するオープンソース **Document Studio** を公開しました。
>
> 「参考資料 → 分析 → 承認 → 専用プラグイン → 新しい資料」という流れを目指しています。現行版は実験的な alpha で、架空企業の承認済みデモを使った ZIP 出力を試せます。社内限定資料の配布やワンクリック導入はまだ未対応です。
>
> GitHub: https://github.com/wlehd00000-cell/document-studio
>
> 資料作成や社内 DX に関わる方からのフィードバックを歓迎します。

## First-week launch checklist

- [ ] Confirm release commit and manifest checks passed.
- [ ] Upload the 1280×640 social preview in GitHub settings (adding the PNG to git alone does **not** set it as the social preview).
- [ ] Add repository description and topics; enable Discussions only if someone will moderate them.
- [ ] Pin a reviewed pre-release tag; keep **alpha** in the version and avoid describing it as v1.
- [ ] Record the real fictional-company demo and embed a small GIF or video link near the README top **after** verifying it.
- [ ] Share one clear use case in developer and Japanese DX communities. Answer technical questions and acknowledge the private-export limitation.
- [ ] Invite one or two independent contributors to run the quick start and report onboarding friction; improve installation before wider promotion.

## What to measure

Instead of celebrating stars alone, track: first-run ZIP export success, setup time, independently reported issues, repeat users, and patches from outside contributors. Never invent adoption numbers, endorsements, or customer logos.
