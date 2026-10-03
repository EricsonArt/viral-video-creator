"""Caption chunking, highlight scheduling and rendering.

  chunks = make_chunks(words)            # [{t0,t1,words:[{w,hl}]}]   times on the OUTPUT timeline (s)
  img, (ox, oy) = render_chunk(chunk)    # RGBA uint8 (supersampled+downsampled), origin = anchor offset of the text centre
Style (from the brief): base Poppins Bold 74, white, black stroke 10, no box. Highlight: Instrument Serif italic (faux-bold),
pure yellow #FFFF00, same general size, same stroke. After 2-3 normal chunks one highlighted chunk; never two in a row.
"""
import json, re, numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_BASE = "assets/fonts_ttf/Poppins-Bold.ttf"
FONT_HL = "assets/fonts_ttf/InstrumentSerif-Italic.ttf"
SIZE, SIZE_HL, STROKE, SS = 74, 90, 10, 2          # SS = supersampling factor
MAX_W = 940                                         # px (text only) before a chunk wraps to 2 lines
FUNC_END = {"w", "i", "na", "z", "do", "a", "te", "się", "by", "the", "od", "za", "ale", "to", "ci", "tak", "aby", "nie", "co", "cię", "o"}
PHRASES = [("Claude", "Code"), ("Code", "Review"), ("Security", "Review"), ("Frontend", "Design"), ("127", "tysięcy"),
           ("277", "tysięcy"), ("tysięcy", "gwiazdek"), ("5", "agentów"), ("6", "programistów?"), ("5", "minut"),
           ("23", "umiejętności"), ("link", "w"), ("w", "bio"), ("nick", "konta"), ("by", "the"), ("the", "way,"),
           ("na", "GitHubie"), ("na", "raz"), ("za", "darmo"), ("w", "API"), ("Wszystko", "działa"), ("Garry'ego", "Tana"),
           ("z", "innej"), ("innej", "strony"), ("własną", "pracę"), ("w", "kodzie,"), ("pisać", "testy"), ("kontroli", "jakości.")]
KEYWORDS = {"claude", "code", "superpowers", "127", "277", "frontend", "design", "anthropic", "ai", "review", "agentów", "5", "6",
            "programistów", "programistów?", "api", "bezpieczny", "darmo", "nick", "bio", "programista", "programista,", "gstack", "23",
            "umiejętności", "razem", "razem.", "równolegle", "testy", "klucz", "kluczy", "wiralowe", "interfejsy", 
            "skradł", "opublikujesz", "prezesa,", "menedżera", "zespół", "planować,", "profesjonalne", "analizę", "blokuje", "skille"}


# original Whisper word indices that START a new sentence (the transcript has no full stops there)
SENT_START = {11, 15, 20, 29, 37, 45, 50, 53, 59, 65, 68, 72, 79, 84, 87, 90, 109, 111, 116, 124, 136, 139, 148, 150, 155, 166, 176, 183, 196}


def _strip(w): return re.sub(r"[,.]+$", "", w)          # keep '?' and '!'


def make_chunks(words, end_s):
    ws = [dict(w) for w in words]
    n = len(ws)
    ends_punct = [bool(re.search(r"[,.?!]$", w["w"])) for w in ws]
    for t in range(n - 1):                                   # sentence boundary => hard break after word t
        if ws[t + 1]["i"] in SENT_START and ws[t + 1]["i"] != ws[t]["i"]: ends_punct[t] = True
    pair = {(a, b) for a, b in PHRASES}
    INF = 1e9
    best = [INF] * (n + 1); back = [0] * (n + 1); best[0] = 0.0
    for i in range(n):
        if best[i] >= INF: continue
        for k in (1, 2, 3):
            j = i + k
            if j > n: break
            seg = ws[i:j]
            # a chunk may not continue past a word that ends with punctuation (except as its last word)
            if any(ends_punct[t] for t in range(i, j - 1)): continue
            cost = {1: 1.3, 2: 0.0, 3: 0.35}[k]
            if seg[-1]["w"].lower().strip(",.?!") in FUNC_END and j < n: cost += 2.5
            if seg[0]["w"].lower().strip(",.?!") in ("i", "a") and k == 1: cost += 0.5
            # never split a known phrase
            if j < n and (ws[j - 1]["w"], ws[j]["w"]) in pair: cost += 4.0
            # very short on-screen time (< 0.28 s) is unreadable
            nxt_t0 = ws[j]["t0"] if j < n else ws[-1]["t1"]
            if nxt_t0 - seg[0]["t0"] < 0.28: cost += (4.5 if k == 1 else 1.6)
            # width budget
            if sum(len(s["w"]) for s in seg) + k - 1 > 30: cost += 6
            # prefer breaking at punctuation
            if ends_punct[j - 1]: cost -= 0.4
            if best[i] + cost < best[j]: best[j] = best[i] + cost; back[j] = i
    bounds = []; j = n
    while j > 0: i = back[j]; bounds.append((i, j)); j = i
    bounds.reverse()
    chunks = []
    for (i, j) in bounds:
        seg = ws[i:j]
        chunks.append({"t0": seg[0]["t0"], "t1": seg[-1]["t1"], "words": [{"w": _strip(s["w"]), "hl": False} for s in seg]})
    # timing: appear on first word onset, stay until next chunk (capped: don't hang through long gaps)
    chunks[0]["t0"] = 1 / 60                                        # captions start ~17 ms; frame 0 stays clean
    for k, c in enumerate(chunks):
        nxt = chunks[k + 1]["t0"] if k + 1 < len(chunks) else end_s
        c["t1"] = min(nxt, c["t1"] + 0.45) if k + 1 < len(chunks) else end_s
        if k + 1 < len(chunks) and nxt - c["t1"] < 0.12: c["t1"] = nxt          # no flicker gaps
    # ---- highlight schedule: after 2-3 normal chunks, 1-2 meaningful words; never two highlighted chunks in a row
    since = 0
    for k, c in enumerate(chunks):
        if k == 0: since += 1; continue                              # first chunk stays plain
        cand = [t for t, w in enumerate(c["words"]) if w["w"].lower().strip(",.?!") in KEYWORDS]
        prev_hl = any(w["hl"] for w in chunks[k - 1]["words"])
        if cand and since >= 2 and not prev_hl:
            # prefer the last keyword of the chunk (usually the noun); allow 2 adjacent keywords
            pick = cand[-2:] if len(cand) >= 2 and cand[-1] - cand[-2] == 1 else cand[-1:]
            for t in pick: c["words"][t]["hl"] = True
            since = 0
        else:
            since += 1
    return chunks


def _font(path, px): return ImageFont.truetype(path, px)


def render_chunk(chunk):
    """RGBA image; returns (img, (cx, cy)) where (cx,cy) is the pixel position of the text block's visual centre."""
    fb = _font(FONT_BASE, SIZE * SS); fh = _font(FONT_HL, SIZE_HL * SS)
    stroke = STROKE * SS
    words = chunk["words"]
    space = fb.getlength(" ")
    meas = [((fh if w["hl"] else fb).getlength(w["w"])) for w in words]
    total = sum(meas) + space * (len(words) - 1)
    lines = [list(range(len(words)))]
    if total / SS > MAX_W and len(words) > 1:                            # wrap into two lines
        best_split = min(range(1, len(words)), key=lambda s: abs(sum(meas[:s]) - sum(meas[s:])))
        lines = [list(range(best_split)), list(range(best_split, len(words)))]
    line_w = [sum(meas[i] for i in ln) + space * (len(ln) - 1) for ln in lines]
    pad = stroke + 8 * SS
    asc, desc = fb.getmetrics()
    lh = int((asc + desc) * 1.02)
    W = int(max(line_w) + 2 * pad); H = int(lh * len(lines) + 2 * pad)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pos = []
    for li, ln in enumerate(lines):
        x = pad + (max(line_w) - line_w[li]) / 2; base = pad + asc + li * lh
        for i in ln:
            pos.append((i, x, base)); x += meas[i] + space
    for i, x, base in pos:                                              # 1) black strokes of every word
        f = fh if words[i]["hl"] else fb
        d.text((x, base), words[i]["w"], font=f, fill=(0, 0, 0, 255), stroke_width=stroke, stroke_fill=(0, 0, 0, 255), anchor="ls")
    for i, x, base in pos:                                              # 2) fills
        if words[i]["hl"]:
            d.text((x, base), words[i]["w"], font=fh, fill=(255, 255, 0, 255), stroke_width=2 * SS, stroke_fill=(255, 255, 0, 255), anchor="ls")  # faux bold
        else:
            d.text((x, base), words[i]["w"], font=fb, fill=(255, 255, 255, 255), anchor="ls")
    im = im.resize((W // SS, H // SS), Image.LANCZOS)
    return np.array(im), (im.width / 2, im.height / 2)


def cover_card(lines, width_pad=50, size=110, radius_pct=0.028):
    """White rounded rectangle with the cover title (Poppins Bold 110, black). Returns RGBA uint8 incl. soft shadow margin."""
    SSC = 2
    f = _font(FONT_BASE, size * SSC)
    asc, desc = f.getmetrics(); lh = int(size * SSC * 1.18)
    wl = [f.getlength(t) for t in lines]
    inner_w = max(wl); box_w = int(inner_w + 2 * width_pad * SSC)
    box_h = int(lh * len(lines) + 2 * 42 * SSC)
    radius = int(radius_pct * 1080 * SSC)
    margin = 160 * SSC
    im = Image.new("RGBA", (box_w + 2 * margin, box_h + 2 * margin), (0, 0, 0, 0))
    # soft premium shadow
    sh = Image.new("L", im.size, 0); ImageDraw.Draw(sh).rounded_rectangle([margin, margin + 24 * SSC, margin + box_w, margin + box_h + 24 * SSC], radius, fill=255)
    from PIL import ImageFilter
    sh = sh.filter(ImageFilter.GaussianBlur(34 * SSC)).point(lambda v: int(v * 0.22))
    shadow = Image.new("RGBA", im.size, (24, 24, 32, 0)); shadow.putalpha(sh)
    im = Image.alpha_composite(im, shadow)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([margin, margin, margin + box_w, margin + box_h], radius, fill=(255, 255, 255, 255))
    for k, t in enumerate(lines):
        x = margin + box_w / 2; y = margin + 42 * SSC + k * lh + asc + (lh - asc - desc) / 2
        d.text((x, y), t, font=f, fill=(17, 17, 17, 255), anchor="ms")
    im = im.resize((im.width // SSC, im.height // SSC), Image.LANCZOS)
    return np.array(im), (margin // SSC, margin // SSC), (box_w // SSC, box_h // SSC)


if __name__ == "__main__":
    plan = json.load(open("work/plan.json")); words = json.load(open("work/words.json"))
    chunks = make_chunks(words, plan["END_S"])
    json.dump(chunks, open("work/captions.json", "w"), ensure_ascii=False, indent=1)
    print(len(chunks), "chunks;", sum(any(w["hl"] for w in c["words"]) for c in chunks), "highlighted")
    for c in chunks:
        print(f'{c["t0"]:7.3f}-{c["t1"]:7.3f}  ' + " ".join(("«" + w["w"] + "»") if w["hl"] else w["w"] for w in c["words"]))
