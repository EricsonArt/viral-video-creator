import json, cv2, numpy as np, mediapipe as mp, time
from mediapipe.tasks.python import BaseOptions, vision
opts = vision.FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='models/face_landmarker.task'),
    running_mode=vision.RunningMode.VIDEO, num_faces=1,
    output_face_blendshapes=True, output_facial_transformation_matrixes=True,
    min_face_detection_confidence=0.3, min_face_presence_confidence=0.3, min_tracking_confidence=0.3)
lm = vision.FaceLandmarker.create_from_options(opts)
cap = cv2.VideoCapture('../../input/src.mp4'); fps = cap.get(cv2.CAP_PROP_FPS)
W,H = 1080,1920
out=[]; i=0; t0=time.time()
def P(p): return np.array([p.x*W, p.y*H])
while True:
    ok, f = cap.read()
    if not ok: break
    rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
    res = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), int(i*1000/fps))
    rec={'i':i,'t':round(i/fps,4)}
    if res.face_landmarks:
        L = res.face_landmarks[0]
        xy = np.array([[p.x*W,p.y*H] for p in L])
        rec['bbox']=[float(xy[:,0].min()),float(xy[:,1].min()),float(xy[:,0].max()),float(xy[:,1].max())]
        # eye geometry (mesh indices): left eye corners 33(outer),133(inner); right 362(inner),263(outer)
        def ratio(iris, c_out, c_in, up, lo):
            c0,c1 = P(L[c_out]), P(L[c_in]); ir=P(L[iris])
            v = c1-c0; vn=np.linalg.norm(v)+1e-6
            h = float(np.dot(ir-(c0+c1)/2, v/vn)/vn)          # -0.5..0.5 along eye axis
            u,l = P(L[up]), P(L[lo]); lid_c=(u+l)/2
            vv = float((ir[1]-lid_c[1])/(np.linalg.norm(u-l)+1e-6))
            return h, vv, float(np.linalg.norm(u-l)/vn)
        hl,vl,ol = ratio(468,33,133,159,145)
        hr,vr,orr= ratio(473,263,362,386,374)
        # mirror right eye so +h = toward nose for both
        rec['h']=(hl-hr)/2.0 if False else (hl+(-hr))/2.0
        rec['v']=(vl+vr)/2.0
        rec['open']=(ol+orr)/2.0
        bs={b.category_name:b.score for b in res.face_blendshapes[0]}
        rec['blink']=(bs.get('eyeBlinkLeft',0)+bs.get('eyeBlinkRight',0))/2
        rec['lookDown']=(bs.get('eyeLookDownLeft',0)+bs.get('eyeLookDownRight',0))/2
        rec['lookUp']=(bs.get('eyeLookUpLeft',0)+bs.get('eyeLookUpRight',0))/2
        rec['lookIn']=(bs.get('eyeLookInLeft',0)+bs.get('eyeLookInRight',0))/2   # toward nose
        rec['lookOutL']=bs.get('eyeLookOutLeft',0); rec['lookOutR']=bs.get('eyeLookOutRight',0)
        rec['lookL']=bs.get('eyeLookInRight',0)+bs.get('eyeLookOutLeft',0)  # gaze to subject's... (relative) 
        rec['lookR']=bs.get('eyeLookInLeft',0)+bs.get('eyeLookOutRight',0)
        rec['jaw']=bs.get('jawOpen',0)
        if res.facial_transformation_matrixes:
            M=np.array(res.facial_transformation_matrixes[0])[:3,:3]
            yaw=np.degrees(np.arctan2(-M[2,0], np.sqrt(M[2,1]**2+M[2,2]**2)))
            pitch=np.degrees(np.arctan2(M[2,1],M[2,2])); roll=np.degrees(np.arctan2(M[1,0],M[0,0]))
            rec['yaw']=float(yaw); rec['pitch']=float(pitch); rec['roll']=float(roll)
    out.append(rec); i+=1
    if i%200==0: print(i, round(time.time()-t0,1), flush=True)
json.dump(out, open('face_track.json','w'))
print('done', len(out), round(time.time()-t0,1))
