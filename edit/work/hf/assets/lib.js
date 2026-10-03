/* Deterministic scene helpers: every scene is a pure function frame(t) of local time. */
(function(){
const E=(n)=>gsap.parseEase(n);
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const prog=(t,a,b)=>clamp((t-a)/(b-a));
const ease=(n,t,a,b)=>E(n)(prog(t,a,b));
const mix=(a,b,u)=>a+(b-a)*u;
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
function mount(id,duration,frame){
  const clock={t:0};
  const tl=gsap.timeline({paused:true});
  tl.to(clock,{t:duration,duration:duration,ease:"none",onUpdate(){frame(clock.t)}},0);
  window.__timelines=window.__timelines||{}; window.__timelines[id]=tl;
  frame(0);
}
/* run info: local time = source time - run.src0 */
function run(id){const r=PLAN.runs[id];return {r,src0:r.src0,dur:r.dur,L:(s)=>s-r.src0,W:(i)=>({s:PLAN.words[i].s-r.src0,e:PLAN.words[i].e-r.src0,w:PLAN.words[i].w})};}
/* text helpers */
function setText(el,s){ if(el._s!==s){ el.textContent=s; el._s=s; } }
function setHTML(el,s){ if(el._h!==s){ el.innerHTML=s; el._h=s; } }
function setStyle(el,k,v){ const key="_st_"+k; if(el[key]!==v){ el.style[k]=v; el[key]=v; } }
function blur(el,px,op){ // DOF helper; never leave filter:blur(0)
  setStyle(el,"filter",px>0.05?"blur("+px.toFixed(2)+"px)":"none");
  if(op!==undefined) setStyle(el,"opacity",op.toFixed(3));
}
/* typed text: items=[{t0,t1,text}] each revealed linearly; returns joined string */
function typedWords(items,t){
  let out="";
  for(const it of items){
    if(t<it.t0) break;
    const u=clamp((t-it.t0)/Math.max(0.001,it.t1-it.t0));
    const n=Math.ceil(u*it.text.length-1e-6);
    out+=(out?" ":"")+it.text.slice(0,Math.max(n,1));
    if(u<1) break;
  }
  return out;
}
function typedLinear(text,t,t0,t1){ const u=clamp((t-t0)/(t1-t0)); return text.slice(0,Math.floor(u*text.length+1e-6)); }
function caretOn(t){ return (Math.floor(t*2.4)%2)===0; }
/* camera: segs=[{t0,t1,ease,to:{x,y,s}}], start state init. world point (x,y) sits under screen anchor (ax,ay) */
function camState(init,segs,t){
  let cur={...init};
  for(const s of segs){
    if(t<=s.t0) break;
    const u=E(s.ease||"power2.inOut")(prog(t,s.t0,s.t1));
    const nx={x:mix(cur.x,s.to.x,u),y:mix(cur.y,s.to.y,u),s:mix(cur.s,s.to.s,u)};
    if(t<s.t1) return nx;
    cur={...s.to};
  }
  return cur;
}
function camSpeed(init,segs,t,dt=1/240){ const a=camState(init,segs,t-dt),b=camState(init,segs,t+dt); return Math.hypot(b.x-a.x,b.y-a.y)/(2*dt); }
function applyCam(world,cam,ax,ay){
  const tx=ax-cam.x*cam.s, ty=ay-cam.y*cam.s;
  setStyle(world,"transform","translate3d("+tx.toFixed(3)+"px,"+ty.toFixed(3)+"px,0) scale("+cam.s.toFixed(5)+")");
}
/* cursor: pts=[{t,x,y}] eased between; clicks=[t] */
function cursorAt(pts,t){
  if(t<=pts[0].t) return {x:pts[0].x,y:pts[0].y};
  for(let i=1;i<pts.length;i++){
    if(t<=pts[i].t){ const u=E(pts[i].ease||"power2.inOut")(prog(t,pts[i-1].t,pts[i].t)); return {x:mix(pts[i-1].x,pts[i].x,u),y:mix(pts[i-1].y,pts[i].y,u)}; }
  }
  const l=pts[pts.length-1]; return {x:l.x,y:l.y};
}
function press(clicks,t){ // 0..1 pressed amount
  let v=0; for(const c of clicks){ const d=t-c; if(d>=0&&d<0.22) v=Math.max(v,d<0.08?d/0.08:1-(d-0.08)/0.14); } return v;
}
function ringAt(clicks,t){ for(const c of clicks){ const d=t-c; if(d>=0&&d<0.5) return {u:d/0.5}; } return null; }
const CURSOR_SVG='<svg viewBox="0 0 54 54" width="54" height="54"><path d="M8 4 L8 40 L17 31.5 L23.5 46 L30 43 L23.5 29 L36 28.5 Z" fill="#111" stroke="#fff" stroke-width="3.2" stroke-linejoin="round"/></svg>';
window.HF={E,clamp,prog,ease,mix,$,$$,mount,run,setText,setHTML,setStyle,blur,typedWords,typedLinear,caretOn,camState,camSpeed,applyCam,cursorAt,press,ringAt,CURSOR_SVG};
})();
