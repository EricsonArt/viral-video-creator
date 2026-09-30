import cv2, numpy as np, json
cap=cv2.VideoCapture("input/0930.mp4")
prev=None; diffs=[]
i=0
while True:
    ok,f=cap.read()
    if not ok: break
    g=cv2.cvtColor(cv2.resize(f,(135,240)),cv2.COLOR_BGR2GRAY).astype(np.float32)
    if prev is not None:
        diffs.append(float(np.mean(np.abs(g-prev))))
    else: diffs.append(0.0)
    prev=g; i+=1
d=np.array(diffs)
med=np.median(d)
print("frames",i,"median diff",med)
idx=np.argsort(-d)[:25]
for k in sorted(idx):
    print(k, round(k/30,3), round(d[k],2), round(d[k]/med,1))
json.dump(diffs,open("work/framediffs.json","w"))
