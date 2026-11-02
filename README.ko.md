# Document Studio

**AI가 바뀌어도, 회사의 문서 기준은 다음 업무로 이어지도록.**

사람이 검토한 용어·문체·검수 기준을 AI 문서 작업에 연결하는 오픈소스 실험입니다. 이번 공개 데모는 일본어를 기본으로 제공하며, 한국어 예제도 살펴볼 수 있습니다.

[일본어 데모](https://document-studio-public-experiment.wlehd00000.chatgpt.site/) · [한국어 데모](https://document-studio-public-experiment.wlehd00000.chatgpt.site/ko) · [한국어 문서](https://document-studio-public-experiment.wlehd00000.chatgpt.site/example-ko) · [한국어 시작 안내](docs/QUICKSTART_ko.md)

[日本語](README.md) · [English / 상세 기술 설명](README.en.md)

![같은 가상 업무를 일본어 제안서로 구성한 공개 예제](docs/assets/showcase/proposal-ja.jpg)

공개 예제는 4쪽 제안서, 결재 요약, 운영 가이드로 구성했습니다. 회사·예산·목표는 가정이며 실제 기업 성과가 아닙니다. 예산은 240만 원(KRW)을 유지했고, 일본 엔으로 환산하지 않았습니다. 화면은 미리 제작한 문서를 보여 주며 AI를 실행하지 않습니다.

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
