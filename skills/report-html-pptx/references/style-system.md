# Style system: canonical pointer

[design-tokens.json](../system/design-tokens.json)이 colors/font/physical type/spacing/profile/page-family 기본값의 단일 source다. [design-system.md](../system/design-system.md)가 선택과 적용의 권위다. 이 파일에 같은 숫자를 재정의하지 않는다.

`build_design_css.py`는 token JSON으로 [CSS](../assets/demo-esg-design/demo-esg-report.css)의 generated token block을 갱신한다. Layout CSS는 정보 관계와 HTML 구도에 맞춰 편집한다. 기존 type_profile alias는 받아들이며 신규 작업은 문서 purpose에서 profile을 선택한다. 폰트 URL을 복사된 project 위치에 맞추고 실제 loaded/used font를 확인한다.

Document profile과 page family를 별도로 기록한다. `data-design-profile="reading_report"` + `data-page-family="cover"`처럼 cover/opener에 본문 밀도를 적용하지 않는다. Full-image/title-safe composition을 적극 허용하며 3색 band는 explicit opt-in이다. [Office print](office-print-reports.md)는 원본 그림 색을 보존하고 neutral document palette/A4 safety를 사용한다.

[DEMO source cases](demo-esg-design.md), [composition quality](document-design-quality.md), [image placement](demo-esg-image-layout.md), [visual review](demo-esg-review.md)는 해당 작업에서만 읽는다. Token 값은 공식 전사 CI가 아니며 accepted template/user instruction이 우선한다.
