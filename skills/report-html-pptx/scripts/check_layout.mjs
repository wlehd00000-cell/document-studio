#!/usr/bin/env node
// DEMO HTML print-layout checks. Independently authored; see consulting-integration-sources.json.
import path from 'node:path';
import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';

export async function loadPlaywright() {
  const localRequire = createRequire(import.meta.url);
  const supplied = process.env.PLAYWRIGHT_MODULE_DIR;
  if (supplied) {
    const root = path.resolve(supplied);
    for (const candidate of [root, path.join(root, 'playwright')]) {
      for (const entry of ['index.mjs', 'index.js']) {
        try {
          const mod = await import(pathToFileURL(path.join(candidate, entry)).href);
          return mod.default ?? mod;
        } catch {}
      }
    }
    try { return createRequire(path.join(root, '__gs_module_probe.cjs'))('playwright'); } catch {}
  }
  try { return localRequire('playwright'); } catch {}
  throw new Error('Existing playwright package not found; set PLAYWRIGHT_MODULE_DIR. No installation was attempted.');
}

export async function checkLayout(file, options = {}) {
  const issues = [];
  const target = path.resolve(file);
  let input, implementation_sha256;
  let browser;
  try {
    input = { path: target, sha256: createHash('sha256').update(await fs.readFile(target)).digest('hex') };
    implementation_sha256 = createHash('sha256').update(await fs.readFile(fileURLToPath(import.meta.url))).digest('hex');
    const pw = await loadPlaywright();
    const launch = { headless: true };
    if (process.env.GS_QA_BROWSER_EXECUTABLE) launch.executablePath = process.env.GS_QA_BROWSER_EXECUTABLE;
    browser = await pw.chromium.launch(launch);
    const page = await browser.newPage({ viewport: { width: 1600, height: 1200 }, deviceScaleFactor: 1 });
    page.on('requestfailed', request => issues.push({ severity: 'FAIL', code: 'ASSET_REQUEST_FAILED', page: null,
      message: `${request.url()}: ${request.failure()?.errorText ?? 'request failed'}` }));
    await page.emulateMedia({ media: 'print' });
    await page.goto(pathToFileURL(path.resolve(file)).href, { waitUntil: 'load', timeout: 20000 });
    await page.evaluate(async () => {
      await Promise.race([document.fonts.ready, new Promise((_, reject) => setTimeout(() => reject(new Error('Font readiness timed out')), 15000))]);
      await Promise.all([...document.images].map(async img => {
        if (!img.complete) await Promise.race([
          new Promise(resolve => { img.addEventListener('load', resolve, { once: true }); img.addEventListener('error', resolve, { once: true }); }),
          new Promise((_, reject) => setTimeout(() => reject(new Error('Image readiness timed out')), 15000))
        ]);
        if (img.naturalWidth) await img.decode().catch(() => {});
      }));
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    });

    const measured = await page.evaluate(() => {
      const findings = [], dimensions = [], pageElements = [];
      const explicit = [...document.querySelectorAll('[data-pptx-slide]')];
      const candidates = explicit.length ? explicit : [...document.querySelectorAll('.demo-page, .page, .slide, section.s')];
      const set = new Set(candidates);
      const visible = el => {
        if (el.closest('[hidden], [aria-hidden="true"]')) return false;
        for (let parent = el; parent; parent = parent.parentElement) {
          const st = getComputedStyle(parent);
          if (st.display === 'none' || st.visibility === 'hidden') return false;
        }
        return true;
      };
      for (const candidate of candidates) {
        let parent = candidate.parentElement;
        while (parent && !set.has(parent)) parent = parent.parentElement;
        if (!parent && visible(candidate)) pageElements.push(candidate);
      }
      const add = (code, n, text, severity = 'FAIL') => findings.push({ severity, code, page: n, message: text });
      if (!pageElements.length) add('NO_PAGES', null, 'No visible document pages recognized; layout checks were not performed.');
      const outside = (r, b) => r.left < b.left - 2 || r.top < b.top - 2 || r.right > b.right + 2 || r.bottom > b.bottom + 2;
      const intersects = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 2 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 2;

      pageElements.forEach((s, index) => {
        const n = index + 1, sr = s.getBoundingClientRect();
        // The capture selector uses these exact recognized roots; nested legacy
        // .page classes must not produce additional, mismatched screenshots.
        s.dataset.gsLayoutPage = String(n);
        dimensions.push({ page: n, width_px: +sr.width.toFixed(3), height_px: +sr.height.toFixed(3),
          profile: s.dataset.designProfile ?? s.dataset.typeProfile ?? null,
          family: s.dataset.pageFamily ?? null });
        if (sr.width < 1 || sr.height < 1) add('EMPTY_PAGE_BOX', n, 'Page has no measurable width/height.');
        const footer = s.querySelector('.demo-footer, .page-footer, .foot, .footer, footer');
        const fr = footer && visible(footer) ? footer.getBoundingClientRect() : null;
        const walker = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
        let node;
        while ((node = walker.nextNode())) {
          const parent = node.parentElement;
          if (!parent || !node.textContent.trim() || !visible(parent) || parent.closest('script, style, template, noscript')) continue;
          const snippet = node.textContent.trim().replace(/\s+/g, ' ').slice(0, 70);
          const range = document.createRange();
          range.selectNodeContents(node);
          const rects = [...range.getClientRects()].filter(r => r.width > 0 && r.height > 0);
          if (rects.some(r => outside(r, sr))) add('TEXT_OUTSIDE_PAGE', n, `Text extends beyond a page edge: ${snippet}`);
          if (fr && !footer.contains(parent) && rects.some(r => intersects(r, fr))) add('FOOTER_COLLISION', n, `Body text overlaps footer: ${snippet}`);
          let ancestor = parent;
          while (ancestor && ancestor !== s.parentElement) {
            const st = getComputedStyle(ancestor), ar = ancestor.getBoundingClientRect();
            const clipsX = ['hidden', 'clip', 'scroll', 'auto'].includes(st.overflowX);
            const clipsY = ['hidden', 'clip', 'scroll', 'auto'].includes(st.overflowY);
            if (rects.some(r => (clipsX && (r.left < ar.left - 2 || r.right > ar.right + 2)) || (clipsY && (r.top < ar.top - 2 || r.bottom > ar.bottom + 2)))) {
              add('TEXT_CLIPPED', n, `Text exceeds a clipping/scroll container: ${snippet}`);
              break;
            }
            ancestor = ancestor.parentElement;
          }
        }
        for (const el of s.querySelectorAll('img, svg')) {
          if (!visible(el)) continue;
          const r = el.getBoundingClientRect();
          if (outside(r, sr)) add('VISUAL_OUTSIDE_PAGE', n, `${el.tagName.toLowerCase()} extends beyond a page edge.`);
          if (el.tagName === 'IMG' && (!el.complete || !el.naturalWidth)) add('IMAGE_NOT_LOADED', n, `Image did not load: ${el.getAttribute('src')}`);
          if (fr && !footer.contains(el) && intersects(r, fr)) add('FOOTER_COLLISION', n, 'A visual overlaps footer.');
        }
      });
      for (const face of document.fonts) {
        if (face.status === 'error') add('FONT_NOT_LOADED', null, `Declared font failed: ${face.family}`);
      }
      const fonts = [...new Set(pageElements.map(el => getComputedStyle(el).fontFamily))];
      // Computed font families are not proof of the actual per-glyph font.
      const unique = [...new Map(findings.map(f => [JSON.stringify(f), f])).values()];
      return { page_count: pageElements.length, dimensions, findings: unique, computed_font_families: fonts };
    });
    issues.push(...measured.findings);
    if (options.screenshots) {
      await fs.mkdir(options.screenshots, { recursive: true });
      const elements = page.locator('[data-demo-layout-page]');
      let count = 0;
      for (const element of await elements.all()) {
        if (await element.isVisible()) {
          await element.screenshot({ path: path.join(options.screenshots, `page-${String(++count).padStart(2, '0')}.png`) });
        }
      }
    }
    const failures = issues.filter(f => f.severity === 'FAIL').length;
    return { status: failures ? 'fail' : 'automated_checks_passed', ...measured, findings: issues, failures, input, implementation_sha256,
      coverage: 'Print-layout page bounds, text clipping, footer collisions and asset readiness. Other overlaps, actual per-glyph font use, logic, aesthetics and final PPTX are not verified.' };
  } catch (error) {
    return { status: 'unverified', page_count: 0, findings: issues, input, implementation_sha256, error: String(error.message ?? error),
      coverage: 'Layout checks could not complete. No dependency or browser installation was attempted.' };
  } finally {
    if (browser) await browser.close();
  }
}

async function main() {
  const args = process.argv.slice(2);
  const file = args.shift();
  if (!file || file.startsWith('--')) throw new Error('Usage: node check_layout.mjs <html> [--json] [--screenshots <directory>]');
  const options = {};
  let asJson = false;
  while (args.length) {
    const arg = args.shift();
    if (arg === '--json') asJson = true;
    else if (arg === '--screenshots' && args.length) options.screenshots = path.resolve(args.shift());
    else throw new Error(`Unknown or incomplete option: ${arg}`);
  }
  const result = await checkLayout(path.resolve(file), options);
  if (asJson) process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  else {
    for (const finding of result.findings) process.stdout.write(`${finding.severity} ${finding.code} p${finding.page}: ${finding.message}\n`);
    process.stdout.write(`${result.page_count} pages; ${result.status}\n${result.error ?? result.coverage}\n`);
  }
  process.exitCode = result.status === 'unverified' ? 2 : result.failures ? 1 : 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => { process.stdout.write(JSON.stringify({ status: 'unverified', page_count: 0, error: error.message }) + '\n'); process.exitCode = 2; });
}
