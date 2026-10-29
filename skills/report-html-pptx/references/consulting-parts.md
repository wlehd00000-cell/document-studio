# 제안·의사결정 자료의 HTML 구현 예시

DEMO 원본 사례와 기존 72개 시각 패턴으로 표현 목적을 결정한 뒤, 실제 구현 예시가 필요할 때만 [6종 예시](../assets/consulting-parts/index.html)의 해당 section과 [CSS](../assets/consulting-parts/parts.css)를 참고한다. 전체 파일을 새 문서의 고정 순서/템플릿으로 사용하지 않는다. 카탈로그 ID나 예시 개수는 품질 기준이 아니다.

| 예시 ID | 읽는 사람이 이해할 관계 | 자료 조건 |
|---|---|---|
| `demo-executive-summary` | 판단할 결론 → 근거 → 남은 조건 | 결론과 그 근거, 범위/조건 |
| `demo-evidence-implication` | 관측한 값 → 해석 → 확인할 조건 | 같은 기준의 수치/출처 또는 정성 근거 |
| `demo-option-comparison` | 대안 × 공통 기준 → 선택의 조건 | 같은 평가 축과 실제 근거 |
| `demo-issue-action-owner` | 과제 → 대응 → 책임 → 확인 증거 | 과제와 연결된 동작/담당/조건 |
| `demo-roadmap-gates` | 일정 → 선행 조건 → 완료 판단 | 실제 시점/역할/승인 또는 완료 조건 |
| `demo-decision-request` | 결정 사항 → 범위/한계 → 다음 행동 | 실제 선택 항목과 담당/후속 조건 |

한일 문구와 숫자는 HTML 본문/표로 둔다. 가상의 값·업무·출처는 예시임을 페이지마다 명시했다. 실제 제작에서는 원자료로 교체하고 출처·기간·단위·상태를 유지한다. 없는 점수/우열을 채우지 않는다. 색은 의미와 라벨이 함께 있는 경우에만 쓰며, 조건은 결론과 가까이 둔다.

예시는 A4 가로 읽기 자료와 [canonical `reading_report` profile](../system/design-tokens.json)을 사용한다. 공통 CSS에서 Pretendard·본문/표/캡션 조판을 가져오고, 브랜드 띠를 기본값으로 넣지 않는다. 본문/비교/실행의 page family만 정했으며 표지·opener의 밀도에는 적용하지 않는다. 실제 발표자료는 `live_deck` profile과 실제 사용 크기에 맞춰 재구성하되, HTML 제작 고정과 특별 출력 요청에 따른 export 예외는 [route 계약](../system/authoring-routes.md)을 따른다. PPTX 파일이라는 이유로 읽기용 본문을 발표용으로 바꾸지 않는다. 복사한 공통 CSS의 폰트 URL도 프로젝트의 실제 경로에 맞춘다.

페이지는 `[data-pptx-slide]`로 표시한다. 기존 변환기로 텍스트·표/단순 도형의 편집성을 확인하고, 실제 PPTX 화면의 줄 흐름과 조건 누락을 별도로 확인한다. 예시 HTML의 모양만으로 최종 PPTX 품질을 통과 처리하지 않는다. 변환 도구와 기존 디자인 기준은 그대로 재사용한다.

정확한 business copy는 이미지에 굽지 않고, 자연스러운 문장 흐름을 `data-pptx-text-flow="natural"`로 보존한다. 의도적인 의미 경계의 `<br>`만 soft break로 남긴다. 그림의 막대는 명시된 가상 값 12분/9분을 표현하며 진행률이나 실제 DEMO 성과를 뜻하지 않는다.

이 예시들은 consulting-pptx-skill의 전체 스킬/62형 코드 복제본이 아니다. 선별한 표현 목적을 DEMO 기준으로 새로 구현했다. [출처·선별 이유](consulting-integration-sources.json)와 [원 저장소 MIT 고지](consulting-pptx-LICENSE.txt)를 함께 보존한다. 산출물의 뒷표지에 외부 스킬 홍보 문구를 자동 추가하지 않는다.
