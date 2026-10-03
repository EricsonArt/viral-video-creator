import puppeteer from "puppeteer-core";
import fs from "fs";
const exe="/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const SPKI=process.env.SPKI;
const b=await puppeteer.launch({executablePath:exe,headless:true,args:["--no-sandbox","--disable-gpu","--lang=pl-PL","--ignore-certificate-errors-spki-list="+SPKI]});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
// --- youtubetranscript.com states
{
  const p=await b.newPage(); await p.setViewport({width:1032,height:1040,deviceScaleFactor:2});
  await p.goto("https://youtubetranscript.com",{waitUntil:"networkidle2",timeout:60000}); await sleep(1500);
  // hide cookie banners/overlays if any, find input + button
  const info=await p.evaluate(()=>{
    const inp=document.querySelector('input[type="text"],input[name],input'); const btn=document.querySelector('button, input[type=submit], .btn');
    const r=e=>{const q=e.getBoundingClientRect();return {x:q.x,y:q.y,w:q.width,h:q.height,tag:e.tagName,cls:e.className,ph:e.placeholder||e.textContent.trim().slice(0,30)}};
    return {inp:r(inp),btn:r(btn),all:[...document.querySelectorAll('input,button,a.btn')].map(r)};
  });
  console.log(JSON.stringify(info,null,1));
  fs.writeFileSync("../caps/ytt_rects.json",JSON.stringify(info));
  await p.screenshot({path:"assets/ytt_idle.png"});
  await p.mouse.click(211+100,353.6+24); await p.keyboard.type("https://youtu.be/hV3Qm2Zr8Kc",{delay:5});
  await p.evaluate(()=>document.activeElement&&document.activeElement.blur());
  await sleep(300); await p.screenshot({path:"assets/ytt_pasted.png"});
  await p.mouse.move(676+72,353.6+24); await sleep(250);
  await p.screenshot({path:"assets/ytt_hover.png"});
  await p.mouse.down(); await sleep(150);
  await p.screenshot({path:"assets/ytt_go.png"});
  await p.close();
}
// --- YouTube header (real) at 800px viewport
{
  const p=await b.newPage(); await p.setViewport({width:820,height:700,deviceScaleFactor:3});
  await p.setExtraHTTPHeaders({"Accept-Language":"pl-PL,pl;q=0.9"});
  await p.goto("https://www.youtube.com/results?search_query=marketing+viral",{waitUntil:"networkidle2",timeout:60000}); await sleep(3000);
  const hdr=await p.evaluate(()=>{const h=document.querySelector("#masthead-container, ytd-masthead"); const q=h.getBoundingClientRect(); const c=document.querySelector("#chips-wrapper, ytd-feed-filter-chip-bar-renderer"); const qc=c?c.getBoundingClientRect():null; return {m:{x:q.x,y:q.y,w:q.width,h:q.height},c:qc&&{x:qc.x,y:qc.y,w:qc.width,h:qc.height}};});
  console.log(JSON.stringify(hdr));
  await p.screenshot({path:"../caps/yt_820.png"});
  await p.close();
}
await b.close();
