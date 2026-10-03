import { chromium } from 'playwright-core';
import fs from 'fs';
const src = fs.readFileSync('../assets/logos/cc_light.svg', 'utf8');
const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setContent(`<body>${src}</body>`);
const res = await page.evaluate(() => {
  const svg = document.querySelector('svg');
  const paths = [...svg.querySelectorAll('path')];
  const info = paths.map((p, i) => { const b = p.getBBox(); return { i, fill: p.getAttribute('fill'), x: b.x, y: b.y, w: b.width, h: b.height, d: p.getAttribute('d') }; });
  return info;
});
await browser.close();
const clay = res.filter(p => p.fill === '#D97757');
const dark = res.filter(p => p.fill === '#141413');
console.log('paths', res.length, 'clay', clay.length, 'dark', dark.length);
console.log(dark.map(p => `${p.i}:x=${p.x.toFixed(1)} w=${p.w.toFixed(1)}`).join('\n'));
const mark = clay[0];
const pad = 0.5;
fs.writeFileSync('../assets/logos/claude_mark.svg',
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${(mark.x - pad).toFixed(2)} ${(mark.y - pad).toFixed(2)} ${(mark.w + 2*pad).toFixed(2)} ${(mark.h + 2*pad).toFixed(2)}"><path d="${mark.d}" fill="#D97757"/></svg>`);
// Claude Code = mark + first 10 dark glyph paths (Claude Code), drop the last 4 (Docs)
const keep = dark.slice(0, 10);
const x1 = Math.max(...keep.map(p => p.x + p.w));
const y0 = Math.min(mark.y, ...keep.map(p => p.y)), y1 = Math.max(mark.y + mark.h, ...keep.map(p => p.y + p.h));
const body = [mark, ...keep].map(p => `<path d="${p.d}" fill="${p.fill}"/>`).join('');
fs.writeFileSync('../assets/logos/claude_code_lockup.svg',
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${(mark.x - pad).toFixed(2)} ${(y0 - pad).toFixed(2)} ${(x1 - mark.x + 2*pad).toFixed(2)} ${(y1 - y0 + 2*pad).toFixed(2)}">${body}</svg>`);
console.log('written mark + lockup');
