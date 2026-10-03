import cv2, json, numpy as np, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
opts = vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path="work/face_landmarker.task"),
                                    num_faces=1, running_mode=vision.RunningMode.IMAGE)
lm = vision.FaceLandmarker.create_from_options(opts)
cap = cv2.VideoCapture("input/1003 (2).mp4"); out = {}; i = 0
while True:
    ok, f = cap.read()
    if not ok: break
    h, w = f.shape[:2]
    res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB)))
    if res.face_landmarks:
        p = np.array([[q.x * w, q.y * h] for q in res.face_landmarks[0]])
        out[i] = dict(x0=float(p[:,0].min()), x1=float(p[:,0].max()), y0=float(p[:,1].min()), y1=float(p[:,1].max()),
                      chin=float(p[152,1]), mouth=float(p[13,1]), eyes=float((p[159,1]+p[386,1])/2), cx=float(p[1,0]))
    i += 1
json.dump(out, open("work/face_bbox.json", "w"))
print("done", len(out), "of", i)
