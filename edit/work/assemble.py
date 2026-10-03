import json, cv2, numpy as np, subprocess, os, sys, glob, time
from split_comp import compose
W,H,FPS=1080,1920,60
S="/tmp/claude-0/-home-user-viral-video-creator/132d3151-1488-52dc-983e-ad7d135ae2eb/scratchpad"
plan=json.load(open("plan.json")); RUNS=plan["runs"]; END_F=plan["END_F"]
OVDIR="hf/renders/ov_png4"
ovfiles=sorted(glob.glob(OVDIR+"/*.png"))
def run_of(i):
    for r in RUNS:
        if r["f0"]<=i<r["f1"]: return r
    raise IndexError(i)
def src_idx(i): return 2+i//2          # 30 fps source -> 60 fps timeline (each source frame twice), T0 = 2 frames
def read_src(idx): 
    im=cv2.imread(f"{S}/full/{idx+1:04d}.png"); assert im is not None,idx; return im
def frame_base(i):
    r=run_of(i); k=i-r["f0"]; s=src_idx(i)
    if r["layout"]=="cam": return read_src(s)
    g=cv2.imread(f"gfx/{r['id']}/{k:04d}.png"); assert g is not None,(r["id"],k)
    if r["layout"]=="visual": return g
    m=cv2.imread(f"matte3/{s:04d}.png",0); assert m is not None,("matte",s)
    return compose(g,read_src(s),m)
def overlay(base,i):
    ov=cv2.imread(ovfiles[i],cv2.IMREAD_UNCHANGED)
    if ov is None or ov.shape[2]<4: return base
    a=ov[...,3]
    x,y,w,h=cv2.boundingRect((a>0).astype(np.uint8))
    if w==0: return base
    al=(a[y:y+h,x:x+w].astype(np.float32)/255)[...,None]
    reg=base[y:y+h,x:x+w].astype(np.float32)
    base[y:y+h,x:x+w]=np.clip(reg*(1-al)+ov[y:y+h,x:x+w,:3].astype(np.float32)*al+0.5,0,255).astype(np.uint8)
    return base
def frame_at(i): return overlay(frame_base(i),i)
def encode(out,audio,start=0,end=END_F,crf=15,preset="medium"):
    cmd=["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",audio,
         "-map","0:v","-map","1:a",
         "-vf","scale=in_range=pc:out_range=tv:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int,format=yuv420p",
         "-c:v","libx264","-preset",preset,"-crf",str(crf),"-profile:v","high","-level","4.2","-pix_fmt","yuv420p",
         "-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709","-color_range","tv",
         "-c:a","aac","-b:a","256k","-ar","48000","-ac","2","-t",f"{END_F/FPS:.6f}","-movflags","+faststart",out]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE); t0=time.time()
    for i in range(start,end):
        p.stdin.write(frame_at(i).tobytes())
        if i%120==0: print(i,f"{time.time()-t0:.0f}s",flush=True)
    p.stdin.close(); p.wait()
if __name__=="__main__":
    mode=sys.argv[1]
    if mode=="frames":
        os.makedirs("qa",exist_ok=True)
        for i in [int(x) for x in sys.argv[2].split(",")]:
            cv2.imwrite(f"qa/f{i:04d}.png",frame_at(i))
    elif mode=="video":
        encode(sys.argv[2],sys.argv[3],crf=int(sys.argv[4]) if len(sys.argv)>4 else 15)
