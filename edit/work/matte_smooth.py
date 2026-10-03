import cv2, numpy as np, os
os.makedirs("matte3",exist_ok=True)
ranges=[(2,152),(370,480),(714,903)]
def load(s): return cv2.imread(f"matte2/{s:04d}.png",0).astype(np.float32)/255
def shift_to(a_src,a_ref):
    (dx,dy),resp=cv2.phaseCorrelate(a_ref,a_src)   # shift to apply to src to align with ref
    return dx,dy,resp
def warp(a,dx,dy):
    M=np.float32([[1,0,-dx],[0,1,-dy]]); return cv2.warpAffine(a,M,(1080,1920),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
tot=0
for lo,hi in ranges:
    cache={}
    def get(s):
        s=min(max(s,lo),hi)
        if s not in cache:
            cache[s]=load(s)
            for k in [k for k in cache if k<s-2]: del cache[k]
        return cache[s]
    for s in range(lo,hi+1):
        a=get(s); acc=a*0.6; wsum=0.6
        for n in (s-1,s+1):
            if n<lo or n>hi: continue
            b=get(n); dx,dy,resp=shift_to(b,a)
            if np.hypot(dx,dy)<=18 and resp>0.15:
                acc+=0.2*warp(b,dx,dy); wsum+=0.2
        out=np.clip(acc/wsum,0,1)
        cv2.imwrite(f"matte3/{s:04d}.png",(out*255+0.5).astype(np.uint8)); tot+=1
print("smoothed",tot)
