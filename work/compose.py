"""Final compositor: layouts, split camera card + head cutout, camera motion
blur for the graphic world, captions, cover, CTA -> edit/final.mp4.

usage: compose.py [--frames a:b] [--out path] [--noaudio] [--preview]
"""
import argparse, json, math, os, re, subprocess, sys, time
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = os.path.join(ROOT, "bin", "ffmpeg")
W, H, FPS = 1080, 1920, 60
EDL = json.load(open(os.path.join(ROOT, "work", "edl.json")))
CAPS = json.load(open(os.path.join(ROOT, "work", "captions.json")))
END_F = EDL["end_frames_60"]
VIZ = os.path.join(ROOT, "work", "hf", "viz")
DEC = ["-vf", "scale=in_color_matrix=bt709:in_range=limited,format=rgb24"]

# ------------------------------------------------------------------ split geometry
SPLIT_OFF = 280                     # source y -> canvas y (portrait source, scale 1.0)
CARD = dict(x=-65, y=1200, w=1210, h=864, r=200)
FEATHER = 40
CAP_Y = {"SPLIT": 975, "FULLCAM": 668, "VISUAL": 1400}   # caption visual centre


def run_at(f):
    for r in EDL["runs"]:
        if r["f0"] <= f < r["f1"]:
            return r
    raise ValueError(f)


class Pipe:
    """Sequential raw-frame reader from ffmpeg."""
    def __init__(self, path, pix="rgb24", ch=3, extra_in=(), vf=True):
        cmd = [FF, "-v", "error"] + list(extra_in) + ["-i", path]
        cmd += (DEC if (vf and pix == "rgb24") else ["-pix_fmt", pix]) + ["-f", "rawvideo", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=W * H * ch * 2)
        self.sz = W * H * ch
        self.ch = ch
        self.idx = -1
        self.cur = None

    def read(self):
        b = self.p.stdout.read(self.sz)
        if len(b) < self.sz:
            return None
        self.idx += 1
        self.cur = np.frombuffer(b, np.uint8).reshape(H, W, self.ch)
        return self.cur

    def get(self, i):
        while self.idx < i:
            if self.read() is None:
                raise EOFError(i)
        assert self.idx == i, (self.idx, i)
        return self.cur

    def close(self):
        try:
            self.p.stdout.close(); self.p.kill()
        except Exception:
            pass


# ------------------------------------------------------------------ eases (GSAP)
def ease(name, x):
    x = min(max(x, 0.0), 1.0)
    if name == "none" or name == "linear":
        return x
    kind, _, mode = name.partition(".")
    if kind == "sine":
        if mode == "in": return 1 - math.cos(x * math.pi / 2)
        if mode == "out": return math.sin(x * math.pi / 2)
        return -(math.cos(math.pi * x) - 1) / 2
    p = {"power1": 2, "power2": 3, "power3": 4, "power4": 5}[kind]
    if mode == "in": return x ** p
    if mode == "out": return 1 - (1 - x) ** p
    return (2 ** (p - 1)) * x ** p if x < 0.5 else 1 - ((-2 * x + 2) ** p) / 2


class Camera:
    def __init__(self, comp):
        html = open(os.path.join(VIZ, "compositions", comp + ".html")).read()
        js = re.search(r'id="camkeys">(.*?)</script>', html, re.S).group(1)
        c = json.loads(js)
        self.ax, self.ay = c["anchor"]
        self.keys = c["keys"]

    def state(self, t):
        k0 = self.keys[0]
        s = (k0["cx"], k0["cy"], k0["s"])
        for k in self.keys[1:]:
            if t < k["t"]:
                break
            u = ease(k["ease"], (t - k["t"]) / k["d"])
            s = tuple(a + (b - a) * u for a, b in zip(s, (k["cx"], k["cy"], k["s"])))
        return s

    def A(self, t):
        cx, cy, s = self.state(t)
        return np.array([[s, 0, self.ax - s * cx], [0, s, self.ay - s * cy], [0, 0, 1.0]])

    def rel(self, t_from, t_to):
        return self.A(t_to) @ np.linalg.inv(self.A(t_from))

    def disp(self, t_from, t_to):
        M = self.rel(t_from, t_to)
        pts = np.array([[0, 0, 1], [W, 0, 1], [0, H, 1], [W, H, 1], [W / 2, H / 2, 1]]).T
        q = M @ pts
        return float(np.max(np.hypot(q[0] - pts[0], q[1] - pts[1])))


SHUTTER = 0.75 / FPS     # 270 degrees -> blur length = speed * 0.75 / 60
L_CAP = 40 / 0.29        # sigma cap 40 px -> box length cap


def motion_blurred(cam, subs, n, stats):
    """subs: dict subframe_index -> frame (240 fps). Returns output frame n."""
    t = n / FPS
    L = cam.disp(t - SHUTTER / 2, t + SHUTTER / 2)
    base = subs[4 * n]
    if L < 1.0:
        stats["sharp"] += 1
        return base, 0.0
    stats["blur"] += 1
    scale = min(1.0, L_CAP / L)
    acc = np.zeros((H, W, 3), np.float32)
    cnt = 0
    for j in (4 * n - 1, 4 * n, 4 * n + 1):
        fr = subs.get(j, base)
        tj = max(j, 0) / 240.0
        lsub = cam.disp(tj - 1 / 480, tj + 1 / 480) * scale
        K = max(1, int(math.ceil(lsub / 2.0)))
        for d in (np.linspace(-1 / 480, 1 / 480, K) if K > 1 else [0.0]):
            if d == 0.0:
                acc += fr; cnt += 1; continue
            M = cam.rel(tj, tj + d * scale)
            acc += cv2.warpAffine(fr, M[:2], (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            cnt += 1
    return np.clip(acc / cnt + 0.5, 0, 255).astype(np.uint8), min(L, L_CAP)


# ------------------------------------------------------------------ static layers
def squircle_mask(x, y, w, h, r, n=5.0, ss=4):
    """Anti-aliased superellipse-cornered rectangle mask on the canvas."""
    m = np.zeros((H, W), np.float32)
    y0, y1 = max(0, y), min(H, y + h)
    x0, x1 = max(0, x), min(W, x + w)
    m[y0:y1, x0:x1] = 1.0
    # corners (only the top ones are on-canvas)
    for (cx, cy) in ((x + r, y + r), (x + w - r, y + r), (x + r, y + h - r), (x + w - r, y + h - r)):
        bx0, by0 = int(cx - r), int(cy - r)
        yy, xx = np.mgrid[0:2 * r * ss, 0:2 * r * ss].astype(np.float32)
        xx = (xx + 0.5) / ss + bx0; yy = (yy + 0.5) / ss + by0
        inside = (np.abs((xx - cx) / r) ** n + np.abs((yy - cy) / r) ** n) <= 1.0
        # keep only the quadrant pointing outward
        qx = (xx < cx) if cx < x + w / 2 else (xx >= cx)
        qy = (yy < cy) if cy < y + h / 2 else (yy >= cy)
        quad = qx & qy
        val = np.where(quad, inside, True).astype(np.float32)
        val = val.reshape(2 * r, ss, 2 * r, ss).mean(axis=(1, 3))
        for j in range(2 * r):
            Y = by0 + j
            if 0 <= Y < H:
                X0, X1 = max(0, bx0), min(W, bx0 + 2 * r)
                if X1 > X0:
                    m[Y, X0:X1] = np.minimum(m[Y, X0:X1], val[j, X0 - bx0:X1 - bx0])
    return m


def css_shadow(mask):
    """Three-layer premium shadow alpha for a mask (CSS blur radius -> sigma = r/2)."""
    a = np.zeros_like(mask)
    for dy, blur, alpha in ((60, 120, .16), (24, 48, .10), (4, 10, .06)):
        sh = np.zeros_like(mask)
        sh[dy:] = mask[:-dy]
        sh = cv2.GaussianBlur(sh, (0, 0), blur / 2)
        a = 1 - (1 - a) * (1 - sh * alpha)
    return a * (1 - mask)


def cover_layer():
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "Poppins-Bold.ttf"), 110)
    lines = ["Wyświetlenia", "bez klientów?"]
    tw = max(f.getlength(l) for l in lines)
    bw = int(tw + 2 * 50); by0, by1 = 262, 603
    bx0 = (W - bw) // 2
    rad = int(0.028 * W)
    card = Image.new("L", (W, H), 0)
    ImageDraw.Draw(card).rounded_rectangle([bx0, by0, bx0 + bw, by1], rad, fill=255)
    cm = np.asarray(card, np.float32) / 255
    sh = css_shadow(cm)
    rgba = np.zeros((H, W, 4), np.float32)
    # shadow (ink colour) + white card
    rgba[..., :3] = np.array([24, 24, 32], np.float32)[None, None] * (sh[..., None] > 0)
    rgba[..., 3] = sh
    rgba[..., :3] = np.where(cm[..., None] > 0, 255, rgba[..., :3])
    rgba[..., 3] = cm + sh * (1 - cm)
    txt = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(txt)
    lh = 128
    ty = (by0 + by1) / 2 - lh
    for k, l in enumerate(lines):
        lw = f.getlength(l)
        asc, desc = f.getmetrics()
        d.text(((W - lw) / 2, ty + k * lh + (lh - (asc + desc)) / 2 + 8), l, font=f, fill=255)
    tm = np.asarray(txt, np.float32) / 255
    rgba[..., :3] = rgba[..., :3] * (1 - tm[..., None]) + 17 * tm[..., None]
    return rgba, (bx0, by0, bw, by1 - by0)


def load_caption(c):
    import PIL.Image
    im = np.asarray(PIL.Image.open(c["png"]).convert("RGBA"), np.float32)
    return im


def over(dst, rgba, x, y):
    """Alpha-composite float RGBA image onto uint8/float canvas at (x, y)."""
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return dst
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = src[..., 3:4] / 255.0 if src[..., 3].max() > 1.0 else src[..., 3:4]
    reg = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = np.clip(reg * (1 - a) + src[..., :3] * a + 0.5, 0, 255).astype(np.uint8)
    return dst


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "edit", "final.mp4"))
    ap.add_argument("--noaudio", action="store_true")
    ap.add_argument("--crf", default="14")
    ap.add_argument("--preset", default="slow")
    ap.add_argument("--log", default=os.path.join(ROOT, "work", "compose_log.json"))
    a = ap.parse_args()
    fa, fb = (0, END_F) if not a.frames else map(int, a.frames.split(":"))

    # static layers
    card_m = squircle_mask(CARD["x"], CARD["y"], CARD["w"], CARD["h"], CARD["r"])
    card_sh = css_shadow(card_m)
    ramp = np.ones(H, np.float32)
    ramp[CARD["y"]:CARD["y"] + FEATHER] = np.linspace(1, 0, FEATHER)
    ramp[CARD["y"] + FEATHER:] = 0
    cover, cover_box = cover_layer()
    cap_imgs = {}
    cap_frames = []
    bounds = sorted({r["f0"] for r in EDL["runs"]} | {END_F})
    for k, c in enumerate(CAPS):
        f0, f1 = int(round(c["t0"] * FPS)), int(round(c["t1"] * FPS))
        for b in bounds:
            if abs(f0 - b) <= 5: f0 = b   # caption appears with the new layout (J-cut lead <= 83 ms)
            if abs(f1 - b) <= 5: f1 = b
        f0 = max(f0, 1)
        cap_frames.append((f0, f1, k))

    src = Pipe(os.path.join(ROOT, "input", "0930.mp4"))
    cta = Pipe(os.path.join(VIZ, "renders", "cta.mov"), pix="rgba", ch=4, vf=False)
    gfx, gfx_run, cams, subs = None, None, {}, {}
    matte, matte_run = None, None
    enc = None
    if a.out:
        cmd = [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
        if not a.noaudio:
            cmd += ["-i", os.path.join(ROOT, "work", "audio", "master.wav")]
        cmd += ["-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                "-c:v", "libx264", "-preset", a.preset, "-crf", a.crf, "-profile:v", "high", "-tune", "film",
                "-x264-params", "keyint=120:min-keyint=60:aq-mode=3",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
                "-r", str(FPS)]
        if not a.noaudio:
            cmd += ["-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-ac", "2", "-map", "0:v", "-map", "1:a", "-shortest"]
        cmd += ["-movflags", "+faststart", a.out]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    stats = {"sharp": 0, "blur": 0}
    blur_log = []
    t_start = time.time()
    for i in range(fa, fb):
        r = run_at(i)
        lay = r["layout"]
        n = i - r["f0"]
        sfi = i // 2
        frame = None
        if lay in ("VISUAL", "SPLIT"):
            if gfx_run != r["id"]:
                if gfx: gfx.close()
                gfx = Pipe(os.path.join(VIZ, "renders", r["comp"] + "_240.mp4"))
                gfx_run = r["id"]; subs = {}
                cams[r["id"]] = Camera(r["comp"])
            # keep subframes 4n-1 .. 4n+3
            need = 4 * n + 3
            while gfx.idx < need:
                fr = gfx.read()
                if fr is None:
                    break
                subs[gfx.idx] = fr
            for k in [k for k in subs if k < 4 * n - 1]:
                del subs[k]
            g, L = motion_blurred(cams[r["id"]], subs, n, stats)
            if L > 0:
                blur_log.append((i, round(L, 2)))
            frame = g.copy()
        if lay == "FULLCAM":
            frame = src.get(sfi).copy()
        elif lay == "SPLIT":
            s = src.get(sfi)
            if matte_run != r["id"]:
                if matte: matte.close()
                matte = Pipe(os.path.join(ROOT, "work", "matte", r["comp"] + "_matte.webm"), pix="rgba", ch=4, vf=False,
                             extra_in=["-c:v", "libvpx-vp9"])
                matte_run = r["id"]
                m_first = r["f0"] // 2
            alpha = matte.get(sfi - m_first)[..., 3].astype(np.float32) / 255.0
            # shift source + matte down into the card geometry
            sh_src = np.zeros_like(s); sh_src[SPLIT_OFF:] = s[:H - SPLIT_OFF]
            sh_a = np.zeros((H, W), np.float32); sh_a[SPLIT_OFF:] = alpha[:H - SPLIT_OFF]
            f = frame.astype(np.float32)
            f = f * (1 - card_sh[..., None]) + np.array([24, 24, 32], np.float32) * card_sh[..., None]
            f = f * (1 - card_m[..., None]) + sh_src.astype(np.float32) * card_m[..., None]
            head = sh_a * ramp[:, None]
            f = f * (1 - head[..., None]) + sh_src.astype(np.float32) * head[..., None]
            frame = np.clip(f + 0.5, 0, 255).astype(np.uint8)

        # CTA overlay (R13)
        if r["id"] == "R13":
            c = cta.get(n).astype(np.float32)
            if c[..., 3].max() > 0:
                over(frame, c, 0, 0)
        # captions
        for (f0, f1, k) in cap_frames:
            if f0 <= i < f1:
                if k not in cap_imgs:
                    cap_imgs[k] = load_caption(CAPS[k])
                im = cap_imgs[k]
                cy = CAP_Y[lay]
                over(frame, im, int(round(W / 2 - im.shape[1] / 2)), int(round(cy - 86)))
                break
        # cover: frame 0 only
        if i == 0:
            over(frame, cover * np.array([1, 1, 1, 255], np.float32) if cover[..., 3].max() <= 1 else cover, 0, 0)
        if enc:
            enc.stdin.write(frame.tobytes())
        if i % 120 == 0:
            el = time.time() - t_start
            print(f"frame {i}/{fb} {r['id']} {lay} {el:.0f}s", flush=True)
    if enc:
        enc.stdin.close(); enc.wait()
    json.dump({"stats": stats, "blur_frames": blur_log, "cover_box": cover_box,
               "caption_frames": cap_frames}, open(a.log, "w"))
    print("done", stats, time.time() - t_start)


if __name__ == "__main__":
    main()
