# Document Studio — AI 문서 작업의 기준을 재사용하세요

**보고서·제안서를 만들 때 같은 프롬프트를 반복해서 설명하고 있다면, 그 절차를 스킬로 저장해두세요.**

Document Studio는 조사 → 구조 설계 → 작성 → 디자인 → 검수를 재사용하는 MIT 오픈소스 툴킷입니다. 로컬 Codex 스킬과 설치 권한이 있는 ChatGPT 계정용 플러그인 패키지를 제공합니다. 한국어·일본어 비즈니스 문장 교정 모듈을 선택할 수 있습니다.

[⭐ GitHub에서 Star로 저장하기](https://github.com/wlehd00000-cell/document-studio) · [English](../README.md) · [日本語](QUICKSTART_ja.md)


<img src="assets/document-example.png" width="600" alt="Document Studio fictional document example">

*포함된 가상 문서 예시입니다. 실존 기업이나 실측 성과를 나타내지 않습니다.*

## 먼저 문서 한 건을 만들어보세요

회사 자료를 분석하거나 관리자 배포부터 시작할 필요가 없습니다. [첫 사용 안내](TRY_FIRST.md#한국어)에 설치 방법과 그대로 붙여 넣을 가상 제안서 요청문을 넣었습니다.

| 사용 환경 | 시작 방법 |
|---|---|
| ChatGPT | [Starter ZIP](https://github.com/wlehd00000-cell/document-studio/releases/download/v0.1.0-alpha.6/document-studio-starter-v0.1.0-alpha.6.zip)을 Plugin Creator로 개인용 플러그인에 등록. 생성 기능과 권한이 있는 계정만 가능. |
| 로컬 Codex | 아래 명령으로 설치한 뒤, 새 세션에서 `report-html-pptx` 인식 여부 확인. |
| 기업용 평가 | 일반 문서가 만들어지는지 먼저 확인하고 [가상 기업 데모](TRY_FIRST.md#company-demo)로 회사별 규칙 적용을 평가. |

```bash
git clone --branch v0.1.0-alpha.6 --depth 1 https://github.com/wlehd00000-cell/document-studio.git
cd document-studio
python scripts/install_local.py --verify-only
python scripts/install_local.py --language-skills ko,ja
```

Python 3.12와 스킬을 인식하는 로컬 에이전트 환경이 필요합니다. 설치 스크립트를 읽고 실행하세요. 파일 설치와 실제 에이전트의 스킬 인식은 별도로 확인해야 합니다.

## 일반적인 문서 요청과 무엇이 다른가요?

매번 긴 지시문을 다시 쓰는 대신 작성 절차와 검수 기준을 스킬에 분리합니다. 회사별 승인 규칙은 Company Pack으로 별도 관리하도록 설계했습니다. 레이아웃을 한 가지 틀로 고정하는 대신, 검토한 문체·구성 원칙을 새로운 문서에 적용하는 방식입니다.

품질 향상률이나 작업 시간 단축률을 측정한 제품은 아닙니다. 같은 모델·같은 요청으로 스킬 사용 전후의 수정량과 결과물 구조를 비교해보세요.

## 현재 범위

실험용 **alpha.6**입니다. 직접 학습한 모델이나 한 번의 클릭으로 완성되는 PPT 서비스가 아닙니다. 비공개 사내 원본에서 만든 팩은 현재 공개 내보내기가 차단됩니다. 최종 HTML/PPTX 제작과 시각 검수는 별도 과정이며, 모델마다 동일한 결과를 보장하지 않습니다.

[설치와 제약 상세](DOWNLOAD_AND_INSTALL.md) · [회사별 규칙 분석 과정](DEMO_FLOW.md) · [첫 사용자 피드백](https://github.com/wlehd00000-cell/document-studio/issues/4)

방향이 유용해 보인다면 [저장소에 ⭐ Star](https://github.com/wlehd00000-cell/document-studio)를 남겨주세요. 실제 사용 중 막힌 단계는 이슈로 알려주시면 개선 근거가 됩니다.
