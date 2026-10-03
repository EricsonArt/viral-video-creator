import subprocess, numpy as np, json
segs = {"s01": (0, 97), "s04": (255, 355), "s07": (513, 654), "s13": (1362, 1434), "s16": (1614, 1770)}
res = {}
for k, (a, b) in segs.items():
    cmd = ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", f"work/cut/{k}_alpha.webm", "-vf", "alphaextract,format=gray,scale=270:480:flags=area", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    p = subprocess.run(cmd, capture_output=True, check=True)
    arr = np.frombuffer(p.stdout, np.uint8).reshape(-1, 480, 270)
    crown = []; width_mid = []
    for i, fr in enumerate(arr):
        rows = np.where((fr > 128).sum(axis=1) > 3)[0]
        crown.append(int(rows[0]) * 4 if len(rows) else -1)
        # head width at y=0.45*1920 (face level)
        r = fr[int(0.5 * 480)]; cols = np.where(r > 128)[0]
        width_mid.append(int(cols[-1] - cols[0]) * 4 if len(cols) else 0)
    crown = np.array(crown)
    res[k] = crown.tolist()
    print(k, "frames", len(arr), "crown y (src px): min %d p10 %d median %d p90 %d max %d" % (crown.min(), np.percentile(crown, 10), np.median(crown), np.percentile(crown, 90), crown.max()))
json.dump(res, open("work/crown.json", "w"))
