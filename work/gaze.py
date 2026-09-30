import cv2, numpy as np, json, mediapipe as mp
from mediapipe.tasks import python as mpp
from mediapipe.tasks.python import vision
opts=vision.FaceLandmarkerOptions(base_options=mpp.BaseOptions(model_asset_path="work/models/face_landmarker.task"),
    output_face_blendshapes=True, output_facial_transformation_matrixes=True, running_mode=vision.RunningMode.VIDEO, num_faces=1)
lm=vision.FaceLandmarker.create_from_options(opts)
cap=cv2.VideoCapture("input/0930.mp4")
res=[]; i=0
while True:
    ok,f=cap.read()
    if not ok: break
    rgb=cv2.cvtColor(f,cv2.COLOR_BGR2RGB)
    r=lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb), int(i*1000/30))
    if r.face_landmarks:
        L=r.face_landmarks[0]; bs={b.category_name:b.score for b in r.face_blendshapes[0]}
        xs=[p.x for p in L]; ys=[p.y for p in L]
        M=np.array(r.facial_transformation_matrixes[0])
        R=M[:3,:3]; yaw=np.degrees(np.arctan2(R[0,2],R[2,2])); pitch=np.degrees(np.arcsin(-R[1,2]))
        # gaze: horizontal = lookOut_L - lookIn_L etc
        h=(bs['eyeLookOutLeft']-bs['eyeLookInLeft'] + bs['eyeLookInRight']-bs['eyeLookOutRight'])/2
        v=(bs['eyeLookUpLeft']+bs['eyeLookUpRight']-bs['eyeLookDownLeft']-bs['eyeLookDownRight'])/2
        blink=(bs['eyeBlinkLeft']+bs['eyeBlinkRight'])/2
        res.append(dict(i=i,t=i/30,bbox=[min(xs)*1080,min(ys)*1920,max(xs)*1080,max(ys)*1920],yaw=float(yaw),pitch=float(pitch),gh=h,gv=v,blink=blink,
            top=L[10].y*1920, chin=L[152].y*1920, nose=[L[1].x*1080,L[1].y*1920]))
    else: res.append(dict(i=i,t=i/30,none=True))
    i+=1
json.dump(res,open("work/gaze.json","w"))
print("frames",i,"nofaces",sum(1 for r in res if r.get('none')))
