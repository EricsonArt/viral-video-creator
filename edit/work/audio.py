#!/usr/bin/env python3
"""Voice processing, synthesized SFX (pop/tick/click/chime/whoosh x4), intro riser, stems and master mix.

No music is produced: the user asked for none ("nie dodawaj muzyki").
Levels relative to the voice peak: pops/chimes/clicks -10 dB, whooshes -9 dB, ticks -16 dB, riser -14 dB.
"""
import json, subprocess, sys, math
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
PLAN = json.load(open('plan.json'))
EV = json.load(open('hf_events.json'))
END = PLAN['end_s']; N = int(round(END * SR))
rng = np.random.default_rng(20260310)       # deterministic

def run(cmd):
    return subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

# ----------------------------------------------------------------------------- VOICE
# source = embedded camera audio (no separate clean audio exists); light clean-up chain, then loudness to -14 LUFS
run(f"""ffmpeg -v error -y -i audio/src_48k_stereo.wav -t {END} -af "highpass=f=75,afftdn=nr=9:nf=-50:nt=w,equalizer=f=220:t=q:w=1.1:g=-1.2,equalizer=f=3200:t=q:w=1.0:g=1.6,acompressor=threshold=0.09:ratio=2.0:attack=10:release=140:makeup=1.6" -ar 48000 -ac 2 audio/voice_proc.wav""")
v, _ = sf.read('audio/voice_proc.wav')
v = v[:N]
if len(v) < N:
    v = np.vstack([v, np.zeros((N - len(v), 2))])
# declick the very first / last samples (end sits on the decayed tail at ~-37 dB, so no long fade is needed)
fi = int(0.003 * SR); fo = int(0.012 * SR)
v[:fi] *= np.linspace(0, 1, fi)[:, None]
v[-fo:] *= np.linspace(1, 0, fo)[:, None]

def lufs(x):
    import pyloudnorm as pyln
    return pyln.Meter(SR).integrated_loudness(x)

target = -14.0

def true_peak_db(x):
    from scipy.signal import resample_poly
    up = np.stack([resample_poly(x[:, c], 4, 1) for c in range(x.shape[1])], 1)
    return 20 * np.log10(np.abs(up).max() + 1e-12)

def soft_limit(x, ceil_db, look_ms=4.0, rel_ms=80.0):
    """look-ahead limiter: gain reduction only where peaks exceed the ceiling, smooth attack, slow release (transparent for speech)"""
    from scipy.ndimage import minimum_filter1d
    ceil = 10 ** (ceil_db / 20)
    pk = np.abs(x).max(axis=1)
    req = np.minimum(1.0, ceil / (pk + 1e-9))
    la = int(look_ms * 1e-3 * SR)
    req = minimum_filter1d(req, size=2 * la + 1, origin=0)
    g = np.ones_like(req); rel = 1.0 / (rel_ms * 1e-3 * SR); cur = 1.0
    att = 1.0 / (look_ms * 1e-3 * SR)
    for i in range(len(req)):
        if req[i] < cur:
            cur = max(req[i], cur - att * (cur - req[i]) * 4) if cur - req[i] > 1e-4 else req[i]
        else:
            cur = min(req[i], cur + rel * (1 - cur) + 1e-7)
        g[i] = cur
    g = np.minimum(g, 1.0)
    return x * g[:, None]

gain_db = target - lufs(v)
ceil_db = -1.9
for it in range(14):
    vv = soft_limit(v * 10 ** (gain_db / 20), ceil_db)
    l = lufs(vv); tpv = true_peak_db(vv)
    if tpv > -1.05:
        ceil_db -= max(0.1, tpv + 1.05); continue
    if abs(l - target) < 0.06:
        break
    gain_db += (target - l)
v = vv
voice_peak = np.abs(v).max()
sf.write('../stems/voice.wav', v, SR, subtype='PCM_24')

# ----------------------------------------------------------------------------- SFX synthesis
def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))

def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, 'lp', fs=SR, output='sos'), x)

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], 'bp', fs=SR, output='sos'), x)

def norm_peak(x, peak=1.0):
    return x * (peak / (np.abs(x).max() + 1e-12))

def synth_pop(seed=0):
    """dull soft pop: low sine thump with a pitch drop + a touch of lowpassed noise"""
    n = int(0.16 * SR); t = np.arange(n) / SR
    f = 62 + 150 * np.exp(-t / 0.018)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * env_exp(n, 0.035)
    noise = lp(rng.standard_normal(n), 900) * env_exp(n, 0.006) * 0.35
    x = body + noise
    x[:int(0.001 * SR)] *= np.linspace(0, 1, int(0.001 * SR))
    return norm_peak(x)

def synth_tick(seed=0):
    """short soft key press: damped noise burst + low tick, slightly different every time"""
    r = np.random.default_rng(seed)
    n = int(0.045 * SR); t = np.arange(n) / SR
    fc = r.uniform(1600, 2400)
    click = bp(r.standard_normal(n), fc * 0.6, fc * 1.6) * env_exp(n, 0.004)
    thud = np.sin(2 * np.pi * r.uniform(150, 200) * t) * env_exp(n, 0.012) * 0.6
    x = click + thud
    x[:int(0.0005 * SR)] *= np.linspace(0, 1, int(0.0005 * SR))
    return norm_peak(x) * r.uniform(0.82, 1.0)

def synth_click():
    """soft bubbly click: rising sine 'bubble' + soft transient"""
    n = int(0.12 * SR); t = np.arange(n) / SR
    f = 520 + 900 * (1 - np.exp(-t / 0.02))
    ph = 2 * np.pi * np.cumsum(f) / SR
    bub = np.sin(ph) * env_exp(n, 0.028)
    tr = bp(rng.standard_normal(n), 1200, 5000) * env_exp(n, 0.003) * 0.4
    x = bub + tr
    x[:int(0.0008 * SR)] *= np.linspace(0, 1, int(0.0008 * SR))
    return norm_peak(x)

def synth_chime():
    """gentle two-note notification chime (E5 -> B5) with a soft attack and a short airy tail"""
    def note(f, dur, amp):
        n = int(dur * SR); t = np.arange(n) / SR
        s = np.sin(2 * np.pi * f * t) + 0.28 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 3 * f * t)
        e = (1 - np.exp(-t / 0.006)) * np.exp(-t / 0.22)
        return s * e * amp
    a = note(659.25, 0.9, 1.0); b = note(987.77, 1.1, 0.9)
    out = np.zeros(int(1.5 * SR))
    out[:len(a)] += a
    off = int(0.17 * SR); out[off:off + len(b)] += b
    # tiny ambience: two soft echoes
    for d, gdb in ((0.11, -16), (0.23, -22)):
        k = int(d * SR); out[k:] += out[:-k] * 10 ** (gdb / 20)
    return norm_peak(lp(out, 7000))

def synth_whoosh(variant):
    """low airy filtered-noise whoosh; returns (signal, index of loudest sample)."""
    cfg = [
        dict(dur=0.95, peak=0.50, f0=260, f1=2300, f2=420, q=0.9),
        dict(dur=1.05, peak=0.46, f0=200, f1=1900, f2=330, q=1.1),
        dict(dur=0.85, peak=0.52, f0=320, f1=2700, f2=520, q=0.8),
        dict(dur=1.00, peak=0.48, f0=240, f1=2100, f2=380, q=1.0),
    ][variant % 4]
    n = int(cfg['dur'] * SR); t = np.arange(n) / SR
    u = t / cfg['dur']
    pk = cfg['peak']
    # centre-frequency sweep: up to f1 at the peak, then down to f2
    fc = np.where(u < pk, cfg['f0'] * (cfg['f1'] / cfg['f0']) ** (u / pk), cfg['f1'] * (cfg['f2'] / cfg['f1']) ** ((u - pk) / (1 - pk)))
    # amplitude envelope: smooth swell to the peak then a longer release (equal-power raised cosine shapes)
    up = np.sin(0.5 * np.pi * np.clip(u / pk, 0, 1)) ** 2.2
    dn = np.cos(0.5 * np.pi * np.clip((u - pk) / (1 - pk), 0, 1)) ** 2.0
    amp = np.where(u < pk, up, dn)
    # time-varying band-pass via block-wise state-variable filter on white noise
    noise = rng.standard_normal(n)
    out = np.zeros(n); low = band = 0.0
    q = cfg['q']
    f = 2 * np.sin(np.pi * np.minimum(fc, 9000) / SR)
    for i in range(n):
        low += f[i] * band
        high = noise[i] - low - band / q
        band += f[i] * high
        out[i] = band
    out = lp(out, 5500) * amp
    out = out + 0.25 * lp(noise, 380) * amp * (1 - u)   # low body
    out = norm_peak(out)
    out[:int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
    out[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    pk_idx = int(np.argmax(np.abs(lp(out, 600)) * 0 + np.convolve(np.abs(out), np.ones(int(0.02 * SR)) / int(0.02 * SR), 'same')))
    return out, pk_idx

def synth_riser(dur):
    """low smooth swelling riser; peak (and audible end) at the last sample"""
    n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
    f = 55 * (4.2 ** (u ** 1.4))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
    noise = rng.standard_normal(n)
    # filtered noise whose cutoff opens over time (block-wise lowpass)
    nz = np.zeros(n); blk = 2048
    for s in range(0, n, blk):
        fc = 180 + 3800 * (s / n) ** 2
        seg = noise[max(0, s - 512):s + blk]
        y = lp(seg, fc, 2)
        nz[s:s + blk] = y[-len(nz[s:s + blk]):] if len(y) >= len(nz[s:s + blk]) else 0
    amp = (u ** 2.6)
    x = (tone * 0.8 + nz * 1.6) * amp
    x = norm_peak(x)
    x[-int(0.005 * SR):] *= np.linspace(1, 0, int(0.005 * SR))
    return x

# ----------------------------------------------------------------------------- event placement
runs = {r['id']: r for r in PLAN['runs']}
events = []        # (abs_time, kind, note)
for rid, lst in EV.items():
    if rid == 'CTA_START':
        continue
    base = EV['CTA_START'] if rid == 'CTA' else runs[rid]['a'] / PLAN['fps']
    for e in lst:
        events.append((base + e['t'], e['kind'], f"{rid}: {e['note']}"))
events.sort()

sfx = np.zeros((N, 2))
def place(sig, t, gain_db, peak_idx=0):
    start = int(round(t * SR)) - peak_idx
    gain = voice_peak * 10 ** (gain_db / 20)
    seg = sig * gain
    a = max(start, 0); b = min(start + len(seg), N)
    if b <= a:
        return
    seg = seg[a - start:b - start]
    sfx[a:b, 0] += seg; sfx[a:b, 1] += seg

whoosh_n = 0; last_variant = -1
placed = []
tick_i = 0
for t, kind, note in events:
    if kind == 'pop':
        place(synth_pop(), t, -10); placed.append((t, 'dull soft pop', note))
    elif kind == 'click':
        place(synth_click(), t, -10); placed.append((t, 'soft bubbly click', note))
    elif kind == 'chime':
        place(synth_chime(), t, -10); placed.append((t, 'two-note chime', note))
    elif kind == 'tick':
        place(synth_tick(tick_i), t, -16); tick_i += 1; placed.append((t, 'key tick', note))
    elif kind == 'whoosh':
        variant = whoosh_n % 4
        if variant == last_variant:
            variant = (variant + 1) % 4
        sig, pk = synth_whoosh(variant)
        place(sig, t, -9, pk); last_variant = variant; whoosh_n += 1
        placed.append((t, f'whoosh v{variant+1} (peak aligned to whip midpoint)', note))
assert whoosh_n <= 3

# the whoosh variants exist as a bank even if only some are used
variant_bank = {i + 1: synth_whoosh(i)[0] for i in range(4)}
import os
os.makedirs('../stems/extras', exist_ok=True)
for k_, sig_ in variant_bank.items():
    sf.write(f'../stems/extras/whoosh_v{k_}.wav', np.stack([sig_ * 0.7, sig_ * 0.7], 1), SR, subtype='PCM_24')

# riser: audible end exactly on the hook -> first-point cut (C1)
cut1 = PLAN['cuts']['C1'] / PLAN['fps']
RISER_DUR = 2.5
riser = np.zeros((N, 2))
rs = synth_riser(RISER_DUR)
a = int(round((cut1 - RISER_DUR) * SR)); b = a + len(rs)
rgain = voice_peak * 10 ** (-14 / 20)
riser[a:b, 0] = rs * rgain; riser[a:b, 1] = rs * rgain

sf.write('../stems/sfx.wav', np.clip(sfx, -1, 1), SR, subtype='PCM_24')
sf.write('../stems/riser.wav', np.clip(riser, -1, 1), SR, subtype='PCM_24')
json.dump([dict(t=round(t, 4), sound=s, event=n) for t, s, n in placed] + [dict(t=round(cut1 - RISER_DUR, 4), sound='riser start', event='intro riser'), dict(t=round(cut1, 4), sound='riser end', event='hook -> first point cut (R1->R2)')], open('sfx_log.json', 'w'), indent=1, ensure_ascii=False)

# ----------------------------------------------------------------------------- master (voice + sfx + riser; no music)
MASTER_CEIL = float(sys.argv[1]) if len(sys.argv) > 1 else -2.4      # pre-AAC true-peak ceiling (AAC overshoots)
mix0 = v + sfx + riser
gdb = -14.0 - lufs(mix0)
ceil_db = MASTER_CEIL + 0.2
for it in range(16):
    mix = soft_limit(mix0 * 10 ** (gdb / 20), ceil_db)
    l = lufs(mix); tp = true_peak_db(mix)
    if tp > MASTER_CEIL:
        ceil_db -= max(0.1, tp - MASTER_CEIL); continue
    if abs(l + 14.0) < 0.06:
        break
    gdb += (-14.0 - l)
sf.write('master_mix.wav', np.clip(mix, -1, 1), SR, subtype='PCM_24')
print(f"voice: LUFS {lufs(v):.2f}  TP {true_peak_db(v):.2f}")
print(f"master (pre-AAC): LUFS {lufs(mix):.2f}  TP {true_peak_db(mix):.2f}  events placed: {len(placed)}  whooshes: {whoosh_n}")
