#!/usr/bin/env node
/** Measure approved page relationships on the actual rendered DOM. No asset downloads. */
import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { loadPlaywright } from './check_layout.mjs';

const hash = async file => createHash('sha256').update(await fs.readFile(file)).digest('hex');

async function measure(project, plan, browserPath) {
  let browser;
  try {
    const playwright = await loadPlaywright();
    browser = await playwright.chromium.launch({ headless: true,
      ...(browserPath ? { executablePath: browserPath } : {}) });
  } catch (error) {
    return {status:'UNVERIFIED',reason:'Browser unavailable: '+String(error.message ?? error),
      inspected_pages:[],relationships:[],findings:[],screenshots:[],tool:{renderer:'unavailable'}};
  }
  try {
    const html = path.join(project,'html','index.html');
    const page = await browser.newPage({viewport:{width:1600,height:1200},deviceScaleFactor:1});
    const blocked=[];
    await page.route('**/*',async route => {
      const url=route.request().url();
      if (!url.startsWith('file:')) {
        blocked.push('Blocked remote URL: '+url);
        await route.abort();return;
      }
      let local;
      try {local=path.resolve(fileURLToPath(url));} catch {local='';}
      if (!local.startsWith(project+path.sep) || local.includes('..'+path.sep)) {
        blocked.push('Blocked outside-project resource');
        await route.abort();return;
      }
      await route.continue();
    });
    await page.goto(pathToFileURL(html).href,{waitUntil:'load',timeout:20000});
    await page.evaluate(async()=>{
      await document.fonts.ready;
      await Promise.all([...document.images].map(image=>image.decode().catch(()=>null)));
      await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
    });
    const measured=await page.evaluate(pages=>{
      const findings=[],relationships=[],seen=[];
      const rect=r=>({left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height});
      const visible=el=>{
        if (!el || el.closest('[hidden],[aria-hidden="true"]'))return false;
        for(let node=el;node;node=node.parentElement){
          const st=getComputedStyle(node);
          if(st.display==='none'||st.visibility!=='visible'||Number(st.opacity)===0)return false;
        }
        const b=el.getBoundingClientRect();return b.width>0&&b.height>0;
      };
      const outside=(a,b)=>a.left<b.left-2||a.top<b.top-2||a.right>b.right+2||a.bottom>b.bottom+2;
      const overlap=(a,b,axis)=>axis==='horizontal'
        ? Math.min(a.right,b.right)-Math.max(a.left,b.left)
        : Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top);
      for(const pagePlan of pages){
        const pageId=pagePlan.page_id;
        const roots=[...document.querySelectorAll('[data-page-id]')].filter(node=>node.dataset.pageId===pageId);
        if(roots.length!==1){findings.push({page_id:pageId,code:'PAGE_MISSING_OR_DUPLICATE'});continue;}
        const root=roots[0],boundary=root.getBoundingClientRect();
        seen.push(pageId);
        if(!visible(root)){findings.push({page_id:pageId,code:'PAGE_HIDDEN'});continue;}
        const anchors={};
        for(const role of pagePlan.elements){
          const els=[...root.querySelectorAll('[data-grammar-element-id]')].filter(n=>n.dataset.grammarElementId===role.element_id);
          if(!els.length)continue;
          const el=els[0];anchors[role.element_id]=el;
          if(!visible(el)){findings.push({page_id:pageId,element_id:role.element_id,code:'HIDDEN_ANCHOR'});continue;}
          const bounds=el.getBoundingClientRect();
          if(outside(bounds,boundary))findings.push({page_id:pageId,element_id:role.element_id,code:'ANCHOR_OUTSIDE_PAGE'});
          if(el.scrollWidth>el.clientWidth+2||el.scrollHeight>el.clientHeight+2)
            findings.push({page_id:pageId,element_id:role.element_id,code:'ANCHOR_TEXT_CLIPPED'});
          const range=document.createRange();range.selectNodeContents(el);
          if([...range.getClientRects()].some(r=>outside(r,boundary)))
            findings.push({page_id:pageId,element_id:role.element_id,code:'TEXT_OUTSIDE_PAGE'});
          for(let parent=el.parentElement;parent&&parent!==root.parentElement;parent=parent.parentElement){
            const st=getComputedStyle(parent),clip=parent.getBoundingClientRect();
            if((['clip','hidden','auto','scroll'].includes(st.overflowX)&&bounds.right>clip.right+2)
                || (['clip','hidden','auto','scroll'].includes(st.overflowY)&&bounds.bottom>clip.bottom+2)){
              findings.push({page_id:pageId,element_id:role.element_id,code:'ANCHOR_CLIPPED_BY_PARENT'});break;
            }
          }
        }
        for(const rule of pagePlan.rules){
          for(const relation of rule.relationships){
            const first=anchors[relation.leader_element_id],second=anchors[relation.follower_element_id];
            const a=first?.getBoundingClientRect(),b=second?.getBoundingClientRect();
            let passed=false;
            if(first&&second&&visible(first)&&visible(second)){
              if(relation.operator==='above')passed=a.bottom<=b.top+2&&overlap(a,b,'horizontal')>2;
              if(relation.operator==='left_of')passed=a.right<=b.left+2&&overlap(a,b,'vertical')>2;
            }
            relationships.push({page_id:pageId,rule_id:rule.rule_id,operator:relation.operator,
              leader_element_id:relation.leader_element_id,follower_element_id:relation.follower_element_id,
              passed,leader_rect:a?rect(a):null,follower_rect:b?rect(b):null});
            if(!passed)findings.push({page_id:pageId,rule_id:rule.rule_id,code:'RELATIONSHIP_VIOLATION',
              operator:relation.operator});
          }
        }
      }
      for(const face of document.fonts)if(face.status==='error')findings.push({code:'FONT_NOT_LOADED',font:face.family});
      return {inspected_pages:seen,relationships,findings};
    },plan.pages);
    const screens=[];
    const output=path.join(project,'qa','layout-grammar-pages');
    await fs.mkdir(output,{recursive:true});
    for(const id of measured.inspected_pages){
      const target=path.join(output,id+'.png');
      await page.locator('[data-page-id="'+id+'"]').screenshot({path:target});
      screens.push({page_id:id,path:'qa/layout-grammar-pages/'+id+'.png',sha256:await hash(target)});
    }
    const findings=[...measured.findings,...blocked.map(detail=>({code:'BLOCKED_RESOURCE',detail}))];
    return {status:findings.length?'FAIL':'PASS',inspected_pages:measured.inspected_pages,
      relationships:measured.relationships,findings,screenshots:screens,
      tool:{renderer:'Chromium',browser_version:browser.version()}};
  }catch(error){
    return {status:'UNVERIFIED',reason:'Rendering was incomplete: '+String(error.message??error),
      inspected_pages:[],relationships:[],findings:[],screenshots:[],tool:{renderer:'incomplete'}};
  }finally{await browser.close();}
}

const [projectArg,planArg,browserArg]=process.argv.slice(2);
if(!projectArg||!planArg)throw Error('Usage: audit_layout_grammar.mjs PROJECT PLAN [BROWSER_PATH]');
const project=path.resolve(projectArg);
const plan=JSON.parse(await fs.readFile(planArg,'utf8'));
process.stdout.write(JSON.stringify(await measure(project,plan,browserArg))+'\n');
