import cv2, numpy as np, os
W,H=1080,1920
# --- geometry for portrait source (derived from spec: card top y=1200, h=864, 3-layer shadow, squircle radius)
SC=888/1080.0          # source scale -> 888 px wide card (inset), footage pixel-aligned with cutout
CARD_X,CARD_Y,CARD_W,CARD_H=96,1200,888,864
OX,OY=CARD_X,598       # canvas pos of source (0,0)
RAD=190; NSQ=4.0       # squircle corner radius / exponent
FEATHER=40
def squircle_mask(x0,y0,w,h,r,n,ss=4):
    """alpha mask (HxW) of rounded rect with superellipse corners; supersampled"""
    m=np.zeros((H*ss,W*ss),np.uint8)
    X0,Y0,X1,Y1=x0*ss,y0*ss,(x0+w)*ss,(y0+h)*ss; R=r*ss
    ys=np.arange(max(Y0,0),min(Y1,H*ss)); xs=np.arange(max(X0,0),min(X1,W*ss))
    yy,xx=np.meshgrid(ys,xs,indexing="ij")
    cx=np.clip(xx,X0+R,X1-R); cy=np.clip(yy,Y0+R,Y1-R)
    dx=np.abs(xx-cx)/R; dy=np.abs(yy-cy)/R
    inside=(dx**n+dy**n)<=1.0
    m[ys[0]:ys[-1]+1,xs[0]:xs[-1]+1]=inside.astype(np.uint8)*255
    return cv2.resize(m,(W,H),interpolation=cv2.INTER_AREA).astype(np.float32)/255
_cache={}
def prep():
    if "card" in _cache: return _cache
    card=squircle_mask(CARD_X,CARD_Y,CARD_W,CARD_H,RAD,NSQ)
    # three-layer shadow (css blur radius b -> sigma b/2): 0 60 120 .16 / 0 24 48 .10 / 0 4 10 .06
    sh=np.zeros((H,W),np.float32)
    for dy,b,a in ((60,120,.16),(24,48,.10),(4,10,.06)):
        M=np.roll(card,dy,axis=0); M[:dy]=0
        sh=1-(1-sh)*(1-a*cv2.GaussianBlur(M,(0,0),b/2))
    ramp=np.ones(H,np.float32)
    ys=np.arange(H)
    u=np.clip((ys-CARD_Y)/FEATHER,0,1); ramp=1-(u*u*(3-2*u))      # 1 above card top -> 0 at +40px
    _cache.update(card=card,shadow=sh,ramp=ramp[:,None])
    return _cache
SHADOW_RGB=np.array([32,24,24],np.float32)  # BGR of rgb(24,24,32)
def compose(G,S,A):
    """G: graphic BGR u8 (H,W,3); S: source BGR u8 (1920,1080,3); A: matte u8 (1920,1080) in source coords"""
    P=prep()
    out=G.astype(np.float32)
    out=out*(1-P["shadow"][...,None])+SHADOW_RGB*P["shadow"][...,None]
    # scaled source placed at (OX,OY)
    sw,sh_=int(round(1080*SC)),int(round(1920*SC))
    Ss=cv2.resize(S,(sw,sh_),interpolation=cv2.INTER_AREA).astype(np.float32)
    As=cv2.resize(A,(sw,sh_),interpolation=cv2.INTER_AREA).astype(np.float32)/255
    layer=np.zeros((H,W,3),np.float32); alpha_cut=np.zeros((H,W),np.float32)
    x0,y0=OX,OY
    # clip to canvas
    cx0,cy0=max(x0,0),max(y0,0); cx1,cy1=min(x0+sw,W),min(y0+sh_,H)
    layer[cy0:cy1,cx0:cx1]=Ss[cy0-y0:cy1-y0,cx0-x0:cx1-x0]
    alpha_cut[cy0:cy1,cx0:cx1]=As[cy0-y0:cy1-y0,cx0-x0:cx1-x0]
    cm=P["card"][...,None]
    out=out*(1-cm)+layer*cm                      # camera card
    ac=(alpha_cut*P["ramp"])[...,None]           # head cut-out: full above card top, 40px feather below
    out=out*(1-ac)+layer*ac
    return np.clip(out+0.5,0,255).astype(np.uint8)
if __name__=="__main__":
    S="/tmp/claude-0/-home-user-viral-video-creator/132d3151-1488-52dc-983e-ad7d135ae2eb/scratchpad"
    G=cv2.imread("hf/../prev/r1c_2.2.png") if os.path.exists("prev/r1c_2.2.png") else np.full((H,W,3),(245,245,243),np.uint8)
    G=cv2.imread("prev/r1_2.5.png")
    outs=[]
    for i in [10,60,90,120,146]:
        Sf=cv2.imread(f"{S}/full/{i+1:04d}.png"); A=cv2.imread(f"matte2/{i:04d}.png",0)
        o=compose(G,Sf,A); outs.append(cv2.resize(o,(540,960)))
        cv2.putText(outs[-1],str(i),(10,40),cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
    cv2.imwrite("prev/split_test.png",np.hstack(outs[:3]))
    cv2.imwrite("prev/split_test2.png",np.hstack(outs[3:]))
