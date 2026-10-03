import puppeteer from "puppeteer-core";
import fs from "fs";
const exe="/opt/pw-browsers/chromium-1194/chrome-linux/chrome";
const b=await puppeteer.launch({executablePath:exe,headless:true,args:["--no-sandbox","--disable-gpu","--lang=pl-PL","--ignore-certificate-errors-spki-list="+process.env.SPKI]});
const p=await b.newPage(); await p.setViewport({width:820,height:700,deviceScaleFactor:1});
await p.goto("https://www.youtube.com/results?search_query=marketing+viral",{waitUntil:"networkidle2",timeout:60000}); await new Promise(r=>setTimeout(r,2500));
const svg=await p.evaluate(()=>{
  const s=document.querySelector("ytd-topbar-logo-renderer #logo-icon svg, ytd-topbar-logo-renderer svg, #logo-icon svg");
  return s?s.outerHTML:null;});
console.log(svg?svg.length:"none");
if(svg) fs.writeFileSync("assets/logos/youtube_full.svg",svg);
await b.close();
