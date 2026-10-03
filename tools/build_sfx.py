"""SFX stem from the composition event sidecars (hf/runs/*.events.json).
Every sound corresponds to a visible event; levels are relative to the voice sample peak:
  click / pop / chime  -10 dB      whoosh  -9 dB      key / ticks  -16 dB
Output: edit/stems/sfx.wav (full length) + work/sfx_log.json (timestamp, type, source event) for the report.
"""
import json, glob, os, sys, numpy as np, soundfile as sf
sys.path.insert(0, "tools")
import synth
SR = synth.SR
plan = json.load(open("work/plan.json")); runs = {r["id"]: r for r in plan["runs"]}
N = plan["END_F"] * SR // 60
voice, _ = sf.read("edit/stems/voice.wav"); vpk = np.abs(voice).max()
db = lambda x: 10 ** (x / 20)
LEVEL = {"click": -10, "pop": -10, "chime": -10, "whoosh": -9, "key": -16, "ticks": -16}


def env_peak_time(w, win=0.03):
    """time of the loudest point of a whoosh from its smoothed (30 ms RMS) envelope"""
    m = np.sqrt((w ** 2).mean(axis=1)); k = int(win * SR)
    e = np.convolve(m ** 2, np.ones(k) / k, mode="same") ** 0.5
    return int(np.argmax(e)) / SR


out = np.zeros((N, 2)); log = []
whoosh_variant = 0; last_variant = -1
sources = []
for p in sorted(glob.glob("hf/runs/*.events.json")):
    d = json.load(open(p)); rid = d.get("run") or os.path.basename(p).split(".")[0]
    run_id = rid.split("_")[0]
    if run_id not in runs: print("skip (no run)", p); continue
    t_run = runs[run_id]["t0"]
    for e in d["events"]:
        sources.append((t_run, run_id, e))
sources.sort(key=lambda x: x[0] + (x[2].get("t", x[2].get("t0", 0))))

typ_count = 0
for t_run, rid, e in sources:
    ty = e["type"]
    if ty == "whip":
        # pick a variant different from the previous one
        v = whoosh_variant % 4
        if v == last_variant: v = (v + 1) % 4
        w = synth.sfx_whoosh(v); pk = env_peak_time(w)
        t_mid = t_run + e["t"]
        start = int(round((t_mid - pk) * SR))
        w = w * (vpk * db(LEVEL["whoosh"]))
        synth._place(out, w, start)
        log.append({"t": round(t_mid, 4), "type": f"whoosh v{v}", "run": rid, "event": e.get("note", ""), "peak_offset_in_sound_s": round(pk, 4)})
        last_variant = v; whoosh_variant += 1
    elif ty in ("pop", "click", "chime"):
        fn = {"pop": synth.sfx_pop, "click": synth.sfx_click, "chime": synth.sfx_chime}[ty]
        w = fn(len(log) % 3) if ty != "chime" else fn()
        w = w * (vpk * db(LEVEL[ty]))
        t = t_run + e["t"]; synth._place(out, w, int(round(t * SR)))
        log.append({"t": round(t, 4), "type": ty, "run": rid, "event": e.get("note", "")})
    elif ty == "ticks":
        t0 = t_run + e["t0"]; dur = e["t1"] - e["t0"]
        w = synth.sfx_ticks(dur, seed=len(log)) * (vpk * db(LEVEL["ticks"]))
        synth._place(out, w, int(round(t0 * SR)))
        log.append({"t": round(t0, 4), "type": f"tick stream {dur:.2f}s", "run": rid, "event": e.get("note", "")})
    elif ty == "typing":
        t0 = t_run + e["t0"]; t1 = t_run + e["t1"]
        import re
        m = re.search(r"(\d+)\s*(?:chars|characters|znak)", e.get("note", ""))
        n = int(e.get("chars") or (m.group(1) if m else 0) or max(1, int((t1 - t0) / 0.045) + 1))
        for i in range(n):
            t = t0 + (t1 - t0) * (i / max(1, n - 1))
            synth._place(out, synth.sfx_key(typ_count % 3) * (vpk * db(LEVEL["key"]) * (0.8 + 0.2 * ((i * 7) % 5) / 4)), int(round(t * SR)))
            typ_count += 1
        log.append({"t": round(t0, 4), "type": f"typing x{n}", "run": rid, "event": e.get("note", "")})
    else:
        print("unknown event type", ty)

peak = np.abs(out).max()
print(f"sfx: {len(log)} events, peak {20*np.log10(peak+1e-12):.2f} dBFS")
sf.write("edit/stems/sfx.wav", out, SR, subtype="PCM_24")
json.dump(log, open("work/sfx_log.json", "w"), indent=1, ensure_ascii=False)
for l in log: print(f'{l["t"]:8.3f}s  {l["type"]:18s} {l["run"]}  {l["event"][:80]}')
