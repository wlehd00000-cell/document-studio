# Document Studio 디자인 계약

수치·색·글꼴·그리드·profile·page family의 단일 권위는 [design-tokens.json](design-tokens.json)이다. 이것은 관측한 DEMO 보고서를 해석한 제작 시작값이며 공식 전사 CI가 아니다. 명시한 사용자 요구와 채택한 템플릿이 우선한다. 관측과 제안값은 casebook에서 구분한다.

## 두 축을 고른다

문서 전체의 **purpose profile**은 상세 읽기, 인쇄, 승인 판단, 제안, 실행, 읽기용 deck, 실제 발표를 구분한다. 파일 확장자로 밀도를 선택하지 않는다. 새 문서와 수정 문서는 실제 발표용도 포함해 HTML 제작으로 고정한다. 기본 파일은 HTML-to-PPTX로 만든다. 기존 PPTX/Slides 양식은 실제 크기·구도·정체성의 제약이며 자동 native 제작의 근거가 아니다. HTML/PPTX 같은 기술 route는 [authoring-routes.md](authoring-routes.md)를 따른다. `live_deck`에는 작은 보고서 활자를 확대 복사하지 않고 필요한 내용·조건을 다시 구성한다. 기존 템플릿의 변경 범위 밖 크기/글꼴/구도는 보존한다.

각 페이지는 **page family**로 별도 판단한다. `cover`, `chapter_opener`, `editorial`, `narrative`, `evidence`, `comparison`, `process`, `execution`, `appendix`는 역할이며 템플릿 할당량이 아니다. 표지/opener에 본문 최소밀도·3단·본문 header를 강제하지 않는다. 같은 상세 표가 반복되는 부록에는 같은 구도가 적합하다.

| 독자가 할 일 | 시작 profile | 구성 성격 |
|---|---|---|
| 상세 내용을 읽고 근거 확인 | reading_report | 연결 문단과 인접한 표·사진·각주 |
| A4 프린터로 읽기/공유 | office_print | 인쇄 안전 여백, 중립색, 원본 이미지 색 보존 |
| 승인·판단 | executive_approval | 요청/추천/조건을 먼저, 바로 옆 근거와 책임 |
| 제안 검토 | proposal | 큰 concept/object + 설명·비교·실현 조건 |
| 담당이 실행 | execution | 날짜·담당·인계·예외 조건의 일치 |
| PPT를 독립적으로 읽기 | reading_deck | 충분한 상세 근거; screen 폭에 맞춘 서술 |
| 발표자가 설명 | live_deck | 먼 거리에서 읽는 위계; 상세 조건은 부록 등에 보존 |

직원에게 profile ID, case ID, route, rendering 기술을 선택하게 하지 않는다. 읽기/발표/인쇄와 필요한 파일·독자·목적을 이해해 시스템이 결정한다.

## Art direction이 asset보다 먼저다

핵심 표지/큰 이미지 페이지에서는 페이지 map에 한 문장의 의도와 필요한 관계를 기록한다. 예: “거리의 고객 접점을 먼저 보고, 고요한 왼쪽에서 제안의 범위·시점을 읽는다.” 필요한 항목만 사용한다: dominant element, reading sequence, image occupancy, frame/aspect, focal subject, protected crop, quiet/text-safe region, caption location, editable overlays, reference role, actual/concept/proposal state.

이미지 중심 표지는 페이지의 65–100%를 채울 수 있다. 이 수치는 허용/제작 제안이며 모든 표지의 하한선이 아니다. Full bleed 사진, 생성 conceptual scene, product hero, 장소 사진, 타이포 중심, quiet title zone, strong crop, institutional cover를 주제에 맞춰 선택한다. 2쪽 승인문서는 별도 표지가 불필요할 수 있다. 제목·수치·조건은 가능한 한 편집 가능하게 놓고 concept는 가까운 문구 또는 asset inventory에 정확히 표시한다. 실제 시설/행사로 오해할 여지가 있으면 페이지에서도 표시한다.

`focal_point`와 `crop`은 계획/실측을 구분한다. 실제 결과를 보고 피사체, 로고, 포장 표기, 얼굴, 설명 대상이 남는지 확인한다. quiet zone은 이미지 전체의 공백이 아니라 제목/설명에 필요한 영역이다. Body에서는 이미지가 주장과 연결되어야 하며 캡션은 해당 frame에 인접한다.

## 공통 기반과 목적별 자유

한국어 Pretendard Variable과 일본어 Pretendard JP Variable, 정렬/단위/용어, 출처/상태 보존이 공통 기반이다. 혼합 문서는 각 문장의 실제 lang을 표시하고 해당 언어판을 적용한다. 승인된 기존 양식의 글꼴은 근거와 함께 보존한다. 레퍼런스의 title/image/negative-space/caption 관계를 활용하며 색 유사도만으로 DEMO 적용을 판정하지 않는다. 7px 3색 band는 명시적으로 채택한 기존 디자인의 opt-in 표시이며 새 문서의 공통 필수가 아니다. Full-image cover나 live deck에 띠를 강제하지 않는다. Office print 후보의 중립색·A4 여백은 유지한다.

Document Studio 로고는 [공식 투명 원본](../assets/brand/README.md)을 사용한다. 밝은 배경은 `demo-mark.svg`, 어두운 사진/장면은 공식 흰 글자 `demo-mark-white.svg`를 선택하고 비율·색·alpha를 보존한다. 로고를 재색칠하거나 흰 사각 배경에 굽지 않는다. 출처·원본 해시의 단일 기록은 brand 폴더의 `logo-provenance.json`이다. HTML뿐 아니라 최종 PPTX 내부 media에서도 원본 바이트와 투명도가 유지되는지 확인한다.

둥근 카드, pale card + 짧은 색선, 3-icon 요약, 가상 progress, 과대한 숫자, 무관한 스톡 사진, slogan만 있는 빈 페이지, glossy 3D를 기본값으로 삼지 않는다. 카드나 gradient가 실제 정보/원본 asset에 필요한 경우까지 금지하지 않는다. 주제별 personality를 살리고 같은 문서의 위계/용어/색 역할은 유지한다.

## 구현과 변경

HTML 예제의 `data-design-profile`/`data-page-family`는 내부 구현이다. CSS는 JSON에서 `scripts/build_design_css.py`로 생성하고, 레이아웃 CSS는 별도 관계를 구현한다. 생성 CSS를 직접 수정해 기본값을 분산하지 않는다. 최종 PPTX도 같은 profile의 물리 pt를 기준으로 변환하되 실제 slide 물리 크기와 먼 거리 읽기를 검증한다. `legacy_aliases`는 기존 자료를 열 수 있게 남기고 신규 profile 결정의 기준으로 사용하지 않는다.

작은 수정은 기존 profile/asset/crop/map을 재사용하고 실제 영향을 받은 page만 변경한다. copy, data, font, geometry, asset 교체는 [project-state.md](project-state.md)의 dependency/QA 기록을 갱신한다. 자동 검사, 편집 검토, 실제 visual inspection, export 검증, 사용자 수락을 하나의 pass로 합치지 않는다.

## Reference 확장

[DEMO ESG casebook](../references/demo-esg-casebook.json)의 기존 본문 사례와 새 cover/opener/image 사례를 필요에 따라 1–3개 선택한다. `select_esg_reference.py --family cover --limit 3`처럼 목적별 조회가 가능하다. 원본이 있으면 해당 실제 페이지를 본다. 원본이 없어도 보존된 관측으로 진행할 수 있으나 이번 작업에서 직접 보았다고 쓰지 않는다.

다른 감각적 editorial reference도 적극적으로 조회할 수 있다. [external-editorial-references.json](../references/external-editorial-references.json)은 제작사 공식 설명과 확인 범위를 기록한 보조 시작점이다. 작품의 모양/사진/전용 글꼴을 복제하지 않고 현재 최종 언어·자료에서 adaptation을 만든다. 웹 설명만 읽었으면 spatial measurements를 관측했다고 쓰지 않는다.

## 목적과 독립적인 표현 수준

기존 두 축(purpose profile/page family)에 별도로 [창의성·화려함](../references/design-expression.md)을 적용한다. 수치 기본값은 design-tokens.json, 표현 선택/traits는 [design-expression.json](design-expression.json)의 단일 권위다. 새 독립 레퍼런스는 기존 DEMO 관측을 확장하며, 기존 보수적 사례와 같은 구도를 강제하지 않는다. 생성 비유, tactile scene, 실험적인 비대칭, 강한 palette를 주제에 맞게 선택한다. 색만 바꾸는 대신 의미/읽기 관계를 설계한다. 공식형부터 showcase까지 표지와 상세 본문을 실제로 비교한다. 사용자 선택은 두 축을 따로 보존하고, 낮은 화려함도 독창적인 visual을 허용한다.

Follow [production contract](../references/production-contract.md) for independent use/canvas decisions, compact next-step information, actual design measurement and verified role evidence. Existing editorial/visual/export checks remain required.
