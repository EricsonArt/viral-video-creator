#!/usr/bin/env python3
"""Generates one HyperFrames project per visual run: hf/<run>/index.html.

Look: luxury tech - near-white radial ground, floating white cards, 3-layer shadows, Poppins.
Everything is deterministic (no clocks / random); one paused GSAP timeline per composition.
Run durations come from plan.json so every composition matches its run exactly.
"""
import json, os, sys, math

PLAN = json.load(open('plan.json'))
RUN = {r['id']: r for r in PLAN['runs']}
FPS = PLAN['fps']

FONTS = """
@font-face{font-family:"Poppins";font-weight:400;font-style:normal;src:url("assets/fonts/Poppins-Regular.ttf") format("truetype");}
@font-face{font-family:"Poppins";font-weight:600;font-style:normal;src:url("assets/fonts/Poppins-SemiBold.ttf") format("truetype");}
@font-face{font-family:"Poppins";font-weight:700;font-style:normal;src:url("assets/fonts/Poppins-Bold.ttf") format("truetype");}
@font-face{font-family:"Instrument Serif";font-weight:400;font-style:normal;src:url("assets/fonts/InstrumentSerif-Regular.ttf") format("truetype");}
@font-face{font-family:"JetBrains Mono";font-weight:500;font-style:normal;src:url("assets/fonts/JetBrainsMono-Medium.ttf") format("truetype");}
@font-face{font-family:"JetBrains Mono";font-weight:700;font-style:normal;src:url("assets/fonts/JetBrainsMono-Bold.ttf") format("truetype");}
"""

BASE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#F3F3F0}
#root{position:absolute;left:0;top:0;width:100%;height:100%;overflow:hidden;
  background:radial-gradient(farthest-corner at 50% 36%,#FFFFFF 0%,#F3F3F0 100%);
  font-family:"Poppins",sans-serif;color:#111111;}
.abs{position:absolute}
.shadow{box-shadow:0 60px 120px rgba(24,24,32,.16),0 24px 48px rgba(24,24,32,.10),0 4px 10px rgba(24,24,32,.06)}
.card{position:absolute;background:#fff;box-shadow:0 60px 120px rgba(24,24,32,.16),0 24px 48px rgba(24,24,32,.10),0 4px 10px rgba(24,24,32,.06)}
.fade900{-webkit-mask-image:linear-gradient(to bottom,#000 0px,#000 900px,rgba(0,0,0,0) 1060px);mask-image:linear-gradient(to bottom,#000 0px,#000 900px,rgba(0,0,0,0) 1060px)}
.mono{font-family:"JetBrains Mono",monospace}
svg{display:block}
"""

def page(run_id, dur, css, body, script, extra_head=""):
    return f"""<!doctype html>
<html lang="pl"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=1080, height=1920"/>
<script src="lib/gsap.min.js"></script>
{extra_head}
<style>{FONTS}{BASE_CSS}{css}</style></head><body>
<div id="root" data-composition-id="{run_id}" data-start="0" data-duration="{dur:.5f}" data-width="1080" data-height="1920">
{body}
</div>
<script>
const DUR = {dur:.5f};
const tl = gsap.timeline({{ paused: true }});
{script}
window.__timelines["{run_id}"] = tl;
tl.seek(0);
</script></body></html>
"""

def write(run_id, html):
    d = f'hf/{run_id}'
    os.makedirs(d, exist_ok=True)
    for link, target in (('assets', '../assets'), ('lib', '../lib')):
        p = f'{d}/{link}'
        if not os.path.islink(p):
            os.symlink(target, p)
    open(f'{d}/index.html', 'w').write(html)
    json.dump({"id": run_id, "name": run_id}, open(f'{d}/meta.json', 'w'))
    json.dump({"paths": {"blocks": "compositions", "components": "compositions/components", "assets": "assets"}, "media": {"autoProxy": True}}, open(f'{d}/hyperframes.json', 'w'))

# ---------------------------------------------------------------- shared snippets
def typing_script(sel, text, t0, cps, prefix):
    """Deterministic typewriter: reveals per-character spans (#prefix-c0..) at fixed times. Returns (html, js, times)."""
    spans = ''.join(f'<span id="{prefix}-c{i}" style="opacity:0">{"&nbsp;" if ch == " " else ch}</span>' for i, ch in enumerate(text))
    times = [round(t0 + i / cps, 4) for i in range(len(text))]
    js = ''.join(f'tl.set("#{prefix}-c{i}",{{opacity:1}},{t});\n' for i, t in enumerate(times))
    return spans, js, times

def caret_js(sel, t0, t1, period=0.5):
    """Blinking caret: toggled with explicit sets (seek-safe)."""
    js = ''
    t = t0; on = True
    while t < t1:
        js += f'tl.set("{sel}",{{opacity:{1 if on else 0}}},{round(t,4)});\n'
        t += period / 2; on = not on
    js += f'tl.set("{sel}",{{opacity:1}},{round(t1,4)});\n'
    return js

EVENTS = {}   # sfx events collected per run: list of (run, t_rel, kind, note)
def ev(run, t, kind, note):
    EVENTS.setdefault(run, []).append(dict(t=round(t, 4), kind=kind, note=note))

# ================================================================= R1  (SPLIT hook)
def gen_r1():
    r = RUN['R1']; dur = r['dur_f'] / FPS
    spans, tjs, ttimes = typing_script('#r1-typed', 'Dodaj tryb ciemny do aplikacji', 1.98, 26, 'r1t')
    css = """
#cam{position:absolute;left:0;top:0;width:100%;height:100%}
#r1-logo{left:110px;top:624px;width:860px;height:190px;border-radius:72px;display:flex;align-items:center;justify-content:center}
#r1-logo img{width:640px;height:auto}
#r1-ui{left:70px;top:252px;width:940px;height:570px;border-radius:44px;overflow:hidden;background:#FFFFFF}
#r1-ui .hdr{position:absolute;left:0;top:0;width:100%;height:92px;border-bottom:2px solid #F0EEE8;display:flex;align-items:center;padding-left:34px;gap:18px}
#r1-ui .hdr b{font-weight:600;font-size:34px;letter-spacing:-.2px}
#r1-ui .dot{width:16px;height:16px;border-radius:50%;background:#34C759;position:absolute;right:38px;top:38px}
#r1-ui .bubble{position:absolute;left:34px;top:114px;width:872px;height:90px;border-radius:30px;background:#F5F4EE;font-size:34px;font-weight:400;display:flex;align-items:center;padding-left:30px;color:#141413}
#r1-ui .step{position:absolute;left:34px;height:60px;display:flex;align-items:center;gap:18px;font-size:32px;color:#141413}
#r1-ui .step i{display:block;width:16px;height:16px;border-radius:50%;background:#34C759}
#r1-ui .step b{font-weight:600}
#r1-ui .step span.f{font-family:"JetBrains Mono",monospace;font-weight:500;font-size:30px;color:#5E5D59}
#r1-ui .diff{position:absolute;left:34px;top:362px;width:872px;height:160px;border-radius:24px;background:#F5F4EE;overflow:hidden}
#r1-ui .diff .ln{position:absolute;left:0;height:42px;width:100%}
#r1-ui .diff .ln .g{position:absolute;left:0;top:0;height:42px;background:#D7F0DD;border-left:6px solid #34C759}
#r1-ui .diff .ln .t{position:absolute;left:26px;top:11px;height:20px;border-radius:10px;background:#8FBF9C}
#r1-caret{display:inline-block;width:3px;height:36px;background:#D97757;margin-left:2px;vertical-align:middle;opacity:0}
#r1-inf{left:445px;top:50px;width:190px;height:160px;border-radius:72px;display:flex;align-items:center;justify-content:center}
"""
    body = f"""
<div id="cam" class="clip fade900" data-start="0" data-duration="{dur:.5f}" data-track-index="0">
  <div id="r1-logo" class="card"><img src="assets/logos/claudecode_lockup.svg" alt="Claude Code"/></div>
  <div id="r1-ui" class="card">
    <div class="hdr"><svg width="44" height="44" viewBox="0 0 24 24"><path fill="#D97757" d="{CLAUDE_PATH}"/></svg><b>Claude Code</b><span class="dot"></span></div>
    <div class="bubble"><span id="r1-typed">{spans}</span><span id="r1-caret"></span></div>
    <div class="step" id="r1-s1" style="top:226px;opacity:0"><i></i><b>Read</b><span class="f">App.tsx</span></div>
    <div class="step" id="r1-s2" style="top:290px;opacity:0"><i></i><b>Write</b><span class="f">theme.ts</span></div>
    <div class="diff" id="r1-diff" style="opacity:0">
      <div class="ln" style="top:10px"><div class="g" id="r1-g1" style="width:0px"></div><div class="t" id="r1-t1" style="width:0px"></div></div>
      <div class="ln" style="top:56px"><div class="g" id="r1-g2" style="width:0px"></div><div class="t" id="r1-t2" style="width:0px"></div></div>
      <div class="ln" style="top:102px"><div class="g" id="r1-g3" style="width:0px"></div><div class="t" id="r1-t3" style="width:0px"></div></div>
    </div>
  </div>
  <div id="r1-inf" class="card" style="opacity:0">
    <svg width="132" height="86" viewBox="0 0 180 120"><path id="r1-infp" pathLength="1" d="M30,60 C30,25 60,25 90,60 C120,95 150,95 150,60 C150,25 120,25 90,60 C60,95 30,95 30,60 Z" fill="none" stroke="#D97757" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1" stroke-dashoffset="1"/></svg>
  </div>
</div>"""
    script = f"""
// start state: logo card landed (clean landing at frame 0); the rest waits
gsap.set("#r1-ui",{{opacity:0,y:70,scale:.94,transformOrigin:"50% 50%"}});
gsap.set("#r1-inf",{{scale:.6,y:20}});
// logo -> UI reveal (named product intro: logo first, then the real UI)
tl.to("#r1-logo",{{opacity:0,scale:.9,y:-24,duration:.5,ease:"power2.inOut"}},1.02);
tl.to("#r1-ui",{{opacity:1,y:0,scale:1,duration:.62,ease:"power3.out"}},1.12);
// typing in the prompt bubble
{tjs}
{caret_js('#r1-caret', 1.75, ttimes[-1] + 0.5)}
tl.set("#r1-caret",{{opacity:0}},{ttimes[-1] + 0.62});
// tool steps stream in
tl.fromTo("#r1-s1",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:.3,ease:"power2.out"}},3.02);
tl.fromTo("#r1-s2",{{opacity:0,x:-24}},{{opacity:1,x:0,duration:.3,ease:"power2.out"}},3.28);
tl.fromTo("#r1-diff",{{opacity:0}},{{opacity:1,duration:.25,ease:"power1.out"}},3.46);
tl.to("#r1-g1",{{width:872,duration:.22,ease:"power2.out"}},3.52);tl.to("#r1-t1",{{width:560,duration:.22,ease:"power2.out"}},3.52);
tl.to("#r1-g2",{{width:872,duration:.22,ease:"power2.out"}},3.64);tl.to("#r1-t2",{{width:420,duration:.22,ease:"power2.out"}},3.64);
tl.to("#r1-g3",{{width:872,duration:.22,ease:"power2.out"}},3.76);tl.to("#r1-t3",{{width:640,duration:.22,ease:"power2.out"}},3.76);
// infinity tile ("niemal nieograniczonym limitem")
tl.fromTo("#r1-inf",{{opacity:0,scale:.6,y:20}},{{opacity:1,scale:1,y:0,duration:.5,ease:"back.out(1.5)"}},2.58);
tl.to("#r1-infp",{{strokeDashoffset:0,duration:.8,ease:"power2.inOut"}},2.72);
"""
    ev('R1', 1.45, 'pop', 'Claude Code UI card lands')
    for t in ttimes[::2]:
        ev('R1', t, 'tick', 'prompt typing')
    ev('R1', 2.98, 'pop', 'infinity tile lands')
    return page('r1', dur, css, body, script)

# Claude spark path (Simple Icons, 24x24 viewBox)
CLAUDE_PATH = open('hf/assets/logos/claude_mark.svg').read().split(' d="')[1].split('"')[0]

if __name__ == '__main__':
    which = sys.argv[1:] or ['r1']
    for w in which:
        write(w, globals()[f'gen_{w}']())
    try:
        _old = json.load(open('hf_events.json'))
    except Exception:
        _old = {}
    _old.update(EVENTS)
    json.dump(_old, open('hf_events.json', 'w'), indent=1)
    print('generated', which)
