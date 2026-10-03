"""Everything audible besides the voice is synthesised here with numpy/scipy (no samples, no files).

Public API
  music(n_samples)                  -> (n,2) float64   original instrumental bed, 108 BPM, beat 1 at sample 0
  riser(n_samples, end_s, dur_s)    -> (n,2)           low smooth swelling riser whose audible end lands exactly at end_s
  sfx_click/key/ticks/pop/chime/whoosh -> (m,2) one-shot buffers (peak-normalised to 1.0; the mixer applies levels)
"""
import numpy as np
from scipy import signal as ss

SR = 48000


def _rng(seed): return np.random.RandomState(seed)
def _t(n): return np.arange(n) / SR
def _env_ad(n, a, d, curve=3.0):
    t = _t(n); e = np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-t / max(d, 1e-4) * curve / 3)
    return e
def _sos(kind, f, order=2, fs=SR, **kw):
    return ss.butter(order, f, btype=kind, fs=fs, output="sos")
def _filt(x, kind, f, order=2): return ss.sosfilt(_sos(kind, f, order), x)
def _norm(x, peak=1.0):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x
def _stereo(x, pan=0.0):                       # equal-power pan, pan in [-1,1]
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)
def _mf(m): return 440.0 * 2 ** ((m - 69) / 12)
def _place(buf, x, pos):
    """add stereo/mono x into buf at sample pos (clipped to buffer)."""
    pos = int(round(pos))
    if pos >= len(buf) or pos + len(x) <= 0: return
    a = max(0, -pos); b = min(len(x), len(buf) - pos)
    buf[pos + a: pos + b] += x[a:b]


# ---------------------------------------------------------------------------------------------- reverb
def _ir(seconds=1.7, seed=7, damp=5200):
    r = _rng(seed); n = int(seconds * SR); t = _t(n)
    out = []
    for ch in range(2):
        x = r.randn(n) * np.exp(-t / (seconds / 5.5))
        x = _filt(x, "lowpass", damp, 2)
        x[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        out.append(x / np.sqrt((x ** 2).sum()))
    return np.stack(out, axis=1)
def _reverb(x, wet=0.25, seconds=1.7):
    ir = _ir(seconds)
    y = np.stack([ss.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)
    return x * (1 - wet) + y * wet * 3.2


# ---------------------------------------------------------------------------------------------- music
def music(n, bpm=108.0, seed=11):
    beat = 60.0 / bpm * SR
    bar = beat * 4
    out = np.zeros((n, 2))
    pad = np.zeros((n, 2)); pluck = np.zeros((n, 2)); drums = np.zeros((n, 2)); bass = np.zeros((n, 2))
    r = _rng(seed)
    # A minor, 4-chord loop (i - VI - III - VII), one chord per bar
    chords = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]   # (bass midi, chord midi)
    n_bars = int(np.ceil(n / bar)) + 1
    for b in range(n_bars):
        root, tones = chords[b % 4]
        t0 = b * bar
        # ---- pad: 3 detuned saws per tone, lowpassed, slow attack / long release, overlaps next bar
        ln = int(bar + 0.9 * SR); tt = _t(ln)
        env = np.minimum(1, tt / 0.45) * np.where(tt < bar / SR, 1.0, np.exp(-(tt - bar / SR) / 0.28))
        for ti, m in enumerate(tones):
            for dt_c, pan in ((-6, -0.55), (0, 0.0), (7, 0.55)):
                f = _mf(m) * 2 ** (dt_c / 1200)
                ph = r.rand() * 2 * np.pi
                x = ss.sawtooth(2 * np.pi * f * tt + ph) * 0.5 + np.sin(2 * np.pi * f * tt + ph) * 0.5
                x = _filt(x, "lowpass", 1100 + 250 * np.sin(2 * np.pi * (0.07 * (t0 / SR) + ti * 0.3)), 2) * env * 0.045
                _place(pad, _stereo(x, pan), t0)
        # ---- bass: soft 8th pulse on the root (hits at 0, 1.5, 2, 3.5 beats)
        for hb in (0, 1.5, 2, 3.5):
            ln2 = int(0.42 * SR); t2 = _t(ln2); f = _mf(root)
            x = np.sin(2 * np.pi * f * t2) + 0.28 * np.sin(2 * np.pi * 2 * f * t2)
            x = np.tanh(1.4 * x) * _env_ad(ln2, 0.004, 0.2) * 0.33
            _place(bass, _stereo(x, 0.0), t0 + hb * beat)
        # ---- kick on beats 1 and 3 (soft), beat 1 of bar 0 sits exactly on sample 0
        for hb in (0, 2):
            ln3 = int(0.3 * SR); t3 = _t(ln3)
            fk = 48 + 90 * np.exp(-t3 / 0.028)
            x = np.sin(2 * np.pi * np.cumsum(fk) / SR) * np.exp(-t3 / 0.11) * 0.62
            x[: int(0.0015 * SR)] *= np.linspace(0.3, 1, int(0.0015 * SR))
            _place(drums, _stereo(x, 0.0), t0 + hb * beat)
        # ---- hats on every off-beat 8th (very soft) + sparse shaker 16ths
        for k in range(8):
            ln4 = int(0.045 * SR); x = _filt(r.randn(ln4), "highpass", 7500, 2) * np.exp(-_t(ln4) / 0.011)
            amp = 0.07 if k % 2 == 1 else 0.0
            if amp: _place(drums, _stereo(x * amp, 0.25), t0 + (k * 0.5 + 0.0) * beat)
        for k in range(16):
            if k % 4 in (1, 3):
                ln5 = int(0.03 * SR); x = _filt(r.randn(ln5), "bandpass" if False else "highpass", 6000, 2) * np.exp(-_t(ln5) / 0.007)
                _place(drums, _stereo(x * 0.028, -0.3), t0 + k * 0.25 * beat)
        # ---- pluck arpeggio (kalimba-ish, restrained; 2-bar motif, no lead melody)
        arp = [0, 1, 2, 1, 2, 1, 0, 2] if (b % 2 == 0) else [1, 2, 1, 0, 2, 0, 1, 2]
        for k, idx in enumerate(arp):
            if (k + b) % 3 == 2: continue                       # sparse: skip some notes
            m = tones[idx] + 12
            ln6 = int(0.5 * SR); t6 = _t(ln6); f = _mf(m)
            x = (np.sin(2 * np.pi * f * t6 + 1.2 * np.sin(2 * np.pi * 2 * f * t6) * np.exp(-t6 / 0.05)) * np.exp(-t6 / 0.16))
            x *= 0.075 * np.minimum(1, t6 / 0.003)
            _place(pluck, _stereo(x, -0.35 + 0.7 * ((k * 3) % 5) / 4), t0 + k * 0.5 * beat)
    pad = pad[:n]; pluck = pluck[:n]; drums = drums[:n]; bass = bass[:n]
    # ping-pong style delay on pluck (dotted 8th) then reverb on pad+pluck
    d = int(0.75 * beat); dl = np.zeros_like(pluck)
    for rep, g in ((1, 0.42), (2, 0.2), (3, 0.09)):
        sh = d * rep
        dl[sh:, 0] += pluck[:-sh, 1] * g; dl[sh:, 1] += pluck[:-sh, 0] * g
    wet = _reverb(pad * 1.0 + (pluck + dl) * 1.0, wet=0.28, seconds=1.8)
    out = wet + bass + drums
    out = _filt(out.T, "highpass", 32, 2).T
    out = np.tanh(out * 1.1) / 1.1                                           # gentle glue, avoids peaks
    # declick start (5 ms) and 800 ms fade-out; flat level otherwise
    nfi = int(0.005 * SR); out[:nfi] *= np.sin(np.linspace(0, np.pi / 2, nfi))[:, None] ** 2
    nfo = int(0.8 * SR); out[-nfo:] *= (np.cos(np.linspace(0, np.pi / 2, nfo)) ** 2)[:, None]
    return out


# ---------------------------------------------------------------------------------------------- riser
def riser(n, end_s, dur_s=2.6, seed=3):
    """low, smooth swelling riser; amplitude/pitch/filter all climb and the sound stops exactly at end_s."""
    r = _rng(seed)
    m = int(round(dur_s * SR)); t = _t(m); u = t / dur_s
    # noise: band-pass whose centre rises 140 -> 2200 Hz (log), amplitude ~ u^2.4 (smooth swell)
    fc = 140 * (2200 / 140) ** u
    noise = r.randn(m)
    y = np.zeros(m)
    # time-varying band-pass via short blocks (cross-faded) – smooth enough for a riser
    blk = 2048; hop = blk // 2; win = np.hanning(blk)
    for s in range(0, m - blk, hop):
        f0 = fc[s + blk // 2]
        sos = ss.butter(2, [max(60, f0 * 0.7), min(SR / 2 - 100, f0 * 1.4)], btype="band", fs=SR, output="sos")
        seg = ss.sosfilt(sos, noise[s:s + blk]) * win
        y[s:s + blk] += seg
    y = _norm(y)
    # tonal swell: sine sweeping 55 -> 190 Hz + a soft octave
    ph = 2 * np.pi * np.cumsum(55 * (190 / 55) ** u) / SR
    tone = np.sin(ph) + 0.35 * np.sin(2 * ph)
    amp = (u ** 2.4)
    sig = (0.62 * y + 0.55 * tone) * amp
    sig = _filt(sig, "lowpass", 4800, 2)
    # smooth 2 ms release so the audible end is clean but still lands on end_s
    k = int(0.002 * SR); sig[-k:] *= np.linspace(1, 0, k)
    sig[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    out = np.zeros((n, 2)); end = int(round(end_s * SR)); start = end - m
    wide = np.stack([sig, np.roll(sig, int(0.0007 * SR))], axis=1)          # tiny Haas widening
    _place(out, _norm(wide), start)
    return out


# ---------------------------------------------------------------------------------------------- one-shot SFX
def sfx_click(seed=0):
    """soft bubbly click: short sine with upward pitch glide + tiny noise tick."""
    r = _rng(100 + seed); n = int(0.085 * SR); t = _t(n)
    f = 420 + 900 * (1 - np.exp(-t / 0.012)) + 25 * seed
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.022)
    x += 0.25 * _filt(r.randn(n), "bandpass" if False else "highpass", 2500) * np.exp(-t / 0.004)
    x[: int(0.0008 * SR)] *= np.linspace(0, 1, int(0.0008 * SR))
    return _stereo(_norm(_filt(x, "lowpass", 5200)), 0.0)

def sfx_key(seed=0):
    """short soft key press: damped thump + band-limited tick."""
    r = _rng(200 + seed); n = int(0.05 * SR); t = _t(n)
    thump = np.sin(2 * np.pi * (150 + 12 * seed) * t) * np.exp(-t / 0.012)
    tick = ss.sosfilt(ss.butter(2, [1800, 4200], btype="band", fs=SR, output="sos"), r.randn(n)) * np.exp(-t / 0.004)
    x = 0.8 * thump + 0.7 * tick
    x[: int(0.0006 * SR)] *= np.linspace(0, 1, int(0.0006 * SR))
    return _stereo(_norm(x), 0.0)

def sfx_ticks(dur, seed=0, rate=22.0):
    """light tick stream (data streaming): irregular very short ticks."""
    r = _rng(300 + seed); n = int(dur * SR); out = np.zeros((n, 2)); t = 0.0
    while t < dur - 0.02:
        ln = int(0.012 * SR); x = _filt(r.randn(ln), "highpass", 3200) * np.exp(-_t(ln) / 0.0025)
        _place(out, _stereo(x * (0.5 + 0.5 * r.rand()), -0.2 + 0.4 * r.rand()), t * SR)
        t += (1 / rate) * (0.55 + 0.9 * r.rand())
    return _norm(out)

def sfx_pop(seed=0):
    """dull soft pop for a card/tile/device landing."""
    r = _rng(400 + seed); n = int(0.16 * SR); t = _t(n)
    f = 70 + 150 * np.exp(-t / 0.018) + 6 * seed
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.045)
    x += 0.2 * _filt(r.randn(n), "lowpass", 900) * np.exp(-t / 0.012)
    x[: int(0.001 * SR)] *= np.linspace(0, 1, int(0.001 * SR))
    return _stereo(_norm(_filt(x, "lowpass", 1800)), 0.0)

def sfx_chime(seed=0):
    """gentle two-note notification chime (E5 -> B5), soft attack, bell-ish partials."""
    n = int(0.95 * SR); out = np.zeros((n, 2))
    for k, (f, delay) in enumerate(((659.26, 0.0), (987.77, 0.13))):
        m = int(0.8 * SR); t = _t(m)
        x = (np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.08) + 0.12 * np.sin(2 * np.pi * 2 * f * t))
        x *= np.minimum(1, t / 0.006) * np.exp(-t / 0.22)
        _place(out, _stereo(x * (1.0 if k == 0 else 0.85), -0.1 + 0.2 * k), delay * SR)
    return _norm(_filt(out.T, "lowpass", 6500, 2).T)

WHOOSH_TOTAL = 1.05            # s  (whip: 0.45 out + 0.6 in)
WHOOSH_PEAK = 0.45             # s from the start of the whoosh to its loudest point = midpoint of the whip
def sfx_whoosh(variant=0):
    """low airy filtered-noise whoosh; loudest point exactly at WHOOSH_PEAK (the whip midpoint)."""
    p = [dict(f0=260, f1=1500, f2=420, q=0.9, seed=1), dict(f0=200, f1=1900, f2=360, q=0.8, seed=2),
         dict(f0=320, f1=1300, f2=500, q=1.1, seed=3), dict(f0=240, f1=1700, f2=300, q=0.7, seed=4)][variant % 4]
    r = _rng(500 + p["seed"]); n = int(WHOOSH_TOTAL * SR); t = _t(n); tp = WHOOSH_PEAK
    # amplitude: power-curve rise (ease-in like the outgoing power3.in) to the peak, then slower decay (power3.out)
    up = np.clip(t / tp, 0, 1) ** 2.6
    dn = np.clip(1 - (t - tp) / (WHOOSH_TOTAL - tp), 0, 1) ** 2.2
    amp = np.where(t <= tp, up, dn)
    # centre frequency sweeps f0 -> f1 (at peak) -> f2
    fc = np.where(t <= tp, p["f0"] * (p["f1"] / p["f0"]) ** (np.clip(t / tp, 0, 1) ** 1.4),
                  p["f1"] * (p["f2"] / p["f1"]) ** (np.clip((t - tp) / (WHOOSH_TOTAL - tp), 0, 1) ** 0.8))
    noise = r.randn(n); y = np.zeros(n); blk = 1024; hop = blk // 2; win = np.hanning(blk)
    for s in range(0, n - blk, hop):
        f0 = fc[s + blk // 2]; bw = p["q"]
        lo = max(50.0, f0 / (1 + bw)); hi = min(SR / 2 - 200, f0 * (1 + bw))
        sos = ss.butter(2, [lo, hi], btype="band", fs=SR, output="sos")
        y[s:s + blk] += ss.sosfilt(sos, noise[s:s + blk]) * win
    y = y * amp
    y = _filt(y, "lowpass", 5200, 2)
    # exact peak alignment: renormalise so the argmax is at tp
    L = np.stack([y, np.roll(y, int(0.0012 * SR))], axis=1)
    L[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))[:, None]
    L[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))[:, None]
    return _norm(L)
