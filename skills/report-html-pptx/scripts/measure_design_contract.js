() => {
  const visible = n => !!n && n.getBoundingClientRect().width > 0 && n.getBoundingClientRect().height > 0 && getComputedStyle(n).visibility !== 'hidden';
  const hex = color => {const m=color.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/);return m ? '#'+m.slice(1).map(x=>Number(x).toString(16).padStart(2,'0')).join('') : color;};
  const nodes = Array.from(document.querySelectorAll('[data-pptx-slide]'));
  return nodes.map((node,index) => {
    const rect=node.getBoundingClientRect(), style=getComputedStyle(node);
    const frame=node.querySelector('[data-demo-content-frame],.page-inner,.content,.body');
    let margins=null;
    if(frame){const r=frame.getBoundingClientRect(),s=getComputedStyle(frame);margins={left:r.left-rect.left+parseFloat(s.paddingLeft),right:rect.right-r.right+parseFloat(s.paddingRight)};}
    const candidates=[...node.querySelectorAll('[data-demo-role="body"],.lead,.report-detail p,p,li,td,h1,h2')].filter(visible).filter(n=>n.textContent.trim());
    const body=candidates.find(n=>n.matches('[data-demo-role="body"],.lead,.report-detail p'));
    const samples=[];
    const add=(n,role)=>{if(!n||samples.some(x=>x.element===n))return;const id='demo-contract-'+index+'-'+samples.length;n.setAttribute('data-demo-contract-sample',id);samples.push({element:n,selector:'[data-demo-contract-sample="'+id+'"]',key:n.getAttribute('data-demo-design-key')||role+'-'+samples.length,role,language:n.closest('[lang]')?.lang||document.documentElement.lang,languages:[...new Set([n.closest('[lang]')?.lang||document.documentElement.lang,...[...n.querySelectorAll('[lang]')].map(x=>x.lang)].map(x=>x.split('-')[0]))],text:n.textContent.trim().slice(0,160),font_size_px:parseFloat(getComputedStyle(n).fontSize),font_family:getComputedStyle(n).fontFamily});};
    add(body,'body');candidates.filter(n=>n.matches('[data-demo-role="body"],.report-detail p')).forEach(n=>add(n,'body'));
    add(candidates.find(n=>/[\u3000-\u9fff\uac00-\ud7af]/.test(n.textContent)),'cjk');add(candidates.find(n=>n.matches('h1,h2')),'title');
    node.querySelectorAll('[lang]').forEach(n=>{if(visible(n)&&n.textContent.trim())add(n,'language');});
    return {page:index+1,profile:node.getAttribute('data-design-profile')||node.closest('[data-design-profile]')?.getAttribute('data-design-profile')||document.body.getAttribute('data-design-profile'),
      family:node.getAttribute('data-page-family')||(node.classList.contains('cover')?'cover':'body'),canvas:[rect.width,rect.height],paper:hex(style.backgroundColor),frame:margins,
      grids:[...node.querySelectorAll('[data-demo-grid],.evidence-spread,.report-detail,.data-area')].filter(visible).filter(n=>getComputedStyle(n).display==='grid').map((n,i)=>({key:n.getAttribute('data-demo-design-key')||'grid-'+i,gap:parseFloat(getComputedStyle(n).columnGap)||0,columns:getComputedStyle(n).gridTemplateColumns})),
      samples:samples.map(({element,...rest})=>rest)};
  });
}
