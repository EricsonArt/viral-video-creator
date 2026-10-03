import { chromium } from 'playwright-core';
const [,, url, out, w='1280', h='900', full='0'] = process.argv;
const browser = await chromium.launch({
  executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
  args: ['--no-sandbox', `--proxy-server=${process.env.HTTPS_PROXY || ''}`, '--ignore-certificate-errors'],
});
const ctx = await browser.newContext({ viewport: { width: +w, height: +h }, deviceScaleFactor: 2, locale: 'pl-PL', ignoreHTTPSErrors: true });
const page = await ctx.newPage();
await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 }).catch(e => console.log('goto warn', e.message));
await page.waitForTimeout(2500);
await page.screenshot({ path: out, fullPage: full === '1' });
console.log('saved', out, await page.title());
await browser.close();
