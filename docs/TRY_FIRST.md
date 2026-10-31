# Try Document Studio: one fictional task, one working route

Document Studio is an open-source document-workflow toolkit, not an AI model. Start with a small generic task before company-profile analysis. No paid service is sold by this repository; your AI account, usage and optional rendering tools may have their own costs or requirements.

## Fast agent-skill install

**Already use Codex and have Node.js 22.20+ and Git?** This is the shortest route to inspect and try Document Studio's agent workflow skills. Run the following command **from your own project directory** (not inside the Document Studio source checkout):

```bash
npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y
```

The [open-source skills CLI](https://github.com/vercel-labs/skills/blob/main/docs/commands.md) copies the ten `SKILL.md` skill folders into the current project's agent skills directory. The skills were discovered and a ten-skill copy install was verified in an isolated Codex project on **2026-10-31**. Start a fresh Codex session, check that `report-html-pptx` is available, then try the [fictional first task](#first-task). You can first inspect the list without installing:

```bash
npx --yes skills add wlehd00000-cell/document-studio --list
```

**Scope matters:** this is a local agent-skills install, not a ChatGPT Plugin Creator registration, not a new AI model, and not a full copy of the repository-level Company Pack analyzer/export scripts. The full company-specific export demonstration needs the source checkout and Python instructions below. Visual HTML/PPTX generation and quality checks still depend on your AI agent and runtime. Review skill instructions before allowing agent actions; the installer itself does not certify output or security. Other supported agents can use the CLI with their own `-a` option; only the Codex route above was tested here.

## ChatGPT

**Check eligibility first:** can your account select Plugin Creator and create a plugin? If not, this ZIP route is unavailable on that account. Do not spend time downloading repeatedly; choose the local route below if you use a compatible local agent. A subscription name alone does not establish eligibility.

1. [Download the Starter ZIP for alpha.6](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/document-studio-starter-v0.1.0-alpha.6.zip). [Inspect/check the archive](DOWNLOAD_AND_INSTALL.md) before installation.
2. Select Plugin Creator, attach the ZIP, and send:

   > Create a private Document Studio plugin from the attached ZIP in my current account. Inspect the manifest and skills. Return the saved plugin URL/ID and its scope. If creation is unavailable, report the exact blocker; do not claim that downloading the ZIP installed it.

3. Open the returned plugin, start a new conversation with it selected, and use the first task below. **The returned saved plugin URL/ID is the registration evidence.** ZIP creation alone is not success.

For Business deployment, use the [administrator guide](WORKSPACE_ADMIN_GUIDE.md). Account registration has not been independently verified for every account type.

## Local Codex

Requires Git, Python 3.12 as used by this project, and a local agent environment that discovers SKILL.md skills. Read the installer before running it. Run each line from the same terminal:

```bash
git clone --branch v0.1.0-alpha.6 --depth 1 https://github.com/wlehd00000-cell/document-studio.git
cd document-studio
python scripts/install_local.py --verify-only
python scripts/install_local.py --language-skills ko,ja
```

Use `python3` if that is your Python command. The installer reports the chosen skills directory. It uses `CODEX_HOME/skills` if configured; otherwise it chooses an existing supported skill location or defaults to `~/.agents/skills`. You can supply `--skills-dir` to match your agent. It refuses differing existing skills unless explicitly updated with `--replace` and a backup. It does not install Python rendering dependencies or an AI model.

**Check success:** installer JSON says `installed` or `already_installed`, and lists the selected skills. Start a fresh agent session, confirm that `report-html-pptx` is discovered, and run the first task. File-copy verification is not proof that your agent has loaded the skills or can export PPTX.

## First task

Use this with the installed plugin or discovered local `report-html-pptx` skill:

> Use Document Studio to create a two-page HTML proposal in English for a fictional employee onboarding pilot. Audience: the operations manager. Decision: approve or decline a four-week pilot for 12 new starters. Fictional budget: $2,400. Page 1: recommendation, problem and proposed approach. Page 2: schedule, budget, three success measures and risks. Treat all numbers as fictional assumptions, not measured results. Use the generic workflow; no real company brand or source files. Provide the HTML artifact and state which factual and visual checks were actually completed. Ask only for information that is essential to proceed.

Check the actual artifact: two readable pages, clear decision, consistent figures, no invented evidence, no clipped text, and an honest QA status. Output quality depends on the agent and rendering tools. A claimed PASS without the relevant check is a defect worth reporting.

**Compare fairly:** run the same brief in a separate session without Document Studio using the same model/settings. Compare revision effort and document structure; record the observed result rather than assuming the toolkit is better.

## Company demo

Only after the generic task works, [download the fictional retail demo](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/demo-retail-documents-v0.1.0-alpha.6.zip) and follow the account registration route above. Ask it to apply the approved `demo-retail` Company Pack to a new fictional proposal. The starter alone is not an approved company profile.

Reference analysis, human approval and company-plugin export are a separate, more involved workflow: [five-scene walkthrough](DEMO_FLOW.md). The current public exporter blocks packs derived from private/restricted sources. Do not begin a real internal-company rollout expecting that capability to be available.

## 한국어

**매번 보고서용 프롬프트를 새로 쓰는 대신, 조사·작성·디자인·검수 순서를 재사용하는 도구입니다.** 직접 학습시킨 모델이 아니라 ChatGPT 또는 로컬 에이전트에서 사용하는 스킬·플러그인입니다.

- **Codex 빠른 설치:** Node.js 22.20 이상과 Git이 있다면 프로젝트 폴더에서 `npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y`를 실행하세요. 10개 스킬만 복사하며 ChatGPT 플러그인이나 회사 맞춤 ZIP 제작 도구는 설치하지 않습니다.
- ChatGPT: 위의 Starter ZIP을 받고 Plugin Creator로 개인용 플러그인을 생성합니다. 계정에 생성 기능이 있어야 합니다. 반환된 플러그인 주소가 있어야 등록된 것입니다.
- 로컬 Codex: 위의 설치 명령을 실행하고 새 세션에서 `report-html-pptx`가 인식되는지 확인합니다.
- 첫 요청:

> Document Studio로 가상 기업의 신입 온보딩 개선 제안서를 한국어 HTML 2페이지로 만들어줘. 독자는 운영팀장, 요청할 결정은 12명 대상 4주 시범운영 승인, 가상 예산은 300만 원이야. 1페이지는 문제·제안·기대효과, 2페이지는 일정·예산·성과지표 3개·위험요인으로 구성해줘. 숫자는 가정임을 표시하고 실제 기업 자료는 쓰지 마. HTML 파일과 실제로 수행한 검수 결과를 제공해줘.

사용 후 [첫 사용 피드백](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md)에 설치 경로, 막힌 단계, 결과물 생성 여부를 알려주세요. 다운로드 수를 설치 수로 집계하지 않습니다.

## 日本語

**毎回プロンプトを書き直す代わりに、調査・執筆・デザイン・確認の手順を再利用するツールです。** 独自に学習したAIモデルではなく、対応するAI環境で使うスキル／プラグインです。

- **Codexの簡単インストール：** Node.js 22.20以降とGitを用意し、プロジェクトフォルダで `npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y` を実行します。10個のスキルのみをコピーする方法で、ChatGPTプラグインや会社別ZIP作成ツールはインストールされません。
- ChatGPT：Starter ZIPを取得し、Plugin Creatorで個人用プラグインを作成します。対象アカウントに作成機能・権限が必要です。保存されたプラグインのURLを確認してください。
- ローカルCodex：上記のコマンドでインストールし、新しいセッションで `report-html-pptx` が認識されるか確認してください。
- 最初の依頼：

> Document Studioを使い、架空企業の新入社員オンボーディング改善提案書を日本語のHTMLで2ページ作成してください。読者は業務責任者、求める判断は12名を対象とした4週間の試行の承認、仮の予算は30万円です。1ページ目に課題・提案・期待効果、2ページ目に日程・予算・評価指標3つ・リスクをまとめてください。数値は仮定と明記し、実在企業の資料は使わないでください。HTMLファイルと、実際に実施した確認の結果を提示してください。

[初回利用のフィードバック](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md)では、利用環境・止まった手順・成果物の有無を教えてください。ダウンロード数をインストール数とは扱いません。
