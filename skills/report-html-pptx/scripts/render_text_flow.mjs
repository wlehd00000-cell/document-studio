/** Existing Node Playwright fallback for the same rendered-line measurement. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL,fileURLToPath} from 'node:url';

const scriptDir=path.dirname(fileURLToPath(import.meta.url));
const argv=process.argv.slice(2), opts={}, flags=new Set(['protected-term']);
if(argv.includes('--help')){
  process.stdout.write('Usage: render_text_flow.mjs input.html --output-dir qa-dir [--playwright-module existing-package-path] [--browser-path executable] [--pages 1,2]\n');
  process.exit(0);
}
let input;
for(let i=0;i<argv.length;i++){
  const arg=argv[i];
  if(!arg.startsWith('--')){if(input)throw Error('Unexpected positional argument');input=arg;continue;}
  const key=arg.slice(2), value=argv[++i];
  if(!value||value.startsWith('--'))throw Error(`Missing value for ${arg}`);
  if(flags.has(key))(opts[key]??=[]).push(value);else opts[key]=value;
}
const known=new Set(['output-dir','revision','page-selector','block-selector','content-selector','boundary-selector',
 'pages','protected-term','terms-json','viewport-width','viewport-height','scale','browser-path','timeout-ms','playwright-module']);
for(const key of Object.keys(opts))if(!known.has(key))throw Error(`Unknown option --${key}`);
if(!input||!opts['output-dir'])throw Error('Usage: render_text_flow.mjs input.html --output-dir qa-dir [--playwright-module existing-package-path]');
const source=fs.realpathSync(input), output=path.resolve(opts['output-dir']);
if(!/\.html?$/i.test(source))throw Error('Input must be a local HTML file');
const relative=path.relative(output,path.dirname(source));
if(!relative||(!relative.startsWith('..')&&!path.isAbsolute(relative)))throw Error('Choose a separate QA output directory');
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const save=value=>{
  const temporary=path.join(output,`.text-flow-${process.pid}-${crypto.randomUUID()}.tmp`);
  fs.writeFileSync(temporary,JSON.stringify(value,null,2)+'\n');
  fs.renameSync(temporary,path.join(output,'text-flow-audit.json'));
};
const width=Number(opts['viewport-width']||1280),height=Number(opts['viewport-height']||1400),
 scale=Number(opts.scale||1), timeout=Number(opts['timeout-ms']||30000);
if(![width,height,scale,timeout].every(x=>Number.isFinite(x)&&x>0))throw Error('Viewport, scale and timeout must be positive');
const selected=opts.pages?[...new Set(opts.pages.split(',').map(Number))].sort((a,b)=>a-b):[];
if(selected.some(x=>!Number.isInteger(x)||x<1))throw Error('Pages must contain positive integers');
let terms=opts['protected-term']||[];
if(opts['terms-json']){
  const supplied=JSON.parse(fs.readFileSync(opts['terms-json'],'utf8'));
  if(!Array.isArray(supplied)||supplied.some(s=>typeof s!=='string'||!s))throw Error('terms-json must be an array of nonempty strings');
  terms=terms.concat(supplied);
}
const options={pageSelector:opts['page-selector'],blockSelector:opts['block-selector']||'h1,h2,h3,p,td,th,li,figcaption,.source,.sources,[data-text-flow]',
 protectedTerms:[...new Set(terms)].sort(),selectedPages:selected,contentSelector:opts['content-selector'],boundarySelector:opts['boundary-selector']};
const implementation=path.join(scriptDir,'text_flow_measure.js');
const measure=fs.readFileSync(implementation,'utf8');
// Resolve only an existing package. This helper never installs a dependency/browser.
const moduleName=opts['playwright-module']?pathToFileURL(path.resolve(opts['playwright-module'])).href:'playwright';
const loadedPlaywright=await import(moduleName);
const chromium=loadedPlaywright.chromium||loadedPlaywright.default?.chromium;
if(!chromium)throw Error('Existing Playwright module does not expose chromium');
const files={[source]:hash(source)},external=new Set(),failed=[];
const browser=await chromium.launch({headless:true,...(opts['browser-path']?{executablePath:opts['browser-path']}: {})});
let started=false;
try{
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:scale});
  page.setDefaultTimeout(timeout);
  page.on('request',request=>{
    const url=new URL(request.url());
    if(url.protocol==='file:'){
      const name=fileURLToPath(url);
      if(fs.existsSync(name)&&fs.statSync(name).isFile()&&!files[name])files[name]=hash(name);
    }else if(['http:','https:'].includes(url.protocol))external.add(request.url());
  });
  page.on('requestfailed',r=>failed.push({url:r.url(),error:r.failure()}));
  page.on('response',r=>{if(r.status()>=400)failed.push({url:r.url(),status:r.status()});});
  const settle=async()=>page.evaluate(async ms=>{
    let timer;
    try{await Promise.race([(async()=>{
      await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode().catch(()=>null)));
      await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
    })(),new Promise((_,reject)=>timer=setTimeout(()=>reject(Error('Asset readiness timed out')),ms))]);}
    finally{clearTimeout(timer);}
  },timeout);
  await page.goto(pathToFileURL(source).href,{waitUntil:'load',timeout});
  await settle();
  const measurePage=()=>page.evaluate(({code,options})=>new Function('return ('+code+'\n)')()(options),{code:measure,options});
  const screen=await measurePage();
  if(selected.length&&selected.at(-1)>screen.total_pages)throw Error('Requested page exceeds document page count');
  if(!screen.pages.some(p=>p.status==='measured'))throw Error('No visible pages selected');
  fs.mkdirSync(output,{recursive:true});started=true;
  save({schema_version:1,status:'measuring',revision:opts.revision||null,input:source});
  const screenshots=[];
  for(const sheet of screen.pages){
    if(sheet.status!=='measured')continue;
    const name=`page-${sheet.page}.png`;
    await page.locator(screen.page_selector).nth(sheet.locator_index).screenshot({path:path.join(output,name)});
    screenshots.push({page:sheet.page,file:name,sha256:hash(path.join(output,name))});
  }
  await page.emulateMedia({media:'print'});await settle();
  const printed=await measurePage(), modes=[screen,printed];
  const layout=modes.flatMap(m=>m.pages.flatMap(p=>p.layout_findings)).length;
  const warnings=modes.flatMap(m=>m.pages.flatMap(p=>p.blocks.flatMap(b=>b.warnings))).length;
  const fontErrors=modes.flatMap(m=>m.fonts.filter(f=>f.status==='error'));
  const incomplete=modes.some(m=>m.pages.some(p=>p.status==='hidden'||!p.blocks.length));
  const localFiles=Object.fromEntries(Object.entries(files).sort(([a],[b])=>a.localeCompare(b)));
  const fingerprint=crypto.createHash('sha256').update(JSON.stringify(localFiles)).digest('hex');
  const summary={total_pages:screen.total_pages,measured_pages:screen.pages.filter(p=>p.status==='measured').map(p=>p.page),
    hidden_pages:screen.pages.filter(p=>p.status==='hidden').map(p=>p.page),layout_findings:layout,editorial_candidates:warnings,
    coverage_status:incomplete?'incomplete':'selected_pages_measured',
    structural_status:layout||failed.length||screen.missing_images.length||printed.missing_images.length||fontErrors.length?'findings':incomplete?'incomplete':'no_detected_findings'};
  const hashes={};
  for(const name of ['render_text_flow.py','render_text_flow.mjs','text_flow_measure.js']){
    const file=path.join(scriptDir,name);if(fs.existsSync(file))hashes[name]=hash(file);
  }
  save({schema_version:1,status:'measured',revision:opts.revision||null,implementation_hashes:hashes,
    measured_at:new Date().toISOString(),source_evidence:{input:source,local_files:localFiles,fingerprint,external_resources_unhashed:[...external].sort()},
    renderer:{engine:'Chromium',version:browser.version(),viewport:[width,height],scale},options,screen,print:printed,screenshots,
    resource_failures:failed,font_errors:fontErrors,summary,visual_review:'pending',editorial_review:'pending',user_acceptance:'not_assessed'});
  process.stdout.write(JSON.stringify({status:'measured',audit:path.join(output,'text-flow-audit.json'),...summary,visual_review:'pending',editorial_review:'pending'})+'\n');
}catch(error){
  if(started)save({schema_version:1,status:'failed',revision:opts.revision||null,input:source,error:String(error)});
  throw error;
}finally{await browser.close();}
