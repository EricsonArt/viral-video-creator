"""Caption plan (1-3 word chunks) + RGBA rendering with PIL.

Timings come from the final voice track's word timestamps (the voice
timeline is the untouched source timeline, so Whisper times apply 1:1).
"""
import json, os, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_B = os.path.join(ROOT, "assets", "fonts", "Poppins-Bold.ttf")
FONT_S = os.path.join(ROOT, "assets", "fonts", "InstrumentSerif-Italic.ttf")

# (first word idx, last word idx, highlighted word idxs)
CHUNKS = [
    (0, 1, []), (2, 2, []), (3, 5, []), (6, 6, [6]),
    (7, 9, []), (10, 11, []), (12, 13, []), (14, 16, [15]),
    (17, 19, []), (20, 22, []), (23, 25, [24]),
    (26, 27, []), (28, 29, []), (30, 31, []), (32, 33, [32]),
    (34, 35, []), (36, 37, []), (38, 39, [38]),
    (40, 41, []), (42, 42, []), (43, 44, []), (45, 46, [45]),
    (47, 48, []), (49, 50, []), (51, 52, []), (53, 53, [53]),
    (54, 55, []), (56, 57, []), (58, 60, [59, 60]),
    (61, 63, []), (64, 65, []), (66, 67, []), (68, 69, [69]),
    (70, 71, []), (72, 74, []), (75, 77, [76, 77]),
    (78, 78, []), (79, 80, []), (81, 82, []), (83, 83, [83]),
    (84, 86, []), (87, 88, []), (89, 91, [91]),
    (92, 94, []), (95, 97, []), (98, 99, [99]),
    (100, 100, []), (101, 103, []), (104, 104, [104]),
    (105, 105, []), (106, 107, []), (108, 108, []), (109, 110, []), (111, 111, [111]),
    (112, 114, []), (115, 116, []), (117, 118, [117, 118]), (119, 122, None), (123, 124, [123, 124]),
    (125, 126, []), (127, 129, []), (130, 131, []), (132, 133, [133]),
    (134, 135, []), (136, 138, []), (139, 140, [139, 140]),
    (141, 143, []), (144, 145, []), (146, 146, [146]),
    (147, 148, []), (149, 149, []), (150, 151, []), (152, 154, [154]),
    (155, 156, []), (157, 159, []), (160, 162, []), (163, 164, [163, 164]),
    (165, 166, []), (167, 168, []), (169, 169, []), (170, 171, []), (172, 174, [172, 173, 174]),
]


def words():
    d = json.load(open(os.path.join(ROOT, "work", "transcript_large.json")))
    return [w for s in d["segments"] for w in s["words"]]


def clean(w):
    w = w.strip()
    return re.sub(r"[,.]$", "", w)


def plan(end_s):
    W = words()
    out = []
    fixed = []
    for a, b, hl in CHUNKS:
        if hl is None:  # "I nie da ci" is 4 short words -> split 2 + 2
            fixed += [(a, a + 1, []), (a + 2, b, [])]
        else:
            fixed.append((a, b, hl))
    seen = [i for a, b, _ in fixed for i in range(a, b + 1)]
    assert seen == list(range(len(W))), "caption plan must cover every word once, in order"
    for k, (a, b, hl) in enumerate(fixed):
        t0 = W[a]["s"]
        t1 = W[fixed[k + 1][0]]["s"] if k + 1 < len(fixed) else end_s
        toks = [(clean(W[i]["w"]), i in hl) for i in range(a, b + 1)]
        out.append({"t0": t0, "t1": t1, "tokens": toks, "words": [a, b]})
    out[0]["t0"] = 1 / 60  # frame 0 stays a clean cover
    # never highlight two chunks in a row
    for p, q in zip(out, out[1:]):
        assert not (any(h for _, h in p["tokens"]) and any(h for _, h in q["tokens"])), (p, q)
    return out


def render_chunk(tokens, max_w=1000):
    """Returns RGBA image of one caption line + the baseline offset."""
    fb = ImageFont.truetype(FONT_B, 74)
    fs = ImageFont.truetype(FONT_S, 88)
    stroke = 10
    parts = []
    space = fb.getlength(" ")
    for txt, hl in tokens:
        f = fs if hl else fb
        w = f.getlength(txt)
        parts.append((txt, hl, f, w))
    total = sum(p[3] for p in parts) + space * (len(parts) - 1)
    scale = min(1.0, (max_w - 2 * stroke) / total)
    if scale < 1.0:
        fb = ImageFont.truetype(FONT_B, int(74 * scale))
        fs = ImageFont.truetype(FONT_S, int(88 * scale))
        parts = [(t, h, fs if h else fb, (fs if h else fb).getlength(t)) for t, h, _, _ in parts]
        space = fb.getlength(" ")
        total = sum(p[3] for p in parts) + space * (len(parts) - 1)
    H = 150
    W = int(total + 2 * stroke + 8)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base = 104  # shared baseline
    x = stroke + 4
    for txt, hl, f, w in parts:
        asc = f.getmetrics()[0]
        y = base - asc
        # outline first (black, 10 px), then fill
        d.text((x, y), txt, font=f, fill=(0, 0, 0, 255), stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        if hl:
            d.text((x, y), txt, font=f, fill=(255, 255, 0, 255), stroke_width=2, stroke_fill=(255, 255, 0, 255))  # faux bold
        else:
            d.text((x, y), txt, font=f, fill=(255, 255, 255, 255))
        x += w + space
    return img, base


if __name__ == "__main__":
    edl = json.load(open(os.path.join(ROOT, "work", "edl.json")))
    P = plan(edl["end_s"])
    os.makedirs(os.path.join(ROOT, "work", "caps"), exist_ok=True)
    for k, c in enumerate(P):
        img, base = render_chunk(c["tokens"])
        fn = os.path.join(ROOT, "work", "caps", "c%03d.png" % k)
        img.save(fn)
        c["png"] = fn; c["base"] = base; c["w"] = img.width
    json.dump(P, open(os.path.join(ROOT, "work", "captions.json"), "w"), ensure_ascii=False, indent=1)
    print(len(P), "chunks")
    for c in P:
        print("%6.2f-%6.2f  %s" % (c["t0"], c["t1"], " ".join(("[" + t + "]") if h else t for t, h in c["tokens"])))
