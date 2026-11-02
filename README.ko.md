# Document Studio

[日本語](README.md) · [한국어](README.ko.md) · [English](README.en.md)

**회사의 문서 제작을, 플러그인으로 재사용.**

사람이 승인한 회사 규칙과 문서 제작 스킬을 묶어 회사별 플러그인 패키지를 만드는 오픈소스 실험입니다. 직원의 요청을 구성·집필·디자인·편집 가능한 PowerPoint 출력으로 연결합니다.

[한국어 소개 사이트](https://document-studio-public-experiment.wlehd00000.chatgpt.site/ko) · [관리자 평가 절차 — 일본어](docs/MANAGER_GUIDE_ja.md) · [문서 안내](docs/README.md)

실험 단계의 **alpha.6**입니다. 현재 공개 내보내기 도구는 가상 Pack과 배포 권한을 확인한 공개 자료를 대상으로 하며, 비공개 사내 자료 기반 내부 배포는 미지원입니다.

## 궁금한 내용부터 확인하세요

| 목적 | 다음 안내 |
|---|---|
| 만들 수 있는 자료 살펴보기 | [설치 없이 예제 보기 — 일본어 중심](docs/SHOWCASE.md) |
| 팀에서 쓸 수 있는지 평가 | [관리자 준비·현재 제약·가상 Pack 평가 — 일본어](docs/MANAGER_GUIDE_ja.md) |
| 직접 문서 한 건 만들기 | [한국어 첫 사용 안내](docs/QUICKSTART_ko.md) |
| 구현과 명령어 확인 | [기술 가이드 — 영어](docs/TECHNICAL_GUIDE.md) |

## 관리자는 기준을 준비하고, 직원은 자료를 요청합니다

회사의 용어·문체·디자인·출처 등을 확인한 근거와 함께 **Company Pack**으로 관리합니다. 필요한 회사 기준을 유지하면서 구성과 표현을 목적에 맞게 정하는 구조입니다. 지정 양식이 있는 자료에는 해당 배치 규칙도 적용합니다.

| 담당 | 진행 방식 |
|---|---|
| 관리자 | 권한 있는 참고 자료 선택 → 제안된 규칙 확인·승인 → Pack과 스킬 패키지 생성 → 지원 환경에 도입하고 동작 확인 |
| 직원 요청 이후 | 목적·독자·언어·형식과 사용할 Pack 확인 → 구성과 필요한 조사 → 집필과 언어 확인 → HTML 디자인·표시 확인 → 필요한 PPTX 출력과 최종 확인 |

기본 스킬 8개와 선택한 일본어·한국어 교정 모듈을 묶습니다. 도입한 환경의 AI가 역할별 지침과 스크립트를 적용하므로 직원이 내부 스킬 이름을 차례로 지정할 필요는 없습니다. [내부 흐름 보기](https://document-studio-public-experiment.wlehd00000.chatgpt.site/ko#plugin-flow)

## 예제에서 확인할 세 가지

| 확인할 점 | 예제 |
|---|---|
| 처음 정한 디자인 규칙 유지 | [같은 두 페이지를 흑백 A4·정렬 A4·가로형 제안서로 비교](https://document-studio-public-experiment.wlehd00000.chatgpt.site/compare?lang=ko) |
| 독자에 맞는 정보 순서 | [제안서·결재 요약·운영 가이드](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example-ko) |
| 표현을 과감하게 변경 | [같은 업무의 요점을 재구성한 창의력 확장 한 페이지](https://document-studio-public-experiment.wlehd00000.chatgpt.site/creative?lang=ko) |

[![흑백 A4와 정렬 A4를 비교한 일본어 미리보기. 링크에서 한국어로 확인할 수 있습니다.](docs/assets/showcase/comparison-ja.jpg)](https://document-studio-public-experiment.wlehd00000.chatgpt.site/compare?lang=ko)

예제는 가상 업무이며 예산은 240만 원(KRW)입니다. 화면은 미리 제작한 정적 HTML을 표시하고 AI를 실행하지 않습니다. 표시 측정은 이 예제에 한정하며 새 생성·기업 성과·인쇄·PPTX를 검증한 결과가 아닙니다. [원고·규칙·검토 조건 — 일본어](showcase/README.md)

논점부터 상의하고 싶다면 선택형 [심층 컨설팅 기획](https://document-studio-public-experiment.wlehd00000.chatgpt.site/consulting?lang=ko)도 살펴볼 수 있습니다. 창의력 설정과 별개이며 명시적으로 선택할 때 사용하는 진행 방식입니다.

## HTML에서 편집 가능한 PowerPoint로

HTML로 원고와 레이아웃을 확인한 뒤 브라우저의 위치·크기·글자를 측정합니다. 지원하는 본문·수치·도형을 PowerPoint의 편집 가능한 요소로 다시 구성해 회의 전 수치 수정이나 담당자·문장 변경을 이어가도록 합니다.

사진이나 복잡한 장식은 이미지로 유지할 수 있습니다. 실제 서체·표시·편집성 확인이 필요하며 모든 HTML의 완전한 일치를 보장하지 않습니다. 공개 예제의 PPTX 변환은 미검증입니다. [업무 활용과 변환 구조 — 일본어](docs/PPTX_OUTPUT_ja.md)

## 작은 업무 하나부터 시작하세요

개인 사용은 [한국어 첫 사용 안내](docs/QUICKSTART_ko.md), 회사별 패키지 평가는 [관리자 가이드의 가상 Pack — 일본어](docs/MANAGER_GUIDE_ja.md)으로 시작할 수 있습니다.

| 확인 항목 | 현재 상태 |
|---|---|
| 승인한 가상 Pack·배포 권한 있는 공개 자료 Pack의 ZIP 생성 | 구현된 평가 경로 |
| 설치·Pack 선택·새 요청·HTML/PPTX 품질 | 도입 환경에서 별도 확인 |
| 비공개 자료의 내부 배포·원클릭 사내 도입 | 미지원 |

[HTML 열람 ZIP·플러그인 ZIP·소스의 차이 — 일본어](docs/FAQ_ja.md#どのzipを選べばよいですか)를 확인하세요. ZIP 저장만으로 플러그인이 설치되지는 않습니다.

기업에서 AI를 어떻게 활용할지 문서 업무를 통해 검증하는 개인 프로젝트입니다. 관심이 있다면 Star로 저장하고, 사용 결과와 필요했던 수정을 [첫 사용 피드백](https://github.com/wlehd00000-cell/document-studio/issues/new?template=first_run.md)으로 알려 주세요. 한국어·일본어·영어 모두 가능합니다.

[자주 묻는 질문 — 일본어](docs/FAQ_ja.md) · [기여 — 영어](CONTRIBUTING.md) · [변경 이력 — 영어](CHANGELOG.md) · [보안 — 영어](SECURITY.md)

독자 제작물은 [MIT](LICENSE), 동봉 서체 등은 [제3자 권리 고지](THIRD_PARTY_NOTICES.md)를 따릅니다. 소속 기업이나 상표권자의 도입·추천·보증을 의미하지 않습니다.
