"""QA on the rendered final: joins, split alignment, contact sheet, audio."""
import json, os, subprocess, sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINAL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "edit", "final.mp4")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "work", "qa")
os.makedirs(OUT, exist_ok=True)
EDL = json.load(open(os.path.join(ROOT, "work", "edl.json")))
FONT = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "Poppins-Bold.ttf"), 22)
W, H = 1080, 1920


def frames(idx):
    cap = cv2.VideoCapture(FINAL)
    out = {}
    for i in sorted(set(idx)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, f = cap.read()
        if ok:
            out[i] = f
    return out


def label(im, s):
    d = ImageDraw.Draw(im)
    d.text((6, 4), s, font=FONT, fill=(255, 255, 0), stroke_width=3, stroke_fill=(0, 0, 0))
    return im


def thumb(f, w=216, crop=None):
    if crop:
        x, y, cw, ch = crop
        f = f[y:y + ch, x:x + cw]
    h = int(w * f.shape[0] / f.shape[1])
    return Image.fromarray(cv2.cvtColor(cv2.resize(f, (w, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB))


def grid(ims, cols, path):
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), (0, 0, 0))
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % cols) * w, (k // cols) * h))
    sheet.save(path, quality=88)
    return path


report = {}
cap = cv2.VideoCapture(FINAL)
nfr = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS)
report["frames"] = nfr; report["fps"] = fps
report["size"] = [int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))]

# 1) joins: both sides of every layout cut
cuts = [r["f0"] for r in EDL["runs"][1:]]
F = frames([c + d for c in cuts for d in (-2, -1, 0, 1)])
ims = []
join_stats = []
for c in cuts:
    for d in (-1, 0):
        ims.append(label(thumb(F[c + d], 200), f"f{c + d} {(c + d) / 60:.3f}s"))
    a, b = F[c - 2].astype(np.float32), F[c - 1].astype(np.float32)
    x, y = F[c].astype(np.float32), F[c + 1].astype(np.float32)
    join_stats.append({"cut_frame": c, "diff_prev_pair": float(np.abs(a - b).mean()), "diff_across": float(np.abs(b - x).mean()),
                       "diff_next_pair": float(np.abs(x - y).mean()),
                       "mean_luma_before": float(b.mean()), "mean_luma_after": float(x.mean())})
grid(ims, 8, os.path.join(OUT, "joins.jpg"))
report["joins"] = join_stats

# 2) split: first frame of every split run + fastest head motion frames
g = json.load(open(os.path.join(ROOT, "work", "gaze.json")))
nose = np.array([r["nose"] for r in g])
sp = []
for r in EDL["runs"]:
    if r["layout"] != "SPLIT":
        continue
    sp.append(r["f0"])
    s0, s1 = r["f0"] // 2, r["f1"] // 2
    v = np.hypot(*np.diff(nose[s0:s1], axis=0).T)
    top = np.argsort(-v)[:2] + s0 + 1
    sp += [int(t * 2) for t in top] + [int(t * 2 + 1) for t in top]
F = frames(sp)
ims = [label(thumb(F[i], 300, (240, 900, 600, 500)), f"f{i} {i / 60:.2f}s") for i in sorted(F)]
grid(ims, 6, os.path.join(OUT, "split_heads.jpg"))
report["split_check_frames"] = sorted(F)

# 3) whole-video contact sheet (every 0.5 s) + frame 0 + last frame
idx = list(range(0, nfr, 30)) + [nfr - 1]
F = frames(idx)
ims = [label(thumb(F[i], 180), f"{i / 60:.1f}s") for i in sorted(F)]
grid(ims, 12, os.path.join(OUT, "contact_all.jpg"))
F0 = frames([0, 1, nfr - 2, nfr - 1])
Image.fromarray(cv2.cvtColor(F0[0], cv2.COLOR_BGR2RGB)).save(os.path.join(OUT, "frame0_cover.png"))
grid([label(thumb(F0[i], 360), f"f{i}") for i in sorted(F0)], 4, os.path.join(OUT, "first_last.jpg"))
last = F0[nfr - 1].astype(np.float32)
report["last_frame_mean"] = float(last.mean()); report["last_frame_std"] = float(last.std())
report["last_two_diff"] = float(np.abs(F0[nfr - 1].astype(np.float32) - F0[nfr - 2].astype(np.float32)).mean())

json.dump(report, open(os.path.join(OUT, "qa_video.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in report.items() if k != "joins"}, indent=1))
for j in join_stats:
    print(j)
