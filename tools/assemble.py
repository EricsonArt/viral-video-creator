"""Assemble the finished 9:16 short from the run plan.

  python tools/assemble.py --out work/video_noaudio.mp4                # whole video
  python tools/assemble.py --range 0 400 --out work/part.mp4          # output-frame range (QA)
  python tools/assemble.py --dump 0,1,92,... --dumpdir work/qa        # PNG dump of selected output frames (no encode)

Layers (all numpy, uint8/float32, 1080x1920):
  FULLCAM    : source frame (30 fps, each shown for 2 output frames, offset D=2 frames lead-in)
  FULLVISUAL : HyperFrames render hf/renders/<run>.mp4 (60 fps)
  SPLIT      : HyperFrames background + rounded camera card (footage scaled S, narrower card) + head cut-out
               built from the SAME source frame (matte = remove-background alpha, gated by mediapipe selfie-multiclass)
  overlays   : captions (Pillow), cover title on frame 0 only, CTA input card on r14 (ProRes4444 alpha from HyperFrames)
"""
import argparse, json, os, subprocess, sys, time
import numpy as np, cv2
sys.path.insert(0, "tools")
import captions as cap

W, H, FPS = 1080, 1920, 60
plan = json.load(open("work/plan.json")); runs = plan["runs"]; D = plan["D"]; END_F = plan["END_F"]
SEG = {"r01": ("s01", 0), "r04": ("s04", 255), "r07": ("s07", 513), "r13": ("s13", 1362), "r16": ("s16", 1614)}

# ------------------------------------------------------------------ SPLIT geometry (portrait source -> narrower card)
S = 0.74                         # footage scale inside the card (head+shoulders fit the 720 px visible card height)
CARD_TOP = 1200
CROWN_TARGET = 1135              # median head-top lands here (hair pops ~65 px above the card)
SRC_CROWN_MED = 570.0
OY = CROWN_TARGET - S * SRC_CROWN_MED
OX = 540 - S * 540
CARD_X0, CARD_X1 = OX, OX + S * W
CARD_R = 140
FEATHER = 40
ROI_TOP = 600                    # rows above this never receive card/head pixels

# ------------------------------------------------------------------ caption zones (centre y) – see REPORT for the face-driven reasoning
CAP_Y = {"SPLIT": 1000, "FULLVISUAL": 1400, "FULLCAM": 330}
CTA_SHIFT_Y = 190                # CTA pill moved below the chin (face is huge in this selfie framing)


def rd(cmd, w, h, ch):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 8)
    n = w * h * ch
    def gen():
        while True:
            b = p.stdout.read(n)
            if len(b) < n: return
            yield np.frombuffer(b, np.uint8).reshape(h, w, ch) if ch > 1 else np.frombuffer(b, np.uint8).reshape(h, w)
    return gen(), p


def reader_rgb(path, rgba=False, vcodec=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-c:v", vcodec] if vcodec else []) + ["-i", path, "-f", "rawvideo", "-pix_fmt", "rgba" if rgba else "rgb24", "-"]
    return rd(cmd, W, H, 4 if rgba else 3)


def reader_alpha(path):
    cmd = ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", path, "-vf", "alphaextract,format=gray", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    return rd(cmd, W, H, 1)


class Seq:
    """sequential frame access: get(n) returns frame n (n non-decreasing)"""
    def __init__(self, gen, start=0): self.gen = gen; self.i = start - 1; self.cur = None
    def get(self, n):
        while self.i < n:
            self.cur = next(self.gen); self.i += 1
        return self.cur


def squircle_alpha(w, h, r, n=4.0, ss=4):
    """anti-aliased rounded rectangle with superellipse (squircle) corners; (h includes the part off-canvas)"""
    ww, hh = w * ss, h * ss
    x = (np.arange(ww, dtype=np.float32) + 0.5) / ss; y = (np.arange(hh, dtype=np.float32) + 0.5) / ss
    cx = np.clip(x, r, w - r); cy = np.clip(y, r, h - r)
    dx = np.abs(x - cx)[None, :] / r; dy = np.abs(y - cy)[:, None] / r
    inside = ((dx ** n + dy ** n) <= 1.0).astype(np.float32)
    return cv2.resize(inside, (w, h), interpolation=cv2.INTER_AREA)


def build_static_card():
    """card alpha (canvas rows ROI_TOP..H), 3-layer shadow, feather ramp for the head"""
    x0 = int(round(CARD_X0)); x1 = int(round(CARD_X1)); cw = x1 - x0
    ch = (H - CARD_TOP) + 400                                  # card continues below the canvas
    m = squircle_alpha(cw, ch, CARD_R)
    full = np.zeros((H + 400, W), np.float32)
    full[CARD_TOP:CARD_TOP + ch, x0:x1] = m[: full.shape[0] - CARD_TOP]
    card_a = full[:H]
    def shadow(dy, sigma, op):
        t = np.zeros_like(full); t[dy:, :] = full[: full.shape[0] - dy]
        return cv2.GaussianBlur(t, (0, 0), sigma)[:H] * op
    sh1 = shadow(60, 60, 0.16); sh2 = shadow(24, 24, 0.10); sh3 = shadow(4, 5, 0.06)
    sh_a = 1 - (1 - sh1) * (1 - sh2) * (1 - sh3)
    ramp = np.clip((CARD_TOP + FEATHER - np.arange(H, dtype=np.float32)) / FEATHER, 0, 1)[:, None]   # 1 above the card edge -> 0 at +40 px
    return card_a, sh_a, ramp


class Splitter:
    def __init__(self):
        self.card_a, self.sh_a, self.ramp = build_static_card()
        self.M = np.float32([[S, 0, OX], [0, S, OY]])
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision
        import mediapipe as mp
        self.mp = mp
        self.seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=mpt.BaseOptions(model_asset_path="work/selfie_multiclass.tflite"),
            running_mode=vision.RunningMode.IMAGE, output_category_mask=True, output_confidence_masks=False))
        self.k41 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(os.environ.get('GATEK', '41')),) * 2)
        self.cache = {}

    def head_alpha(self, src_rgb, a_rembg):
        res = self.seg.segment(self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(src_rgb)))
        cat = res.category_mask.numpy_view()
        person = np.isin(cat, (1, 2, 3, 4)).astype(np.uint8)
        person = cv2.resize(person, (W, H), interpolation=cv2.INTER_NEAREST)
        gate = cv2.GaussianBlur(cv2.dilate(person, self.k41).astype(np.float32), (0, 0), 5)
        a = a_rembg.astype(np.float32) / 255.0 * gate
        CH = float(os.environ.get('CHOKE', '0.05'))
        a = np.clip((a - CH) / (1 - 2 * CH), 0, 1)             # mild choke: trims the wall-coloured fringe without eating wispy hair
        return cv2.GaussianBlur(a, (0, 0), 0.8)

    def fg(self, key, src_rgb, a_rembg):
        """premultiplied RGBA float32 for rows ROI_TOP..H (cached per source frame)"""
        if key in self.cache: return self.cache[key]
        foot = cv2.warpAffine(src_rgb, self.M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        ha = cv2.warpAffine(self.head_alpha(src_rgb, a_rembg), self.M, (W, H), flags=cv2.INTER_AREA)
        ha = ha * self.ramp
        r0 = ROI_TOP
        card_a = self.card_a[r0:, :, None]; sh_a = self.sh_a[r0:, :, None]; ha = ha[r0:, :, None]; foot = foot[r0:]
        rgb = np.array([24, 24, 32], np.float32)[None, None, :] * sh_a
        a = sh_a
        rgb = foot * card_a + rgb * (1 - card_a); a = card_a + a * (1 - card_a)
        rgb = foot * ha + rgb * (1 - ha); a = ha + a * (1 - ha)
        out = np.concatenate([rgb, a], axis=2)
        self.cache = {key: out}                                  # keep only the latest (frames advance monotonically)
        return out


def blend_fg(bg_rgb, fg):
    r0 = ROI_TOP
    out = bg_rgb.copy()
    roi = out[r0:].astype(np.float32)
    out[r0:] = np.clip(fg[..., :3] + roi * (1 - fg[..., 3:4]) + 0.5, 0, 255).astype(np.uint8)
    return out


def paste_rgba(dst, img, cx, cy, alpha_mul=1.0):
    """alpha-blend RGBA uint8 `img` centred at (cx,cy) onto dst (in place)."""
    h, w = img.shape[:2]
    x0 = int(round(cx - w / 2)); y0 = int(round(cy - h / 2))
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    sub = img[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)
    a = sub[..., 3:4] / 255.0 * alpha_mul
    reg = dst[ya:yb, xa:xb].astype(np.float32)
    dst[ya:yb, xa:xb] = np.clip(sub[..., :3] * a + reg * (1 - a) + 0.5, 0, 255).astype(np.uint8)


def ease_out(t): return 1 - (1 - t) ** 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="work/video_noaudio.mp4"); ap.add_argument("--range", nargs=2, type=int)
    ap.add_argument("--dump", default=None); ap.add_argument("--dumpdir", default="work/qa")
    ap.add_argument("--crf", default="17"); ap.add_argument("--no-captions", action="store_true"); ap.add_argument("--placeholders", action="store_true")
    ap.add_argument("--cta", default="hf/renders/r14_cta.mov")
    a = ap.parse_args()
    f_lo, f_hi = (a.range if a.range else (0, END_F))
    dump = set(int(x) for x in a.dump.split(",")) if a.dump else None
    if dump: os.makedirs(a.dumpdir, exist_ok=True)
    need_frames = sorted(dump) if dump else list(range(f_lo, f_hi))

    words = json.load(open("work/words.json"))
    chunks = cap.make_chunks(words, plan["END_S"])
    cap_imgs = [cap.render_chunk(c) for c in chunks]
    cover_img, _, (cbw, cbh) = cap.cover_card(["Zespół 6", "programistów"])
    run_of = lambda f: next(r for r in runs if r["out_f0"] <= f < r["out_f1"])

    # --- sequential readers (frames are visited in increasing order)
    src = Seq(reader_rgb("input/1003 (2).mp4")[0])
    gfx = {}; alpha = {}
    def gfx_get(r, k):
        p = f"hf/renders/{r['id']}.mp4"
        if r["id"] not in gfx:
            if not os.path.exists(p) or a.placeholders: gfx[r["id"]] = None
            else: gfx[r["id"]] = Seq(reader_rgb(p)[0])
        s = gfx[r["id"]]
        if s is None:
            ph = np.full((H, W, 3), (243, 243, 240), np.uint8); cv2.putText(ph, r["id"], (60, 200), cv2.FONT_HERSHEY_SIMPLEX, 4, (180, 180, 180), 8); return ph
        return s.get(k)
    def alpha_get(r, srcf):
        seg, s0 = SEG[r["id"]]
        if r["id"] not in alpha: alpha[r["id"]] = Seq(reader_alpha(f"work/cut/{seg}_alpha.webm")[0])
        return alpha[r["id"]].get(srcf - s0)
    splitter = Splitter()
    cta = None
    if os.path.exists(a.cta): cta = {"seq": Seq(reader_rgb(a.cta, rgba=True, vcodec="prores")[0])}
    r14 = next(r for r in runs if r["id"] == "r14")

    enc = None
    if not dump:
        vf = "scale=out_color_matrix=bt709:out_range=tv:flags=bicubic,format=yuv420p"
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", vf,
               "-c:v", "libx264", "-preset", "slow", "-crf", a.crf, "-maxrate", "16M", "-bufsize", "32M", "-profile:v", "high", "-level", "4.2",
               "-g", "120", "-bf", "3", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
               "-movflags", "+faststart", a.out]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    t0 = time.time(); last_src = -1
    for f in need_frames:
        r = run_of(f); srcf = max(0, (f - D) // 2)
        k = f - r["out_f0"]
        if r["layout"] == "FULLCAM":
            frame = src.get(srcf).copy()
        elif r["layout"] == "FULLVISUAL":
            frame = gfx_get(r, k).copy()
        else:  # SPLIT
            bg = gfx_get(r, k)
            s_rgb = src.get(srcf); a_r = alpha_get(r, srcf)
            fg = splitter.fg((r["id"], srcf), s_rgb, a_r)
            frame = blend_fg(bg, fg)
        if r["id"] != "r14" or True:
            pass
        if r["id"] == "r14" and cta is not None:
            ov = cta["seq"].get(k)
            if CTA_SHIFT_Y: ov = np.roll(ov, CTA_SHIFT_Y, axis=0)
            al = ov[..., 3:4].astype(np.float32) / 255.0
            frame = np.clip(ov[..., :3] * al + frame.astype(np.float32) * (1 - al) + 0.5, 0, 255).astype(np.uint8)
        # captions (never on frame 0 – clean cover frame)
        t = f / FPS
        if not a.no_captions and f >= 1:
            for ci, c in enumerate(chunks):
                if c["t0"] - 1e-6 <= t < c["t1"] - 1e-6:
                    img, (cx_, cy_) = cap_imgs[ci]
                    age = (f - int(round(c["t0"] * FPS))) / FPS
                    pop = ease_out(min(1.0, max(0.0, age / 0.07)))
                    sc = 0.86 + 0.14 * pop
                    im2 = img if sc >= 0.999 else cv2.resize(img, (max(2, int(img.shape[1] * sc)), max(2, int(img.shape[0] * sc))), interpolation=cv2.INTER_AREA)
                    paste_rgba(frame, im2, 540, CAP_Y[r["layout"]], alpha_mul=min(1.0, 0.35 + 0.65 * pop))
                    break
        if f == 0:                                         # cover title on frame 0 only
            paste_rgba(frame, cover_img, 540, (262 + 603) / 2)
        if dump is not None:
            cv2.imwrite(os.path.join(a.dumpdir, f"f{f:05d}.png"), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        else:
            enc.stdin.write(np.ascontiguousarray(frame).tobytes())
            if (f - f_lo) % 120 == 0: print(f"frame {f}/{f_hi}  {time.time()-t0:.0f}s  run {r['id']} {r['layout']}", flush=True)
    if enc:
        enc.stdin.close(); enc.wait(); print("encoded", a.out, f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
