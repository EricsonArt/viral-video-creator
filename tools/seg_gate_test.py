import subprocess, numpy as np, cv2, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
def alpha_frame(seg, idx):
    cmd=["ffmpeg","-v","error","-c:v","libvpx-vp9","-i",f"work/cut/{seg}_alpha.webm","-vf",f"select=eq(n\\,{idx}),alphaextract,format=gray","-frames:v","1","-f","rawvideo","-pix_fmt","gray","-"]
    return np.frombuffer(subprocess.run(cmd,capture_output=True,check=True).stdout,np.uint8).reshape(1920,1080)
def src_frame(n):
    cmd=["ffmpeg","-v","error","-i","input/1003 (2).mp4","-vf",f"select=eq(n\\,{n})","-frames:v","1","-f","rawvideo","-pix_fmt","rgb24","-"]
    return np.frombuffer(subprocess.run(cmd,capture_output=True,check=True).stdout,np.uint8).reshape(1920,1080,3)
opts = vision.ImageSegmenterOptions(base_options=mpt.BaseOptions(model_asset_path="work/selfie_multiclass.tflite"),
                                    running_mode=vision.RunningMode.IMAGE, output_category_mask=True, output_confidence_masks=False)
seg = vision.ImageSegmenter.create_from_options(opts)
tiles=[]
for sg,idx,n in (("s01",0,0),("s01",53,53),("s13",17,1379),("s07",60,573)):
    f=src_frame(n); a=alpha_frame(sg,idx).astype(np.float32)/255
    res=seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB,data=f))
    cat=res.category_mask.numpy_view()            # 0 background, 1 hair, 2 body-skin, 3 face-skin, 4 clothes, 5 others
    cat=cv2.resize(cat.astype(np.uint8),(1080,1920),interpolation=cv2.INTER_NEAREST)
    person=(cat>0).astype(np.uint8)
    gate=cv2.dilate(person,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(41,41))).astype(np.float32)
    gate=cv2.GaussianBlur(gate,(0,0),6)
    a2=a*gate
    bg=np.full_like(f,(255,225,190))
    comp=(f*a2[...,None]+bg*(1-a2[...,None])).astype(np.uint8)
    cls=np.zeros_like(f); pal={1:(150,90,30),2:(230,170,140),3:(250,200,170),4:(30,40,90),5:(200,0,200)}
    for c,col in pal.items(): cls[cat==c]=col
    tiles.append(np.vstack([cv2.resize(comp,(270,480)),cv2.resize(cls,(270,480))]))
cv2.imwrite("work/cut/gate_test.png",cv2.cvtColor(np.hstack(tiles),cv2.COLOR_RGB2BGR)); print("ok")
