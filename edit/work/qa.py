#!/usr/bin/env python3
"""QA measurements for REPORT.md: loudness (ebur128), ffprobe facts, audio sync of SFX, join gaps, SPLIT seam, last frames."""
import json, re, subprocess, os
import numpy as np, soundfile as sf, cv2
from scipy.signal import butter, sosfilt

os.makedirs('qa', exist_ok=True)
FINAL = '../final.mp4'
PLAN = json.load(open('plan.json')); FPS = 60
out = {}

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

# ---- ffprobe
p = json.loads(sh(f'ffprobe -v error -show_streams -show_format -of json "{FINAL}"').stdout)
v = [s for s in p['streams'] if s['codec_type'] == 'video'][0]; a = [s for s in p['streams'] if s['codec_type'] == 'audio'][0]
out['probe'] = dict(width=v['width'], height=v['height'], fps=v['r_frame_rate'], codec=v['codec_name'], profile=v.get('profile'), pix_fmt=v['pix_fmt'],
                    nb_frames=v.get('nb_frames'), v_duration=float(v['duration']), a_codec=a['codec_name'], a_rate=a['sample_rate'], a_channels=a['channels'],
                    a_duration=float(a['duration']), v_start=float(v.get('start_time', 0)), a_start=float(a.get('start_time', 0)),
                    color=(v.get('color_space'), v.get('color_primaries'), v.get('color_transfer'), v.get('color_range')), size_mb=round(int(p['format']['size']) / 1e6, 1),
                    bit_rate_mbps=round(int(p['format']['bit_rate']) / 1e6, 2))

# ---- loudness
def ebur(path, extra=''):
    r = sh(f'ffmpeg -nostats -hide_banner -i "{path}" {extra} -af ebur128=peak=true -f null - 2>&1')
    t = r.stdout + r.stderr
    I = re.findall(r'I:\s+(-?[\d.]+) LUFS', t); P = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', t)
    return dict(lufs=float(I[-1]) if I else None, true_peak=float(P[-1]) if P else None)
out['loudness'] = {
    'voice': ebur('../stems/voice.wav'), 'sfx': ebur('../stems/sfx.wav'), 'riser': ebur('../stems/riser.wav'),
    'master_mix_wav': ebur('master_mix.wav'), 'final_mp4_audio': ebur(FINAL)}

# ---- voice gaps: quiet runs (RMS 10 ms below -32 dB) in the voice stem
vx, sr = sf.read('../stems/voice.wav'); m = vx.mean(axis=1)
w = int(0.010 * sr); n = len(m) // w
db = 20 * np.log10(np.sqrt((m[:n * w].reshape(n, w) ** 2).mean(axis=1)) + 1e-9)
runs = []; i = 0
while i < n:
    if db[i] < -32:
        j = i
        while j < n and db[j] < -32: j += 1
        runs.append(((j - i) * 10, round(i / 100, 2)))
        i = j
    else:
        i += 1
out['voice_quiet_runs_ms'] = sorted(runs, reverse=True)[:5]
out['voice_first_sound_ms'] = int(np.argmax(db > -30) * 10)
out['voice_last_sound_s'] = round(max(k for k in range(n) if db[k] >= -35) / 100 + 0.01, 3)

# ---- whoosh peak vs whip midpoint, riser end vs cut
sfx, _ = sf.read('../stems/sfx.wav'); ms = np.abs(sfx).max(axis=1)
r4 = [r for r in PLAN['runs'] if r['id'] == 'R4'][0]
mid = r4['a'] / FPS + 2.0
win = int(0.02 * 48000)
env = np.convolve(ms, np.ones(win) / win, 'same')
lo, hi = int((mid - 0.6) * 48000), int((mid + 0.6) * 48000)
pk = lo + int(np.argmax(env[lo:hi]))
out['whoosh'] = dict(whip_midpoint_s=round(mid, 4), whoosh_peak_s=round(pk / 48000, 4), offset_ms=round((pk / 48000 - mid) * 1000, 1))
ris, _ = sf.read('../stems/riser.wav'); rm = np.abs(ris).max(axis=1)
nz = np.where(rm > 1e-4)[0]
out['riser'] = dict(start_s=round(nz[0] / 48000, 4), audible_end_s=round(nz[-1] / 48000, 4), cut_C1_s=PLAN['cuts']['C1'] / FPS, peak_vs_voice_peak_db=round(20 * np.log10(rm.max() / np.abs(vx).max()), 1))
out['sfx_peak_vs_voice_peak_db'] = round(20 * np.log10(ms.max() / np.abs(vx).max()), 1)

# ---- frames
cap = cv2.VideoCapture(FINAL); nfr = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); out['frames_read'] = nfr
def frame(nn):
    cap.set(cv2.CAP_PROP_POS_FRAMES, nn); ok, f = cap.read(); return f
# last frames: non-black, non-frozen
last = [frame(nfr - k).astype(np.int16) for k in range(1, 7)]
out['last_frames_mean'] = [round(float(x.mean()), 1) for x in last]
out['last_frames_diff'] = [round(float(np.abs(last[i] - last[i + 1]).mean()), 2) for i in range(5)]
first = frame(0); out['first_frame_mean'] = round(float(first.mean()), 1)
# cut joins
joins = {}
for cname, cf in PLAN['cuts'].items():
    a_ = frame(cf - 1); b_ = frame(cf)
    joins[cname] = dict(frame=cf, t=round(cf / FPS, 4), diff_prev_next=round(float(np.abs(a_.astype(np.int16) - b_.astype(np.int16)).mean()), 1),
                        mean_prev=round(float(a_.mean()), 1), mean_next=round(float(b_.mean()), 1))
    cv2.imwrite(f'qa/join_{cname}.png', np.hstack([cv2.resize(a_, (270, 480)), cv2.resize(b_, (270, 480))]))
out['joins'] = joins
# duplicated / missing frame check across the whole video (frame-to-frame diff) -- source is 30 fps so pairs repeat in CAM runs
diffs = []; prev = None
cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
for k in range(nfr):
    ok, f = cap.read()
    if not ok: break
    g = cv2.resize(f, (108, 192)).astype(np.int16)
    if prev is not None: diffs.append(float(np.abs(g - prev).mean()))
    prev = g
diffs = np.array(diffs)
out['frame_diff_stats'] = dict(mean=round(float(diffs.mean()), 3), max=round(float(diffs.max()), 2), max_at_frame=int(diffs.argmax()) + 1, zero_diff_frames=int((diffs < 0.02).sum()))
np.save('qa/frame_diffs.npy', diffs)
# whole-video contact sheet (every 1 s)
sh(f'ffmpeg -v error -y -i "{FINAL}" -vf "fps=1,scale=216:384,tile=14x3:padding=4:color=gray" -frames:v 1 qa/contact_whole.png')
json.dump(out, open('qa/qa.json', 'w'), indent=1)
print(json.dumps(out, indent=1))
