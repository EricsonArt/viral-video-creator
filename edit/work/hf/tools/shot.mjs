import puppeteer from "puppeteer-core";
const [,, url, out, w="1032", h="1040", dsf="2", wait="3000"] = process.argv;
const exe = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const b = await puppeteer.launch({executablePath: exe, headless: true, args:["--no-sandbox","--disable-gpu","--lang=pl-PL","--ignore-certificate-errors-spki-list=PS48cX347wDVcRynzq+DFqswl2PLNE1sG6uQvxMCOS0="]});
const p = await b.newPage();
await p.setViewport({width:+w,height:+h,deviceScaleFactor:+dsf});
await p.setExtraHTTPHeaders({"Accept-Language":"pl-PL,pl;q=0.9,en;q=0.5"});
try { await p.goto(url,{waitUntil:"networkidle2",timeout:60000}); } catch(e){ console.log("goto:",e.message); }
await new Promise(r=>setTimeout(r,+wait));
await p.screenshot({path:out});
console.log("title:", await p.title());
await b.close();
