import re
s = open('gen_hf2.py').read()

# ---- R2: lighter wash, cleaner first internal framing
s = s.replace("background:rgba(255,255,255,.72)}}", "background:rgba(255,255,255,.88)}}")
s = s.replace("A = cam_xy(855, 428.5, s0, FW, FH, IW, IH)", "A = cam_xy(590, 428.5, s0, FW, FH, IW, IH)")
s = s.replace("B = cam_xy(735, 486, 1.42, FW, FH, IW, IH)", "B = cam_xy(660, 460, 1.42, FW, FH, IW, IH)")
s = s.replace("C = cam_xy(700, 448, 1.30, FW, FH, IW, IH)", "C = cam_xy(640, 448, 1.30, FW, FH, IW, IH)")

# ---- R5: vertical, centred flow
NEW_R5 = r'''def gen_r5():
    r = RUN['R5']; dur = r['dur_f'] / FPS
    widths = [500, 540, 460, 520, 410, 530, 480, 430, 500, 360]
    bars = ''.join(f'<div class="ln{" hl" if i in (1,4,7) else ""}" id="r5-l{i}" style="top:{44 + i * 44}px;width:{w}px"></div>' for i, w in enumerate(widths))
    css = """
#cam{position:absolute;left:0;top:0;width:100%;height:100%}
#r5-prompt{left:230px;top:70px;width:620px;height:520px;border-radius:40px;overflow:hidden}
#r5-prompt .ln{position:absolute;left:50px;height:24px;border-radius:12px;background:#E4E2DA;transform-origin:0% 50%}
#r5-prompt .ln.hl{background:#EBC2B0}
#r5-short{left:340px;top:235px;width:400px;height:190px;border-radius:40px;opacity:0}
#r5-short .ln{position:absolute;left:44px;height:24px;border-radius:12px;background:#E4E2DA}
#r5-short .ln.hl{background:#EBC2B0}
#r5-wire{position:absolute;left:538px;top:425px;width:4px;height:225px;border-radius:2px;background:#E4E2DA;opacity:0;transform-origin:50% 0%}
#r5-dot{position:absolute;left:530px;top:420px;width:20px;height:20px;border-radius:50%;background:#D97757;opacity:0}
#r5-model{left:430px;top:650px;width:220px;height:220px;border-radius:72px;display:flex;align-items:center;justify-content:center}
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
tl.to("#r5-dot",{y:228,duration:.45,ease:"power2.in"},1.62);
tl.to("#r5-dot",{opacity:0,scale:.2,duration:.12},2.06);
tl.fromTo("#r5-model",{scale:1},{scale:1.07,duration:.18,ease:"power2.out",transformOrigin:"50% 50%"},2.04);
tl.to("#r5-model",{scale:1,duration:.3,ease:"power2.inOut"},2.22);
tl.fromTo("#r5-spark",{rotation:0},{rotation:90,duration:.7,ease:"power2.inOut",transformOrigin:"50% 50%"},2.04);
"""
    ev('R5', 2.06, 'pop', 'compressed prompt arrives at the model tile')
    return page('r5', dur, css, body, script)

'''
s = re.sub(r"def gen_r5\(\):.*?(?=# =+ R7)", lambda m: NEW_R5, s, flags=re.S)

# ---- R7: more bottom room, edge fades
s = s.replace("CW, CH = 960, 880", "CW, CH = 960, 940")
s = s.replace("P1 = cam_xy(480, 250, 1.15, CW, CH, CW, CH)", "P1 = cam_xy(480, 250, 1.15, CW, CH, CW, CH)")
s = s.replace("P2 = cam_xy(480, 640, 1.15, CW, CH, CW, CH)", "P2 = cam_xy(480, 700, 1.15, CW, CH, CW, CH)")
s = s.replace("#r7-box{{position:absolute;left:100px;top:520px;", "#r7-box{{position:absolute;left:100px;top:540px;")
s = s.replace("#r7-btn{{position:absolute;left:100px;top:722px;", "#r7-btn{{position:absolute;left:100px;top:770px;")
s = s.replace("#r7-card{{position:absolute;left:60px;top:250px;", "#r7-card{{position:absolute;left:60px;top:250px;")
s = s.replace(""" #r7-caret{{display:inline-block;width:4px;height:50px;""", """ #r7-caret{{display:inline-block;width:4px;height:50px;""")
s = s.replace("#r7-caret{{display:inline-block;width:4px;height:50px;background:#FF5A1F;vertical-align:middle;opacity:0;margin-left:2px}}",
 "#r7-caret{{display:inline-block;width:4px;height:50px;background:#FF5A1F;vertical-align:middle;opacity:0;margin-left:2px}}\n#r7-fT{{position:absolute;left:0;top:0;width:100%;height:120px;background:linear-gradient(#0B0B0C,rgba(11,11,12,0));opacity:0}}\n#r7-fB{{position:absolute;left:0;bottom:0;width:100%;height:120px;background:linear-gradient(rgba(11,11,12,0),#0B0B0C);opacity:0}}")
s = s.replace(""" </div>
</div>\"\"\"
    script = f\"\"\"
// product window is the subject""", """ </div>
 <div id="r7-fT"></div><div id="r7-fB"></div>
</div>\"\"\"
    script = f\"\"\"
// product window is the subject""")
s = s.replace("""tl.to("#r7-in",{{x:{P1[0]},y:{P1[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},0.35);
tl.to("#r7-in",{{x:{P2[0]},y:{P2[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},2.25);
tl.to("#r7-in",{{x:{P1[0]},y:{P1[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},4.25);""",
"""tl.to("#r7-in",{{x:{P1[0]},y:{P1[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},0.35);
tl.to("#r7-fB",{{opacity:1,duration:.6,ease:"power2.inOut"}},0.35);
tl.to("#r7-in",{{x:{P2[0]},y:{P2[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},2.25);
tl.to("#r7-fB",{{opacity:0,duration:.6,ease:"power2.inOut"}},2.25);
tl.to("#r7-fT",{{opacity:1,duration:.6,ease:"power2.inOut"}},2.25);
tl.to("#r7-in",{{x:{P1[0]},y:{P1[1]},scale:1.15,duration:.6,ease:"power2.inOut"}},4.25);
tl.to("#r7-fT",{{opacity:0,duration:.6,ease:"power2.inOut"}},4.25);
tl.to("#r7-fB",{{opacity:1,duration:.6,ease:"power2.inOut"}},4.25);""")
open('gen_hf2.py', 'w').write(s)
print('patched')
