"""240 fps HyperFrames renders -> 60 fps motion-blurred frames.
output frame k = mean(f[4k-1], f[4k], f[4k+1])  (centred 3-of-4 sub-frames == 270 deg shutter).
Stationary frames are identical sub-frames, so they stay perfectly sharp."""
import subprocess, numpy as np, cv2, os, sys, collections
W,H=1080,1920
RUNS={"R1":"r1","R3":"r3","R4":"r4","R5":"r5","R7":"r7","R8":"r8"}
def decode(path):
    cmd=["ffmpeg","-v","error","-i",path,"-vf","scale=in_color_matrix=bt709:in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int,format=bgr24","-f","rawvideo","-"]
    p=subprocess.Popen(cmd,stdout=subprocess.PIPE,bufsize=W*H*3*8)
    n=W*H*3
    while True:
        b=p.stdout.read(n)
        if len(b)<n: break
        yield np.frombuffer(b,np.uint8).reshape(H,W,3)
    p.wait()
# camera speed (px/s) per run as a function of local time; used to fill the gaps between 240 fps sub-frames
def _p3in(u): return u**4
def _p3out(u): return 1-(1-u)**4
def speed_R3(t,D=1160.0,a=2.50,wo=0.45,wi=0.60):
    def x(t):
        m=a+wo; e=m+wi
        if t<=a: return 0.0
        if t>=e: return -D
        if t<m: return -D/2*_p3in((t-a)/wo)
        return -D/2-D/2*_p3out((t-m)/wi)
    h=1/960; return abs(x(t+h)-x(t-h))/(2*h)
SPEED={"R3":speed_R3}
def subframe_blur(img,rid,j):
    f=SPEED.get(rid)
    if f is None: return img
    k=int(round(f(j/240.0)/240.0))        # px travelled between two sub-frames
    return cv2.blur(img,(k,1)) if k>=2 else img
def run_one(rid,name):
    out=f"gfx/{rid}"; os.makedirs(out,exist_ok=True)
    path=f"hf/renders/{name}_240.mp4"
    frames=list(decode(path)) if False else None
    buf=collections.deque(maxlen=3); idx=-1; k=0
    # sequential: we need f[4k-1], f[4k], f[4k+1]
    cache={}
    total=None
    gen=decode(path); fr=[]
    # stream with sliding window
    window={}
    n=0
    for f in gen:
        window[n]=subframe_blur(f,rid,n)
        # when we have 4k+1 available, emit k
        while True:
            need=4*k+1
            if need in window or (need>n and False): break
            break
        if (4*k+1) in window:
            a=window.get(4*k-1,window[max(4*k,0)]); b=window[4*k]; c=window[4*k+1]
            m=(a.astype(np.uint16)+b.astype(np.uint16)+c.astype(np.uint16))//3
            cv2.imwrite(f"{out}/{k:04d}.png",m.astype(np.uint8),[cv2.IMWRITE_PNG_COMPRESSION,1])
            k+=1
            for old in [x for x in window if x<4*k-1]: del window[old]
        n+=1
        if n%1 == 0 and False: pass
        # keep a copy since the pipe buffer array is a view over bytes (immutable) -> safe
    # last frame k: needs f[4k+1] which doesn't exist -> clamp to f[4k]
    last=n
    while 4*k<last:
        a=window.get(4*k-1,window[4*k]); b=window[4*k]; c=window.get(4*k+1,b)
        m=(a.astype(np.uint16)+b.astype(np.uint16)+c.astype(np.uint16))//3
        cv2.imwrite(f"{out}/{k:04d}.png",m.astype(np.uint8),[cv2.IMWRITE_PNG_COMPRESSION,1]); k+=1
    print(rid,"240fps frames",n,"-> 60fps frames",k,flush=True)
if __name__=="__main__":
    for rid in (sys.argv[1:] or RUNS):
        run_one(rid,RUNS[rid])
