// Captures the REAL https://clipcash.systemskala.pl/ (mobile layout, 430 css px wide, DSF 3) in the states r12 needs.
// Safety: the page's own account-lookup + every non-GET /api call is aborted, so nothing is ever sent or submitted;
// we type into a local page instance, press with mouse.down and release OUTSIDE the button (no click is ever fired).
import { chromium } from 'playwright-core';
import fs from 'fs';
const W = 430, H = 900, DSF = 3;
const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--no-sandbox', `--proxy-server=${process.env.HTTPS_PROXY || ''}`, '--ignore-certificate-errors'],
});
let page, ctx;
for (let i = 0; i < 25; i++) {           // the site A/B-tests its headline per visit: we need the "3 filmy na jutro" variant
  ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: DSF, locale: 'pl-PL', ignoreHTTPSErrors: true });
  page = await ctx.newPage();
  await page.route('**/api/**', r => { const q = r.request(); if (q.method() === 'GET' && !/\/lookup/.test(q.url())) r.continue(); else r.abort(); });
  await page.goto('https://clipcash.systemskala.pl/', { waitUntil: 'networkidle', timeout: 60000 }).catch(e => console.log('goto warn', e.message));
  await page.waitForTimeout(2500);
  const h = await page.evaluate(() => document.querySelector('h2')?.innerText);
  console.log('try', i, h);
  if (/3 filmy/.test(h)) break;
  await ctx.close();
}
await page.addStyleTag({ content: 'div.fixed.z-50{display:none !important} .say-swap{display:none !important} *,*::before,*::after{transition:none !important}' });
await page.addStyleTag({ content: '.animate-spin{visibility:hidden !important}' }).then(h => h.evaluate(e => e.id = 'hidespin'));
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(500);

const shot = async (name) => { await page.screenshot({ path: `full/${name}.png`, fullPage: true }); console.log('shot', name); };
const rect = (sel) => page.evaluate((s) => { const r = document.querySelector(s).getBoundingClientRect(); return { x: r.x, y: r.y + scrollY, w: r.width, h: r.height }; }, sel);
const NICK = 'input[placeholder^="nick"]';
const metrics = { W, H, DSF };
metrics.nick = await rect(NICK);
metrics.btn = await rect('button.btn-3d-accent');
metrics.h2 = await rect('h2');
metrics.card = await rect('section.rise');
metrics.nickBox = await page.evaluate((s) => { let e = document.querySelector(s); while (e && getComputedStyle(e).backgroundColor !== 'rgb(255, 255, 255)') e = e.parentElement; const r = e.getBoundingClientRect(); return { x: r.x, y: r.y + scrollY, w: r.width, h: r.height }; }, NICK);
const pRect = (re) => page.evaluate((src) => { const p = [...document.querySelectorAll('p')].find(p => new RegExp(src).test(p.innerText)); const r = p.getBoundingClientRect(); return { x: r.x, y: r.y + scrollY, w: r.width, h: r.height }; }, re);
metrics.zaDarmo = await pRect('^Za darmo');
metrics.sub = await pRect('^Wzorowane');
metrics.eyebrow = await pRect('^ANALIZA');
const measure = (txt) => page.evaluate(({ s, txt }) => {
  const inp = document.querySelector(s); const cs = getComputedStyle(inp);
  const sp = document.createElement('span'); sp.style.cssText = `position:absolute;visibility:hidden;white-space:pre;font:${cs.font};letter-spacing:${cs.letterSpacing}`; sp.textContent = txt; document.body.appendChild(sp);
  const w = sp.getBoundingClientRect().width; sp.remove(); const r = inp.getBoundingClientRect();
  return +(r.x + parseFloat(cs.paddingLeft) + w).toFixed(3);
}, { s: NICK, txt });
metrics.caretX = [await measure('')];

await shot('base');

// highlight state for the "Za darmo" line (real DOM: only a background + ink text added; geometry unchanged)
await page.evaluate(() => {
  const p = [...document.querySelectorAll('p')].find(p => /^Za darmo/.test(p.innerText));
  const t = p.textContent; p.innerHTML = '';
  const sp = document.createElement('span'); sp.id = '__hl'; sp.textContent = t;
  sp.style.cssText = 'background:#FBEEE8;color:#111111;font-weight:500;padding:3px 14px;margin:0 -14px;border-radius:10px;box-decoration-break:clone;-webkit-box-decoration-break:clone';
  p.appendChild(sp);
});
await shot('highlight');
await page.evaluate(() => { const sp = document.getElementById('__hl'); const p = sp.parentElement; p.textContent = sp.textContent; });
await shot('base2');   // sanity: must equal base

// typing in the REAL nick input
await page.focus(NICK);
await page.waitForTimeout(150);
await shot('t0');
const word = 'twoj_nick';
for (let i = 0; i < word.length; i++) {
  await page.keyboard.type(word[i]);
  await page.waitForTimeout(60);
  await shot('t' + (i + 1));
  metrics.caretX.push(await measure(word.slice(0, i + 1)));
  if (i === 2) {   // grab the real spinner (frozen at 0 deg) as its own little image
    await page.evaluate(() => document.getElementById('hidespin').remove());
    await page.addStyleTag({ content: '.animate-spin{animation:none !important}' });
    await page.waitForTimeout(100);
    const sr = await page.evaluate(() => { const e = document.querySelector('.animate-spin'); if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x, y: r.y + scrollY, w: r.width, h: r.height }; });
    metrics.spinner = sr;
    if (sr) await page.screenshot({ path: 'full/spinner.png', clip: { x: Math.round(sr.x) - 1, y: Math.round(sr.y) - 1, width: 18, height: 18 } });
    await page.addStyleTag({ content: '.animate-spin{visibility:hidden !important}' }).then(h => h.evaluate(e => e.id = 'hidespin'));
    await page.waitForTimeout(100);
  }
}
// press (mouse.down on the real button), then release OUTSIDE it so no click is ever dispatched on the button
const b = metrics.btn;
await page.mouse.move(b.x + b.w * 0.62, b.y + b.h / 2, { steps: 8 });
await page.waitForTimeout(200);
await page.mouse.down();
await page.waitForTimeout(200);
await shot('press');
metrics.btnPress = await page.evaluate(() => { const e = document.querySelector('button.btn-3d-accent'); const cs = getComputedStyle(e); return { transform: cs.transform, bs: cs.boxShadow }; });
await page.mouse.move(8, 8, { steps: 6 });
await page.mouse.up();
await page.waitForTimeout(250);
await shot('idle');
fs.writeFileSync('metrics.json', JSON.stringify(metrics, null, 1));
console.log(JSON.stringify(metrics));
await browser.close();
