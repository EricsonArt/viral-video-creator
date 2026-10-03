// the page's own loading spinner (Tailwind classes copied from the real DOM), frozen at 0deg, on the real white input row
import { chromium } from 'playwright-core';
const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--no-sandbox', `--proxy-server=${process.env.HTTPS_PROXY || ''}`, '--ignore-certificate-errors'],
});
const ctx = await browser.newContext({ viewport: { width: 430, height: 900 }, deviceScaleFactor: 3, locale: 'pl-PL', ignoreHTTPSErrors: true });
const page = await ctx.newPage();
await page.route('**/api/**', r => r.abort());
await page.goto('https://clipcash.systemskala.pl/', { waitUntil: 'networkidle', timeout: 60000 }).catch(e => console.log('goto warn', e.message));
await page.waitForTimeout(2000);
await page.addStyleTag({ content: 'div.fixed.z-50{display:none !important} *,*::before,*::after{transition:none !important} .animate-spin{animation:none !important}' });
const r = await page.evaluate(() => {
  const inp = document.querySelector('input[placeholder^="nick"]'); const row = inp.parentElement;
  const sp = document.createElement('span'); sp.className = 'h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-accent border-t-transparent'; sp.setAttribute('aria-hidden', 'true');
  row.appendChild(sp); const b = sp.getBoundingClientRect(); return { x: b.x, y: b.y + scrollY, w: b.width, h: b.height };
});
console.log(JSON.stringify(r));
await page.screenshot({ path: 'spinner.png', clip: { x: r.x - 1, y: r.y - 1, width: r.w + 2, height: r.h + 2 } });
await browser.close();
