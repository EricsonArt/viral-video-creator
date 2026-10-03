import re
s = open('gen_hf2.py').read()

NEW_R5 = r'''def gen_r5():
    r = RUN['R5']; dur = r['dur_f'] / FPS
    widths = [500, 540, 460, 520, 410, 530, 480, 430, 500, 360]
    bars = ''.join(f'<div class="ln{" hl" if i in (1,4,7) else ""}" id="r5-l{i}" style="top:{58 + i * 48}px;width:{w}px"></div>' for i, w in enumerate(widths))
    css = """
#cam{position:absolute;left:0;top:0;width:100%;height:100%}
#r5-prompt{left:70px;top:190px;width:620px;height:560px;border-radius:40px;overflow:hidden}
#r5-prompt .ln{position:absolute;left:50px;height:24px;border-radius:12px;background:#E4E2DA;transform-origin:0% 50%}
#r5-prompt .ln.hl{background:#EBC2B0}
#r5-short{left:290px;top:345px;width:400px;height:190px;border-radius:40px;opacity:0}
#r5-short .ln{position:absolute;left:44px;height:24px;border-radius:12px;background:#E4E2DA}
#r5-short .ln.hl{background:#EBC2B0}
#r5-model{left:790px;top:330px;width:220px;height:220px;border-radius:72px;display:flex;align-items:center;justify-content:center}
"""
    body = f"""
<div id="cam" class="clip fade900" data-start="0" data-duration="{dur:.5f}" data-track-index="0">
  <div id="r5-prompt" class="card">{bars}</div>
  <div id="r5-short" class="card"><div class="ln" style="top:44px;width:300px"></div><div class="ln hl" style="top:84px;width:330px"></div><div class="ln" style="top:124px;width:250px"></div></div>
  <div id="r5-model" class="card"><svg id="r5-spark" width="120" height="120" viewBox="0 0 24 24"><path fill="#D97757" d="M12 1.5 C12.7 7.3 16.7 11.3 22.5 12 C16.7 12.7 12.7 16.7 12 22.5 C11.3 16.7 7.3 12.7 1.5 12 C7.3 11.3 11.3 7.3 12 1.5 Z"/></svg></div>
</div>"""
    script = ""
    # compress: lines 3..9 collapse (staggered), the card squeezes and hands over to the compact prompt card
    for i in range(3, 10):
        script += f'tl.to("#r5-l{i}",{{opacity:0,scaleX:.08,duration:.32,ease:"power2.in"}},{round(0.40 + (i - 3) * 0.055, 3)});\n'
    for i in range(0, 3):
        script += f'tl.to("#r5-l{i}",{{y:{(2 - i) * -2 + 0},scaleX:{[.6,.62,.5][i]},duration:.5,ease:"power2.inOut"}},0.75);\n'
    script += """
tl.to("#r5-prompt",{scaleY:.34,scaleX:.66,opacity:0,duration:.5,ease:"power2.inOut",transformOrigin:"50% 50%"},0.78);
tl.fromTo("#r5-short",{opacity:0,scale:1.12},{opacity:1,scale:1,duration:.42,ease:"power3.out",transformOrigin:"50% 50%"},0.92);
// compact prompt travels to the model tile, tile receives it
tl.to("#r5-short",{x:100,duration:.5,ease:"power3.inOut"},1.5);
tl.fromTo("#r5-model",{scale:1},{scale:1.07,duration:.18,ease:"power2.out",transformOrigin:"50% 50%"},2.0);
tl.to("#r5-model",{scale:1,duration:.3,ease:"power2.inOut"},2.18);
tl.fromTo("#r5-spark",{rotation:0},{rotation:90,duration:.7,ease:"power2.inOut",transformOrigin:"50% 50%"},2.0);
"""
    ev('R5', 2.02, 'pop', 'compressed prompt reaches the model tile')
    return page('r5', dur, css, body, script)

'''

NEW_R7 = r'''def gen_r7():
    r = RUN['R7']; dur = r['dur_f'] / FPS
    CW, CH = 960, 880
    handle = 'eryk_hajduczek'
    spans, tjs, ttimes = typing_script('#r7-typed', handle, 2.95, 14, 'r7t')
    P1 = cam_xy(480, 250, 1.15, CW, CH, CW, CH)
    P2 = cam_xy(480, 640, 1.15, CW, CH, CW, CH)
    css = f"""
#r7-card{{position:absolute;left:60px;top:250px;width:{CW}px;height:{CH}px;border-radius:56px;background:#0B0B0C;overflow:hidden;
  box-shadow:0 60px 120px rgba(24,24,32,.16),0 24px 48px rgba(24,24,32,.10),0 4px 10px rgba(24,24,32,.06)}}
#r7-in{{position:absolute;left:0;top:0;width:{CW}px;height:{CH}px;transform-origin:0 0}}
#r7-lab{{position:absolute;left:100px;top:46px;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:28px;letter-spacing:2.5px;color:#F2A27C}}
#r7-mas{{position:absolute;left:700px;top:40px}}
#r7-h{{position:absolute;left:100px;top:96px;width:580px;font-family:"Instrument Serif",serif;font-size:76px;line-height:78px;letter-spacing:-1.2px;color:#fff}}
#r7-p{{position:absolute;left:100px;top:352px;width:760px;font-size:30px;line-height:44px;color:#A8A8A8;font-weight:400}}
#r7-box{{position:absolute;left:100px;top:520px;width:760px;height:178px;border-radius:44px;background:#fff}}
#r7-box .tt{{position:absolute;left:34px;top:26px;height:52px;border-radius:26px;background:#0B0B0C;color:#fff;font-size:30px;font-weight:600;padding:0 28px;line-height:52px}}
#r7-box .ig{{position:absolute;left:188px;top:26px;height:52px;line-height:52px;font-size:30px;color:#7A7A7A;font-weight:600}}
#r7-box .at{{position:absolute;left:38px;top:96px;font-size:50px;color:#8A8A8A;line-height:64px}}
#r7-box .tx{{position:absolute;left:98px;top:96px;font-size:50px;color:#111;line-height:64px;font-weight:600;white-space:nowrap}}
#r7-ph{{position:absolute;left:98px;top:96px;font-size:44px;color:#8F8F8F;line-height:64px;white-space:nowrap}}
#r7-caret{{display:inline-block;width:4px;height:50px;background:#FF5A1F;vertical-align:middle;opacity:0;margin-left:2px}}
#r7-btn{{position:absolute;left:100px;top:722px;width:760px;height:96px;border-radius:48px;background:#FF5A1F;box-shadow:0 8px 0 #D94710,0 24px 40px rgba(255,90,31,.28);
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
</div>"""
    script = f"""
// product window is the subject: the outer world stays still, only the picture inside moves (1.15x, 0.6 s, power2.inOut)
tl.to("#r7-in",{{x:{P1[0]},y:{P1[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},0.35);
tl.to("#r7-in",{{x:{P2[0]},y:{P2[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},2.25);
tl.to("#r7-in",{{x:{P1[0]},y:{P1[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},4.25);
{caret_js('#r7-caret', 2.6, ttimes[-1] + 0.45)}
tl.set("#r7-ph",{{opacity:0}},2.93);
{tjs}
// press the button
tl.to("#r7-btn",{{scale:.965,y:6,duration:.09,ease:"power2.out",transformOrigin:"50% 50%"}},3.98);
tl.to("#r7-btn",{{scale:1,y:0,duration:.16,ease:"power2.out"}},4.09);
tl.set("#r7-caret",{{opacity:0}},4.0);
"""
    ev('R7', 0.38, 'pop', 'first internal camera move settles on the product window')
    for t in ttimes:
        ev('R7', t, 'tick', 'handle typing')
    ev('R7', 3.98, 'click', 'button pressed')
    return page('r7', dur, css, body, script)

'''
s = re.sub(r"def gen_r5\(\):.*?(?=# =+ R7)", lambda m: NEW_R5, s, flags=re.S)
s = re.sub(r"def gen_r7\(\):.*?(?=# =+ CTA)", lambda m: NEW_R7, s, flags=re.S)
open('gen_hf2.py', 'w').write(s)
print('spliced')
