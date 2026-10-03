#!/usr/bin/env python3
"""R2, R4, R5, R7 + CTA compositions (imports shared helpers from gen_hf.py)."""
import json, sys
from gen_hf import *   # page, write, RUN, FPS, ev, EVENTS, typing_script, caret_js, CLAUDE_PATH

GITHUB_PATH = open('hf/assets/logos/github.svg').read().split(' d="')[1].split('"')[0]

MASCOT = """<svg width="150" height="188" viewBox="0 0 120 150" xmlns="http://www.w3.org/2000/svg">
<defs><radialGradient id="mb" cx="40%" cy="30%" r="80%"><stop offset="0" stop-color="#FF8B4E"/><stop offset="1" stop-color="#FF5A1F"/></radialGradient>
<radialGradient id="mball" cx="35%" cy="30%" r="70%"><stop offset="0" stop-color="#7C9BFF"/><stop offset="1" stop-color="#2447E8"/></radialGradient></defs>
<path d="M62 30 Q66 14 75 9" stroke="#FF6A2C" stroke-width="4" fill="none" stroke-linecap="round"/><circle cx="76" cy="8" r="6.5" fill="url(#mball)"/>
<ellipse cx="14" cy="94" rx="9" ry="15" fill="#FF6A2C"/><ellipse cx="106" cy="94" rx="9" ry="15" fill="#FF6A2C"/>
<ellipse cx="60" cy="86" rx="46" ry="52" fill="url(#mb)"/>
<ellipse cx="60" cy="104" rx="29" ry="21" fill="#FF9166" opacity=".85"/>
<ellipse cx="38" cy="42" rx="15" ry="7" fill="#fff" opacity=".28" transform="rotate(-25 38 42)"/>
<circle cx="44" cy="68" r="15.5" fill="#fff"/><circle cx="78" cy="68" r="15.5" fill="#fff"/>
<circle cx="47" cy="72" r="7.5" fill="#15110F"/><circle cx="81" cy="72" r="7.5" fill="#15110F"/>
<circle cx="49" cy="69.5" r="2.2" fill="#fff"/><circle cx="83" cy="69.5" r="2.2" fill="#fff"/>
<circle cx="29" cy="89" r="6" fill="#FF9AA0" opacity=".55"/><circle cx="93" cy="89" r="6" fill="#FF9AA0" opacity=".55"/>
<path d="M50 89 Q60 99 70 89" stroke="#3B1B0E" stroke-width="3.2" fill="none" stroke-linecap="round"/>
<ellipse cx="42" cy="139" rx="15" ry="7.5" fill="#F2551A"/><ellipse cx="78" cy="139" rx="15" ry="7.5" fill="#F2551A"/></svg>"""

OMNI_GLYPH = """<svg width="{w}" height="{w}" viewBox="14 14 62 56" xmlns="http://www.w3.org/2000/svg"><g stroke="#fff" stroke-width="5.5" stroke-linecap="round" fill="none"><line x1="22" y1="42" x2="38" y2="42"/><path d="M39 42 C52 42,54 26,66 24"/><path d="M39 42 C54 42,56 42,68 42"/><path d="M39 42 C52 42,54 58,66 60"/></g><circle cx="39" cy="42" r="5.6" fill="#fff"/></svg>"""

def check_svg(w, bg='#34C759'):
    return f'<svg width="{w}" height="{w}" viewBox="0 0 40 40"><circle cx="20" cy="20" r="20" fill="{bg}"/><path d="M11 20.5 L17.5 27 L29.5 13.5" fill="none" stroke="#fff" stroke-width="4.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def cam_xy(fx, fy, s, vw, vh, iw, ih):
    """top-left translation so that image point (fx,fy) sits at the view centre, clamped to keep the image covering the view."""
    x = vw / 2 - fx * s; y = vh / 2 - fy * s
    x = min(0, max(vw - iw * s, x)); y = min(0, max(vh - ih * s, y))
    return round(x, 1), round(y, 1)

# ================================================================= R2
def gen_r2():
    r = RUN['R2']; dur = r['dur_f'] / FPS
    FW, FH = 1032, 1040
    IW, IH = 1279, 857
    s0 = FH / IH   # cover scale 1.2135
    A = cam_xy(590, 428.5, s0, FW, FH, IW, IH)
    B = cam_xy(660, 460, 1.42, FW, FH, IW, IH)
    C = cam_xy(640, 448, 1.30, FW, FH, IW, IH)
    css = f"""
#cam{{position:absolute;left:0;top:0;width:100%;height:100%}}
#r2-gh{{left:110px;top:470px;width:860px;height:500px;border-radius:40px}}
#r2-gh .mk{{position:absolute;left:64px;top:64px}}
#r2-gh .own{{position:absolute;left:64px;top:232px;font-size:44px;line-height:60px;font-weight:600;color:#6B6B6B}}
#r2-gh .nm{{position:absolute;left:58px;top:294px;font-size:104px;line-height:124px;font-weight:700;letter-spacing:-2px;color:#111}}
#r2-gh .pub{{position:absolute;right:64px;top:74px;border:3px solid #D0D7DE;border-radius:40px;padding:6px 26px;font-size:30px;color:#57606A;font-weight:600}}
#r2-gh .ds{{position:absolute;left:64px;top:430px;font-size:32px;line-height:44px;color:#57606A}}
#r2-logo{{left:0;top:1100px;width:1080px;height:1920px}}
#r2-tile{{position:absolute;left:410px;top:500px;width:260px;height:260px;border-radius:72px;
  background:linear-gradient(145deg,#F0647A 0%,#E54D5E 100%);display:flex;align-items:center;justify-content:center;
  box-shadow:0 60px 120px rgba(24,24,32,.16),0 24px 48px rgba(24,24,32,.10),0 4px 10px rgba(24,24,32,.06)}}
#r2-word{{position:absolute;left:0;width:1080px;top:800px;line-height:136px;text-align:center;font-size:112px;font-weight:700;letter-spacing:-2px;color:#111}}
#r2-bgblur{{position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:hidden;opacity:0}}
#r2-bgblur .dup{{position:absolute;left:-900px;top:-120px;width:2865px;height:1920px;background:url("assets/logos/omniroute_dashboard.png") 0 0/100% 100% no-repeat;filter:blur(40px) saturate(.7) brightness(1.05)}}
#r2-bgblur .wash{{position:absolute;left:0;top:0;width:100%;height:100%;background:rgba(255,255,255,.93)}}
#r2-frame{{position:absolute;left:24px;top:200px;width:{FW}px;height:{FH}px;border-radius:36px;background:#fff;overflow:hidden;opacity:0;
  box-shadow:0 60px 120px rgba(24,24,32,.16),0 24px 48px rgba(24,24,32,.10),0 4px 10px rgba(24,24,32,.06)}}
#r2-img{{position:absolute;left:0;top:0;width:{IW}px;height:{IH}px;transform-origin:0 0}}
"""
    body = f"""
<div id="r2-bgblur"><div class="dup"></div><div class="wash"></div></div>
<div id="cam" class="clip" data-start="0" data-duration="{dur:.5f}" data-track-index="0">
  <div id="r2-gh" class="card">
    <div class="mk"><svg width="150" height="150" viewBox="0 0 24 24"><path fill="#111" d="{GITHUB_PATH}"/></svg></div>
    <div class="pub">Public</div>
    <div class="own">diegosouzapw /</div>
    <div class="nm">OmniRoute</div>
    <div class="ds">Free MIT AI gateway</div>
  </div>
  <div id="r2-logo" class="abs">
    <div id="r2-tile">{OMNI_GLYPH.format(w=150)}</div>
    <div id="r2-word">OmniRoute</div>
  </div>
</div>
<div id="r2-frame"><img id="r2-img" src="assets/logos/omniroute_dashboard.png" alt="OmniRoute dashboard"/></div>
"""
    script = f"""
gsap.set("#r2-img",{{x:{A[0]},y:{A[1]},scale:{s0:.4f}}});
gsap.set("#r2-logo",{{opacity:0}});
tl.set("#r2-logo",{{opacity:1}},2.0);
// STEP to next item: world camera 0.5 s power3.inOut, starts 0.25 s before the name is spoken ("OmniRoute" ~2.3 s)
tl.fromTo("#cam",{{y:0}},{{y:-1100,duration:.5,ease:"power3.inOut"}},2.05);
// logo -> real UI reveal (frame stays stationary, only the picture inside moves)
tl.to("#r2-logo",{{opacity:0,scale:1.06,duration:.45,ease:"power2.inOut",transformOrigin:"540px 720px"}},3.12);
tl.fromTo("#r2-bgblur",{{opacity:0}},{{opacity:1,duration:.6,ease:"power2.out"}},3.12);
tl.fromTo("#r2-frame",{{opacity:0,y:50,scale:.95,transformOrigin:"540px 720px"}},{{opacity:1,y:0,scale:1,duration:.6,ease:"power3.out"}},3.1);
// internal camera moves 1.15x-1.4x, 0.6 s, power2.inOut
tl.to("#r2-img",{{x:{B[0]},y:{B[1]},scale:1.42,duration:.6,ease:"power2.inOut"}},3.95);
tl.to("#r2-img",{{x:{C[0]},y:{C[1]},scale:1.30,duration:.6,ease:"power2.inOut"}},5.25);
"""
    ev('R2', 3.62, 'pop', 'real OmniRoute UI frame lands')
    return page('r2', dur, css, body, script)

# ================================================================= R4
def gen_r4():
    r = RUN['R4']; dur = r['dur_f'] / FPS
    OFF = 1080        # world x offset of card B
    X1 = 463          # camera travel at the whip midpoint (matches speeds of out/in curves)
    spans = ''
    css = """
#cam{position:absolute;left:0;top:0;width:100%;height:100%;transform-origin:540px 760px}
#r4-a{left:110px;top:420px;width:860px;height:600px;border-radius:44px}
#r4-b{left:__BX__px;top:400px;width:860px;height:760px;border-radius:44px}
#r4-a .hd{position:absolute;left:56px;top:54px;display:flex;align-items:center;gap:22px;font-size:46px;font-weight:600}
#r4-a .track{position:absolute;left:56px;top:250px;width:748px;height:52px;border-radius:26px;background:#EFEDE6;overflow:hidden}
#r4-a .fill{position:absolute;left:0;top:0;height:52px;width:466px;border-radius:26px;background:#D97757}
#r4-a .pct{position:absolute;left:56px;top:330px;font-size:112px;font-weight:700;letter-spacing:-3px;color:#111}
#r4-stamp{position:absolute;right:56px;top:76px;border:10px solid #FF3B30;border-radius:22px;padding:2px 26px;font-size:76px;font-weight:700;color:#FF3B30;letter-spacing:2px;opacity:0;transform-origin:50% 50%}
#r4-b .tiles{position:absolute;left:94px;top:50px;display:flex;gap:24px}
#r4-b .tile{position:relative;width:150px;height:150px;border-radius:48px;background:#F7F6F2;display:flex;align-items:center;justify-content:center}
#r4-b .tile img{width:84px;height:84px}
#r4-badge{position:absolute;right:-14px;top:-14px;opacity:0}
#r4-b .sess{position:absolute;left:56px;top:262px;width:748px;height:440px;border-radius:30px;background:#F8F7F3;overflow:hidden}
#r4-b .row{position:absolute;left:30px;height:34px;display:flex;align-items:center;gap:16px;font-size:30px;opacity:0}
#r4-b .row i{display:block;width:14px;height:14px;border-radius:50%;background:#34C759}
#r4-b .row b{font-weight:600}
#r4-b .row span{font-family:"JetBrains Mono",monospace;font-weight:500;color:#5E5D59;font-size:28px}
#r4-b .bar{position:absolute;left:30px;height:26px;border-radius:13px;background:#D7E9DC;opacity:0}
#r4-b .sweep{position:absolute;left:30px;top:396px;width:688px;height:10px;border-radius:5px;background:#E6E4DC;overflow:hidden}
#r4-b .sweep div{position:absolute;left:0;top:0;width:200px;height:10px;border-radius:5px;background:#34C759}
""".replace('__BX__', str(110 + OFF))
    tiles = ''.join(f'<div class="tile"><img src="assets/logos/{n}.svg" alt=""/>{"<div id=r4-badge>" + check_svg(60) + "</div>" if i == 0 else ""}</div>' for i, n in enumerate(['gemini-color', 'deepseek-color', 'mistral-color', 'groq']))
    rows = [('Read', 'route.ts', 20), ('Write', 'fallback.ts', 74), ('Read', 'session.ts', 128), ('Write', 'limits.ts', 182), ('Read', 'config.ts', 236), ('Write', 'index.ts', 290)]
    rows_html = ''.join(f'<div class="row" id="r4-row{i}" style="top:{y}px"><i></i><b>{k}</b><span>{f}</span></div>' for i, (k, f, y) in enumerate(rows))
    body = f"""
<div id="cam" class="clip" data-start="0" data-duration="{dur:.5f}" data-track-index="0">
  <div id="r4-a" class="card">
    <div class="hd"><svg width="64" height="64" viewBox="0 0 24 24"><path fill="#D97757" d="{CLAUDE_PATH}"/></svg><span>Claude</span></div>
    <div class="track"><div class="fill" id="r4-fill"></div></div>
    <div class="pct" id="r4-pct">62%</div>
    <div id="r4-stamp">LIMIT</div>
  </div>
  <div id="r4-b" class="card">
    <div class="tiles">{tiles}</div>
    <div class="sess">{rows_html}<div class="sweep"><div id="r4-sweep"></div></div></div>
  </div>
</div>"""
    # whip: outgoing 0.45 s power3.in, incoming 0.6 s power3.out, swap/midpoint at WT
    WT = 2.0
    script = f"""
const pc = {{v:62}};
tl.to(pc,{{v:100,duration:.95,ease:"power2.inOut",onUpdate:()=>{{document.getElementById("r4-pct").textContent=Math.round(pc.v)+"%";}}}},0.30);
tl.to("#r4-fill",{{width:748,duration:.95,ease:"power2.inOut"}},0.30);
tl.fromTo("#r4-stamp",{{opacity:0,scale:1.9,rotation:-2}},{{opacity:1,scale:1,rotation:-8,duration:.2,ease:"power4.in"}},1.18);
// WHIP (max one per run): out {WT-.45:.2f}-{WT:.2f} power3.in, in {WT:.2f}-{WT+.6:.2f} power3.out
tl.fromTo("#cam",{{x:0}},{{x:-{X1},duration:.45,ease:"power3.in"}},{WT-.45:.2f});
tl.to("#cam",{{x:-{OFF},duration:.6,ease:"power3.out"}},{WT:.2f});
// DOF: the card that lost focus softens while the new hero is active
tl.to("#r4-a",{{filter:"blur(9px)",opacity:.4,duration:.5,ease:"power2.inOut"}},{WT:.2f});
// free provider card: check badge, then the session keeps streaming
tl.fromTo("#r4-badge",{{opacity:0,scale:.3}},{{opacity:1,scale:1,duration:.38,ease:"back.out(2)"}},3.12);
""" + ''.join(f'tl.fromTo("#r4-row{i}",{{opacity:0,x:-22}},{{opacity:1,x:0,duration:.28,ease:"power2.out"}},{round(3.55 + i * 0.42, 2)});\n' for i in range(6)) + f"""
tl.to("#r4-sweep",{{x:488,duration:1.1,ease:"sine.inOut"}},3.9);
tl.to("#r4-sweep",{{x:0,duration:1.1,ease:"sine.inOut"}},5.1);
// GLIDE (scale change <= 0.04)
tl.to("#cam",{{scale:1.035,duration:2.0,ease:"sine.inOut"}},4.2);
"""
    ev('R4', 1.30, 'pop', 'LIMIT stamp lands')
    ev('R4', WT, 'whoosh', 'WHIP midpoint (camera at peak speed)')
    ev('R4', 2.62, 'pop', 'free provider card lands')
    ev('R4', 3.20, 'chime', 'check badge confirms connection')
    for i in range(6):
        ev('R4', 3.55 + i * 0.42, 'tick', 'session lines stream in')
    return page('r4', dur, css, body, script)

# ================================================================= R5 (SPLIT)
def gen_r5():
    r = RUN['R5']; dur = r['dur_f'] / FPS
    widths = [500, 540, 460, 520, 410, 530, 480, 430, 500, 360]
    bars = ''.join(f'<div class="ln{" hl" if i in (1,4,7) else ""}" id="r5-l{i}" style="top:{40 + i * 43}px;width:{w}px"></div>' for i, w in enumerate(widths))
    css = """
#cam{position:absolute;left:0;top:0;width:100%;height:100%}
#r5-prompt{left:230px;top:46px;width:620px;height:500px;border-radius:40px;overflow:hidden}
#r5-prompt .ln{position:absolute;left:50px;height:24px;border-radius:12px;background:#E4E2DA;transform-origin:0% 50%}
#r5-prompt .ln.hl{background:#EBC2B0}
#r5-short{left:340px;top:201px;width:400px;height:190px;border-radius:40px;opacity:0}
#r5-short .ln{position:absolute;left:44px;height:24px;border-radius:12px;background:#E4E2DA}
#r5-short .ln.hl{background:#EBC2B0}
#r5-wire{position:absolute;left:538px;top:391px;width:4px;height:215px;border-radius:2px;background:#E4E2DA;opacity:0;transform-origin:50% 0%}
#r5-dot{position:absolute;left:530px;top:386px;width:20px;height:20px;border-radius:50%;background:#D97757;opacity:0}
#r5-model{left:440px;top:600px;width:200px;height:200px;border-radius:72px;display:flex;align-items:center;justify-content:center}
"""
    body = f"""
<div id="cam" class="clip fade900" data-start="0" data-duration="{dur:.5f}" data-track-index="0">
  <div id="r5-prompt" class="card">{bars}</div>
  <div id="r5-short" class="card"><div class="ln" style="top:44px;width:300px"></div><div class="ln hl" style="top:84px;width:330px"></div><div class="ln" style="top:124px;width:250px"></div></div>
  <div id="r5-wire"></div><div id="r5-dot"></div>
  <div id="r5-model" class="card"><svg id="r5-spark" width="120" height="120" viewBox="0 0 24 24"><path fill="#D97757" d="M12 1.5 C12.7 7.3 16.7 11.3 22.5 12 C16.7 12.7 12.7 16.7 12 22.5 C11.3 16.7 7.3 12.7 1.5 12 C7.3 11.3 11.3 7.3 12 1.5 Z"/></svg></div>
</div>"""
    script = ""
    for i in range(3, 10):
        script += f'tl.to("#r5-l{i}",{{opacity:0,scaleX:.08,duration:.32,ease:"power2.in"}},{round(0.40 + (i - 3) * 0.055, 3)});\n'
    script += """
tl.to("#r5-prompt",{scaleY:.37,scaleX:.66,opacity:0,duration:.5,ease:"power2.inOut",transformOrigin:"50% 50%"},0.78);
tl.fromTo("#r5-short",{opacity:0,scale:1.12},{opacity:1,scale:1,duration:.42,ease:"power3.out",transformOrigin:"50% 50%"},0.92);
// the compact prompt is sent down the wire to the model tile
tl.fromTo("#r5-wire",{opacity:0,scaleY:0},{opacity:1,scaleY:1,duration:.4,ease:"power2.out"},1.45);
tl.fromTo("#r5-dot",{opacity:0,y:0},{opacity:1,y:0,duration:.1},1.55);
tl.to("#r5-dot",{y:218,duration:.45,ease:"power2.in"},1.62);
tl.to("#r5-dot",{opacity:0,scale:.2,duration:.12},2.06);
tl.fromTo("#r5-model",{scale:1},{scale:1.07,duration:.18,ease:"power2.out",transformOrigin:"50% 50%"},2.04);
tl.to("#r5-model",{scale:1,duration:.3,ease:"power2.inOut"},2.22);
tl.fromTo("#r5-spark",{rotation:0},{rotation:90,duration:.7,ease:"power2.inOut",transformOrigin:"50% 50%"},2.04);
"""
    ev('R5', 2.06, 'pop', 'compressed prompt arrives at the model tile')
    return page('r5', dur, css, body, script)

# ================================================================= R7
def gen_r7():
    r = RUN['R7']; dur = r['dur_f'] / FPS
    CW, CH = 960, 940
    handle = 'eryk_hajduczek'
    spans, tjs, ttimes = typing_script('#r7-typed', handle, 2.95, 14, 'r7t')
    P1 = cam_xy(480, 250, 1.15, CW, CH, CW, CH)
    P2 = cam_xy(480, 700, 1.15, CW, CH, CW, CH)
    css = f"""
#r7-card{{position:absolute;left:60px;top:250px;width:{CW}px;height:{CH}px;border-radius:56px;background:#0B0B0C;overflow:hidden;
  box-shadow:0 60px 120px rgba(24,24,32,.16),0 24px 48px rgba(24,24,32,.10),0 4px 10px rgba(24,24,32,.06)}}
#r7-in{{position:absolute;left:0;top:0;width:{CW}px;height:{CH}px;transform-origin:0 0}}
#r7-lab{{position:absolute;left:100px;top:46px;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:28px;letter-spacing:2.5px;color:#F2A27C}}
#r7-mas{{position:absolute;left:700px;top:40px}}
#r7-h{{position:absolute;left:100px;top:96px;width:580px;font-family:"Instrument Serif",serif;font-size:76px;line-height:78px;letter-spacing:-1.2px;color:#fff}}
#r7-p{{position:absolute;left:100px;top:352px;width:760px;font-size:30px;line-height:44px;color:#A8A8A8;font-weight:400}}
#r7-box{{position:absolute;left:100px;top:540px;width:760px;height:178px;border-radius:44px;background:#fff}}
#r7-box .tt{{position:absolute;left:34px;top:26px;height:52px;border-radius:26px;background:#0B0B0C;color:#fff;font-size:30px;font-weight:600;padding:0 28px;line-height:52px}}
#r7-box .ig{{position:absolute;left:216px;top:26px;height:52px;line-height:52px;font-size:30px;color:#7A7A7A;font-weight:600}}
#r7-box .at{{position:absolute;left:38px;top:96px;font-size:50px;color:#8A8A8A;line-height:64px}}
#r7-box .tx{{position:absolute;left:98px;top:96px;font-size:50px;color:#111;line-height:64px;font-weight:600;white-space:nowrap}}
#r7-ph{{position:absolute;left:98px;top:96px;font-size:44px;color:#8F8F8F;line-height:64px;white-space:nowrap}}
#r7-caret{{display:inline-block;width:4px;height:50px;background:#FF5A1F;vertical-align:middle;opacity:0;margin-left:2px}}
#r7-fT{{position:absolute;left:0;top:0;width:100%;height:120px;background:linear-gradient(#0B0B0C,rgba(11,11,12,0));opacity:0}}
#r7-fB{{position:absolute;left:0;bottom:0;width:100%;height:120px;background:linear-gradient(rgba(11,11,12,0),#0B0B0C);opacity:0}}
#r7-btn{{position:absolute;left:100px;top:770px;width:760px;height:96px;border-radius:48px;background:#FF5A1F;box-shadow:0 8px 0 #D94710,0 24px 40px rgba(255,90,31,.28);
  display:flex;align-items:center;justify-content:center;gap:16px;font-size:38px;font-weight:700;color:#fff}}
"""
    arrow = '<svg width="38" height="38" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    body = f"""
<div id="r7-card" class="clip" data-start="0" data-duration="{dur:.5f}" data-track-index="0">
 <div id="r7-in">
  <div id="r7-lab">ANALIZA KONTA · ZA DARMO</div>
  <div id="r7-mas">{MASCOT}</div>
  <div id="r7-h">3 filmy na jutro, rozpisane pod Twoje konto</div>
  <div id="r7-p">Wzorowane na prawdziwych hitach z Twojej niszy. Do tego to, co hamuje Twoje konto, i jak to naprawić. W minutę.</div>
  <div id="r7-box"><div class="tt">TikTok</div><div class="ig">Instagram</div><div class="at">@</div>
    <div id="r7-ph">nick albo nazwa</div>
    <div class="tx"><span id="r7-typed">{spans}</span><span id="r7-caret"></span></div></div>
  <div id="r7-btn"><span>Chcę moje 3 filmy</span>{arrow}</div>
 </div>
 <div id="r7-fT"></div><div id="r7-fB"></div>
</div>"""
    script = f"""
// product window is the subject: the outer world stays still, only the picture inside moves (1.15x, 0.6 s, power2.inOut)
tl.to("#r7-in",{{x:{P1[0]},y:{P1[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},0.35);
tl.to("#r7-fB",{{opacity:1,duration:.6,ease:"power2.inOut"}},0.35);
tl.to("#r7-in",{{x:{P2[0]},y:{P2[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},2.25);
tl.to("#r7-fB",{{opacity:0,duration:.6,ease:"power2.inOut"}},2.25);
tl.to("#r7-fT",{{opacity:1,duration:.6,ease:"power2.inOut"}},2.25);
tl.to("#r7-in",{{x:{P1[0]},y:{P1[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},4.25);
tl.to("#r7-fT",{{opacity:0,duration:.6,ease:"power2.inOut"}},4.25);
tl.to("#r7-fB",{{opacity:1,duration:.6,ease:"power2.inOut"}},4.25);
{caret_js('#r7-caret', 2.6, ttimes[-1] + 0.45)}
tl.set("#r7-ph",{{opacity:0}},2.93);
{tjs}
// press the button
tl.to("#r7-btn",{{scale:.965,y:6,duration:.09,ease:"power2.out",transformOrigin:"50% 50%"}},3.98);
tl.to("#r7-btn",{{scale:1,y:0,duration:.16,ease:"power2.out"}},4.09);
tl.set("#r7-caret",{{opacity:0}},4.0);
"""
    for t in ttimes:
        ev('R7', t, 'tick', 'handle typing')
    ev('R7', 3.98, 'click', 'button pressed')
    return page('r7', dur, css, body, script)

# ================================================================= CTA (transparent overlay, outro)
def gen_cta():
    t0 = PLAN['onsets']['P10'] - 0.02          # card appears with "to weź link w bio"
    end_s = PLAN['end_s']
    dur = round(round((end_s - t0) * FPS) / FPS, 5)
    handle = 'eryk_hajduczek'
    spans, tjs, ttimes = typing_script('#cta-typed', handle, 0.48, 14, 'ctat')
    css = """
html,body{background:transparent!important}
#root{background:transparent!important}
#cta{position:absolute;left:43px;top:1612px;width:994px;height:212px;border-radius:44px;background:#fff;
  box-shadow:0 60px 120px rgba(24,24,32,.16),0 24px 48px rgba(24,24,32,.10),0 4px 10px rgba(24,24,32,.06)}
#cta .av{position:absolute;left:34px;top:58px;width:96px;height:96px;border-radius:50%;background:#E4E2DA;overflow:hidden}
#cta .at{position:absolute;left:160px;top:62px;font-size:56px;line-height:88px;color:#767676;font-weight:600}
#cta .tx{position:absolute;left:214px;top:62px;font-size:56px;line-height:88px;color:#111;font-weight:600;white-space:nowrap}
#cta-caret{display:inline-block;width:4px;height:58px;background:#FF5A1F;vertical-align:middle;opacity:0;margin-left:2px}
#cta-btn{position:absolute;right:30px;top:62px;width:96px;height:88px;border-radius:44px;background:#FF5A1F;box-shadow:0 6px 0 #D94710;display:flex;align-items:center;justify-content:center}
"""
    body = f"""
<div id="cta" class="clip" data-start="0" data-duration="{dur:.5f}" data-track-index="0">
  <div class="av"><svg width="96" height="96" viewBox="0 0 96 96"><circle cx="48" cy="38" r="17" fill="#fff"/><path d="M14 96 C14 70 30 60 48 60 C66 60 82 70 82 96 Z" fill="#fff"/></svg></div>
  <div class="at">@</div>
  <div class="tx"><span id="cta-typed">{spans}</span><span id="cta-caret"></span></div>
  <div id="cta-btn"><svg width="48" height="48" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
</div>"""
    press = ttimes[-1] + 0.2
    script = f"""
gsap.set("#cta",{{opacity:0,y:30,scale:.94,transformOrigin:"50% 50%"}});
tl.to("#cta",{{opacity:1,y:0,scale:1,duration:.3,ease:"power3.out"}},0);
{caret_js('#cta-caret', 0.2, ttimes[-1] + 0.15)}
{tjs}
tl.to("#cta-btn",{{scale:.9,y:5,duration:.08,ease:"power2.out",transformOrigin:"50% 50%"}},{press:.3f});
tl.to("#cta-btn",{{scale:1,y:0,duration:.14,ease:"power2.out"}},{press+.1:.3f});
tl.set("#cta-caret",{{opacity:0}},{press:.3f});
"""
    ev('CTA', 0.2, 'pop', 'CTA input card lands (t relative to CTA start)')
    for t in ttimes:
        ev('CTA', t, 'tick', 'handle typing')
    ev('CTA', press, 'click', 'CTA button pressed')
    EVENTS['CTA_START'] = t0
    return page('cta', dur, css, body, script)

if __name__ == '__main__':
    which = sys.argv[1:] or ['r2', 'r4', 'r5', 'r7', 'cta']
    existing = {}
    try:
        existing = json.load(open('hf_events.json'))
    except Exception:
        pass
    for w in which:
        write(w, globals()[f'gen_{w}']())
    existing.update(EVENTS)
    json.dump(existing, open('hf_events.json', 'w'), indent=1)
    print('generated', which)
