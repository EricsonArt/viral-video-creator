import cv2, glob, json, numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
S="/tmp/claude-0/-home-user-viral-video-creator/132d3151-1488-52dc-983e-ad7d135ae2eb/scratchpad"
opts=vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path="models/face_landmarker.task"),
    output_face_blendshapes=True, output_facial_transformation_matrixes=True, num_faces=1,
    running_mode=vision.RunningMode.IMAGE)
det=vision.FaceLandmarker.create_from_options(opts)
files=sorted(glob.glob(f"{S}/f30/*.jpg"))
out=[]
for i,f in enumerate(files):
    im=mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(cv2.imread(f),cv2.COLOR_BGR2RGB))
    r=det.detect(im)
    if not r.face_landmarks: out.append({"i":i,"t":i/30,"ok":False}); continue
    lm=np.array([[p.x,p.y,p.z] for p in r.face_landmarks[0]])
    bs={b.category_name:b.score for b in r.face_blendshapes[0]}
    M=np.array(r.facial_transformation_matrixes[0])
    R=M[:3,:3]
    yaw=np.degrees(np.arctan2(-R[2,0],np.sqrt(R[2,1]**2+R[2,2]**2)))
    pitch=np.degrees(np.arctan2(R[2,1],R[2,2]))
    roll=np.degrees(np.arctan2(R[1,0],R[0,0]))
    # iris offsets relative to eye corners (478 landmarks incl. iris 468-477)
    def off(iris_c,c_in,c_out,top,bot):
        ic=lm[iris_c]; a=lm[c_in]; b=lm[c_out]
        h=(ic[0]-a[0])/(b[0]-a[0]+1e-9)  # 0..1 from inner->outer corner (x-based)
        t=lm[top]; bt=lm[bot]
        v=(ic[1]-t[1])/(bt[1]-t[1]+1e-9)
        return h,v
    hL,vL=off(468,133,33,159,145)   # left eye (subject's right in image?) 
    hR,vR=off(473,362,263,386,374)
    out.append({"i":i,"t":i/30,"ok":True,
        "bbox":[float(lm[:,0].min()),float(lm[:,1].min()),float(lm[:,0].max()),float(lm[:,1].max())],
        "yaw":float(yaw),"pitch":float(pitch),"roll":float(roll),
        "hL":float(hL),"vL":float(vL),"hR":float(hR),"vR":float(vR),
        "lookL":float(bs["eyeLookInLeft"]-bs["eyeLookOutLeft"]),"lookR":float(bs["eyeLookInRight"]-bs["eyeLookOutRight"]),
        "lookUp":float((bs["eyeLookUpLeft"]+bs["eyeLookUpRight"])/2),"lookDown":float((bs["eyeLookDownLeft"]+bs["eyeLookDownRight"])/2),
        "blink":float((bs["eyeBlinkLeft"]+bs["eyeBlinkRight"])/2),"jaw":float(bs["jawOpen"])})
json.dump(out,open(f"{S}/face30.json","w"))
ok=[o for o in out if o["ok"]]
print("detected",len(ok),"/",len(out))
