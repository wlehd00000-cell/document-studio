# First-user launch: alpha.6

Date: 2026-10-31. Primary goal: **organic GitHub stars**. Start from the inspected baseline of one star; the first milestone is 10, then 25. These are goals, not forecasts or promised outcomes. Five independently confirmed first runs and two repeat uses are supporting evidence that the traffic finds real value.

## Diagnosis and decision

The repository was created on October 29; alpha.6 was published on October 30. At inspection on October 31, each alpha.6 ZIP had two downloads. There is no verified installation telemetry. This is too little evidence to conclude that demand is absent. GitHub About description and topics were empty at inspection; changing them still requires a repository-settings-capable interface.

The current front door mixed enterprise governance, code-level packaging and document creation. The new entry point is one fictional proposal, then company customization. Initial audience: Korean/Japanese business-document creators who already use an eligible ChatGPT plugin environment, plus local Codex users. People without a compatible environment cannot complete installation today; record that as product friction rather than blaming the user.

**Positioning:** reusable document workflow and approved conventions. Do not call it a newly trained model, promise identical documents across models, or advertise a private-company deployment path the exporter blocks.

## Live entry points

- [First-run guide](TRY_FIRST.md): account eligibility, local installation, complete English/Korean/Japanese task briefs.
- [Public first-user thread](https://github.com/wlehd00000-cell/document-studio/issues/4): installation and output feedback.
- [Structured feedback](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md).
- [Pinned evaluation release](https://github.com/wlehd00000-cell/document-studio/releases/tag/v0.1.0-alpha.6).

## Channel order and publication status

| Priority | Channel | What belongs there | Status |
|---|---|---|---|
| 1 | Existing Korean Threads audience | Personal problem, modest scope, one fictional task, guide link | Copy below prepared; not posted from this session |
| 1 | GeekNews Show | Maker disclosure, runnable project, local setup and limitations | Copy below prepared; not posted from this session |
| 2 | Qiita | Reproducible technical explanation of local skills and verification | Article below prepared; not posted from this session |
| Later | Show HN | Runnable toolkit after independent first-run reports | Deferred; avoid sending visitors to an account-gated dead end |
| Not a launch channel | Unrelated GitHub issues/unsolicited bulk messages | No relevance or established audience | Do not use |

Only GitHub is an authenticated publishing channel available for this work. No claim is made that external community posts have been published. Publication requires an authenticated account on the relevant service. Do not create accounts or impersonate users to fill the gap.

Official rules checked on October 31:

- [GeekNews guidelines](https://news.hada.io/guidelines): self-made tools belong in Show; avoid repeated distribution and solicitation of votes. New accounts can face a posting wait.
- [Qiita guidelines](https://help.qiita.com/ja/articles/qiita-community-guideline): useful technical knowledge, rather than a sales-only article.
- [Show HN guidelines](https://news.ycombinator.com/showhn.html): readers must be able to try the work; avoid a landing-page-only launch and requests for upvotes.

Recheck rules at publication time. No advertising spend, paid promotions or promised support response times are authorized by this plan.

## Ready-to-post: GeekNews Show

**Title:** Document Studio — AI 보고서 작성 절차와 회사별 문서 규칙을 재사용하는 오픈소스

**URL:** https://github.com/wlehd00000-cell/document-studio

직접 만든 문서 제작 스킬·플러그인을 MIT 라이선스로 공개했습니다.

AI로 업무 문서를 만들다 보면 매번 독자, 문체, 구성, 검수 기준을 다시 설명하게 됩니다. 이 과정을 조사 → 구조 설계 → 작성 → 디자인 → 검수라는 재사용 가능한 절차로 나누고, 회사별로 승인한 규칙은 별도 Company Pack으로 관리하도록 만들었습니다.

현재는 실험용 알파입니다. 로컬 Codex용 스킬 설치와 ChatGPT용 플러그인 ZIP을 제공하며, 한국어·일본어 비즈니스 문장 교정 모듈을 선택할 수 있습니다. ChatGPT 설치는 Plugin Creator와 생성 권한이 있는 계정에서만 가능합니다. 비공개 사내 자료 기반 팩 배포나 클릭 한 번으로 완성되는 PPT 서비스는 아직 지원하지 않습니다.

첫 체험은 회사 자료 없이 가상 온보딩 제안서 2페이지를 만드는 방식입니다. 설치 명령과 그대로 붙여 넣을 요청문을 정리했습니다.
https://github.com/wlehd00000-cell/document-studio/blob/main/docs/TRY_FIRST.md

직접 학습한 모델이 아니라 기존 AI 환경에서 쓰는 작업 절차입니다. 실제로 설치가 되는지, 결과물에서 무엇을 다시 손봐야 하는지에 대한 피드백이 특히 필요합니다.

## Ready-to-post: Threads (three connected posts)

### 1/3

AI로 보고서를 만들 때마다 같은 설명을 반복했습니다.

누가 읽는지, 어떤 문체인지, 어떻게 구성할지, 무엇을 확인해야 하는지.

이걸 매번 프롬프트로 다시 쓰는 대신, 재사용할 수 있는 작업 절차로 묶어봤습니다. Document Studio라는 이름으로 오픈소스로 공개했습니다.

### 2/3

핵심은 조사 → 구조 설계 → 작성 → 디자인 → 검수의 순서를 나눠두는 것입니다. 회사별로 승인한 문서 규칙을 별도 팩으로 관리하는 구조도 넣었습니다.

아직 알파라 설치 가능한 환경이 제한돼 있습니다. ChatGPT는 Plugin Creator가 있는 계정, 로컬에서는 Codex용 스킬로 시작할 수 있습니다. 사내 비공개 자료로 만든 팩의 배포는 아직 지원하지 않습니다.

### 3/3

처음부터 회사 자료를 넣을 필요는 없습니다. 가상 온보딩 제안서 2페이지를 만드는 요청문으로 시작할 수 있게 했습니다.

보고서나 제안서를 반복해서 만드는 분이라면 한번 써보고, 설치에서 어디에 막혔는지 또는 결과물에서 뭘 다시 고쳤는지 알려주세요. 그 부분부터 개선하려고 합니다.

방향이 마음에 들면 GitHub Star로 저장해두셔도 좋습니다.

설치·첫 요청문:
https://github.com/wlehd00000-cell/document-studio/blob/main/docs/TRY_FIRST.md

## Ready-to-post: Qiita technical article

**Title:** Codexの文書作成スキルを再利用する：Document Studioのローカル導入と初回確認

**Suggested tags:** Python, AI, Codex, ドキュメント

### 何を作ったか

報告書をAIに依頼するたびに、読者、文章の調子、構成、確認基準を説明し直すことがありました。そこで、調査・構成・執筆・デザイン・確認をSKILL.md形式の手順として分け、再利用できるツールキットを作りました。Document StudioはMITライセンスの実験的なalphaで、独自に学習したAIモデルではありません。

この記事では、アカウントごとの権限に左右されるChatGPTプラグイン登録ではなく、ローカルのスキル配置を確認します。

### インストール前の条件

Git、Python 3.12、およびSKILL.mdを検出できるローカルのエージェント環境を使用します。インストーラーはスキルをコピーしますが、AIモデルやPowerPoint変換用の依存関係はインストールしません。実行前に `scripts/install_local.py` を確認してください。

```bash
git clone --branch v0.1.0-alpha.6 --depth 1 https://github.com/wlehd00000-cell/document-studio.git
cd document-studio
python scripts/install_local.py --verify-only
python scripts/install_local.py --language-skills ja
```

`--verify-only` はマニフェストとファイルのハッシュを照合するもので、インストールは行いません。次のコマンドで8つのコアスキルと日本語モジュールを配置します。既存の異なるファイルは通常の実行では上書きしません。

配置先は設定済みの `CODEX_HOME/skills`、または既存の対応ディレクトリを考慮して決まります。新規の既定値は `~/.agents/skills` です。利用環境に合わせて `--skills-dir` で指定できます。

### コピー完了と利用可能は別

JSONの `installed` / `already_installed` と配置先を確認したあと、新しいエージェントセッションで `report-html-pptx` が認識されるか確認します。ファイルのコピーが成功しても、エージェントによる検出やHTML/PPTX出力まで保証するものではありません。

初回は[日本語の依頼例](https://github.com/wlehd00000-cell/document-studio/blob/main/docs/TRY_FIRST.md#日本語)を使い、架空企業のオンボーディング提案書を2ページのHTMLで作ります。実在企業の資料は不要です。

### 比較するときに見る点

同じモデル、同じ設定、同じ依頼内容で、スキルあり／なしを別セッションで試します。ページ数、意思決定の分かりやすさ、数値の整合性、文字のはみ出し、修正にかかった手間を記録します。本稿は品質向上率を測定したベンチマークではありません。

### 現在の制約

会社別のルールをCompany Packとして承認・管理する仕組みもありますが、非公開の社内資料を基にしたパックの配布は現行の公開エクスポーターではできません。最終成果物の作成と表示確認も別工程です。モデル間で同じ見た目や品質を保証するものではありません。

ソース：https://github.com/wlehd00000-cell/document-studio

導入で止まった場合は、環境、リリース、最後に完了した手順、エラーを[初回フィードバック](https://github.com/wlehd00000-cell/document-studio/issues/4)に記載してください。機密ファイルやアカウント情報は不要です。

## Directory submission attempts (2026-10-31)

| Directory | Published submission? | Observed result |
|---|---|---|
| alanhoff/awesome-agent-skills-open-agent-craft | No | The documented recommendation issue route returned HTTP 410: issues disabled. |
| anbeime/skill | No | Its submit-skill form was reviewed; issue creation returned HTTP 403: resource not accessible by integration. |

No external listing acceptance or external social publication is claimed. Large lists with minimum age/star requirements were not submitted to when this new repository did not meet the bar. The repository's star count remained **1** at the last check in this session.

## Follow-through after GitHub authorization

- Reworked Korean and Japanese overview pages around a first document task and a clear Star/bookmark link; linked both from the top of the English README.
- Added a narrowly triggered GitHub workflow to render the included fictional document as an inspectable example. Its first attempt exposed a renderer/Ubuntu version incompatibility; the runner was pinned to Ubuntu 24.04. The next run exposed deliberately clipped decorative artwork being counted as content overflow. Text geometry checks now distinguish the decoration from actual text. The final run passed, published the PNG and source-hash provenance, and the rendered image was inspected before being linked in all three overview pages.
- AgentSkillsDir: completed the public resource form (public repository URL, name, description, Plugins category; no contact details). The response was **“Resource submissions are currently closed.”** No submission acceptance is claimed.
- OpenAgentSkill: repository scan and a direct representative SKILL.md URL both returned **“Validation failed. Please try again.”** No submission acceptance is claimed.
- agentskill.sh: the public import returned **“Too many submissions. Please try again in an hour.”** No retry loop or rate-limit bypass was attempted.
- GitHub browser sign-in: user approved GitHub access and selected Google in the secure method picker. Automatic review then blocked access to the Google authentication origin because that origin requires explicit approval. Repository settings and authenticated external GitHub submissions remain incomplete.

## Measurement and next decisions

Use voluntary issue reports only; no hidden tracking was added.

| Stage | Evidence | Current state |
|---|---|---|
| Discovery | Optional referral answer in first-run issue | Not measured |
| Download | Release asset counter | Two per ZIP when inspected; not unique people |
| Installation | Saved plugin confirmation or local installer result reported by an external user | No independently confirmed report in this session |
| Activation | External user reports an inspected first HTML artifact | No independently confirmed report in this session |
| Retention | Same user reports a second useful document | Not measured |

Decision rules: if most people stop at account eligibility, prioritize a less restricted distribution route. If they install but never generate, fix first-task discovery. If they generate but do not reuse, collect concrete revision problems before adding features. Do not buy traffic to a route most visitors cannot complete.

Suggested GitHub About text (not applied automatically):

> Reusable AI document workflows and reviewed company conventions. ChatGPT plugin + local Codex skills; Korean/Japanese modules. MIT, experimental alpha.

Suggested topics: `document-automation`, `chatgpt`, `codex`, `agent-skills`, `powerpoint`, `korean`, `japanese`, `python`.
