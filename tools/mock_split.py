import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
src = cv2.cvtColor(cv2.imread("work/cut/a_12.png", cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)  # has alpha (cutout)
# real RGB frame for the card (not alpha-multiplied)
import subprocess
subprocess.run(["ffmpeg","-v","error","-y","-ss","0.4","-i","work/cut/test_1s.mp4","-frames:v","1","work/cut/rgb_12.png"],check=True)
rgb = cv2.cvtColor(cv2.imread("work/cut/rgb_12.png"), cv2.COLOR_BGR2RGB)
alpha = src[...,3]
H,W = 1920,1080

def ground():
    yy,xx = np.mgrid[0:H,0:W].astype(np.float32)
    d = np.sqrt(((xx-540)/(0.8*W))**2 + ((yy-0.36*H)/(0.62*H))**2)
    d = np.clip(d,0,1)[...,None]
    return (255*(1-d) + 243*d).astype(np.uint8).repeat(3,axis=2)

def squircle_mask(w,h,r,n=4.0):
    # superellipse-style rounded rect mask via supersampling
    ss=2
    m = np.zeros((h*ss,w*ss),np.float32)
    yy,xx = np.mgrid[0:h*ss,0:w*ss].astype(np.float32)
    x=xx/ss; y=yy/ss
    cx=np.clip(x,r,w-r); cy=np.clip(y,r,h-r)
    dx=np.abs(x-cx)/r; dy=np.abs(y-cy)/r
    inside = (dx**n + dy**n) <= 1.0
    m = inside.astype(np.float32)
    m = cv2.resize(m,(w,h),interpolation=cv2.INTER_AREA)
    return m

def compose(s, crown_y, card_x, card_w, card_top=1200, radius=200, extend=False):
    out = ground().astype(np.float32)
    # transform: scale s about source crown (540 w, 530 h) -> (cx, crown_y)
    src_cx, src_crown = 540, 530
    ox = 540 - s*src_cx
    oy = crown_y - s*src_crown
    M = np.float32([[s,0,ox],[0,s,oy]])
    foot = cv2.warpAffine(rgb, M, (W,H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT if extend else cv2.BORDER_CONSTANT)
    if extend:
        foot = cv2.GaussianBlur(foot,(0,0),1)  # (visual only)
    al = cv2.warpAffine(alpha, M, (W,H), flags=cv2.INTER_AREA)
    # card
    ch = H - card_top + 400
    cm = squircle_mask(card_w, ch, radius)
    card_alpha = np.zeros((H,W),np.float32)
    x0=card_x; y0=card_top
    xs=max(0,x0); xe=min(W,x0+card_w); ye=min(H,y0+ch)
    card_alpha[y0:ye, xs:xe] = cm[0:ye-y0, xs-x0:xe-x0]
    # shadow
    sh = cv2.GaussianBlur(card_alpha,(0,0),40)*0.25
    out = out*(1-sh[...,None]) + np.array([24,24,32],np.float32)*sh[...,None]
    out = out*(1-card_alpha[...,None]) + foot.astype(np.float32)*card_alpha[...,None]
    # cutout head above card top, feather 40px below top edge
    yy = np.arange(H,dtype=np.float32)[:,None]
    ramp = np.clip(1 - (yy-(card_top-0))/40.0, 0, 1)   # 1 above top edge, fades to 0 over 40px below
    a2 = (al.astype(np.float32)/255.0)*ramp
    out = out*(1-a2[...,None]) + foot.astype(np.float32)*a2[...,None]
    return np.clip(out,0,255).astype(np.uint8)

A = compose(s=0.62, crown_y=1130, card_x=-65, card_w=1210, extend=True)
B = compose(s=0.82, crown_y=1130, card_x=(1080-int(1080*0.82))//2, card_w=int(1080*0.82), radius=170, extend=False)
C = compose(s=0.72, crown_y=1100, card_x=(1080-int(1080*0.72))//2, card_w=int(1080*0.72), radius=150, extend=False)
sheet = np.concatenate([cv2.resize(x,(540,960)) for x in (A,B,C)],axis=1)
cv2.imwrite("work/cut/mock_split.png", cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR))
print("ok")
