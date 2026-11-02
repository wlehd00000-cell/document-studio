# Document Studio

**회사의 문서 제작을, 플러그인으로 재사용.**

사람이 승인한 회사 규칙과 문서 제작 스킬을 묶어 회사별 플러그인 패키지를 만드는 오픈소스 실험입니다. 직원의 요청을 구성·집필·디자인·편집 가능한 PowerPoint 출력으로 연결하는 방향을 검증합니다. 일본어가 기본이며 한국어로도 살펴볼 수 있습니다.

[일본어 데모](https://document-studio-public-experiment.wlehd00000.chatgpt.site/) · [한국어 데모](https://document-studio-public-experiment.wlehd00000.chatgpt.site/ko) · [한국어 문서](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example-ko) · [한국어 시작 안내](docs/QUICKSTART_ko.md)

[日本語](README.md) · [English / 상세 기술 설명](README.en.md)

![같은 가상 업무를 일본어 제안서로 구성한 공개 예제](docs/assets/showcase/proposal-ja.jpg)

공개 예제는 4쪽 제안서, 결재 요약, 운영 가이드로 구성했습니다. 회사·예산·목표는 가정이며 실제 기업 성과가 아닙니다. 예산은 240만 원(KRW)을 유지했고, 일본 엔으로 환산하지 않았습니다. 화면은 미리 제작한 문서를 보여 주며 AI를 실행하지 않습니다.

## 관리자의 준비와 직원의 사용

관리자는 사용 권한이 있는 참고 자료를 고르고, 추출한 규칙을 검토해 Company Pack으로 승인합니다. 이를 기본 스킬 8개와 선택한 일본어·한국어 교정 모듈에 묶어 패키지를 만듭니다. 설치와 새 요청의 동작 확인은 별도입니다.

직원이 요청하면 `report-html-pptx`가 목적·독자·언어·형식과 사용할 승인 Pack을 확인합니다. **구성과 필요한 조사 → 집필과 언어 확인 → 디자인과 필요한 이미지 → HTML 표시 확인 → 요청한 PPTX 출력과 최종 확인**으로 이어집니다. 원고·HTML만 요청하면 해당 단계까지 진행하고, 부분 수정은 영향받는 단계로 돌아갑니다.

현재 공개 exporter는 가상 Pack과 배포 권한을 확인한 공개 자료의 Pack을 대상으로 합니다. **비공개 사내 자료 기반 내부 배포와 원클릭 사내 도입은 아직 지원하지 않습니다.**

[홈에서 내부 흐름 보기](https://document-studio-public-experiment.wlehd00000.chatgpt.site/ko#plugin-flow) · [관리자 평가 절차와 명령어 — 일본어](docs/MANAGER_GUIDE_ja.md) · [설치와 현재 제약 — 영어](docs/WORKSPACE_ADMIN_GUIDE.md)

## 직접 살펴볼 내용

- 같은 업무의 범위·예산·조건이 서로 다른 문서에서도 유지되는지 확인합니다.
- 제안서의 근거·비용·일정, 결재 요약의 승인 범위, 가이드의 담당자·절차·예외 대응을 비교합니다.
- [공개 HTML 소스와 검토 조건](showcase/README.md)을 확인하거나, [예제 묶음](https://document-studio-public-experiment.wlehd00000.chatgpt.site/downloads/document-studio-demo.zip)을 내려받을 수 있습니다.

## 작은 첫 사용

Codex에서는 Node.js 22.20 이상과 Git이 있는 자신의 작업 폴더에서 다음 명령을 실행합니다.

```bash
npx --yes skills add wlehd00000-cell/document-studio --skill '*' -a codex --copy -y
```

새 Codex 세션에서 스킬 인식을 확인합니다. ChatGPT의 플러그인 등록은 Plugin Creator 기능과 저장 권한이 있는 계정에서 별도로 진행해야 합니다. [설치와 첫 요청](docs/TRY_FIRST.md)을 참고하세요.

8개 기본 스킬과 한국어·일본어의 2개 선택 언어 스킬을 제공합니다. 실험 단계의 alpha 버전이며, 사내 비공개 자료 기반 Company Pack의 배포는 공개 exporter에서 차단됩니다. 워크스페이스 자동 배포와 모델 간 동일 품질, 조직 전체의 생산성 향상은 입증하지 않았습니다. [기술 설명](README.en.md)과 [현재 한계](docs/WORKSPACE_ADMIN_GUIDE.md)를 함께 확인할 수 있습니다.

방향이 유용하다면 GitHub의 Star로 저장해 주세요. 직접 사용한 결과와 수정이 필요했던 부분은 [첫 사용 피드백](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md)으로 알려 주세요.

독자 제작물은 [MIT](LICENSE), 예제에 동봉한 글꼴은 각 OFL 고지를 따릅니다. [제3자 고지](THIRD_PARTY_NOTICES.md)를 확인하세요. 개인 프로젝트이며 소속 기업이나 상표권자의 도입·추천·보증을 의미하지 않습니다.

## 고정 디자인 규칙 비교

[흑백 A4·정렬 보고서·가로형 제안서 비교](https://document-studio-public-experiment.wlehd00000.chatgpt.site/compare?lang=ko)에서 같은 본문과 수치를 확인할 수 있습니다. 처음 정의한 여백·본문 크기·색·숫자 정렬을 두 페이지와 일본어·한국어에서 유지합니다. 화면의 측정은 정적 HTML 예제에 한정하며, AI의 새 문서 생성이나 준수율을 평가한 결과는 아닙니다.

## 창의력 예제와 컨설팅 기획

[실험적·몰입형 한 페이지](https://document-studio-public-experiment.wlehd00000.chatgpt.site/creative?lang=ko)는 같은 가상 업무의 요점을 재구성한 별도 안입니다. [심층 컨설팅 기획](https://document-studio-public-experiment.wlehd00000.chatgpt.site/consulting?lang=ko)은 명시적 선택 시 독립 조사·반론·실제 문서 비교로 논지를 발전시키고, 방향 선택과 최종 원고 수락을 거쳐 본제작으로 진행하는 기능입니다. 사이트에서는 정적 예제와 설명만 표시합니다.

## 편집 가능한 PowerPoint 출력

HTML에서 원고와 레이아웃을 확인한 뒤, 실제 배치·치수·글자 조판을 측정해 대응하는 본문·수치·표의 글자·도형을 PowerPoint의 편집 가능한 요소로 재구성합니다. 사진과 복잡한 장식은 이미지로 유지할 수 있습니다. 출력 후 표시·글자 보존·서체·편집성을 확인하는 과정까지 포함합니다. 모든 HTML의 완전 일치를 보장하지 않으며, 공개 웹 예제의 PPTX 변환과 실제 표시는 아직 검증하지 않았습니다. [구조도](https://document-studio-public-experiment.wlehd00000.chatgpt.site/ko#pptx-output) · [변환 명세](skills/html-to-pptx/SKILL.md)
