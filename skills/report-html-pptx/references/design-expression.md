# 문서의 창의성과 화려함을 조절한다

목적·독자·분량·읽기/발표/인쇄는 유지하면서 원하는 느낌을 별도로 선택한다. 단일 기준은 [design-expression.json](../system/design-expression.json), 실제 시각 레퍼런스는 [expression casebook](creative-reference-casebook.json)과 [한일 비교 갤러리](../assets/creative-directions/index.html)다. 기존 DEMO 관측은 기반이며 창의성의 상한선이 아니다.

## 선택과 재사용

네 출발점은 **단정한 공식 문서 / 감각적인 편집물 / 과감한 제안서 / 몰입감 있는 쇼케이스**다. 각각 창의성 및 시각적 화려함 두 축의 조합이며 서로 독립적으로 바꿀 수 있다. 높은 창의성+차분한 색감, 익숙한 구성+풍부한 사진도 유효하다. 장르나 임원 독자라는 이유만으로 단정함을 강제하지 않는다.

사용자가 지정한 느낌, 제출한 `design_preferences`, 같은 프로젝트에서 채택한 방향을 이어받는다. 특정 축만 바꾸면 다른 축과 목적 조건은 보존한다. 새 preset을 선택하면 두 축을 새 preset 값으로 바꾸고 이번에 명시한 축을 우선 적용한다. `preset: auto`는 추천을 새로 맡긴 것이다. 미지정 새 작업은 사용자가 채택한 [직원 가이드 수준](accepted-composition-default.md)의 expressive/rich에서 시작한다. 창의적인 본문 구성과 의미 있는 시각 설명을 기본으로 실제 제작하며, 기존 작업은 채택한 선택을 재사용한다. 기존 양식 수정은 채택한 양식의 구도를 보존한다. 느낌 선택은 optional이며 새 필수 설문·생성 승인·원샷 중간승인을 만들지 않는다.

대화의 “차분하지만 독창적으로”는 expressive/subtle, “익숙한 구성으로 화려하게”는 restrained/rich, “이미지 생성해서 과감하고 멋지게”는 expressive/rich의 근거 있는 후보가 될 수 있다. 문맥과 사용자의 원래 표현을 기록한다. 애매한 취향은 routine 선택으로 구체화하고 진행한다. 선택 변경은 새 표지뿐 아니라 실제 영향을 받은 본문·이미지·export 검수까지 갱신한다. 일회성 선택은 영구 개인 기본값으로 저장하지 않는다. 이번 3.9.0의 가이드 구성 기본값은 사용자가 명시적으로 플러그인 기본값 저장을 요청한 범위다.

## 두 축이 실제로 바꾸는 것

창의성은 **비유의 독창성, 예상 밖의 크기/시점, 조형 언어, 페이지의 읽는 순서**를 바꾼다. 화려함은 **색 대비, 이미지 존재감, 질감/층, 빛과 장면의 몰입도**를 바꾼다. 낮음은 낮은 품질, 높음은 더 많은 장식이 아니다. 모든 축에서 정교한 정렬·실제 원고·완성도를 유지한다.

| 출발점 | 표지·챕터 | 상세 본문 | 참고 |
|---|---|---|---|
| 단정한 공식 문서 | 명료한 타이포, 정통 구도, 사실 이미지/선형 모티프 | 단위·조건·표의 명확한 정렬 | DEMO-EXP-FORMAL + 관련 DEMO 관측 |
| 감각적인 편집물 | 사진 crop, 비대칭 제목, 주제별 editorial motif | 사진 rail, 주장의 위계, 연결 문단 | DEMO-EXP-EDITORIAL |
| 과감한 제안서 | 독창적 시각 비유, mixed media, 과감한 scale | 연결 장면+국소 설명, 여러 단에 걸친 원고/사진 흐름, 실제 근거/조건 | DEMO-EXP-EXPRESSIVE |
| 몰입감 있는 쇼케이스 | 개념 세계, 촉각적 조형, 장면 전환 | 장면 안팎의 읽는 순서, 대비가 명확한 native 설명, 주·보조 이미지와 조건 | DEMO-EXP-SHOWCASE |
| 독창적이지만 차분하게 | 정교한 paper metaphor, muted palette | 전체/국소 확대의 대응, 차분한 문단과 native 표시, 세밀한 공간 관계 | DEMO-EXP-QUIET-IMAGINATIVE |
| 익숙하지만 풍부하게 | 정통 grid+강한 이미지/색 대비 | 전통적인 정보 구조+선명한 영역 구분 | DEMO-EXP-RICH-CLASSIC |

새로운 핵심 구도에서는 표현에 맞는 독립 레퍼런스 1–2개와 필요한 DEMO 근거 사례를 함께 선택한다. 고창의성 요청은 과감한/교차축 레퍼런스를 실제로 보고, 보수적인 DEMO 표지 하나만 선택하고 끝내지 않는다. 먼저 `select_creative_reference.py --summary --creativity expressive --intensity subtle --family cover` 또는 `--summary --preset showcase --family evidence`로 최대 3개의 ID·용도를 가볍게 고른다. 선택한 사례의 실제 적용 관계와 페이지가 필요할 때에만 상세 전체 결과와 연결된 예시를 읽는다. 썸네일만으로 상세 본문 가독성을 판단하지 않는다.

복제할 것은 샘플 이미지나 문구가 아니라 **구도와 의미의 관계**다. 새로운 프로젝트의 주제·근거·문장·실제 assets로 다시 설계한다. 샘플의 산업/풍경·추상 portal을 모든 문서에 반복하지 않는다. DEMO ESG에는 선형 표지, 대각선 object, full-scene 사례 등 창의적 공간 관계가 이미 있다. 저장된 실제 관측의 출처와 관찰 범위를 보존하며 새 독립 예시를 공식 ESG 원본처럼 기록하지 않는다.

## 디자인과 이미지 생성에 전달

본문은 [body-composition.md](body-composition.md)와 [독립 본문 4종](../assets/body-compositions/index.html)을 함께 사용한다. 창의성은 본문 질문을 설명하는 구도와 이미지 역할에도 적용한다. 표지의 이미지·색감만 바꾸고 본문을 기존 분할 양식으로 고정하지 않는다. select_creative_reference.py --preset expressive --body-only --family process로 표지와 별도로 본문 관계를 찾는다. 본문의 사진 면적이 작아도 국소 연결·확대·원고 흐름에서 높은 창의성을 표현할 수 있다.

기존 `content/brief.json.design_expression`에 유효한 preset·두 축·선택 근거만 기록한다. page map에는 이번 페이지가 표현하는 독자 질문, dominant element, reading sequence, 적용한 reference 관계를 짧게 둔다. asset의 `production.expression`에는 이 record 또는 brief 참조를 전달한다. 새로운 registry를 만들지 않는다.

과감한/실험적 선택의 큰 visual이 유용한 경우 image generation을 적극 사용한다. 생성 요청에는 현재 의미, 독창적인 비유/공간 관계, 선택한 질감/빛, 최종 frame/crop/quiet zone, editable overlays를 구체화한다. “corporate, clean, safe, minimal” 같은 관습적인 prompt가 선택된 과감함을 지우지 않게 한다. 생성 이미지/복합 사진/타이포/벡터를 목적에 맞게 혼합하고, full scene을 centered stock object로 축소하지 않는다. SVG로 충분한 정확한 표/간단한 도형은 native로 만든다.

기존 금지는 무조건적인 스타일 금지가 아니다. 과도한 수치, 반복 카드, glossy 3D, gradient를 **자동 기본값**으로 삼지 않는다는 뜻이다. 사용자와 목적에 맞는 질감·3D·강한 color plane·실험적 비대칭은 선택할 수 있다. 공식 로고·패키지·사실 사진의 정체성, 정확한 수치/관계, 편집 가능한 중요 텍스트는 유지한다. 실재로 보일 수 있는 생성 장면은 가까운 caption에서 concept임을 알린다.

## 표지뿐 아니라 본문을 검수

선택한 두 축이 표지/챕터/대표 상세 본문에서 실제로 드러나는지 시각적으로 확인한다. 색만 바꾼 같은 구도, 과감함을 고른 뒤 공식형으로 되돌아간 결과, 이미지에 중요한 텍스트를 구운 결과는 수정한다. 자료의 출처·비교 조건·책임·예외를 삭제하거나 글자를 작게 만들어 화려함을 확보하지 않는다. 이미지 하나가 모든 페이지의 반복 장식이 되지 않게 한다.

office print에서는 인쇄 profile의 여백/소모/읽기 조건을 유지하면서 비유·crop·타이포 관계로 창의성을 표현한다. 인쇄와 immersive 화면 연출이 실제로 충돌하면 현재 사용처 안에서 변형한 이유를 알리고, 필요 시 별도 화면 버전을 권한다. 파일 기술 경로와 표현 수준은 별개다. 구조적 검사, 실제 시각 검토, export 확인과 사용자 수락을 분리한다.
