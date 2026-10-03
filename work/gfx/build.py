#!/usr/bin/env python3
"""Assemble one HyperFrames project dir per scene: gfx/runs/<id>/ (index.html + shared libs/fonts/assets)."""
import sys, shutil, os, re, json
G = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(G)
def build(sid):
    src = os.path.join(G, 'scenes', f'{sid}.html')
    dst = os.path.join(G, 'runs', sid)
    os.makedirs(dst, exist_ok=True)
    for d in ('lib', 'fonts'):
        shutil.rmtree(os.path.join(dst, d), ignore_errors=True)
    shutil.copytree(os.path.join(G, 'lib'), os.path.join(dst, 'lib'))
    shutil.copytree(os.path.join(W, 'assets', 'fonts'), os.path.join(dst, 'fonts'))
    shutil.copy(os.path.join(W, 'assets', 'fonts.css'), os.path.join(dst, 'fonts.css'))
    shutil.copy(os.path.join(W, 'hf', 'node_modules', 'gsap', 'dist', 'gsap.min.js'), os.path.join(dst, 'lib', 'gsap.min.js'))
    shutil.copy(os.path.join(G, 'lib', 'dither.png'), os.path.join(dst, 'dither.png'))
    ad = os.path.join(G, 'assets')
    if os.path.isdir(ad):
        shutil.rmtree(os.path.join(dst, 'assets'), ignore_errors=True)
        shutil.copytree(ad, os.path.join(dst, 'assets'))
    shutil.copy(src, os.path.join(dst, 'index.html'))
    html = open(src, encoding='utf8').read()
    m = re.search(r'<script type="application/json" id="events">(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else []
if __name__ == '__main__':
    for s in sys.argv[1:]:
        print(s, build(s))
