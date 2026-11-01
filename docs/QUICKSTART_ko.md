# Document Studio

**다음 보고서에도 이어 쓸 수 있는 문서 제작 워크플로우.**

보고서·제안서·발표자료를 만들 때마다 문체, 구성, 검수 기준을 다시 설명하는 일이 반복됩니다. Document Studio는 조사·구조 설계·작성·디자인·검수 절차를 에이전트 스킬로 정리해 다음 작업에서도 활용할 수 있도록 돕습니다.

[English](../README.md) · [日本語](QUICKSTART_ja.md) · [구성 살펴보기](SHOWCASE.md) · [전체 문서](README.md)

MIT 오픈소스 · 실험 버전 alpha.6 · Codex 및 플러그인 생성 권한이 있는 ChatGPT 계정에서 사용

## 무엇을 재사용하나요?

**스킬은 제작 절차를, Company Pack은 검토한 회사별 규칙을 담습니다.**

스킬에는 독자와 목적 확인, 근거 조사, 원고 작성, 시각 구성, 결과물 검수 등의 작업 지침이 들어 있습니다. 회사별 용어·색상·배치 원칙이 필요하면 담당자가 검토한 Company Pack을 함께 사용할 수 있습니다. 새 문서의 독자와 내용은 그때의 요청에 맞춰 정합니다.

먼저 일반 문서 한 건을 만들어 보고, 회사별 규칙이 필요할 때 팩을 추가하세요.

## 시작 방법

### Codex

Node.js 22.20 이상과 Git을 준비하고 **본인의 작업 프로젝트 폴더**에서 실행하세요.

```bash
npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y
```

새 Codex 세션에서 `report-html-pptx`가 인식되는지 확인합니다. 이 방법은 스킬 10개를 설치합니다. 회사별 ZIP 제작 도구까지 사용하려면 [전체 소스 설치 안내](TRY_FIRST.md#local-codex)를 따르세요.

### ChatGPT

Plugin Creator와 플러그인 생성 권한이 있는 계정에서 [Starter ZIP 등록 절차](TRY_FIRST.md#chatgpt)를 따르세요. 저장된 플러그인의 주소와 ID를 확인한 뒤 새 대화에서 선택합니다.

## 첫 문서 요청

설치한 스킬이나 플러그인에 다음과 같이 요청해 보세요.

> Document Studio로 가상 기업의 신입 온보딩 개선 제안서를 한국어 HTML 2페이지로 만들어 줘. 독자는 운영팀장이고, 요청할 결정은 12명 대상 4주 시범 운영 승인이야. 가상 예산은 300만 원이야.
>
> 1페이지는 문제·제안·기대효과, 2페이지는 일정·예산·성과지표 3개·위험요인으로 구성해 줘.
>
> 숫자는 가정임을 표시하고 실제 기업 자료는 쓰지 마. HTML 파일과 실제로 수행한 사실 확인·시각 검수 결과를 제공해 줘.

승인할 내용이 분명한지, 예산과 일정이 맞는지, 글이 잘리지 않는지 확인하세요. 검수를 수행하지 못한 부분도 결과에 명시되어야 합니다.

## 회사별 규칙을 추가하려면

가상의 [소매기업 팩](../company-packs/demo-retail/pack.json)과 [제조기업 팩](../company-packs/demo-manufacturing/pack.json)으로 형식을 살펴볼 수 있습니다. 직접 만드는 경우에는 **사용 권한이 있는 PDF/PPTX → 근거 추출 → 담당자 검토 → Company Pack 승인 → 새 문서 제작** 순서로 진행합니다.

공개 배포 요건을 충족한 승인 팩은 스킬과 함께 플러그인 ZIP으로 내보낼 수 있습니다. [분석·검토 절차](DEMO_FLOW.md)와 [기술 안내](TECHNICAL_GUIDE.md)를 참고하세요.

## 현재 지원 범위

- PDF/PPTX 근거 추출, 회사별 규칙 검토·승인, 공개 배포가 허가된 팩의 ZIP 내보내기를 지원합니다.
- HTML 렌더링, 글꼴, 편집 가능한 PPTX, 계정별 설치는 실제 사용 환경에서 별도로 확인해야 합니다.
- 비공개·제한 자료에서 만든 팩의 내보내기와 워크스페이스 자동 배포는 현재 지원하지 않습니다.

결과물은 사용하는 AI와 제작 환경의 영향을 받습니다. 품질 향상률이나 시간 단축률은 확립되지 않았습니다. [평가와 한계](TECHNICAL_GUIDE.md#evaluation-and-limitations)에서 확인한 범위를 볼 수 있습니다.

[첫 사용 경험 남기기](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md) · [팀 도입 검토](WORKSPACE_ADMIN_GUIDE.md) · [변경 이력](../CHANGELOG.md)
