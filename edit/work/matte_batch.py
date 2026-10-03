import cv2, numpy as np, json, os, sys, time
from matte import matte
S="/tmp/claude-0/-home-user-viral-video-creator/132d3151-1488-52dc-983e-ad7d135ae2eb/scratchpad"
OUT="matte"; os.makedirs(OUT,exist_ok=True)
face=json.load(open(f"{S}/face30.json"))
ranges=[(2,152),(370,480),(714,903)]
frames=[i for a,b in ranges for i in range(a,b+1)]
stats={}
t0=time.time()
for n,i in enumerate(frames):
    bgr=cv2.imread(f"{S}/full/{i+1:04d}.png")   # ffmpeg numbering starts at 1 -> source frame i
    bb=face[i]["bbox"]; cx=(bb[0]+bb[2])/2*1080; fy=bb[1]*1920
    a=matte(bgr,cx,fy,gf_r=6,gf_eps=3e-4)
    # keep largest connected component (+ nearby strands)
    m=(a>0.3).astype(np.uint8)
    nlab,lab,st,_=cv2.connectedComponentsWithStats(m,connectivity=8)
    if nlab>2:
        big=1+np.argmax(st[1:,cv2.CC_STAT_AREA])
        keep=(lab==big).astype(np.uint8)
        keep=cv2.dilate(keep,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(25,25)))
        a=a*keep
    cv2.imwrite(f"{OUT}/{i:04d}.png",(a*255+0.5).astype(np.uint8))
    ys,xs=np.where(a>0.5)
    stats[i]={"top":int(ys.min()),"left":int(xs.min()),"right":int(xs.max())}
    if n%25==0: print(n,len(frames),i,f"{time.time()-t0:.0f}s",flush=True)
json.dump(stats,open("matte_stats.json","w"))
print("done",time.time()-t0)
