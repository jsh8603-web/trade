// .consult-collect.js — 특정 conversation 탭의 응답 수집 (goto 없음, 기존 탭 매칭). basic 셀렉터.
// usage: node .consult-collect.js <maxWaitMs> <selectors-basic.json> <urlSubstring>
const { chromium } = require('playwright');
const fs = require('fs');
const MAX = Number(process.argv[2]) || 180000;
const SEL = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const URLSUB = process.argv[4] || '';
const contSel = SEL.responseContainer.split(',')[0].trim();

async function pageText(page) {
  try {
    const conts = await page.$$(contSel);
    if (!conts.length) return '';
    const lastC = conts[conts.length - 1];
    const blocks = await lastC.$$(SEL.responseBlock);
    if (blocks.length) {
      const parts = [];
      for (const b of blocks) parts.push((await b.innerText()).trim());
      return parts.join('\n\n');
    }
    return (await lastC.innerText()).trim();
  } catch (_) { return ''; }
}

(async () => {
  let browser;
  try { browser = await chromium.connectOverCDP('http://localhost:9223'); }
  catch (e) { console.log(JSON.stringify({ ok: false, error: 'CDP: ' + e.message })); process.exit(2); }
  const ctx = browser.contexts()[0];
  process.stderr.write('PAGES:\n' + ctx.pages().map(p => '  ' + p.url()).join('\n') + '\n');
  const start = Date.now();
  let best = '', stable = 0;
  while (Date.now() - start < MAX) {
    const page = ctx.pages().find(p => p.url().includes(URLSUB));
    if (!page) { process.stderr.write('target tab not found yet\n'); await new Promise(r => setTimeout(r, 4000)); continue; }
    let stop = false;
    try { stop = !!(await page.$(SEL.stopButton)); } catch (_) {}
    const t = await pageText(page);
    process.stderr.write(`[${new Date().toISOString()}] len=${t.length} stop=${stop} stable=${stable}\n`);
    if (!stop && t && t === best && t.length > 400) { stable++; if (stable >= 4) break; }
    else stable = 0;
    if (t.length >= best.length) best = t;
    await new Promise(r => setTimeout(r, 4000));
  }
  console.log(JSON.stringify({ ok: best.length > 400, len: best.length, text: best }));
  process.exit(0);
})();
