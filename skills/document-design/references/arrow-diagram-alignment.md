# 화살표 도식의 항목별 가운데 정렬

신규 화살표 도식에서는 화살표 사이의 각 항목을 독립된 카드 영역으로 본다. 첫 항목·중앙 항목·마지막 항목 모두 **자기 영역 안에서 가운데 정렬**한다. 제목뿐 아니라 그 항목에 붙은 설명도 같은 중심을 따른다. 카드 배경이나 테두리를 반드시 추가한다는 뜻은 아니다.

동등한 단계는 같은 폭을 배정하고, 화살표는 항목과 분리된 연결 영역에 둔다. 문구 길이에 따른 양끝 배치나 도식 전체의 `justify-content:space-between`만으로 항목을 정렬하지 않는다. 길어진 한일 문구는 자기 영역 안에서 자연스럽게 줄바꿈하고 각 줄을 가운데 정렬한다. 한 항목의 문구가 길면 필요한 높이와 인접 간격을 다시 확인한다.

다음은 가로 3단계의 로컬 구현 예시다. 단계·화살표 쌍을 추가하면 같은 방식으로 4단계 이상을 구성할 수 있다. 색·글꼴·크기·간격은 현재 문서의 승인된 디자인 값을 그대로 쓴다. 특정 보고서의 경로나 문구를 고정하지 않는다.

```css
.demo-arrow-flow {
  display: flex;
  align-items: center;
  width: 100%;
}
.demo-arrow-step {
  flex: 1 1 0;
  min-width: 0;
  text-align: center;
}
.demo-arrow-step > p {
  margin: 0;
  text-align: center;
  overflow-wrap: break-word;
}
.demo-arrow-link {
  flex: 0 0 2em;
  text-align: center;
}
```

```html
<div class="demo-arrow-flow">
  <div class="demo-arrow-step"><p>入力条件</p></div>
  <span class="demo-arrow-link">→</span>
  <div class="demo-arrow-step"><p>構造化</p></div>
  <span class="demo-arrow-link">→</span>
  <div class="demo-arrow-step"><p>編集可能な出力</p></div>
</div>
```

설명이 필요하면 각 `.demo-arrow-step` 안에 별도의 `<p>`로 둔다. 화살표는 인접 항목의 텍스트 상자에 합치지 않는다. 세로·분기 도식도 각 노드의 자체 영역을 기준으로 같은 가운데 정렬을 적용하되 관계와 읽는 순서는 보존한다.

HTML에서는 항목 폭, 각 줄의 중심, 화살표와의 간격을 확인한다. PPTX에서는 항목 문구가 별도 편집 가능한 텍스트로 남고 단락의 가운데 정렬과 영역 중심이 보존되는지 검사한다. 관련 페이지의 실제 PowerPoint 출력에서 긴 문구의 줄바꿈·잘림도 확인한다. 기존 본문·표·머리말·꼬리말의 정렬이나 채택 양식은 해당 수정 요청이 없는 한 바꾸지 않는다.
