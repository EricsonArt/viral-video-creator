#!/usr/bin/env python3
"""Final compositor: 1080x1920 @ 60 fps.

layers per frame:
  FULL CAM    -> source frame (already 1080x1920 portrait, no zoom, no moves)
  FULL VISUAL -> HyperFrames run (240 fps render, 3 of 4 sub-frames blended -> 60 fps motion blur)
  SPLIT       -> HyperFrames graphic + squircle camera card + head cut-out from the SAME source frame
then captions, cover (frame 0 only) and the CTA card (outro).
Usage: compose.py --video out.mp4 | compose.py --probe n1,n2,...   (PNG dumps to frames/probe)
"""
import json, subprocess, sys, os, math, argparse
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 60
PLAN = json.load(open('plan.json'))
EV = json.load(open('hf_events.json'))
RUNS = PLAN['runs']; CHUNKS = PLAN['chunks']; END_F = PLAN['end_f']
SRC = '../../input/src.mp4'
OY = 360                       # SPLIT: source y-offset inside the card (card top y=1200 <-> source row 840)
CARD = dict(x=-65, y=1200, w=1210, h=864, r=200)
ZONE = {'CAM': 350, 'VISUAL': 1400, 'SPLIT': 868}   # caption centre y per layout

# ----------------------------------------------------------------------------- helpers
def spawn_reader(cmd):
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=W * H * 3 * 2)

def read_frame(proc):
    buf = proc.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        return None
    return np.frombuffer(buf, np.uint8).reshape(H, W, 3)

class SrcReader:
    """sequential reader of source frames (30 fps) starting at a given index"""
    def __init__(self, start=0):
        self.idx = start - 1; self.cur = None
        ss = ['-ss', f'{start / 30.0 + 0.001:.4f}'] if start else []
        self.p = spawn_reader(['ffmpeg', '-v', 'error', *ss, '-i', SRC, '-an', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    def get(self, idx):
        while self.idx < idx:
            f = read_frame(self.p)
            if f is None:
                break
            self.cur = f; self.idx += 1
        return self.cur

class GfxReader:
    """60 fps frames of one HyperFrames run: 240 fps render, sub-frames 4k-1,4k,4k+1 averaged (270-degree shutter)"""
    def __init__(self, rid, start=0):
        ss = ['-ss', f'{start / 60.0:.4f}'] if start else []
        vf = "tmix=frames=3,select='eq(mod(n\\,4)\\,1)'"
        self.p = spawn_reader(['ffmpeg', '-v', 'error', *ss, '-i', f'hf/out/{rid}_240.mp4', '-vf', vf, '-vsync', '0', '-an', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        self.idx = start - 1; self.cur = None
    def get(self, idx):
        while self.idx < idx:
            f = read_frame(self.p)
            if f is None:
                break
            self.cur = f; self.idx += 1
        return self.cur


# ----------------------------------------------------------------------------- analytic camera speed (for smoothing the 240 fps sub-frame copies)
def _ease_inout_cubic_slope(x):
    x = min(max(x, 0.0), 1.0)
    return 12 * x * x if x < 0.5 else 12 * (1 - x) ** 2          # d/dx of power3.inOut ... peak 3 at x=.5

def cam_motion(rid, t):
    """returns (axis, speed px/s) of the WORLD camera of a run at run-relative time t (0 when at rest)"""
    if rid == 'R2':
        a, d = 2.05, 0.5
        if a <= t <= a + d:
            return 'y', 1100 * _ease_inout_cubic_slope((t - a) / d) / d
        return None, 0.0
    if rid == 'R4':
        X1, OFF, WT = 463.0, 1080.0, 2.0
        if WT - 0.45 <= t < WT:                 # out: power3.in
            u = (t - (WT - 0.45)) / 0.45
            return 'x', X1 * 3 * u * u / 0.45
        if WT <= t <= WT + 0.6:                 # in: power3.out
            u = (t - WT) / 0.6
            return 'x', (OFF - X1) * 3 * (1 - u) ** 2 / 0.6
    return None, 0.0

def smooth_motion(frame, rid, t):
    axis, speed = cam_motion(rid, t)
    if not axis or speed < 150:
        return frame
    sub = speed / 240.0                           # px between two 240 fps sub-frames
    sigma = 0.55 * sub
    if sigma < 0.8:
        return frame
    k = int(sigma * 6) | 1
    if axis == 'x':
        return cv2.GaussianBlur(frame, (k, 1), sigmaX=sigma, sigmaY=0.01, borderType=cv2.BORDER_REPLICATE)
    return cv2.GaussianBlur(frame, (1, k), sigmaX=0.01, sigmaY=sigma, borderType=cv2.BORDER_REPLICATE)

# ----------------------------------------------------------------------------- captions + cover
FN = ImageFont.truetype('assets/fonts/Poppins-Bold.ttf', 74)
FH = ImageFont.truetype('assets/fonts/InstrumentSerif-Italic.ttf', 96)
FC = ImageFont.truetype('assets/fonts/Poppins-Bold.ttf', 110)
STROKE = 7

def render_chunk(c):
    toks = PLAN['tokens']
    words = [(toks[i][0], i in c['hl']) for i in range(c['a'], c['b'] + 1)]
    space = FN.getlength(' ')
    items = [(t, hl, FH if hl else FN, (FH if hl else FN).getlength(t)) for t, hl in words]
    lines = [[]]; wsum = 0
    for it in items:
        add = it[3] + (space if lines[-1] else 0)
        if wsum + add > 1010 and lines[-1]:
            lines.append([]); wsum = 0; add = it[3]
        lines[-1].append(it); wsum += add
    lh = 104
    ch = lh * len(lines) + 70
    im = Image.new('RGBA', (W, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pos = []
    for li, line in enumerate(lines):
        lw = sum(it[3] for it in line) + space * (len(line) - 1)
        x = (W - lw) / 2; base = 35 + 74 + li * lh
        for t, hl, f, w in line:
            pos.append((x, base, t, hl, f)); x += w + space
    for x, base, t, hl, f in pos:      # pass 1: black stroke
        d.text((x, base), t, font=f, fill=(0, 0, 0, 255), stroke_width=STROKE + (2 if hl else 0), stroke_fill=(0, 0, 0, 255), anchor='ls')
    for x, base, t, hl, f in pos:      # pass 2: fills (highlight = Instrument Serif, bold-italic via extra stroke, pure yellow)
        if hl:
            d.text((x, base), t, font=f, fill=(255, 255, 0, 255), stroke_width=2, stroke_fill=(255, 255, 0, 255), anchor='ls')
        else:
            d.text((x, base), t, font=f, fill=(255, 255, 255, 255), anchor='ls')
    a = np.array(im).astype(np.float32)
    return a, ch

def render_cover():
    lines = ['Claude Code', 'za darmo']
    asc, desc = FC.getmetrics()
    lw = max(FC.getlength(t) for t in lines)
    bw = int(lw + 100); bh = 341
    x0 = (W - bw) // 2; y0 = 262
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle((x0, y0 + 24, x0 + bw, y0 + bh + 24), radius=30, fill=(24, 24, 32, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    layer.alpha_composite(sh)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=30, fill=(255, 255, 255, 255))
    lh = asc + desc
    top = y0 + (bh - lh * 2) / 2
    for i, t in enumerate(lines):
        w = FC.getlength(t)
        d.text(((W - w) / 2, top + i * lh + asc), t, font=FC, fill=(0, 0, 0, 255), anchor='ls')
    return np.array(layer).astype(np.float32)

def blend_rgba(frame, rgba, x, y, alpha_mul=1.0):
    """frame: uint8 HxWx3 (modified in place); rgba: float32 hxwx4; top-left at (x,y)"""
    h, w = rgba.shape[:2]
    y0, y1 = max(y, 0), min(y + h, H); x0, x1 = max(x, 0), min(x + w, W)
    if y1 <= y0 or x1 <= x0:
        return
    sub = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = (sub[..., 3:4] / 255.0) * alpha_mul
    reg = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = np.clip(reg * (1 - a) + sub[..., :3] * a, 0, 255).astype(np.uint8)

# ----------------------------------------------------------------------------- SPLIT geometry
def squircle_mask():
    """anti-aliased squircle card mask for canvas rows 1200..1920 (corners n=4 'superellipse')"""
    ss = 3
    ys = (np.arange(H - CARD['y'] * 1) )   # rows from card top to bottom of canvas
    hh = H - CARD['y']
    yy = (np.arange(hh * ss) + 0.5) / ss                    # relative to card top
    xx = (np.arange(W * ss) + 0.5) / ss - CARD['x']          # relative to card left
    X, Y = np.meshgrid(xx, yy)
    r = CARD['r']; w = CARD['w']; h = CARD['h']
    dx = np.maximum(np.maximum(r - X, X - (w - r)), 0)
    dy = np.maximum(np.maximum(r - Y, Y - (h - r)), 0)
    inside = ((dx / r) ** 4 + (dy / r) ** 4) <= 1.0
    inside &= (X >= 0) & (X <= w) & (Y >= 0) & (Y <= h)
    m = inside.astype(np.float32).reshape(hh, ss, W, ss).mean(axis=(1, 3))
    return m

def card_shadow(card_a):
    full = np.zeros((H, W), np.float32); full[CARD['y']:] = card_a
    s1 = cv2.GaussianBlur(np.roll(full, -10, axis=0), (0, 0), 28) * 0.20
    s2 = cv2.GaussianBlur(np.roll(full, -4, axis=0), (0, 0), 9) * 0.10
    sh = np.clip(s1 + s2, 0, 1)
    sh[CARD['y']:] = 0       # shadow only outside (above) the card
    return sh

FACE = json.load(open('face_track.json'))

def refine_alpha(a_u8, rgb, sidx):
    """keep only the head component (face-mesh bbox guided), tighten + guided-filter the matte against the real source frame"""
    y0, y1 = 40, 900
    bb = FACE[min(sidx, len(FACE) - 1)]['bbox']
    a_full = a_u8.astype(np.float32) / 255.0
    # region of interest: face bbox grown for hair / ears
    rx0, rx1 = int(max(0, bb[0] - 150)), int(min(W, bb[2] + 150))
    ry0, ry1 = int(max(0, bb[1] - 260)), int(min(H, bb[3] + 40))
    roi = np.zeros((H, W), np.float32); roi[ry0:ry1, rx0:rx1] = 1
    n, lab = cv2.connectedComponents(((a_full > 0.5) & (roi > 0)).astype(np.uint8))
    cx, cy = int((bb[0] + bb[2]) / 2), int(bb[1] + (bb[3] - bb[1]) * 0.55)
    keep_lab = lab[cy, cx]
    if keep_lab == 0:
        sizes = [(lab == i).sum() for i in range(1, n)]
        keep_lab = 1 + int(np.argmax(sizes)) if sizes else 0
    comp = (lab == keep_lab).astype(np.uint8) if keep_lab else np.zeros((H, W), np.uint8)
    if sidx < 8:   # motion-blurred opening frames: cut thin attachments (wall chunks) off the head component
        comp = cv2.morphologyEx(comp, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (91, 91)))
    region = cv2.GaussianBlur(cv2.dilate(comp, np.ones((31, 31), np.uint8)).astype(np.float32), (0, 0), 6)
    if sidx < 3:   # motion-blurred opening frames: additionally clamp the matte to a head ellipse built from the face-mesh bbox
        ell = np.zeros((H, W), np.float32)
        top = bb[1] - 200
        cv2.ellipse(ell, (int((bb[0] + bb[2]) / 2), int((top + bb[3]) / 2)), (int((bb[2] - bb[0]) / 2 + 70), int((bb[3] - top) / 2)), 0, 0, 360, 1.0, -1)
        region = region * cv2.GaussianBlur(ell, (0, 0), 8)
    a = (a_full * region)[y0:y1]
    guide = rgb[y0:y1].astype(np.float32) / 255.0
    a = cv2.erode(a, np.ones((3, 3), np.uint8))
    g = cv2.ximgproc.guidedFilter(guide, a, 9, 4e-4)
    g = np.clip((g - 0.22) / (0.82 - 0.22), 0, 1)
    g = g * g * (3 - 2 * g)
    out = np.zeros((H, W), np.float32); out[y0:y1] = g
    return out

# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video'); ap.add_argument('--probe'); ap.add_argument('--audio', default='../stems/master_mix.wav')
    ap.add_argument('--start', type=int, default=0); ap.add_argument('--stop', type=int, default=END_F)
    args = ap.parse_args()
    probe = [int(x) for x in args.probe.split(',')] if args.probe else None

    chunk_imgs = [render_chunk(c) for c in CHUNKS]
    cover = render_cover()
    card_a = squircle_mask(); shadow = card_shadow(card_a)
    ramp = np.ones(H, np.float32)
    ramp[1216:1256] = np.linspace(1, 0, 40); ramp[1256:] = 0
    rng = np.random.default_rng(7)
    noise_bank = [rng.integers(-1, 2, (H, W, 1)).astype(np.int16) for _ in range(6)]
    cta_start = round(EV['CTA_START'] * FPS)
    cta_dir = 'hf/out/cta_png'

    def run_of(n):
        for r in RUNS:
            if r['a'] <= n < r['b']:
                return r
        return RUNS[-1]

    frames_needed = probe if probe else range(args.start, args.stop)
    first = frames_needed[0] if probe else args.start
    # readers (sequential unless probing)
    src = None; gfx = {}
    enc = None
    if args.video:
        cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-framerate', str(FPS), '-i', '-',
               '-i', args.audio,
               '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
               '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-profile:v', 'high', '-g', '120', '-bf', '3',
               '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
               '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-ac', '2', '-r', str(FPS), '-movflags', '+faststart', '-t', f'{END_F / FPS:.5f}', args.video]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    matte_cache = {}

    def get_src(n):
        nonlocal src
        if src is None:
            src = SrcReader(n // 2)
        return src.get(n // 2)

    os.makedirs('frames/probe', exist_ok=True)
    for n in frames_needed:
        r = run_of(n)
        lay = r['layout']; k = n - r['a']
        t = n / FPS
        if lay == 'CAM':
            frame = get_src(n).copy()
        elif lay == 'VISUAL':
            if r['id'] not in gfx:
                gfx[r['id']] = GfxReader(r['id'].lower(), k)
            frame = smooth_motion(gfx[r['id']].get(k).copy(), r['id'], k / FPS)
            frame = np.clip(frame.astype(np.int16) + noise_bank[n % 6], 0, 255).astype(np.uint8)
        else:   # SPLIT
            if r['id'] not in gfx:
                gfx[r['id']] = GfxReader(r['id'].lower(), k)
            frame = gfx[r['id']].get(k).copy()
            frame = np.clip(frame.astype(np.int16) + noise_bank[n % 6], 0, 255).astype(np.uint8)
            s = get_src(n)
            sidx = n // 2
            # card shadow (outside the card only)
            reg = frame.astype(np.float32)
            reg *= (1 - shadow[..., None] * 0.9)
            frame = reg.astype(np.uint8)
            # camera card: source frame shifted by OY, squircle mask
            card_src = s[CARD['y'] - OY:H - OY]
            ca = card_a[..., None]
            frame[CARD['y']:] = np.clip(card_src * ca + frame[CARD['y']:] * (1 - ca), 0, 255).astype(np.uint8)
            # head cut-out from the SAME source frame, same transform (pixel aligned), feathered 40 px at the card's top edge
            folder = 'a1' if r['id'] == 'R1' else 'a5'
            if sidx not in matte_cache:
                a_u8 = cv2.imread(f'matte/{folder}/{sidx:04d}.png', 0)
                matte_cache.clear(); matte_cache[sidx] = refine_alpha(a_u8, s, sidx)
            alpha = matte_cache[sidx]
            ya, yb = OY, 1290
            a = (alpha[ya - OY:yb - OY] * ramp[ya:yb, None])[..., None]
            frame[ya:yb] = np.clip(s[ya - OY:yb - OY] * a + frame[ya:yb] * (1 - a), 0, 255).astype(np.uint8)
        # captions
        if n >= 1:
            for ci, c in enumerate(CHUNKS):
                if c['start'] - 0.0005 <= t < c['end'] - 0.0005 or (ci == len(CHUNKS) - 1 and t >= c['start'] - 0.0005):
                    img, ch = chunk_imgs[ci]
                    cy = ZONE[r['layout']]
                    kk = int(round((t - c['start']) * FPS))
                    if kk < 4:      # tiny pop-in (4 frames)
                        sc = 0.9 + 0.1 * (1 - (1 - (kk + 1) / 4) ** 2)
                        im2 = cv2.resize(img, (int(W * sc), int(ch * sc)), interpolation=cv2.INTER_AREA)
                        blend_rgba(frame, im2, (W - im2.shape[1]) // 2, int(cy - im2.shape[0] / 2), alpha_mul=min(1.0, 0.45 + 0.2 * (kk + 1)))
                    else:
                        blend_rgba(frame, img, 0, int(cy - ch / 2))
                    break
        # cover: frame 0 only
        if n == 0:
            blend_rgba(frame, cover, 0, 0)
        # CTA card (outro)
        if n >= cta_start:
            kk = n - cta_start + 1
            p = f'{cta_dir}/frame_{kk:06d}.png'
            if os.path.exists(p):
                bgra = cv2.imread(p, cv2.IMREAD_UNCHANGED)
                rgba = np.dstack([bgra[..., 2], bgra[..., 1], bgra[..., 0], bgra[..., 3]]).astype(np.float32)
                blend_rgba(frame, rgba, 0, 0)
        if probe:
            cv2.imwrite(f'frames/probe/f{n:04d}.png', frame[..., ::-1])
        elif enc:
            enc.stdin.write(frame.tobytes())
        if enc and n % 120 == 0:
            print('frame', n, flush=True)
    if enc:
        enc.stdin.close(); enc.wait()
        print('encoded', args.video)

if __name__ == '__main__':
    main()
