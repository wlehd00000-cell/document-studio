// Executed only inside the supplied HTML renderer. No source DOM mutation.
({pageSelector, blockSelector, protectedTerms, selectedPages, contentSelector, boundarySelector}) => {
  const visibility=new WeakMap();
  const visible = el => {
    if(visibility.has(el)) return visibility.get(el);
    const r=el.getBoundingClientRect(), s=getComputedStyle(el);
    const result=r.width>0 && r.height>0 && s.display!=='none' && s.visibility!=='hidden';
    visibility.set(el,result); return result;
  };
  let selector=pageSelector;
  if(!selector) selector=['[data-pptx-slide]','[data-fixed-page]','.page','.slide'].find(s=>document.querySelector(s));
  if(!selector) throw Error('No page elements found. Supply --page-selector.');
  const matched=[...document.querySelectorAll(selector)];
  const all=matched.filter(el=>!el.parentElement?.closest(selector));
  if(!all.length) throw Error('Page selector matched no elements. Check --page-selector.');
  const startBad=/^[、。，．：；？！ー）］｝〉》」』】〕ぁぃぅぇぉっゃゅょァィゥェォッャュョ]/;
  const endBad=/[（［｛〈《「『【〔]$/;
  // Unit suffixes need real boundaries: "개선" and "분석" are not units.
  const unitStart=/^(?:[%‰℃°]|(?:개|건|명|회|원|억|만|천|조|톤|년|월|일|시간|분|초|배|㎡|㎥)(?=$|[\s.,;:!?)\]·/]|(?:으로|에서|까지|부터|보다|당|의|은|는|이|가|을|를|에|도|과|와|로)(?=$|[\s.,;:!?)\]·/])|입니다|이었다|이다)|(?:tCO[2₂](?:eq)?|kg|m[23²³]|MW(?:h)?|kW(?:h)?|TJ|ppm|ha|t|g)(?=[^A-Za-z]|$))/;
  const bounds=r=>({x:r.x,y:r.y,width:r.width,height:r.height});
  const intersects=(a,b,tolerance=1)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>tolerance&&
    Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>tolerance;
  const lineBounds=(line,sheet)=>({left:line.x+sheet.left,right:line.x+sheet.left+line.used_width,
    top:line.y+sheet.top,bottom:line.y+sheet.top+line.height});
  const pages=all.map((sheet,index)=>{
    if(selectedPages.length&&!selectedPages.includes(index+1)) return null;
    if(!visible(sheet)) return {page:index+1,locator_index:matched.indexOf(sheet),id:sheet.id||null,status:'hidden',blocks:[],layout_findings:[]};
    const sr=sheet.getBoundingClientRect(), findings=[], clipped=new Set();
    const elements=[...sheet.querySelectorAll(blockSelector)].filter(visible);
    const blocks=elements.map((el,n)=>{
      const er=el.getBoundingClientRect(), rows=[], warnings=[];
      let logicalText='', manualBreaks=0, koreanLanguageMismatch=false;
      const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT); let node;
      while(node=walker.nextNode()){
        if(node.nodeType===Node.ELEMENT_NODE){
          if(node.parentElement?.closest(blockSelector)===el){
            if(node.tagName==='BR'){logicalText+='\n';manualBreaks++;}
            if(node.tagName==='WBR') logicalText+='\u200b';
          }
          continue;
        }
        // A nested block measures its own text; retain the parent's direct text.
        if(!visible(node.parentElement)||node.parentElement.closest(blockSelector)!==el) continue;
        const baseOffset=logicalText.length;
        logicalText+=node.textContent;
        if(/[가-힣ㄱ-ㅎㅏ-ㅣ]/.test(node.textContent)&&!/^ko\b/i.test(node.parentElement.closest('[lang]')?.lang||document.documentElement.lang))
          koreanLanguageMismatch=true;
        let offset=0;
        for(const ch of node.textContent){
          const sourceStart=baseOffset+offset;
          const range=document.createRange();range.setStart(node,offset);offset+=ch.length;range.setEnd(node,offset);
          const r=range.getBoundingClientRect(); if(!r.width||!r.height||/[\r\n\t]/.test(ch)) continue;
          let row=rows.find(row=>Math.abs(row.bottom-r.bottom)<=Math.max(2,Math.min(row.height,r.height)*0.2));
          if(!row){row={top:r.top,bottom:r.bottom,height:r.height,chars:[]};rows.push(row);}
          row.chars.push({text:ch,x:r.x,right:r.right,top:r.top,bottom:r.bottom,
                         sourceStart,sourceEnd:baseOffset+offset});
        }
      }
      const lines=rows.sort((a,b)=>a.top-b.top).map(row=>{
        const chars=row.chars.sort((a,b)=>a.x-b.x), left=Math.min(...chars.map(c=>c.x)),right=Math.max(...chars.map(c=>c.right));
        const top=Math.min(...chars.map(c=>c.top)),bottom=Math.max(...chars.map(c=>c.bottom));
        const nonspace=chars.filter(c=>!/[\s\u200b]/.test(c.text));
        return {text:chars.map(c=>c.text).join('').trim(),x:left-sr.x,y:top-sr.y,
                used_width:right-left,available_width:el.clientWidth,height:bottom-top,
                source_start:nonspace.length?Math.min(...nonspace.map(c=>c.sourceStart)):null,
                source_end:nonspace.length?Math.max(...nonspace.map(c=>c.sourceEnd)):null,
                outside_block:left<er.left-1||right>er.right+1,
                outside_block_y:top<er.top-1||bottom>er.bottom+1,
                outside_page:left<sr.left-1||right>sr.right+1||top<sr.top-1||bottom>sr.bottom+1};
      }).filter(l=>l.text);
      if(!lines.length) return null;
      const style=getComputedStyle(el), lang=el.closest('[lang]')?.lang||document.documentElement.lang;
      const korean=/^ko\b/i.test(lang), body=['P','LI','FIGCAPTION'].includes(el.tagName);
      if(koreanLanguageMismatch) warnings.push({kind:'korean-language-tag',language:lang||null});
      if(korean&&body&&manualBreaks&&!el.dataset.textFlowBreakReason)
        warnings.push({kind:'korean-manual-body-breaks',count:manualBreaks,
                       note:'Review authored line breaks; paragraph and rendered line are different.'});
      lines.forEach((line,i)=>{
        if(/^ja\b/i.test(lang)&&startBad.test(line.text)) warnings.push({kind:'kinsoku-start',line:i+1});
        if(/^ja\b/i.test(lang)&&endBad.test(line.text)) warnings.push({kind:'kinsoku-end',line:i+1});
        if(i>0&&Array.from(line.text).length<=2) warnings.push({kind:'short-tail',line:i+1});
        if(korean){
          if(/^[,，.。;；:：!?！？%‰°)\]｝〉》」』】〕]/.test(line.text))
            warnings.push({kind:'korean-punctuation-start',line:i+1});
          if(/[([（［｛〈《「『【〔]$/.test(line.text))
            warnings.push({kind:'korean-opening-punctuation-end',line:i+1});
          if(body&&i===lines.length-1&&i>0&&Array.from(line.text).length<=8&&line.used_width<line.available_width*0.25)
            warnings.push({kind:'korean-short-tail',line:i+1,text:line.text,
                           note:'Editorial candidate, not an automatic failure.'});
        }
        if(i<lines.length-1){
          if(korean&&line.source_end!==null&&lines[i+1].source_start!==null){
            const next=lines[i+1], gap=logicalText.slice(line.source_end,next.source_start);
            const left=(logicalText.slice(0,line.source_end).match(/[^\s\u200b]+$/)||[''])[0];
            const right=(logicalText.slice(next.source_start).match(/^[^\s\u200b]+/)||[''])[0];
            if(!gap&&/[가-힣ㄱ-ㅎㅏ-ㅣ]/.test(left+right))
              warnings.push({kind:'korean-eojeol-split',line:i+1,token:left+right,
                             before:line.text.slice(-24),after:next.text.slice(0,24)});
            if(/^[\s\u200b]*$/.test(gap)&&/[0-9][0-9,.]*(?:천|만|억|조)?$/.test(line.text)&&unitStart.test(next.text))
              warnings.push({kind:'korean-number-unit-split',line:i+1,
                             before:line.text.slice(-24),after:next.text.slice(0,24)});
          }
          const sentenceEnd=/[。！？]|[.!?](?=\s)/;
          const tail=line.text.split(sentenceEnd).pop();
          if(sentenceEnd.test(line.text)&&tail&&Array.from(tail.trim()).length>0&&Array.from(tail.trim()).length<=4)
            warnings.push({kind:'next-sentence-fragment',line:i+1,fragment:tail});
          for(const term of protectedTerms){
            const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
            const pattern=new RegExp(term.split(/\s+/).map(escape).join('[\\s\\u200b]+'),'g');
            let match;
            while((match=pattern.exec(logicalText))){
              const end=match.index+match[0].length;
              if(line.source_end!==null&&lines[i+1].source_start!==null&&
                 match.index<line.source_end&&end>lines[i+1].source_start)
                warnings.push({kind:'protected-term-split',line:i+1,term});
            }
          }
        }
      });
      if(el.scrollWidth>el.clientWidth+1||lines.some(l=>l.outside_block)) findings.push({kind:'horizontal-overflow',block:n+1});
      // Range geometry follows the laid-out characters, including lines drawn
      // outside a fixed box with overflow:visible. Element bounds alone miss it.
      if(lines.some(l=>l.outside_block_y)&&el.scrollHeight>el.clientHeight+1)
        findings.push({kind:'vertical-glyph-overflow',block:n+1,
          drawn_bottom:Math.max(...lines.map(l=>l.y+l.height)),box_bottom:er.bottom-sr.top});
      if(lines.some(l=>l.outside_page)) findings.push({kind:'glyph-outside-page',block:n+1});
      for(let container=el;container&&sheet.contains(container);container=container.parentElement){
        if(!clipped.has(container)&&container.scrollHeight>container.clientHeight+1&&getComputedStyle(container).overflowY!=='visible'){
          findings.push({kind:'vertical-clipping-or-scroll',block:n+1,container:container.id||container.tagName});
          clipped.add(container);
        }
        if(container===sheet) break;
      }
      if(er.left<sr.left-1||er.right>sr.right+1||er.top<sr.top-1||er.bottom>sr.bottom+1)
        findings.push({kind:'outside-page',block:n+1});
      return {id:el.id||`page-${index+1}-block-${n+1}`,index:n+1,tag:el.tagName,classes:el.className,
              language:el.closest('[lang]')?.lang||document.documentElement.lang,
              font:{family:style.fontFamily,size:style.fontSize,weight:style.fontWeight,line_height:style.lineHeight},
              wrapping:{word_break:style.wordBreak,overflow_wrap:style.overflowWrap,
                        white_space:style.whiteSpace,line_break:style.lineBreak,
                        manual_breaks:manualBreaks,break_reason:el.dataset.textFlowBreakReason||null},
              rect:{x:er.x-sr.x,y:er.y-sr.y,width:er.width,height:er.height},
              drawn_bounds:{x:Math.min(...lines.map(l=>l.x)),y:Math.min(...lines.map(l=>l.y)),
                right:Math.max(...lines.map(l=>l.x+l.used_width)),bottom:Math.max(...lines.map(l=>l.y+l.height))},
              lines,warnings};
    }).filter(Boolean);
    if(contentSelector&&boundarySelector){
      const content=sheet.querySelector(contentSelector);
      const boundary=[...sheet.querySelectorAll(boundarySelector)].filter(visible);
      if(content&&boundary.length){
        const top=Math.min(...boundary.map(e=>e.getBoundingClientRect().top));
        for(const b of blocks){const el=elements[b.index-1];
          if(content.contains(el)&&!boundary.some(e=>e===el||e.contains(el))&&
             Math.max(el.getBoundingClientRect().bottom,b.drawn_bounds.bottom+sr.top)>top-1)
            findings.push({kind:'content-boundary-collision',block:b.id,
              drawn_bottom:b.drawn_bounds.bottom,boundary_top:top-sr.top});}
      }
    }
    // Only disjoint text owners are compared; parent/table/inline descendants
    // are measured separately and must not become false neighbor collisions.
    for(let i=0;i<blocks.length;i++)for(let j=i+1;j<blocks.length;j++){
      const a=blocks[i],b=blocks[j],ae=elements[a.index-1],be=elements[b.index-1];
      if(ae.contains(be)||be.contains(ae))continue;
      const overlap=a.lines.some(al=>b.lines.some(bl=>intersects(lineBounds(al,sr),lineBounds(bl,sr))));
      if(!overlap)continue;
      const reason=ae.dataset.textFlowOverlapReason||be.dataset.textFlowOverlapReason;
      if(reason){a.warnings.push({kind:'declared-text-overlap',with:b.id,reason});continue;}
      findings.push({kind:'text-neighbor-collision',block:a.id,with:b.id});
    }
    const visuals=[...sheet.querySelectorAll('img,svg,canvas,[data-visual-boundary]')].filter(visible)
      .filter(el=>!el.parentElement?.closest('svg,canvas,[data-visual-boundary]')).map((el,n)=>{
        let r=el.getBoundingClientRect(),left=r.left,right=r.right,top=r.top,bottom=r.bottom;
        // SVG content may extend outside its viewport when overflow is visible.
        if(el.tagName.toLowerCase()==='svg'&&getComputedStyle(el).overflow==='visible'){
          try{const box=el.getBBox(),matrix=el.getScreenCTM();
            if(matrix){const points=[[box.x,box.y],[box.x+box.width,box.y],[box.x,box.y+box.height],[box.x+box.width,box.y+box.height]]
              .map(([x,y])=>new DOMPoint(x,y).matrixTransform(matrix));
              left=Math.min(left,...points.map(p=>p.x));right=Math.max(right,...points.map(p=>p.x));
              top=Math.min(top,...points.map(p=>p.y));bottom=Math.max(bottom,...points.map(p=>p.y));}
          }catch{} // Keep conservative element geometry if SVG cannot supply it.
        }
        // Respect actual clip ancestors: large intentionally cropped photographs
        // are valid when their visible part stays inside the page.
        for(let parent=el.parentElement;parent&&sheet.contains(parent);parent=parent.parentElement){
          const style=getComputedStyle(parent),pr=parent.getBoundingClientRect();
          if(style.overflowX!=='visible'){left=Math.max(left,pr.left);right=Math.min(right,pr.right);}
          if(style.overflowY!=='visible'){top=Math.max(top,pr.top);bottom=Math.min(bottom,pr.bottom);}
          if(parent===sheet)break;
        }
        const outside=right>left&&bottom>top&&(left<sr.left-1||right>sr.right+1||top<sr.top-1||bottom>sr.bottom+1);
        if(outside)findings.push({kind:'visual-outside-page',visual:el.id||`visual-${n+1}`});
        return {id:el.id||`visual-${n+1}`,tag:el.tagName,rect:bounds(r),
          visible_bounds:{left:left-sr.left,right:right-sr.left,top:top-sr.top,bottom:bottom-sr.top},outside_page:outside};
      });
    return {page:index+1,locator_index:matched.indexOf(sheet),id:sheet.id||null,status:'measured',rect:bounds(sr),blocks,visuals,layout_findings:findings};
  }).filter(Boolean);
  const images=[...document.images].filter(visible).filter(i=>!i.complete||!i.naturalWidth).map(i=>i.currentSrc||i.src);
  const fonts=[...document.fonts].map(f=>({family:f.family,status:f.status,weight:f.weight}));
  return {page_selector:selector,total_pages:all.length,pages,missing_images:images,fonts};
}

