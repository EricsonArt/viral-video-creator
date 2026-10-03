"""Build work/words.json (corrected words, final-timeline times) and work/plan.json (visual runs).

Timeline conventions
  * source video: 30 fps, 1793 frames, 59.7667 s.  Output: 60 fps.
  * Lead-in D = 2 output frames (33.3 ms) before the first spoken word (spec: ~40 ms).  Every source frame is shown for
    2 output frames, so output frame f  <->  source time (f - D)/60 (clamped at 0).
  * END = D + 2*1791 = 3584 frames = 59.733 s.
  * All run boundaries sit on the source-frame grid (even output frames offset by D) => hard cuts never split a source frame.
"""
import json, math

FPS = 60
SRC_FPS = 30
D = 2
SRC_FRAMES = 1793
SRC_END = 1791                      # last 2 source frames (59.70-59.77 s) = motion-blurred hand reaching for the phone -> dropped
END_F = D + 2 * SRC_END             # 3584
T = lambda f: f / FPS

tx = json.load(open("work/transcript.json"))
W = tx["words"]

# ---- text corrections (index in the Whisper large-v3 word list -> displayed text). Timings stay Whisper's.
fix = {
    5: "Claude", 20: "Claude", 24: "rzucać", 32: "testy", 52: "Anthropic", 83: "zmian", 98: "skradł",
    108: "opublikujesz", 141: "link", 168: "link", 149: "gstack", 152: "Garry'ego", 176: "Daje", 177: "Ci",
    183: "Claude", 184: "oceni", 189: "kierownika", 192: "menedżera", 194: "kontroli",
}
merge_into_prev = {14: "Superpowers", 153: None}       # 14 'Powers' merges with 13; 153 "'ego" merges with 152
words = []
for i, w in enumerate(W):
    txt = w["w"].strip()
    if i in fix: txt = fix[i]
    if i == 13: continue                                # 'Super' (merged)
    if i == 14:                                         # 'Powers' -> 'Superpowers' from 3.50
        words.append({"i": i, "w": "Superpowers", "start": W[13]["start"], "end": W[14]["end"]}); continue
    if i == 153: continue
    if i == 154: txt = "Tana"
    if i == 142:                                        # 'wbije' -> "w bio"  (split into two short words)
        mid = w["start"] + (w["end"] - w["start"]) * 0.45
        words.append({"i": i, "w": "w", "start": w["start"], "end": mid})
        words.append({"i": i, "w": "bio", "start": mid, "end": w["end"]}); continue
    if i == 169:
        mid = w["start"] + (w["end"] - w["start"]) * 0.45
        words.append({"i": i, "w": "w", "start": w["start"], "end": mid})
        words.append({"i": i, "w": "bio", "start": mid, "end": w["end"]}); continue
    e = w["end"]
    if i == 152: e = W[153]["end"]
    words.append({"i": i, "w": txt, "start": w["start"], "end": e})

# ---- visual runs: (id, layout, src_start_s, src_end_s)   src seconds on the 30 fps source grid
CUTS = [0.0, 91/30, 198/30, 261/30, 349/30, 390/30, 519/30, 648/30, 848/30, 886/30, 1035/30, 1191/30, 1368/30,
        1429/30, 1559/30, 1621/30, 1764/30, SRC_END/30]
LAYOUTS = ["SPLIT", "FULLVISUAL", "FULLCAM", "SPLIT", "FULLCAM", "FULLVISUAL", "SPLIT", "FULLVISUAL", "FULLCAM",
           "FULLVISUAL", "FULLCAM", "FULLVISUAL", "SPLIT", "FULLCAM", "FULLVISUAL", "SPLIT", "FULLCAM"]
assert len(CUTS) == len(LAYOUTS) + 1
runs = []
for k, lay in enumerate(LAYOUTS):
    sf0, sf1 = round(CUTS[k] * SRC_FPS), round(CUTS[k + 1] * SRC_FPS)
    f0 = 0 if k == 0 else D + 2 * sf0
    f1 = END_F if k == len(LAYOUTS) - 1 else D + 2 * sf1
    runs.append({"id": f"r{k+1:02d}", "layout": lay, "src_f0": sf0, "src_f1": sf1, "out_f0": f0, "out_f1": f1,
                 "frames": f1 - f0, "t0": T(f0), "t1": T(f1), "dur": T(f1 - f0)})
assert runs[0]["out_f0"] == 0 and runs[-1]["out_f1"] == END_F
for a, b in zip(runs, runs[1:]):
    assert a["out_f1"] == b["out_f0"] and a["layout"] != b["layout"]

# word times on the OUTPUT timeline (seconds)
for w in words:
    w["t0"] = round(w["start"] + D / FPS, 3)
    w["t1"] = round(w["end"] + D / FPS, 3)

json.dump({"fps": FPS, "D": D, "END_F": END_F, "END_S": T(END_F), "runs": runs}, open("work/plan.json", "w"), indent=1)
json.dump(words, open("work/words.json", "w"), ensure_ascii=False, indent=1)

print(f"END = {END_F} frames = {T(END_F):.3f}s   words={len(words)}")
for r in runs:
    ws = [w for w in words if r["t0"] - 0.001 <= w["t0"] < r["t1"]]
    print(f'{r["id"]} {r["layout"]:10s} out_f {r["out_f0"]:4d}-{r["out_f1"]:4d} ({r["frames"]:3d}f) {r["t0"]:7.3f}-{r["t1"]:7.3f} dur {r["dur"]:.3f} | ' +
          " ".join(w["w"] for w in ws)[:90])
