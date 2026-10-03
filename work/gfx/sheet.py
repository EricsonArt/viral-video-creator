#!/usr/bin/env python3
"""usage: sheet.py video.mp4 out.png t1 t2 ... [--cols N] [--w W]"""
import sys, subprocess, os, tempfile
from PIL import Image, ImageDraw
args = sys.argv[1:]
vid, out = args[0], args[1]
cols, w = 4, 360
ts = []
i = 2
while i < len(args):
    if args[i] == '--cols': cols = int(args[i+1]); i += 2
    elif args[i] == '--w': w = int(args[i+1]); i += 2
    else: ts.append(float(args[i])); i += 1
ims = []
for t in ts:
    fn = tempfile.mktemp(suffix='.png')
    subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',vid,'-frames:v','1','-vf',f'scale={w}:-1',fn],check=True)
    im = Image.open(fn).convert('RGB'); d = ImageDraw.Draw(im); d.rectangle([0,0,80,22],fill=(0,0,0)); d.text((4,4),f't={t:.2f}',fill=(255,255,0)); ims.append(im); os.remove(fn)
h = ims[0].size[1]; rows = (len(ims)+cols-1)//cols
s = Image.new('RGB',(cols*w, rows*h),(40,40,40))
for k, im in enumerate(ims): s.paste(im, ((k%cols)*w, (k//cols)*h))
s.save(out); print(out, s.size)
