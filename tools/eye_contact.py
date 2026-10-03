import cv2, json, numpy as np, mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision
plan = json.load(open("work/plan.json"))
opts = vision.FaceLandmarkerOptions(
    base_options=mpt.BaseOptions(model_asset_path="work/face_landmarker.task"),
    output_face_blendshapes=True, output_facial_transformation_matrixes=True, num_faces=1,
    running_mode=vision.RunningMode.IMAGE)
lm = vision.FaceLandmarker.create_from_options(opts)
cap = cv2.VideoCapture("input/1003 (2).mp4")
frames = {}
i = 0
cam_runs = [r for r in plan["runs"] if r["layout"] == "FULLCAM"]
need = set()
for r in cam_runs: need.update(range(r["src_f0"], r["src_f1"]))
# also all frames of the video at every 3rd frame for a global view
need.update(range(0, 1793, 3))
rows = {}
while True:
    ok, f = cap.read()
    if not ok: break
    if i in need:
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        res = lm.detect(img)
        if res.face_landmarks:
            bs = {b.category_name: b.score for b in res.face_blendshapes[0]}
            M = np.array(res.facial_transformation_matrixes[0])
            R = M[:3,:3]
            yaw = np.degrees(np.arctan2(R[0,2], R[2,2])); pitch = np.degrees(np.arcsin(-R[1,2])); roll = np.degrees(np.arctan2(R[1,0], R[1,1]))
            horiz = ((bs["eyeLookOutLeft"]-bs["eyeLookInLeft"]) + (bs["eyeLookInRight"]-bs["eyeLookOutRight"]))/2   # + = looking to viewer's... (sign irrelevant, magnitude used)
            vert = ((bs["eyeLookUpLeft"]+bs["eyeLookUpRight"])-(bs["eyeLookDownLeft"]+bs["eyeLookDownRight"]))/2
            blink = (bs["eyeBlinkLeft"]+bs["eyeBlinkRight"])/2
            rows[i] = dict(f=i, t=round(i/30,3), yaw=round(float(yaw),1), pitch=round(float(pitch),1), roll=round(float(roll),1), gx=round(float(horiz),3), gy=round(float(vert),3), blink=round(float(blink),2))
        else:
            rows[i] = dict(f=i, t=round(i/30,3), none=True)
    i += 1
json.dump(rows, open("work/eye_contact.json","w"))
print("frames analysed", len(rows), "no-face", sum(1 for v in rows.values() if v.get("none")))
