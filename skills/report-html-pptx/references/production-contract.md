# 누락 없이 다음 작업으로 이어간다

v4의 단계 범위·증거·완료 상태는 [workflow-execution.md](workflow-execution.md)를 따른다. 원샷과 부분 수정은 같은 프로젝트 파일을 재사용하며, 단계 완료와 문서 QA·사용자 수락을 합치지 않는다. prepare는 실제 추천·출처 관측을 함께 받을 수 있다. 새 workflow가 있는 프로젝트는 입력·출력 해시와 확인한 범위를 묶은 단계 기록을 사용한다.

이 계약은 **실제 조판·파일 제작에 진입한 문서**에 적용한다. 주제 조사·강의 논지·목차·슬라이드별 원고·발표 대본만 요청한 editorial-first 단계에는 판형·파일 확장자 결정을 선행 조건으로 강제하지 않는다. 해당 단계의 검증된 원고가 실제 HTML/PPTX 제작으로 넘어올 때 정해지지 않은 제작 필드만 확인하고 그때 prepare를 실행한다. 이미 확정된 독자·목적·원고·출처는 재사용한다.

새 문서는 여섯 핵심 선택과 **사용처·판형**을 별도로 해결한다. 파일 확장자는 판형이나 발표 용도가 아니다. 이미 명시된 값은 재사용하고 누락만 한 묶음으로 묻는다. 부분 답변과 미응답을 기존 brief에 이어 쓰며 AI가 임의로 넣은 값을 사용자 확정으로 바꾸지 않는다.

## 짧은 실행 정보

새 문서에서는 집필·구성 전에 `scripts/production_contract.py prepare --submission <선택 JSON> --brief <기존 또는 새 brief>`를 실행한다. fields에는 기존 여섯 값, 최상위 use와 canvas에는 해결한 사용처·판형을 넣는다. 미응답 값은 넣지 않는다. choice_origins에 실제 요청·답변·채택한 brief 위치를 보존한다. 항목별 및 명시적인 8개 묶음 위임의 판정 규칙은 [intake-and-collaboration.md](intake-and-collaboration.md)에 단일 정의한다. 화면 추천·침묵·‘계속’은 답변이 아니다.

prepare/status는 누락·추천·다음 허용 작업과 선택 토큰만 짧게 반환한다. 제작 가능 전에는 자료 대조 등 독립 작업을 계속한다. 전체 폴더 구조나 레퍼런스 전체를 먼저 만들거나 읽을 필요가 없다. 기존 brief는 `status --brief <brief> --stage writing|design|export`로 이어받는다. 같은 선택을 다시 추정하지 않는다.

사용처는 reading/live/office_print/template_edit, 판형은 a4-portrait/a4-landscape/widescreen/esg-landscape다. 읽기용 계획서는 A4 세로를 추천하되 채택 없이 확정하지 않는다. 판형·방향이 명시된 원본 양식은 그 값과 실제 위치를 확인해 재사용한다. 사용자의 다른 판형은 그대로 유지할 수 있는 실제 경로를 확인하고 임의로 표준 판형에 끼워 맞추지 않는다.

원샷은 선택 해결 뒤 내부 검토를 거쳐 완성한다. ‘디자인 먼저 검토’는 collaborative + review_checkpoint=design으로 보존한다. 사용자 응답을 기다리는 검토 지점은 interaction.pending_user_review=true로 기록하고, 실제 응답 뒤에만 해제한다. 원샷에 사용자 중간 승인 단계를 추가하지 않는다.

## 토큰과 레퍼런스를 결과에 전달

디자인은 status가 반환한 profile/판형/글꼴/바탕/타이포/여백·간격과 선택 표현을 사용한다. 토큰 CSS를 실제 HTML에 연결한다. data-design-profile은 실제 페이지에 붙이고 data-demo-content-frame은 실제 내용 영역에, data-demo-role=body는 대표 본문에, data-demo-grid는 검사할 실제 그리드에 붙인다. 변수만 선언한 것은 적용 증거가 아니다.

예시 1–3개에서 필요한 공간 관계를 골라 기존 페이지 맵에 reader_question / reference_id / adopted_relationship / implementation 위치를 남긴다. 표지와 가장 정보가 많은 본문을 실제 원고로 만들어 내부 검토한 뒤 확장한다. 관계도가 핵심이면 그것도 포함한다. 색 유사도나 예시 ID만으로 적용 완료를 주장하지 않는다. 카드 반복·배열 리듬과 실제 설명 관계는 시각 검토가 맡는다.

`audit --brief <brief> --html <현재 HTML> --out <project>/qa/design-contract.json --browser-path <필요할 때만 기존 브라우저>`는 브라우저의 실제 크기·CSS·사용 글꼴·여백·본문 크기·그리드 간격을 측정한다. 실제 글리프의 플랫폼 글꼴을 확인하므로 글꼴 이름만 적은 대체 표시를 통과시키지 않는다. 구조 검사와 별개이며 원고나 시각적 완성도 합격을 뜻하지 않는다.

사진 표지는 바탕색과 본문 크기 검사를 적용하지 않는다. 의미 있는 다른 바탕·글꼴·본문 크기·여백·간격은 brief.design.deviations에 page(숫자 또는 *), property(font/paper/body_pt/margin_x_px/grid_gap_px), value, status(intentional/user_accepted/template_preserved), reason, origin을 기록한다. 실제로 채택한 디자인 의도나 보존할 원본을 가리킨다. 발견한 오류를 숨기는 포괄 예외를 만들지 않는다. 판형은 디자인 예외로 바꾸지 못한다.

## 완료 증거

qa/skill-use.json의 applied 항목은 skill, status(planned/in_progress/verified/not_needed), 적용 job·scope를 기록한다. verified의 evidence는 [{path: 프로젝트 상대 경로, sha256: 실제 파일 해시}]이며 실제 존재해야 한다. 아직 없는 PPTX·검토 파일은 planned로만 기록한다. 새 전체 문서는 architecture/writing/design 적용을 확인하고 최종 PPTX에는 export 적용도 확인한다. 조건부 역할은 실제 이유를 보존한다.

기존 project_state gate에 현재 선택, 디자인 실측, 실제 역할 적용 증거, 최종 PPTX 판형 대조가 연결된다. 원고·띄어쓰기·의미 단위 줄내림·시각 검토·출력 검토의 기존 증거도 모두 필요하다. HTML/CSS/글꼴/brief/검사기 변경은 해당 실측 증거를 오래된 것으로 만든다. 자동 passed 문구만으로 완료하지 않는다.

변환 CLI와 함수는 DEMO 프로젝트의 현재 brief·디자인·HTML 검수 상태를 확인한다. 이미 검토한 HTML만 변환하는 제한된 요청에는 --reviewed-html-only를 명시할 수 있다. 새 전체 문서의 질문·디자인·검수 누락을 피하는 옵션으로 사용하지 않는다. 원본의 보호 작업 사본은 바이트가 같을 때만 같은 실측을 재사용하고, 수정된 사본은 새 검토가 필요하다.

이 기능은 패키지의 검사·변환 경로다. 호스트 모델의 모든 도구 호출을 강제하는 hook, 모델 재학습 또는 Luna 새 채팅 검증은 아니다.
