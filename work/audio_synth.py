#!/usr/bin/env python3
"""Synthesise SFX, riser and music stems (all full length, 48 kHz stereo, 24-bit) from events.json."""
import json, os, subprocess
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
W = os.path.dirname(os.path.abspath(__file__))
plan = json.load(open(os.path.join(W, 'plan.json')))
events = json.load(open(os.path.join(W, 'events.json')))
END = plan['end']
N = int(round(END * SR))
OUT = os.path.join(os.path.dirname(W), 'edit', 'stems')
os.makedirs(OUT, exist_ok=True)

voice, _ = sf.read(os.path.join(OUT, 'voice.wav'))
vpeak = np.abs(voice).max()
vpeak_db = 20 * np.log10(vpeak)
print(f'voice sample peak {vpeak_db:.2f} dBFS')
def lin(db_rel_voice_peak):  # level relative to the voice peak
    return vpeak * 10 ** (db_rel_voice_peak / 20)

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)
def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)
def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)
def norm(x):
    return x / (np.abs(x).max() + 1e-12)
def t_(n):
    return np.arange(n) / SR

def svf_sweep(x, fc, q):
    """Chamberlin state-variable filter, time-varying centre frequency fc[n] (Hz), returns band-pass output."""
    low = band = 0.0; out = np.zeros_like(x)
    f = 2 * np.sin(np.pi * np.minimum(fc, SR / 6) / SR); qq = 1.0 / q
    for i in range(len(x)):
        low += f[i] * band
        high = x[i] - low - qq * band
        band += f[i] * high
        out[i] = band
    return out

# ------------------------------------------------------------------ SFX
def s_click():
    n = int(0.14 * SR); t = t_(n)
    f = 380 + 330 * np.exp(-t / 0.018)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.minimum(1, t / 0.0012) * np.exp(-t / 0.032)
    rng = np.random.default_rng(11)
    tick = hp(rng.standard_normal(n), 3000) * np.exp(-t / 0.0018) * 0.35
    return norm(body + tick)

def s_pop():
    n = int(0.28 * SR); t = t_(n)
    f = 68 + 95 * np.exp(-t / 0.022)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.minimum(1, t / 0.002) * np.exp(-t / 0.055)
    rng = np.random.default_rng(5)
    puff = lp(rng.standard_normal(n), 900) * np.exp(-t / 0.012) * 0.25
    return norm(lp(body + puff, 1800))

def s_key(seed):
    rng = np.random.default_rng(seed)
    n = int(0.08 * SR); t = t_(n)
    sh = 1 + rng.uniform(-0.08, 0.08)
    thock = np.sin(2 * np.pi * np.cumsum(150 * sh + 90 * sh * np.exp(-t / 0.01)) / SR) * np.exp(-t / 0.014) * 0.7
    click = bp(rng.standard_normal(n), 1800 * sh, 5200 * sh) * np.exp(-t / 0.0035)
    return norm(thock + click)

def s_ticks(dur, seed=3):
    rng = np.random.default_rng(seed)
    n = int((dur + 0.05) * SR); out = np.zeros(n); t = 0.0
    while t < dur:
        k = int(0.006 * SR); tt = t_(k)
        tick = hp(rng.standard_normal(k), 3500) * np.exp(-tt / 0.0016)
        a = rng.uniform(0.45, 1.0)
        i = int(t * SR); out[i:i + k] += tick[:max(0, min(k, n - i))] * a
        t += rng.uniform(0.024, 0.036)
    return norm(out)

def s_chime():
    n = int(1.3 * SR); t = t_(n); out = np.zeros(n)
    for f0, t0, g in ((659.25, 0.0, 1.0), (987.77, 0.15, 0.85)):
        m = t >= t0; tt = np.where(m, t - t0, 0)
        env = np.minimum(1, tt / 0.005) * np.exp(-tt / 0.30) * m
        out += g * env * (np.sin(2 * np.pi * f0 * tt) + 0.22 * np.sin(2 * np.pi * 2 * f0 * tt) + 0.07 * np.sin(2 * np.pi * 3 * f0 * tt))
    return norm(lp(out, 6000))

WHOOSH = {   # (seed, sweep lo, peak, hi, resonance Q, body Hz)
    'A': (101, 260, 1750, 420, 1.1, 82),
    'B': (202, 190, 1350, 300, 0.9, 74),
    'C': (303, 330, 2150, 520, 1.3, 90),
    'D': (404, 220, 1550, 360, 1.0, 78),
}
def s_whoosh(variant, total=1.05, peak_t=0.45):
    seed, f_lo, f_pk, f_end, q, body = WHOOSH[variant]
    n = int(total * SR); t = t_(n)
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(n)
    up = np.clip(t / peak_t, 0, 1); dn = np.clip((t - peak_t) / (total - peak_t), 0, 1)
    fc = np.where(t < peak_t, f_lo * (f_pk / f_lo) ** (up ** 1.4), f_pk * (f_end / f_pk) ** (dn ** 0.8))
    y = svf_sweep(x, fc, 2.2 + q) * 0.8
    air = lp(hp(x, 600), 3500) * 0.28
    env = np.where(t < peak_t, up ** 1.9, (1 - dn) ** 1.7)
    env = np.minimum(env, 1.0) * np.minimum(1, (total - t) / 0.02)
    bodyw = np.sin(2 * np.pi * np.cumsum(body * (0.8 + 0.4 * env)) / SR) * env * 0.25
    out = (y + air) * env + bodyw
    return norm(lp(out, 5200)), peak_t

def s_whoosh_soft(variant='C'):
    w, pk = s_whoosh(variant, total=0.8, peak_t=0.35)
    return w, pk

# ------------------------------------------------------------------ build SFX stem
L = np.zeros(N); R = np.zeros(N)
def place(sig, t0, gain_db, pan=0.0, peak_at=None):
    i0 = int(round((t0 - (peak_at or 0)) * SR))
    g = lin(gain_db)
    a = 10 ** (-abs(pan) * 3 / 20)
    gl, gr = (g, g * a) if pan > 0 else (g * a, g) if pan < 0 else (g, g)
    s0 = max(0, -i0); e = min(len(sig), N - i0)
    if e > s0:
        L[i0 + s0:i0 + e] += sig[s0:e] * gl; R[i0 + s0:i0 + e] += sig[s0:e] * gr

used = []
variant_cycle = ['A', 'B', 'C']; vi = 0; last_variant = None
key_i = 0
for ev in sorted(events, key=lambda e: e['t']):
    t = ev['t']; ty = ev['type']
    if ty == 'whoosh':
        v = variant_cycle[vi % 3]; vi += 1
        assert v != last_variant
        w, pk = s_whoosh(v); place(w, t, -9.0, peak_at=pk); last_variant = v
        used.append(dict(t=t, type='whoosh', variant=v, level_db=-9.0, peak_aligned_to='whip midpoint'))
    elif ty == 'whoosh_soft':
        v = variant_cycle[vi % 3]; vi += 1
        assert v != last_variant
        w, pk = s_whoosh_soft(v); place(w, t, -12.0, peak_at=pk); last_variant = v
        used.append(dict(t=t, type='whoosh (soft logo reveal)', variant=v, level_db=-12.0, peak_aligned_to='logo morph'))
    elif ty == 'pop':
        place(s_pop(), t, -10.0); used.append(dict(t=t, type='pop', level_db=-10.0))
    elif ty == 'click':
        place(s_click(), t, -10.0); used.append(dict(t=t, type='click', level_db=-10.0))
    elif ty == 'chime':
        place(s_chime(), t, -10.0); used.append(dict(t=t, type='chime', level_db=-10.0))
    elif ty == 'key':
        key_i += 1; place(s_key(30 + key_i), t, -16.0, pan=((key_i % 3) - 1) * 0.15); used.append(dict(t=t, type='key', level_db=-16.0))
    elif ty == 'ticks':
        place(s_ticks(ev.get('dur', 0.5)), t, -16.0); used.append(dict(t=t, type='ticks', dur=ev.get('dur', 0.5), level_db=-16.0))
sfx = np.stack([L, R], axis=1)
sf.write(os.path.join(OUT, 'sfx.wav'), sfx, SR, subtype='PCM_24')

# ------------------------------------------------------------------ riser (ends exactly on the hook -> first-point cut)
cut = plan['runs'][0]['end']
RDUR = 2.5
n = int(RDUR * SR); t = t_(n); rng = np.random.default_rng(77)
prog = t / RDUR
noise = rng.standard_normal(n)
fc = 140 * (2600 / 140) ** (prog ** 1.2)
nz = svf_sweep(noise, fc, 1.6)
nz = lp(nz, 3500)
f_saw = 55 * 2 ** (1.15 * prog)
tone = np.zeros(n)
for det in (-0.006, 0.0, 0.006):
    ph = np.cumsum(f_saw * (1 + det)) / SR
    tone += 2 * (ph % 1.0) - 1
tone = tone / 3; tone = lp(tone, 500) * (1 - prog ** 2) + lp(tone, 1800) * prog ** 2
sub = np.sin(2 * np.pi * np.cumsum(f_saw / 2) / SR)
env = (prog ** 2.2) * np.minimum(1, t / 0.12)
r = (nz / (np.abs(nz).max() + 1e-9) * 0.55 + tone * 0.6 + sub * 0.35) * env
r = r * np.minimum(1, (RDUR - t) / 0.006)           # stop on the last sample: the audible end IS the cut
r = norm(r) * lin(-14.0)
riser = np.zeros((N, 2)); i0 = int(round((cut - RDUR) * SR))
riser[i0:i0 + n, 0] = r; riser[i0:i0 + n, 1] = r
# very slight stereo width from a delayed copy (Haas, 9 ms) so it feels wide without smearing the end point
d = int(0.009 * SR); riser[i0 + d:i0 + n, 1] = r[:-d]
sf.write(os.path.join(OUT, 'riser.wav'), riser, SR, subtype='PCM_24')

# ------------------------------------------------------------------ music: original warm minimal electronic bed, 110 BPM
BPM = 110.0; beat = 60.0 / BPM; bar = 4 * beat
nbars = int(np.ceil(END / bar)) + 1
def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
CH = [  # (bass midi, chord midis)   Fmaj7 - G6 - Am7 - Cmaj7(add9)
    (41, [53, 57, 60, 64, 67]),
    (43, [55, 59, 62, 64, 69]),
    (45, [57, 60, 64, 67, 71]),
    (36, [55, 59, 62, 64, 71]),
]
mus = np.zeros((N, 2))
rng = np.random.default_rng(2024)

def saw(f, n, det):
    ph = np.cumsum(np.full(n, f * (1 + det))) / SR
    return 2 * (ph % 1.0) - 1
def tri(f, n):
    ph = np.cumsum(np.full(n, f)) / SR
    return 2 * np.abs(2 * (ph % 1.0) - 1) - 1

# pad: one chord per 2 bars, cross-overlapping with long release; first chord starts at full level (no fade-in)
pad = np.zeros((N, 2))
for ci in range(int(np.ceil(END / (2 * bar))) + 1):
    root, notes = CH[ci % 4]
    t0 = ci * 2 * bar; t1 = t0 + 2 * bar + 1.1
    i0 = int(t0 * SR); n = min(int((t1 - t0) * SR), N - i0)
    if n <= 0: break
    tt = t_(n)
    atk = 0.005 if ci == 0 else 0.7
    e = np.minimum(1, tt / atk) * np.minimum(1, np.maximum(0, (t1 - t0 - tt)) / 1.1)
    vl = np.zeros(n); vr = np.zeros(n)
    for k, m in enumerate(notes):
        f = mtof(m)
        for det, pan in ((-0.0055, -1), (0.0, 0), (0.0055, 1)):
            s = saw(f, n, det)
            if pan <= 0: vl += s * (1 - 0.35 * max(0, pan + 1) * 0 if True else 1)
            if pan >= 0: vr += s
    # slow filter movement: crossfade between a dark and a bright version
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.07 * tt + 0.13 * ci))
    dl, dr = lp(vl, 700), lp(vr, 700); bl, br = lp(vl, 1700), lp(vr, 1700)
    pl = (dl * (1 - lfo) + bl * lfo) * e; pr = (dr * (1 - lfo) + br * lfo) * e
    pad[i0:i0 + n, 0] += pl; pad[i0:i0 + n, 1] += pr
pad /= (np.abs(pad).max() + 1e-9)

# sub bass: one note per bar on the chord root (sine, soft attack, gentle decay)
bass = np.zeros(N)
for b in range(nbars):
    root = CH[(b // 2) % 4][0]
    i0 = int(b * bar * SR); n = min(int(bar * SR), N - i0)
    if n <= 0: break
    tt = t_(n)
    e = np.minimum(1, tt / (0.004 if b == 0 else 0.03)) * np.exp(-tt / 1.6) * np.minimum(1, (bar - tt) / 0.06)
    bass[i0:i0 + n] += np.sin(2 * np.pi * mtof(root) * tt) * e + 0.18 * np.sin(2 * np.pi * 2 * mtof(root) * tt) * e
bass /= (np.abs(bass).max() + 1e-9)

# kick on beats 1 and 3, soft; hats on off-beat 8ths with ghost 16ths; plucks on a sparse pattern
kick = np.zeros(N); hat = np.zeros((N, 2)); pluck = np.zeros((N, 2))
kn = int(0.34 * SR); kt = t_(kn)
kshape = np.sin(2 * np.pi * np.cumsum(46 + 88 * np.exp(-kt / 0.028)) / SR) * np.exp(-kt / 0.11) * np.minimum(1, kt / 0.0015)
kshape += 0.18 * hp(rng.standard_normal(kn), 1500) * np.exp(-kt / 0.004)
hn = int(0.06 * SR); ht = t_(hn)
hshape = hp(rng.standard_normal(hn), 7000) * np.exp(-ht / 0.014)
for b in range(nbars):
    for bt in (0, 2):
        i0 = int((b * bar + bt * beat) * SR); e = min(kn, N - i0)
        if e > 0: kick[i0:i0 + e] += kshape[:e] * (1.0 if bt == 0 else 0.8)
    for s in range(8):                                   # eighths: off-beats stronger, on-beats ghost
        tt0 = b * bar + s * beat / 2 + (0.012 if s % 2 else 0.0)
        i0 = int(tt0 * SR); e = min(hn, N - i0)
        if e > 0:
            g = 0.55 if s % 2 else 0.18
            pan = 0.3 if s % 4 < 2 else -0.3
            hat[i0:i0 + e, 0] += hshape[:e] * g * (1 - max(0, pan)); hat[i0:i0 + e, 1] += hshape[:e] * g * (1 + min(0, pan) * -1 * 0 + max(0, pan) * 0)
    root, notes = CH[(b // 2) % 4]
    pat = [(1, 0), (2.5, 2), (3, 3), (3.5, 1)] if b % 2 == 0 else [(0.5, 3), (1.5, 1), (2, 2), (3.5, 4)]
    for pos, ni in pat:
        f = mtof(notes[ni % len(notes)] + 12)
        pn = int(0.55 * SR); ptt = t_(pn)
        ps = tri(f, pn) * np.exp(-ptt / 0.16) * np.minimum(1, ptt / 0.003)
        ps = lp(ps, 2200)
        i0 = int((b * bar + pos * beat) * SR); e = min(pn, N - i0)
        if e > 0:
            pluck[i0:i0 + e, 0] += ps[:e] * 0.55; pluck[i0:i0 + e, 1] += ps[:e] * 0.55
# reverb (synthetic IR, decorrelated L/R) on pad + plucks
def make_ir(seed, length=1.9, tau=0.5):
    r = np.random.default_rng(seed).standard_normal(int(length * SR)); tt = t_(len(r))
    return lp(r * np.exp(-tt / tau), 4500) * np.minimum(1, tt / 0.012)
irL, irR = make_ir(1), make_ir(2)
def reverb(x):
    mono = x.mean(axis=1)
    wl = fftconvolve(mono, irL)[:N]; wr = fftconvolve(mono, irR)[:N]
    return np.stack([wl, wr], axis=1) / (np.abs(wl).max() + 1e-9)
send = pad * 0.5 + pluck * 0.9
wet = reverb(send) * 0.22
mus[:, 0] = pad[:, 0] * 0.60 + pluck[:, 0] * 0.22 + bass * 0.55 + kick * 0.62 + hat[:, 0] * 0.060 + wet[:, 0]
mus[:, 1] = pad[:, 1] * 0.60 + pluck[:, 1] * 0.22 + bass * 0.55 + kick * 0.62 + hat[:, 1] * 0.060 + wet[:, 1]
mus = lp(mus.T, 14000).T
mus = np.stack([hp(mus[:, 0], 28), hp(mus[:, 1], 28)], axis=1)
# 5 ms declick at the start, 800 ms fade-out ending exactly on END
nfi = int(0.005 * SR); mus[:nfi] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, nfi)))[:, None]
nfo = int(0.800 * SR); mus[-nfo:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, nfo)))[:, None]

def lufs_tp(fn):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', fn, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    i = float(r.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0])
    tp = float(r.split('True peak:')[1].split('Peak:')[1].split('dBFS')[0])
    return i, tp
tmp = os.path.join(W, 'audio', '_mus.wav')
sf.write(tmp, mus, SR, subtype='FLOAT')
li, _ = lufs_tp(tmp); g = -24.0 - li
mus *= 10 ** (g / 20)
sf.write(os.path.join(OUT, 'music.wav'), mus, SR, subtype='PCM_24')
json.dump(used, open(os.path.join(W, 'sfx_log.json'), 'w'), indent=1)
print('music gain', round(g, 2), 'dB; stems written')
for nme in ('voice', 'sfx', 'riser', 'music'):
    i, tp = lufs_tp(os.path.join(OUT, nme + '.wav'))
    d = sf.info(os.path.join(OUT, nme + '.wav'))
    print(f'{nme:6s} {d.duration:8.3f}s  ch{d.channels}  LUFS {i:7.2f}  TP {tp:6.2f}')
