# Document Studio — 보고서 작성 과정을 스킬로 정리했습니다

보고서와 제안서를 만들 때마다 문체, 구성, 검수 기준을 다시 설명하는 일이 번거로워 직접 만든 도구입니다.

Document Studio는 조사 → 구조 설계 → 작성 → 디자인 → 검수를 재사용하는 MIT 오픈소스 툴킷입니다. 로컬 Codex 스킬과 설치 권한이 있는 ChatGPT 계정용 플러그인 패키지를 제공합니다. 한국어·일본어 비즈니스 문장 교정 모듈을 선택할 수 있습니다.

[English](../README.md) · [日本語](QUICKSTART_ja.md)

## 먼저 문서 한 건을 만들어보세요

회사 자료를 분석하거나 관리자 배포부터 시작할 필요가 없습니다. [첫 사용 안내](TRY_FIRST.md#한국어)에 설치 방법과 그대로 붙여 넣을 가상 제안서 요청문을 넣었습니다.

| 사용 환경 | 시작 방법 |
|---|---|
| ChatGPT | [Starter ZIP](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/document-studio-starter-v0.1.0-alpha.6.zip)을 Plugin Creator로 개인용 플러그인에 등록. 생성 기능과 권한이 있는 계정만 가능. |
| 로컬 Codex | 아래 명령으로 스킬을 설치한 뒤, 새 세션에서 `report-html-pptx` 인식 여부 확인. |
| 기업용 평가 | 일반 문서가 만들어지는지 먼저 확인하고 [가상 기업 데모](TRY_FIRST.md#company-demo)로 회사별 규칙 적용을 평가. |

```bash
npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y
```

Node.js 22.20 이상과 Git이 필요합니다. 이 경로는 에이전트 스킬만 설치하며 회사별 ZIP 내보내기 도구는 포함하지 않습니다. 전체 소스를 다루려면 [Python 설치 경로](TRY_FIRST.md#local-codex)를 이용하세요.

설치가 끝나면 새 Codex 세션에서 스킬을 실제로 인식하는지 확인하세요. 파일 복사만으로 문서 품질이 검증되는 것은 아닙니다.

## 일반적인 문서 요청과 무엇이 다른가요?

매번 긴 지시문을 다시 쓰는 대신 작성 절차와 검수 기준을 스킬에 분리합니다. 회사별 승인 규칙은 Company Pack으로 별도 관리하도록 설계했습니다. 레이아웃을 한 가지 틀로 고정하는 대신, 검토한 문체·구성 원칙을 새로운 문서에 적용하는 방식입니다.

품질 향상률이나 작업 시간 단축률을 측정한 제품은 아닙니다. 같은 모델·같은 요청으로 스킬 사용 전후의 수정량과 결과물 구조를 비교해보세요.

## 현재 범위

실험용 **alpha.6**입니다. 직접 학습한 모델이나 한 번의 클릭으로 완성되는 PPT 서비스가 아닙니다. 비공개 사내 원본에서 만든 팩은 현재 공개 내보내기가 차단됩니다. 최종 HTML/PPTX 제작과 시각 검수는 별도 과정이며, 모델마다 동일한 결과를 보장하지 않습니다.

[설치와 제약 상세](DOWNLOAD_AND_INSTALL.md) · [회사별 규칙 분석 과정](DEMO_FLOW.md) · [첫 사용자 피드백](https://github.com/wlehd00000-cell/document-studio/issues/4)

사용해보셨다면 [첫 사용 이슈](https://github.com/wlehd00000-cell/document-studio/issues/4)에 막힌 단계나 결과를 남겨주세요.
