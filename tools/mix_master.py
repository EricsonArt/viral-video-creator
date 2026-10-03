"""Sum voice + sfx + riser + music -> master, target -14 LUFS integrated, true peak <= -1 dBTP (transparent limiter only if needed).
Measures every stem and the master with ffmpeg ebur128 (BS.1770-4 / EBU R128). Writes work/audio_measure.json."""
import json, re, subprocess, numpy as np, soundfile as sf
SR = 48000
def measure(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    t = r.stderr
    summ = t[t.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    LRA = float(re.search(r"LRA:\s+(-?[\d.]+) LU", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    return {"integrated_LUFS": I, "LRA_LU": LRA, "true_peak_dBTP": tp}
stems = {k: sf.read(f"edit/stems/{k}.wav")[0] for k in ("voice", "sfx", "riser", "music")}
n = min(len(v) for v in stems.values()); assert all(len(v) == n for v in stems.values()), {k: len(v) for k, v in stems.items()}
mix = sum(stems.values())
sf.write("work/_mix_raw.wav", mix, SR, subtype="FLOAT")
m0 = measure("work/_mix_raw.wav"); print("sum before master gain:", m0)
gain_db = -14.0 - m0["integrated_LUFS"]
cur = mix * 10 ** (gain_db / 20)
import sys; sys.path.insert(0, "tools")
from limiter import tp_limit
gain_db = -14.0 - m0["integrated_LUFS"]
for it in range(8):
    cur_l, gs = tp_limit(mix * 10 ** (gain_db / 20), ceil_db=-1.2, look_ms=10.0, sr=SR)
    sf.write("work/_mix_m.wav", cur_l, SR, subtype="FLOAT"); mm = measure("work/_mix_m.wav")
    red = -20 * np.log10(gs.min())
    print(f"iter {it}: gain {gain_db:+.2f} dB -> {mm['integrated_LUFS']:.2f} LUFS, TP {mm['true_peak_dBTP']:.2f} dBTP (max limiter reduction {red:.1f} dB)")
    if abs(mm["integrated_LUFS"] + 14.0) <= 0.05 and mm["true_peak_dBTP"] <= -1.0: break
    gain_db += (-14.0 - mm["integrated_LUFS"])
cur = cur_l
sf.write("edit/master_mix.wav", cur_l, SR, subtype="PCM_24")
res = {"voice": measure("edit/stems/voice.wav"), "sfx": measure("edit/stems/sfx.wav"), "riser": measure("edit/stems/riser.wav"),
       "music": measure("edit/stems/music.wav"), "master": measure("edit/master_mix.wav"), "master_gain_db": round(gain_db, 2),
       "limiter_max_reduction_db": round(float(red), 2)}
json.dump(res, open("work/audio_measure.json", "w"), indent=1)
for k, v in res.items(): print(k, v)
