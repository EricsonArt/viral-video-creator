import puppeteer from "puppeteer-core";
import {pathToFileURL} from "url";
import path from "path";
const [,, comp, times, outprefix, clip] = process.argv;
const exe="/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const b=await puppeteer.launch({executablePath:exe,headless:true,args:["--no-sandbox","--disable-gpu","--allow-file-access-from-files"]});
const p=await b.newPage();
await p.setViewport({width:1080,height:1920,deviceScaleFactor:1});
p.on("console",m=>console.log("[console]",m.text()));
p.on("pageerror",e=>console.log("[pageerror]",e.message));
p.on("requestfailed",r=>console.log("[reqfail]",r.url()));
await p.goto(pathToFileURL(path.resolve(comp+".html")).href,{waitUntil:"load"});
await p.evaluate(()=>document.fonts.ready);
const id=await p.evaluate(()=>Object.keys(window.__timelines||{}));
console.log("timelines:",id);
for(const t of times.split(",")){
  await p.evaluate((id,t)=>{const tl=window.__timelines[id[0]]; tl.time(parseFloat(t),false);},id,t);
  await new Promise(r=>setTimeout(r,60));
  const opts={path:`${outprefix}_${t}.png`,omitBackground:!!process.env.OMIT};
  if(clip){const [x,y,w,h]=clip.split(",").map(Number); opts.clip={x,y,width:w,height:h};}
  await p.screenshot(opts);
}
await b.close();
