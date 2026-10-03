import json, numpy as np, soundfile as sf, pyloudnorm as pyln, sys, os, time
sys.path.insert(0, "tools")
import synth
SR = synth.SR
plan = json.load(open("work/plan.json"))
N = plan["END_F"] * SR // 60
os.makedirs("edit/stems", exist_ok=True)
meter = pyln.Meter(SR)
voice, _ = sf.read("edit/stems/voice.wav")
voice_peak = np.abs(voice).max()

# ---- music: flat level, -24 LUFS integrated
t0 = time.time()
m = synth.music(N)
l = meter.integrated_loudness(m)
g = 10 ** ((-24.0 - l) / 20)
m *= g
nfo = int(0.8 * SR)                                   # (fade already baked in before gain; gain is linear -> still flat)
print(f"music: raw {l:.2f} LUFS -> gain {20*np.log10(g):+.2f} dB -> {meter.integrated_loudness(m):.2f} LUFS, peak {20*np.log10(np.abs(m).max()):.2f} dBFS ({time.time()-t0:.0f}s)")
sf.write("edit/stems/music.wav", m, SR, subtype="PCM_24")

# ---- riser: ~2.6 s, audible end exactly on the hook -> first-point cut (run r02 start)
cut_s = plan["runs"][1]["out_f0"] / 60.0
r = synth.riser(N, end_s=cut_s, dur_s=2.6)
peak_target = voice_peak * 10 ** (-14 / 20)           # 14 dB below the voice peak
r *= peak_target / np.abs(r).max()
nz = np.nonzero(np.abs(r).max(axis=1) > 1e-6)[0]
print(f"riser: starts {nz[0]/SR:.4f}s ends {nz[-1]/SR:.4f}s (cut at {cut_s:.4f}s), peak {20*np.log10(np.abs(r).max()):.2f} dBFS, LUFS {meter.integrated_loudness(r):.2f}")
sf.write("edit/stems/riser.wav", r, SR, subtype="PCM_24")

# ---- diagnostics: clicks (sample-to-sample jumps) in music
d = np.abs(np.diff(m[:, 0])); print("music max |diff| %.5f (p99.99 %.5f)" % (d.max(), np.percentile(d, 99.99)))
# whoosh variants alignment
for v in range(4):
    w = synth.sfx_whoosh(v); pk = np.argmax(np.abs(w).max(axis=1)) / SR
    env = np.abs(w).max(axis=1); 
    print(f"whoosh v{v}: len {len(w)/SR:.3f}s peak at {pk:.3f}s (target {synth.WHOOSH_PEAK})")
