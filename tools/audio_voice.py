"""Voice stem: clean + level the camera audio of the supplied short (no separate clean audio exists), pad lead-in, cut at END.

Output: edit/stems/voice.wav  (48 kHz, stereo = dual-mono, 24-bit, exactly END_F/60 s long)
"""
import json, subprocess, numpy as np, soundfile as sf, pyloudnorm as pyln, os

SR = 48000
plan = json.load(open("work/plan.json"))
D, END_F = plan["D"], plan["END_F"]
SRC_END_S = (END_F - D) / 60.0                    # 59.70 s of source audio
N_TOTAL = END_F * SR // 60                        # 2,867,200
N_LEAD = D * SR // 60                             # 1,600 samples = 33.3 ms
os.makedirs("edit/stems", exist_ok=True)

x, sr = sf.read("work/src48k.wav")
assert sr == SR
mono = x.mean(axis=1).astype(np.float64)          # L/R correlation 0.9996 -> dual mono
mono = mono[: int(round(SRC_END_S * SR))]
sf.write("work/voice_raw_mono.wav", mono, SR, subtype="FLOAT")

# --- cleaning chain (ffmpeg): the source is already heavily compressed (-13.6 LUFS, PLR 13.6 dB) and has no clean noise-only
#     region, so NO compressor (it only cost 6 dB of loudness): HPF + light denoise + gentle EQ, then level + transparent peak limiter.
chain = ",".join([
    "highpass=f=75:poles=2",
    "afftdn=nr=6:nf=-45:nt=w",                    # light broadband denoise (6 dB)
    "equalizer=f=280:t=q:w=1.0:g=-2",             # mud
    "equalizer=f=3200:t=q:w=0.9:g=1.5",           # presence
])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "work/voice_raw_mono.wav", "-af", chain, "-ar", str(SR),
                "-c:a", "pcm_f32le", "work/voice_clean_mono.wav"], check=True)
y, _ = sf.read("work/voice_clean_mono.wav")
y = y.astype(np.float64)

# --- lead-in (33.3 ms) before the first word + 5 ms declick at the cut, tail fade (voice tail decays toward the floor)
nfi = int(0.005 * SR)
y[:nfi] *= np.sin(np.linspace(0, np.pi / 2, nfi)) ** 2
nfo = int(0.120 * SR)
y[-nfo:] *= np.cos(np.linspace(0, np.pi / 2, nfo)) ** 2
y = np.concatenate([np.zeros(N_LEAD), y])
y = y[:N_TOTAL] if len(y) >= N_TOTAL else np.concatenate([y, np.zeros(N_TOTAL - len(y))])
assert len(y) == N_TOTAL, (len(y), N_TOTAL)

# --- level: integrated -14 LUFS (BS.1770) via ONE linear gain followed by a look-ahead peak limiter (ceiling -1.2 dBFS);
#     gain is iterated so the *limited* result lands on -14.0 LUFS.
meter = pyln.Meter(SR)
sys_path = __import__("sys").path; sys_path.insert(0, "tools")
from limiter import tp_limit
def limited(sig, g_db):
    out, _ = tp_limit(sig * 10 ** (g_db / 20), ceil_db=-1.5, look_ms=10.0, sr=SR)
    return out[:, 0]
y = np.concatenate([np.zeros(0), y])
lufs0 = meter.integrated_loudness(np.stack([y, y], 1))
g = -14.0 - lufs0
for it in range(6):
    out = limited(y, g)
    l = meter.integrated_loudness(np.stack([out, out], 1))
    if abs(l + 14.0) < 0.03: break
    g += (-14.0 - l)
red = 20 * np.log10(np.abs(y * 10 ** (g / 20)).max() / np.abs(out).max())
print(f"voice: pre {lufs0:.2f} LUFS, final gain {g:+.2f} dB -> {l:.2f} LUFS; sample peak {20*np.log10(np.abs(out).max()):.2f} dBFS; max limiter reduction {red:.1f} dB")
st = np.stack([out, out], axis=1)
sf.write("edit/stems/voice.wav", st, SR, subtype="PCM_24")
print("wrote edit/stems/voice.wav", st.shape, st.shape[0] / SR, "s")
