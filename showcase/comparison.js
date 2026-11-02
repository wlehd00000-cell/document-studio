(() => {
const data=window.DocumentStudioComparison,root=document.getElementById('comparison-root');if(!data||!root)return;
const params=new URLSearchParams(location.search),profiles=data.profiles;
const validProfile=id=>profiles.some(p=>p.id===id);
const state={lang:params.get('lang')==='ko'?'ko':'ja',page:params.get('page')==='2'?2:1,left:validProfile(params.get('left'))?params.get('left'):'mono',right:validProfile(params.get('right'))?params.get('right'):'aligned',mode:params.get('mode')==='focus'?'focus':params.get('mode')==='compare'?'compare':matchMedia('(min-width:1000px)').matches?'compare':'focus',zoom:params.get('zoom')==='100'?'100':'fit',guides:params.get('guides')==='1'};
let renderVersion=0,resizeObserver;
if('scrollRestoration' in history)history.scrollRestoration='manual';
const esc=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const profile=id=>profiles.find(p=>p.id===id),copy=()=>data.copy[state.lang];
const block=(name,title,body)=>`<section class="c-block c-${name}" data-content-region="${name}"><h3 data-fact="${name}-heading">${esc(title)}</h3>${body}</section>`;
function content(page){const t=copy();if(page===1){return block('ask',t.askTitle,`<p data-fact="ask">${esc(t.ask)}</p>`)+block('scope',t.scopeTitle,`<p data-fact="scope">${esc(t.scope)}</p>`)+block('budget',t.budgetTitle,`<table data-fact="budget"><caption>${esc(t.moneyNote)}</caption><thead><tr><th scope="col">${esc(t.item)}</th><th scope="col">${esc(t.amount)}</th></tr></thead><tbody>${data.amounts.map((n,i)=>`<tr><th scope="row">${esc(t.budgetItems[i])}</th><td class="c-number">${n.toLocaleString('en-US')}</td></tr>`).join('')}</tbody><tfoot><tr><th scope="row">${esc(t.total)}</th><td class="c-number">${data.amounts.reduce((a,b)=>a+b,0).toLocaleString('en-US')}</td></tr></tfoot></table>`)+block('conditions',t.conditionTitle,`<p data-fact="conditions">${esc(t.conditions)}</p>`);}
return block('target',t.targetTitle,`<div class="c-chart" role="img" aria-label="${esc(t.targetTitle+': '+data.targets.map((n,i)=>t.weeks[i]+' '+n+t.ui.unit).join(', '))}">${data.targets.map((n,i)=>`<div class="c-chart-col"><div class="c-chart-bar" style="--bar-height:${n/50*100}%"><b>${n}</b></div><span>${esc(t.weeks[i])}</span></div>`).join('')}</div><p class="c-target-note" data-fact="targets">${esc(t.targetNote)}</p>`)+block('plan',t.planTitle,`<dl data-fact="plan">${t.plan.map((text,i)=>`<div class="c-plan-row"><dt>${esc(t.planLabels[i])}</dt><dd>${esc(text)}</dd></div>`).join('')}</dl>`)+block('criteria',t.criteriaTitle,`<p data-fact="criteria">${esc(t.criteria)}</p>`)+block('decision',t.decisionTitle,`<p data-fact="decision">${esc(t.decision)}</p>`)+`<section class="c-block c-limit" data-content-region="limit"><p data-fact="limit">${esc(t.limit)}</p></section>`;}
function paper(p,page,namespace){const t=copy();return `<article class="contract-page preset-${p.id} c-page-${page}" lang="${state.lang}" data-profile="${p.id}" data-page="${page}" aria-labelledby="${namespace}-title" style="width:${p.width}mm;height:${p.height}mm;--c-margin:${p.margin}mm;--c-line:${p.line};--c-gap:${p.gap}mm;--c-title-size:${p.titlePt}pt"><div class="contract-frame"><header class="c-head"><strong>MOA RETAIL</strong><span>${esc(t.company)} · ${data.version}</span></header><div class="c-title"><span class="c-kicker">OPERATIONS / FICTIONAL PILOT · ${String(page).padStart(2,'0')}</span><h2 id="${namespace}-title" data-fact="title">${esc(t.titles[page-1])}</h2><p data-fact="subtitle">${esc(t.subtitles[page-1])}</p></div><div class="c-body">${content(page)}${p.image&&page===1?`<figure class="c-art" data-content-region="art"><img src="assets/refill-concept.png" alt="${esc(t.imageNote)}" width="1536" height="1024"><figcaption>${esc(t.imageNote)}</figcaption></figure>`:''}</div><footer class="c-foot"><span>${esc(t.fiction)}</span><span>${String(page).padStart(2,'0')} / 02</span></footer></div><div class="rule-frame" aria-hidden="true"><span>${p.margin}mm</span></div></article>`;}
function choices(selected){return profiles.map(p=>`<option value="${p.id}"${p.id===selected?' selected':''}>${esc(p.name[state.lang])}</option>`).join('');}
function selectedProfiles(){return state.mode==='focus'?[profile(state.left)]:[profile(state.left),profile(state.right)];}
function card(p,index){const u=copy().ui;return `<section class="sample-card" data-sample="${p.id}"><header class="sample-head"><div><h2>${esc(p.name[state.lang])}</h2><p>${p.width} × ${p.height}mm · ${p.margin}mm · ${p.bodyPt}pt / ${p.line}</p></div><button type="button" data-enlarge="${p.id}">${esc(state.mode==='compare'?u.enlarge:u.other)}</button></header><div class="sheet-viewport"><div class="sheet-size">${paper(p,state.page,`visible-${index}-${p.id}-${state.page}`)}</div></div><div class="sample-status" data-status="${p.id}" role="status">${esc(u.pending)}</div></section>`;}
function auditCard(p){const u=copy().ui;return `<section class="audit-card" data-audit="${p.id}"><h3>${esc(p.name[state.lang])}</h3><p>${esc(p.description[state.lang])} · ${esc(u.measuredPages)}<span class="palette-dots" aria-label="${esc(u.color)}">${p.palette.map(c=>`<i style="--dot:${c}"></i>`).join('')}</span>${p.image?esc(u.paletteImage):esc(u.photoOff)}</p><table><thead><tr><th>${esc(u.before)}</th><th>${esc(u.measured)}</th><th>${esc(u.check)}</th></tr></thead><tbody><tr><td colspan="3">${esc(u.pending)}</td></tr></tbody></table></section>`;}
function updateUrl(){if((/\/compare(?:\.html)?\/?$/).test(location.pathname)){const url=new URL(location.href);for(const key of ['lang','page','left','right','mode','zoom'])url.searchParams.set(key,String(state[key]));url.searchParams.set('guides',state.guides?'1':'0');history.replaceState(null,'',url);}}
function fitSheets(){root.querySelectorAll('.sheet-size').forEach(holder=>{const page=holder.querySelector('.contract-page'),viewport=holder.parentElement,width=parseFloat(getComputedStyle(page).width),height=parseFloat(getComputedStyle(page).height);const scale=state.zoom==='100'?1:Math.min(1,viewport.clientWidth/width);holder.style.width=`${width*scale}px`;holder.style.height=`${height*scale}px`;page.style.transform=`scale(${scale})`;});}
function render(){const active=document.activeElement?.id,u=copy().ui,items=selectedProfiles(),version=++renderVersion;document.documentElement.lang=state.lang;root.className=state.guides?'show-contract-guides':'';root.innerHTML=`<header class="comparison-header"><div><a href="${state.lang==='ja'?'index.html':'ko.html'}">← ${esc(u.back)}</a><strong>Document Studio</strong></div><div class="comparison-buttons comparison-language" role="group" aria-label="${esc(u.language)}"><button id="lang-ja" type="button" data-language="ja" aria-pressed="${state.lang==='ja'}">日本語</button><button id="lang-ko" type="button" data-language="ko" aria-pressed="${state.lang==='ko'}">한국어</button><a href="https://github.com/wlehd00000-cell/document-studio">GitHub ↗</a></div></header><main class="comparison-shell"><section class="comparison-intro"><div class="eyebrow">${u.eyebrow}</div><h1>${esc(u.title)}</h1><p>${esc(u.lead)}</p><small>${esc(u.source)}</small></section><div class="comparison-controls"><div class="comparison-control-group"><span>${esc(u.page)}</span><div class="comparison-buttons"><button id="page-1" type="button" data-page="1" aria-pressed="${state.page===1}">${esc(u.p1)}</button><button id="page-2" type="button" data-page="2" aria-pressed="${state.page===2}">${esc(u.p2)}</button></div></div><label for="compare-mode">${esc(u.mode)}<select id="compare-mode"><option value="compare"${state.mode==='compare'?' selected':''}>${esc(u.compare)}</option><option value="focus"${state.mode==='focus'?' selected':''}>${esc(u.focus)}</option></select></label><label for="compare-left">${esc(u.left)}<select id="compare-left">${choices(state.left)}</select></label><label for="compare-right"${state.mode==='focus'?' hidden':''}>${esc(u.right)}<select id="compare-right">${choices(state.right)}</select></label><label for="compare-zoom">${esc(u.mode)}<select id="compare-zoom"><option value="fit"${state.zoom==='fit'?' selected':''}>${esc(u.fit)}</option><option value="100"${state.zoom==='100'?' selected':''}>${esc(u.actual)}</option></select></label><button id="compare-guides" type="button" aria-pressed="${state.guides}">${esc(state.guides?u.guideOn:u.guide)}</button></div><p class="comparison-hint">${esc(state.guides?u.guideNote:u.zoomNote)}</p><div class="comparison-stage ${state.mode==='focus'?'focus':''}">${items.map(card).join('')}</div><h2 class="contract-section-heading">${esc(u.rules)}</h2><div class="contract-audits ${state.mode==='focus'?'focus':''}">${items.map(auditCard).join('')}</div><footer class="comparison-foot"><p>${esc(u.statusNote)}</p><div><a href="design-contracts.json" target="_blank" rel="noopener">${esc(u.download)} ↗</a><a href="https://document-studio-public-experiment.wlehd00000.chatgpt.site/downloads/document-studio-demo.zip" download>${esc(u.html)} ↓</a><a href="example.html?view=all&size=large">${esc(u.purpose)} ↗</a></div></footer></main><div class="audit-rack" aria-hidden="true">${profiles.map(p=>[1,2].map(page=>paper(p,page,`audit-${p.id}-${page}`)).join('')).join('')}</div>`;updateUrl();fitSheets();resizeObserver?.disconnect();resizeObserver=new ResizeObserver(fitSheets);root.querySelectorAll('.sheet-viewport').forEach(v=>resizeObserver.observe(v));if(active){root.querySelector('#'+active)?.focus({preventScroll:true});}const family=state.lang==='ja'?'Pretendard JP':'Pretendard';document.fonts.load(`11pt "${family}"`,state.lang==='ja'?'日本語の文書':'한국어 문서').then(()=>document.fonts.ready).then(()=>requestAnimationFrame(()=>{if(version===renderVersion){fitSheets();runAudits();}})).catch(()=>{if(version===renderVersion)root.querySelectorAll('.sample-status').forEach(e=>{e.textContent=u.fontFailed;e.classList.add('has-warning');});});}
const mm=px=>px*25.4/96,pt=px=>px*72/96,close=(a,b,tolerance=.25)=>Math.abs(a-b)<=tolerance;
function rgb(color){const values=color.match(/[\d.]+/g)?.map(Number);if(!values||values.length<3)return null;if(values.length>3&&values[3]===0)return null;return '#'+values.slice(0,3).map(v=>Math.round(v).toString(16).padStart(2,'0')).join('');}
function signature(page){return JSON.stringify([...page.querySelectorAll('[data-fact]')].map(e=>[e.dataset.fact,e.textContent.replace(/\s+/g,' ').trim()]));}
function runAudits(){
  const u=copy().ui;
  const reference=[1,2].map(n=>signature(root.querySelector(`.audit-rack [data-profile="mono"][data-page="${n}"]`)));
  for(const p of [...new Set(selectedProfiles().map(p=>p.id))].map(profile)){
    const pages=[...root.querySelectorAll(`.audit-rack [data-profile="${p.id}"]`)];
    const family=state.lang==='ja'?'Pretendard JP':'Pretendard';
    const metrics=pages.map(page=>{
      const style=getComputedStyle(page), frame=getComputedStyle(page.querySelector('.contract-frame'));
      const paragraph=getComputedStyle(page.querySelector('.c-ask p,.c-criteria p'));
      return {width:mm(parseFloat(style.width)),height:mm(parseFloat(style.height)),
        padding:['paddingTop','paddingRight','paddingBottom','paddingLeft'].map(k=>mm(parseFloat(frame[k]))),
        body:pt(parseFloat(paragraph.fontSize)),line:parseFloat(paragraph.lineHeight)/parseFloat(paragraph.fontSize),
        heading:pt(parseFloat(getComputedStyle(page.querySelector('.c-title h2')).fontSize)),
        font:paragraph.fontFamily.includes(family)&&document.fonts.check(`11pt "${family}"`)};
    });
    const colorSet=new Set();
    for(const page of pages)for(const e of [page,...page.querySelectorAll('*')]){
      if(e.closest('.rule-frame')||e.tagName==='IMG')continue;
      const style=getComputedStyle(e);if(style.display==='none')continue;
      for(const key of ['color','backgroundColor','borderTopColor','borderRightColor','borderBottomColor','borderLeftColor']){
        const value=rgb(style[key]);if(value)colorSet.add(value);
      }
    }
    const positions=pages.map(page=>{
      const r=page.getBoundingClientRect(),h=page.querySelector('.c-head').getBoundingClientRect(),f=page.querySelector('.c-foot').getBoundingClientRect();
      return {header:h.top-r.top,footer:f.top-r.top};
    });
    let fits=true;
    const overlaps=(a,b)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1;
    for(const page of pages){
      const bounds=page.getBoundingClientRect(),foot=page.querySelector('.c-foot').getBoundingClientRect();
      const head=page.querySelector('.c-head').getBoundingClientRect(),title=page.querySelector('.c-title').getBoundingClientRect();
      const pad=p.margin*96/25.4,regions=[...page.querySelectorAll('[data-content-region]')].map(e=>e.getBoundingClientRect());
      if(head.bottom>title.top+1||title.bottom>Math.min(...regions.map(r=>r.top))+1||Math.max(...regions.map(r=>r.bottom))>foot.top-5||foot.bottom>bounds.bottom-pad+1)fits=false;
      for(let i=0;i<regions.length;i++)for(let j=i+1;j<regions.length;j++)if(overlaps(regions[i],regions[j]))fits=false;
      for(const e of page.querySelectorAll('[data-fact]')){
        const r=e.getBoundingClientRect();
        if(e.scrollWidth>e.clientWidth+1||r.left<bounds.left+pad-1||r.right>bounds.right-pad+1)fits=false;
      }
    }
    const first=metrics[0],numbers=[...pages[0].querySelectorAll('.c-number')];
    const colorPass=[...colorSet].every(c=>p.palette.includes(c))&&pages.every((page,i)=>page.querySelectorAll('img').length===(p.image&&i===0?1:0));
    const aligned=numbers.length===6&&numbers.every(e=>getComputedStyle(e).textAlign==='right');
    const loaded=metrics.every(m=>m.font),same=pages.every((page,i)=>signature(page)===reference[i]);
    const rows=[
      [u.paper,`${p.width} × ${p.height}mm`,`${first.width.toFixed(1)} × ${first.height.toFixed(1)}mm`,metrics.every(m=>close(m.width,p.width)&&close(m.height,p.height))],
      [u.margins,`${p.margin}mm × 4`,first.padding.map(v=>v.toFixed(1)).join(' / ')+'mm',metrics.every(m=>m.padding.every(v=>close(v,p.margin)))],
      [u.body,`${p.bodyPt}pt / ${p.line}`,`${first.body.toFixed(1)}pt / ${first.line.toFixed(2)}`,metrics.every(m=>close(m.body,p.bodyPt,.05)&&close(m.line,p.line,.01))],
      [u.heading,`${p.titlePt}pt`,`${first.heading.toFixed(1)}pt`,metrics.every(m=>close(m.heading,p.titlePt,.05))],
      [u.font,family,loaded?u.loaded:u.fontFailed,loaded],
      [u.color,p.palette.join(' '),[...colorSet].join(' '),colorPass],
      [u.alignment,u.rightAligned,aligned?u.rightAligned:u.bad,aligned],
      [u.fitCheck,u.inside,fits?u.inside:u.bad,fits],
      [u.positions,u.consistent,`${mm(positions[0].header).toFixed(1)} / ${mm(positions[0].footer).toFixed(1)}mm`,close(positions[0].header,positions[1].header,.6)&&close(positions[0].footer,positions[1].footer,.6)],
      [u.same,u.common,same?u.common:u.bad,same]
    ];
    for(const audit of root.querySelectorAll(`[data-audit="${p.id}"]`))audit.querySelector('tbody').innerHTML=rows.map(([label,expected,observed,pass])=>`<tr data-pass="${pass}"><td><b>${esc(label)}</b><br>${esc(expected)}</td><td>${esc(observed)}</td><td>${esc(pass?u.ok:u.bad)}</td></tr>`).join('');
    const passes=rows.filter(r=>r[3]).length;
    for(const status of root.querySelectorAll(`[data-status="${p.id}"]`)){
      status.textContent=`${u.measuredPages} · ${passes}/${rows.length} ${u.ok}`;
      status.classList.toggle('has-warning',passes!==rows.length);status.dataset.contractPass=String(passes===rows.length);
    }
  }
}
root.addEventListener('change',e=>{const id=e.target.id;if(id==='compare-mode')state.mode=e.target.value;if(id==='compare-left')state.left=e.target.value;if(id==='compare-right')state.right=e.target.value;if(id==='compare-zoom')state.zoom=e.target.value;render();});
root.addEventListener('click',e=>{const lang=e.target.closest('[data-language]'),page=e.target.closest('[data-page]'),enlarge=e.target.closest('[data-enlarge]');if(lang){state.lang=lang.dataset.language;render();}else if(page){state.page=Number(page.dataset.page);render();}else if(enlarge){if(state.mode==='compare'){state.left=enlarge.dataset.enlarge;state.mode='focus';}else state.mode='compare';render();}else if(e.target.id==='compare-guides'){state.guides=!state.guides;render();}});
render();
})();
