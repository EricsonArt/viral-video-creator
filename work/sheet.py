# usage: sheet.py video out.jpg t0 t1 step [crop x,y,w,h] [cols] [thumbw]
import sys, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
v,out,t0,t1,step=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5])
crop=[int(a) for a in sys.argv[6].split(',')] if len(sys.argv)>6 and sys.argv[6]!='-' else None
cols=int(sys.argv[7]) if len(sys.argv)>7 else 6
tw=int(sys.argv[8]) if len(sys.argv)>8 else 270
cap=cv2.VideoCapture(v); fps=cap.get(cv2.CAP_PROP_FPS)
font=ImageFont.truetype("assets/fonts/Poppins-Bold.ttf",max(14,tw//12))
ims=[]; t=t0
while t<=t1+1e-6:
    fi=int(round(t*fps)); cap.set(cv2.CAP_PROP_POS_FRAMES,fi); ok,f=cap.read()
    if not ok: break
    if crop: x,y,w,h=crop; f=f[y:y+h,x:x+w]
    h,w=f.shape[:2]; th=int(tw*h/w)
    im=Image.fromarray(cv2.cvtColor(cv2.resize(f,(tw,th),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2RGB))
    d=ImageDraw.Draw(im); s=f"{fi/fps:.3f}s f{fi}"
    d.text((5,3),s,font=font,fill=(255,255,0),stroke_width=2,stroke_fill=(0,0,0))
    ims.append(im); t+=step
rows=(len(ims)+cols-1)//cols; W=ims[0].width; H=ims[0].height
sheet=Image.new("RGB",(cols*W,rows*H),(0,0,0))
for k,im in enumerate(ims): sheet.paste(im,((k%cols)*W,(k//cols)*H))
sheet.save(out,quality=88); print(out,len(ims),sheet.size)
