import cv2, numpy as np, json
cap = cv2.VideoCapture("input/1003 (2).mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
res = []
i = 0
while True:
    ok, f = cap.read()
    if not ok: break
    roi = f[560:860, 100:980]            # BGR
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # saturated orange (systemskala.pl) : hue ~8-22, high S and V
    m = ((hsv[...,0]>=6)&(hsv[...,0]<=22)&(hsv[...,1]>200)&(hsv[...,2]>200)).sum()
    # white text bold with black stroke: pure white pixels
    w = ((roi[...,0]>245)&(roi[...,1]>245)&(roi[...,2]>245)).sum()
    res.append((i/fps, int(m), int(w)))
    i += 1
print("frames", i, "fps", fps)
on = [r for r in res if r[1] > 400]
# group into windows
wins=[]; 
for t,m,w in on:
    if wins and t - wins[-1][1] < 0.1: wins[-1][1] = t
    else: wins.append([t,t])
print("orange overlay windows (s):", [(round(a,3), round(b+1/fps,3)) for a,b in wins])
json.dump(res, open("work/overlay_scan.json","w"))
