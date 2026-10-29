(function(){
  'use strict';
  const root=document.getElementById('document-studio-intake-v3');
  const cfg=JSON.parse(root.querySelector('#demo-intake-config').textContent);
  const fields=Object.keys(cfg.contract.fields), language=cfg.language;
  const $=id=>root.querySelector('#'+id);
  const text=(ko,ja)=>language==='ja'?ja:ko;
  let index=0, values=Object.assign({},cfg.prefills), delegated=[], use=cfg.use||'', canvas=cfg.canvas||'', submitted=false;
  let design=Object.assign({},cfg.design_preferences||{});
  const designKeys=['creativity','visual_intensity'];
  function restoreDesign(value){
    if(!value||typeof value!=='object'||Array.isArray(value))return;
    const restored={};
    if(value.preset==='auto'||cfg.expression.presets[value.preset])restored.preset=value.preset;
    designKeys.forEach(key=>{if(cfg.expression.axes[key].choices.some(c=>c.value===value[key]))restored[key]=value[key];});
    design=restored;
  }
  function effectiveDesign(){const preset=cfg.expression.presets[design.preset]||cfg.expression.presets[cfg.expression.default_preset];return Object.fromEntries(designKeys.map(key=>[key,design[key]||preset[key]]));}
  function renderDesign(){
    const chosen=effectiveDesign();$('demo-expression-wrap').hidden=fields[index]!=='output_format';
    $('demo-expression-presets').replaceChildren();
    Object.entries(cfg.expression.presets).forEach(([key,preset])=>{const button=document.createElement('button');button.type='button';button.dataset.preset=key;
      const title=document.createElement('strong');title.textContent=preset[language];const desc=document.createElement('span');desc.textContent=preset['description_'+language];button.append(title,desc);
      button.setAttribute('aria-pressed',String(design.preset===key&&designKeys.every(a=>chosen[a]===preset[a])));
      button.addEventListener('click',()=>{design={preset:key};submitted=false;save();render();});$('demo-expression-presets').append(button);});
    $('demo-expression-auto').setAttribute('aria-pressed',String(!Object.keys(design).length||design.preset==='auto'));
    $('demo-creativity').value=chosen.creativity;$('demo-intensity').value=chosen.visual_intensity;
  }
  const labelFor=(key,value)=>{const item=cfg.contract.fields[key].choices.find(item=>item.value===value);return item?item[language]:value;};
  const relevantChoices=key=>{
    const choices=cfg.contract.fields[key].choices;
    if(key!=='output_format')return choices;
    return choices.filter(item=>item.value==='PPTX'||item.value.split(' + ').every(format=>cfg.verified_formats.includes(format)));
  };
  function currentPayload(){const payload={schema_version:cfg.contract.schema_version,fields:values,use:use||undefined,canvas:canvas||undefined,notes:$('demo-notes').value,conversation_language:language,delegated_fields:delegated};if(Object.keys(design).length)payload.design_preferences=design;return payload;}
  function restore(saved){
    if(!saved||saved.schema_version!=='1.0'||!saved.fields||typeof saved.fields!=='object')return;
    for(const key of fields){const val=saved.fields[key],field=cfg.contract.fields[key];if(typeof val!=='string'||val.length>1500||!val.trim())continue;if(!field.custom&&key!=='output_format'&&!field.choices.some(item=>item.value===val))continue;if(key==='final_language'&&!/^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*(?:\+[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*)*$/.test(val))continue;values[key]=val;}
    if(cfg.contract.use_choices.some(item=>item.value===saved.use))use=saved.use;
    if(cfg.contract.canvas_choices.some(item=>item.value===saved.canvas))canvas=saved.canvas;
    if(typeof saved.notes==='string')$('demo-notes').value=saved.notes.slice(0,6000);
    if(Array.isArray(saved.delegated_fields))delegated=saved.delegated_fields.filter(key=>cfg.contract.fields[key]&&cfg.contract.fields[key].delegatable);
    if(saved.design_preferences)restoreDesign(saved.design_preferences);
  }
  function save(){
    const host=window.openai;
    if(host&&typeof host.setWidgetState==='function'){
      try{Promise.resolve(host.setWidgetState({modelContent:{intake_draft:currentPayload(),submitted:false},privateContent:{step:index}})).catch(()=>{});}catch(error){}
    }
  }
  function summary(){
    $('demo-summary').replaceChildren();
    fields.forEach(key=>{const dt=document.createElement('dt');dt.textContent=cfg.contract.fields[key]['label_'+language];const dd=document.createElement('dd');const recommended=cfg.contract.startup_policy.defaults[key];dd.textContent=values[key]?labelFor(key,values[key]):delegated.includes(key)?text('추천을 맡김','おすすめを依頼'):labelFor(key,recommended==='$conversation_language'?language:recommended)+text(' · 잠정 추천',' · 仮のおすすめ');$('demo-summary').append(dt,dd);});
    const dt=document.createElement('dt');dt.textContent=text('사용처','用途');const dd=document.createElement('dd');dd.textContent=cfg.contract.use_choices.find(item=>item.value===(use||cfg.contract.startup_policy.default_use))[language]+(!use?text(' · 잠정 추천',' · 仮のおすすめ'):'');$('demo-summary').append(dt,dd);
    const chosen=effectiveDesign();
    designKeys.forEach(key=>{const dt=document.createElement('dt');dt.textContent=cfg.expression.axes[key]['label_'+language];const dd=document.createElement('dd');dd.textContent=cfg.expression.axes[key].choices.find(c=>c.value===chosen[key])[language]+(!Object.keys(design).length||design.preset==='auto'?text(' · 추천에 맡김',' · おすすめに委任'):'');$('demo-summary').append(dt,dd);});
  }
  function select(key,value,isDelegation){
    if(isDelegation){delete values[key];if(!delegated.includes(key))delegated.push(key);}else{values[key]=value;delegated=delegated.filter(item=>item!==key);}
    submitted=false;$('demo-error').textContent='';save();render();
  }
  function canContinue(){return true;}
  function render(){
    const key=fields[index], field=cfg.contract.fields[key];
    $('demo-step').textContent=text('선택','選択')+' '+(index+1)+' / '+fields.length;
    $('demo-field-title').textContent=field['label_'+language];
    $('demo-field-help').textContent=cfg.prefills[key]?text('기존 작업 조건을 이어받았습니다. 바꿀 부분만 선택하세요.','既存の作業条件を引き継いでいます。変更する項目だけ選んでください。'):key==='output_format'?text('기본은 수정 가능한 PowerPoint입니다. 다른 형식이 필요하면 선택하거나 입력하세요. 실제 파일 제공은 제작 시 확인합니다.','標準は編集可能なPowerPointです。別の形式が必要な場合は選択・入力してください。実際の提供可否は制作時に確認します。'):text('바꿀 항목만 선택하세요. 건너뛰면 잠정 추천값으로 시작합니다. 자료는 채팅에 함께 첨부하세요.','変える項目だけ選んでください。省略すると仮のおすすめで始めます。資料はチャットに添付してください。');
    $('demo-choices').replaceChildren();
    relevantChoices(key).forEach(choice=>{const button=document.createElement('button');button.type='button';button.textContent=choice[language];button.setAttribute('aria-pressed',String(values[key]===choice.value));button.addEventListener('click',()=>select(key,choice.value,false));$('demo-choices').append(button);});
    if(field.delegatable){const button=document.createElement('button');button.type='button';button.textContent=text('추천을 맡기기','おすすめを依頼');button.setAttribute('aria-pressed',String(delegated.includes(key)));button.addEventListener('click',()=>select(key,'',true));$('demo-choices').append(button);}
    $('demo-custom-wrap').hidden=!(field.custom||key==='output_format');$('demo-custom').value=values[key]||'';
    $('demo-use-wrap').hidden=key!=='output_format';$('demo-use').value=use;$('demo-canvas').value=canvas;
    $('demo-back').disabled=index===0;$('demo-next').disabled=!canContinue();$('demo-next').textContent=index===fields.length-1?text('선택 요약 확인','選択内容を確認'):values[key]||delegated.includes(key)?text('다음','次へ'):text('추천으로 다음','おすすめで次へ');summary();
    renderDesign();$('demo-final').hidden=true;
  }
  function finalize(){
    const payload=currentPayload();$('demo-payload').value=JSON.stringify(payload,null,2);$('demo-final').hidden=false;
    const callback=window.openai&&typeof window.openai.sendFollowUpMessage==='function';
    $('demo-submit').hidden=!callback;$('demo-submit').disabled=false;
    $('demo-transfer-note').textContent=callback?text('아래 버튼으로 요약을 채팅에 보내면 제작 요청을 시작할 수 있습니다. 화면의 선택만으로는 아직 제출되지 않았습니다.','下のボタンから要約をチャットに送ると、制作を依頼できます。画面での選択だけでは未提出です。'):text('이 화면은 채팅에 자동 전송하지 않습니다. JSON을 내려받아 채팅에 첨부하거나 아래 내용을 복사해 보내세요. 자료도 함께 첨부하세요.','この画面からチャットへ自動送信はしません。JSONを保存して添付するか、下の内容をコピーして送信してください。資料も併せて添付してください。');
    $('demo-submit-status').textContent='';
  }
  $('demo-intake-intro').textContent=text('요청과 자료가 있으면 바로 시작합니다. 필요한 조건만 조정할 수 있습니다.','依頼と資料があればすぐ始められます。必要な条件だけ調整できます。');
  $('demo-start-recommended').textContent=text('추천으로 바로 시작','おすすめで始める');
  $('demo-quick-help').textContent=text('선택하지 않은 필수 항목은 채팅에서 이어서 확인합니다. 추천은 답변 없이 확정하지 않습니다.','未回答の必須項目はチャットで確認します。回答なしでおすすめを確定しません。');
  $('demo-start-recommended').addEventListener('click',()=>{summary();finalize();save();$('demo-final').scrollIntoView({block:'start',behavior:'smooth'});});
  $('demo-expression-title').textContent=text('원하는 문서의 느낌 (선택)','資料の雰囲気（任意）');
  $('demo-expression-help').textContent=text('느낌을 고르거나 추천에 맡기세요. 창의성과 화려함은 각각 바꿀 수 있습니다.','雰囲気を選ぶか、おすすめにお任せください。発想の大胆さと華やかさは別々に調整できます。');
  $('demo-expression-auto').textContent=text('느낌은 추천에 맡기기','雰囲気はおすすめに任せる');
  $('demo-expression-detail-label').textContent=text('창의성과 화려함을 따로 조절','大胆さと華やかさを個別に調整');
  [['creativity','demo-creativity','demo-creativity-label'],['visual_intensity','demo-intensity','demo-intensity-label']].forEach(([key,id,label])=>{const axis=cfg.expression.axes[key];$(label).textContent=axis['label_'+language];axis.choices.forEach(choice=>{const option=document.createElement('option');option.value=choice.value;option.textContent=choice[language];$(id).append(option);});$(id).addEventListener('change',()=>{design={...effectiveDesign(),[key]:$(id).value};submitted=false;save();render();});});
  $('demo-expression-auto').addEventListener('click',()=>{design={preset:'auto'};submitted=false;save();render();});
  $('demo-summary-title').textContent=text('현재 선택사항','現在の選択');$('demo-custom-label').textContent=text('직접 입력','直接入力');$('demo-custom-apply').textContent=text('입력한 내용 적용','入力内容を適用');
  $('demo-use-label').textContent=text('어떻게 사용할까요?','どのように使いますか？');const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=text('사용처를 선택하세요','用途を選んでください');$('demo-use').append(placeholder);cfg.contract.use_choices.forEach(item=>{const option=document.createElement('option');option.value=item.value;option.textContent=item[language];$('demo-use').append(option);});
  $('demo-canvas-label').textContent=text('판형·방향','判型・向き');const blankCanvas=document.createElement('option');blankCanvas.value='';blankCanvas.textContent=text('판형을 선택하세요','判型を選んでください');$('demo-canvas').append(blankCanvas);cfg.contract.canvas_choices.forEach(item=>{const option=document.createElement('option');option.value=item.value;option.textContent=item[language];$('demo-canvas').append(option);});
  $('demo-canvas').addEventListener('change',()=>{canvas=$('demo-canvas').value;save();render();});
  $('demo-notes-label').textContent=text('꼭 유지할 내용·추가 요청','必ず残す内容・追加依頼');$('demo-back').textContent=text('이전','戻る');$('demo-final-title').textContent=text('제작 요청 요약','制作依頼の要約');$('demo-submit').textContent=text('요약을 보내고 제작 시작','要約を送って制作を開始');$('demo-download').textContent=text('요약 JSON 저장','要約JSONを保存');$('demo-payload-label').textContent=text('채팅에 보낼 요약','チャットに送る要約');$('demo-intake-footer').textContent=text('처음부터 다시 물을 필요 없이 기존 자료와 정한 조건을 이어받습니다. 파일 제공과 사용자 수락은 별도로 확인합니다.','既存の資料と確認済みの条件を引き継ぎます。ファイルの提供と利用者の承認は別々に確認します。');
  $('demo-custom-apply').addEventListener('click',()=>{const value=$('demo-custom').value.trim();if(!value){$('demo-error').textContent=text('내용을 입력하세요.','内容を入力してください。');return;}const key=fields[index];if(key==='final_language'&&!/^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*(?:\+[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*)*$/.test(value)){$('demo-error').textContent=text('언어 코드를 입력하세요. 예: ja, ko, ja+ko','言語コードを入力してください。例：ja、ko、ja+ko');return;}select(key,value,false);});
  $('demo-use').addEventListener('change',()=>{use=$('demo-use').value;save();render();});$('demo-notes').addEventListener('input',()=>{save();if(!$('demo-final').hidden)$('demo-payload').value=JSON.stringify(currentPayload(),null,2);});
  $('demo-back').addEventListener('click',()=>{index=Math.max(0,index-1);render();});$('demo-next').addEventListener('click',()=>{if(!canContinue())return;if(index===fields.length-1)finalize();else{index++;render();}save();});
  $('demo-download').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(currentPayload(),null,2)],{type:'application/json;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download='document-studio-brief.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('demo-submit-status').textContent=text('요약 파일 저장을 요청했습니다. 다운로드가 되지 않으면 아래 내용을 복사해 채팅으로 보내세요.','要約ファイルの保存を依頼しました。ダウンロードできない場合は、下の内容をコピーしてチャットに送ってください。');});
  $('demo-submit').addEventListener('click',async()=>{if(submitted)return;const callback=window.openai&&window.openai.sendFollowUpMessage;if(typeof callback!=='function'){finalize();return;}$('demo-submit').disabled=true;try{const payload=JSON.stringify(currentPayload());if(payload.length>14000)throw new Error('Brief exceeds callback size limit');await callback.call(window.openai,{prompt:text('Document Studio 문서 제작 요청입니다. 아래 사용자 제출 brief를 검증하고 첨부 자료와 함께 적용해 제작을 진행하세요. 현재 명시값과 기존 조건을 보존하고 미응답 필수 항목은 보존하고 남은 선택만 채팅에서 확인하세요. 추천값을 답변 없이 확정하지 마세요.\n','Document Studio資料作成の依頼です。以下の利用者提出briefを検証し、添付資料と併せて適用してください。現在の明示条件と既存条件を保持し、未回答の必須項目を保持し、残った選択だけをチャットで確認してください。回答なしでおすすめを確定しないでください。\n')+payload,title:text('이 요약으로 제작을 요청합니다','この要約で制作を依頼します')});submitted=true;$('demo-submit-status').textContent=text('채팅 전송을 요청했습니다. 채팅에 실제 도착한 요약을 확인한 후 제작합니다.','チャットへの送信を依頼しました。実際に届いた要約を確認してから制作します。');}catch(error){$('demo-submit-status').textContent=text('전송되지 않았습니다. 요약을 저장하거나 복사해 채팅으로 보내세요.','送信できませんでした。要約を保存するかコピーして、チャットに送ってください。');$('demo-submit').disabled=false;}});
  try{if(window.openai&&window.openai.widgetState)restore(window.openai.widgetState.modelContent?.intake_draft);}catch(error){}
  window.addEventListener('openai:set_globals',event=>{const state=event.detail?.globals?.widgetState;if(state){restore(state.modelContent?.intake_draft);render();}});
  render();
})();
