import cv2, numpy as np, onnxruntime as ort, sys, os, json
MODEL=os.path.expanduser("~/.cache/hyperframes/background-removal/models/u2net_human_seg.onnx")
_sess=None
def sess():
    global _sess
    if _sess is None:
        so=ort.SessionOptions(); so.intra_op_num_threads=4
        _sess=ort.InferenceSession(MODEL,so,providers=["CPUExecutionProvider"])
    return _sess
MEAN=np.array([0.485,0.456,0.406],np.float32); STD=np.array([0.229,0.224,0.225],np.float32)
def run_u2(rgb):
    im=cv2.resize(rgb,(320,320),interpolation=cv2.INTER_AREA).astype(np.float32)/255.0
    im=(im-MEAN)/STD
    x=im.transpose(2,0,1)[None].astype(np.float32)
    s=sess(); d=s.run(None,{s.get_inputs()[0].name:x})[0][0,0]
    return (d-d.min())/(d.max()-d.min()+1e-8)
def matte(bgr, cx, fy, half=450, up=520, down=380, gf_r=10, gf_eps=1e-3, lo=0.12, hi=0.88):
    H,W=bgr.shape[:2]
    x0=int(np.clip(cx-half,0,W-2*half)); x1=x0+2*half
    y0=int(max(0,fy-up)); y1=int(min(H,fy+down))
    rgb=cv2.cvtColor(bgr[y0:y1,x0:x1],cv2.COLOR_BGR2RGB)
    # pad to square so the model sees an undistorted head
    h,w=rgb.shape[:2]; side=max(h,w)
    sq=np.zeros((side,side,3),np.uint8); sq[:h,:w]=rgb
    a=run_u2(sq)
    a=cv2.resize(a,(side,side),interpolation=cv2.INTER_CUBIC)[:h,:w]
    full=np.zeros((H,W),np.float32); full[y0:y1,x0:x1]=a
    guide=bgr.astype(np.float32)/255.0
    g=cv2.ximgproc.guidedFilter(guide,np.clip(full,0,1),gf_r,gf_eps)
    g=np.clip((g-lo)/(hi-lo),0,1)
    g=g*g*(3-2*g)
    return g
if __name__=="__main__":
    bgr=cv2.imread(sys.argv[1]); t=float(sys.argv[3])
    d=json.load(open("/tmp/claude-0/-home-user-viral-video-creator/132d3151-1488-52dc-983e-ad7d135ae2eb/scratchpad/face30.json"))
    o=d[int(round(t*30))]; bb=o["bbox"]; cx=(bb[0]+bb[2])/2*1080; fy=bb[1]*1920
    print("cx",cx,"fy",fy)
    for tag,kw in [("r10e3",dict(gf_r=10,gf_eps=1e-3)),("r6e4",dict(gf_r=6,gf_eps=1e-4)),("r16e3",dict(gf_r=16,gf_eps=3e-3))]:
        a=matte(bgr,cx,fy,**kw)
        ys,xs=np.where(a>0.5); print(tag,"top y",ys.min())
        bg=np.full(bgr.shape,(246,246,244),np.float32)
        comp=(bgr*a[...,None]+bg*(1-a[...,None])).astype(np.uint8)
        hair=comp[560:800,250:850]; hair=cv2.resize(hair,None,fx=1.6,fy=1.6,interpolation=cv2.INTER_CUBIC)
        cv2.imwrite(sys.argv[2]+f"_{tag}.jpg",hair)
