"""Builds all four stems (voice, sfx, riser, music) and the master mix.

Everything except the voice is synthesized here. Timings come from
work/edl.json (visual events) so SFX land on real on-screen events.
"""
import json, os
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy import signal

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EDL = json.load(open(os.path.join(ROOT, "work", "edl.json")))
END = EDL["end_s"]
N = int(round(END * SR))
OUT = os.path.join(ROOT, "edit", "stems")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(930)
meter = pyln.Meter(SR)


def db(x):
    return 20 * np.log10(max(x, 1e-12))


def true_peak(x):
    """4x oversampled peak (dBTP) of a mono or stereo buffer."""
    x = np.atleast_2d(x.T).T if x.ndim == 1 else x
    up = signal.resample_poly(x, 4, 1, axis=0)
    return db(np.abs(up).max())


def lufs(x):
    return meter.integrated_loudness(x if x.ndim == 2 else np.stack([x, x], 1))


def limiter(x, ceiling_db, lookahead_ms=4.0, release_ms=90.0):
    """Transparent lookahead peak limiter driven by 4x-oversampled peaks."""
    from scipy.ndimage import minimum_filter1d, uniform_filter1d
    ceiling = 10 ** (ceiling_db / 20)
    st = x if x.ndim == 2 else x[:, None]
    up = signal.resample_poly(st, 4, 1, axis=0)
    pk = np.abs(up).max(axis=1)[: 4 * len(st)].reshape(-1, 4).max(axis=1)
    need = np.minimum(1.0, ceiling / np.maximum(pk, 1e-9))
    la = max(1, int(lookahead_ms * SR / 1000))
    g = minimum_filter1d(need, size=2 * la + 1, mode="nearest")
    g = uniform_filter1d(g, size=2 * la + 1, mode="nearest")
    a = np.exp(-1.0 / (release_ms * SR / 1000))
    rel = signal.lfilter([1 - a], [1, -a], g, zi=[g[0] * a])[0]
    g = np.minimum(g, rel)
    y = st * g[:, None]
    return (y if x.ndim == 2 else y[:, 0]), g


# ---------------------------------------------------------------- VOICE
def build_voice():
    x, sr = sf.read(os.path.join(ROOT, "work", "audio", "src48k.wav"), always_2d=True)
    assert sr == SR
    m = x.mean(axis=1)[:N]
    if len(m) < N:
        m = np.pad(m, (0, N - len(m)))
    sos = signal.butter(2, 70, "highpass", fs=SR, output="sos")
    m = signal.sosfiltfilt(sos, m)
    # tail: the source stops inside "bio" -> let it decay instead of clicking off
    tail = int(EDL["voice_tail_fade_ms"] / 1000 * SR)
    m[-tail:] *= np.cos(np.linspace(0, np.pi / 2, tail)) ** 2
    m[: int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    v = np.stack([m, m], 1)
    for _ in range(3):
        v *= 10 ** ((-14.0 - lufs(v)) / 20)
        v, _g = limiter(v, -1.5)
    v *= 10 ** ((-14.0 - lufs(v)) / 20)
    v, _g = limiter(v, -1.5)
    return v


# ---------------------------------------------------------------- SYNTH HELPERS
def env_adsr(n, a, d, s, r, sr=SR):
    a, d, r = int(a * sr), int(d * sr), int(r * sr)
    sus = max(n - a - d - r, 0)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False) if a else [],
                        np.linspace(1, s, d, endpoint=False) if d else [],
                        np.full(sus, s), np.linspace(s, 0, r) if r else []])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def place(buf, snd, t, gain=1.0):
    i = int(round(t * SR))
    if snd.ndim == 1:
        snd = np.stack([snd, snd], 1)
    j = min(len(buf), i + len(snd))
    if j > i >= 0:
        buf[i:j] += snd[: j - i] * gain


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x, axis=0)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x, axis=0)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x, axis=0)


# ---------------------------------------------------------------- MUSIC
def build_music():
    beat = EDL["beat_s"]
    bar = beat * 4
    L = N
    mus = np.zeros((L, 2))
    t_all = np.arange(L) / SR
    # F major colour: Fmaj9 | Am7 | Dm9 | Bbmaj9  (one chord per bar)
    chords = [[53, 57, 60, 64, 67], [57, 60, 64, 67, 71], [50, 53, 57, 60, 64], [46, 50, 53, 57, 60]]
    roots = [41, 45, 38, 46]
    nbars = int(np.ceil(END / bar)) + 1

    # warm pad: detuned saws, low-passed, stereo spread; 25 ms attack per chord (no fade-in)
    for b in range(nbars):
        t0 = b * bar
        if t0 >= END:
            break
        n = int(min(bar + 0.35, END - t0 + 0.01) * SR)
        tt = np.arange(n) / SR
        ch = chords[b % 4]
        sL = np.zeros(n); sR = np.zeros(n)
        for k, note in enumerate(ch):
            f = midi(note + 12 if k == 0 and note < 48 else note)
            for det, pan in ((-0.07, 0.8), (0.0, 0.5), (0.07, 0.2)):
                ff = f * 2 ** (det / 12)
                ph = rng.uniform(0, 1)
                saw = 2 * ((ff * tt + ph) % 1.0) - 1
                sL += saw * (1 - pan); sR += saw * pan
        e = env_adsr(n, 0.025, 0.4, 0.8, 0.32)
        pad = np.stack([sL, sR], 1) * e[:, None]
        pad = lp(pad, 1500, 2)
        place(mus, pad * 0.020, t0)

    # soft pluck arpeggio (8ths) - chord tones, very low, not a melody
    patt = [0, 2, 1, 3, 2, 4, 1, 3]
    for b in range(nbars):
        for s in range(8):
            t0 = b * bar + s * beat / 2
            if t0 >= END or b * bar < EDL["riser_end_s"] - 4 * bar:
                continue
            note = chords[b % 4][patt[s]] + 12
            n = int(0.42 * SR)
            tt = np.arange(n) / SR
            f = midi(note)
            tone = np.sin(2 * np.pi * f * tt + 0.8 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 18))
            tone *= np.exp(-tt * 9.5) * (1 - np.exp(-tt * 900))
            vel = 0.75 + 0.25 * ((s % 2) == 0)
            pan = 0.35 + 0.3 * ((s * 3) % 5) / 4
            place(mus, np.stack([tone * (1 - pan), tone * pan], 1) * 0.030 * vel, t0)

    # sub bass: root on 1 and the "and" of 2, sine + gentle saturation (from bar 5)
    for b in range(nbars):
        intro = b * bar < EDL["riser_end_s"] - 1e-6
        for (off, ln) in (((0.0, 3.8),) if intro else ((0.0, 1.6), (1.5, 0.9), (3.0, 0.8))):
            t0 = b * bar + off * beat
            if t0 >= END:
                continue
            n = int(ln * beat * SR)
            tt = np.arange(n) / SR
            f = midi(roots[b % 4] - 12 + 12)
            s_ = np.tanh(1.6 * np.sin(2 * np.pi * f * tt)) / np.tanh(1.6)
            s_ *= env_adsr(n, 0.008, 0.12, 0.7, 0.07)
            place(mus, s_ * 0.11, t0)

    # kick on 1 and 3 (soft), from frame 0
    def kick():
        n = int(0.32 * SR); tt = np.arange(n) / SR
        f = 48 + 70 * np.exp(-tt * 28)
        ph = 2 * np.pi * np.cumsum(f) / SR
        k = np.sin(ph) * np.exp(-tt * 11) + 0.25 * np.exp(-tt * 180) * rng.standard_normal(n) * 0.2
        return lp(k, 2500)
    K = kick()
    nbeats = int(END / beat) + 1
    for i in range(nbeats):
        t0 = i * beat
        if i % 2 == 0 and t0 < END:
            place(mus, K * (0.20 if t0 >= EDL["riser_end_s"] - 1e-6 else 0.15), t0)

    # snap/clap on 2 and 4 after the hook (filtered noise + tone)
    def snap():
        n = int(0.22 * SR); tt = np.arange(n) / SR
        nz = bp(rng.standard_normal(n), 1200, 5200) * np.exp(-tt * 26)
        tone = np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 40) * 0.4
        return nz + tone
    S = snap()
    for i in range(nbeats):
        t0 = i * beat
        if i % 4 in (1, 3) and EDL["riser_end_s"] - 1e-6 <= t0 < END:
            place(mus, np.stack([S * 0.55, S * 0.45], 1) * 0.085, t0)

    # hats: 8ths (offbeat accent), shaker ghost 16ths
    def hat(dec):
        n = int(0.09 * SR); tt = np.arange(n) / SR
        return hp(rng.standard_normal(n), 7000) * np.exp(-tt * dec)
    for i in range(nbeats * 4):
        t0 = i * beat / 4
        if t0 >= END:
            break
        if i % 2 == 0:
            g = 0.050 if (i % 4 == 2) else 0.028
            h = hat(60)
        else:
            g = 0.010
            h = hat(95)
        if t0 < EDL["riser_end_s"] - 1e-6:
            g *= 0.7
        pan = 0.62 if i % 4 == 2 else 0.4
        place(mus, np.stack([h * (1 - pan), h * pan], 1) * g * 2, t0)

    # master bus for the bed: gentle glue + declick in, 800 ms fade out
    mus = np.tanh(mus * 1.2) / 1.2
    dc = int(0.005 * SR)
    mus[:dc] *= np.linspace(0, 1, dc)[:, None]
    fo = int(0.8 * SR)
    mus[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    # one flat gain to hit -24 LUFS
    mus *= 10 ** ((-24.0 - lufs(mus)) / 20)
    return mus


# ---------------------------------------------------------------- SFX
def s_click(v=0):
    n = int(0.09 * SR); tt = np.arange(n) / SR
    f = (1500 + 150 * v) * np.exp(-tt * 34) + 520
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt * 55)
    bub = np.sin(2 * np.pi * (2600 + 120 * v) * tt) * np.exp(-tt * 120) * 0.35
    tr = lp(rng.standard_normal(n), 6000) * np.exp(-tt * 900) * 0.25
    return body + bub + tr


def s_pop(v=0):
    n = int(0.16 * SR); tt = np.arange(n) / SR
    f = (210 + 12 * v) * np.exp(-tt * 22) + 80
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt * 30) * (1 - np.exp(-tt * 1500))
    thump = lp(rng.standard_normal(n), 700) * np.exp(-tt * 60) * 0.6
    return lp(body + thump, 1800)


def s_chime():
    out = np.zeros(int(0.9 * SR))
    for k, (note, t0) in enumerate(((88, 0.0), (95, 0.10))):  # E6 -> B6
        n = int(0.75 * SR); tt = np.arange(n) / SR
        f = midi(note)
        bell = (np.sin(2 * np.pi * f * tt + 1.2 * np.sin(2 * np.pi * f * 2.0 * tt) * np.exp(-tt * 6))
                * np.exp(-tt * 5.5) * (1 - np.exp(-tt * 600)))
        i = int(t0 * SR)
        out[i:i + n] += bell * (0.9 if k else 1.0)
    return lp(out, 7000)


def s_key(v=0):
    n = int(0.03 * SR); tt = np.arange(n) / SR
    tick = bp(rng.standard_normal(n), 1800, 6500) * np.exp(-tt * (420 + 30 * v))
    body = np.sin(2 * np.pi * (380 + 25 * v) * tt) * np.exp(-tt * 260) * 0.5
    return tick + body


def s_whoosh(variant, pre=0.45, post=0.6):
    """Peak exactly at `pre` seconds into the sound (the whip midpoint)."""
    n = int((pre + post) * SR); tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    # amplitude: accelerating in (power3.in feel), decaying out
    a = np.where(tt < pre, np.clip(tt / pre, 0, 1) ** 2.6, np.exp(-(np.clip(tt - pre, 0, None) / (post * 0.38)) ** 1.4))
    lo, hi, q = [(180, 1400, 1.0), (240, 2200, 0.9), (140, 1100, 1.2), (300, 2600, 0.8)][variant]
    fc = np.where(tt < pre, lo + (hi - lo) * np.clip(tt / pre, 0, 1) ** 1.5, hi - (hi - lo) * 0.65 * (np.clip(tt - pre, 0, None) / post) ** 0.7)
    # time-varying band-pass via short blocks
    y = np.zeros(n)
    blk = 512
    zi = None
    for i in range(0, n, blk):
        c = fc[min(i + blk // 2, n - 1)]
        b, a_ = signal.iirpeak(c, q * 1.4, fs=SR)
        seg = x[i:i + blk]
        if zi is None:
            zi = signal.lfilter_zi(b, a_) * 0
        yy, zi = signal.lfilter(b, a_, seg, zi=zi)
        y[i:i + blk] = yy
    y = lp(y, 5000) * a
    air = hp(x, 3000) * a * 0.08
    st = np.stack([y + air, np.roll(y, int(0.0004 * SR)) + air], 1)
    return st


def build_sfx_and_riser(voice_peak_db):
    sfx = np.zeros((N, 2))
    log = []
    ref = voice_peak_db
    lvl = {"click": ref - 10, "pop": ref - 10, "chime": ref - 10, "whoosh": ref - 9, "key": ref - 16}
    last_whoosh = -1
    for k, ev in enumerate(EDL["sfx"]):
        typ, t = ev["type"], ev["t"]
        if typ == "click":
            snd = s_click(k % 3)
        elif typ == "pop":
            snd = s_pop(k % 3)
        elif typ == "chime":
            snd = s_chime()
        elif typ == "key":
            snd = s_key(k % 4)
        elif typ == "whoosh":
            var = ev.get("variant", 0)
            assert var != last_whoosh, "whoosh variant repeated"
            last_whoosh = var
            snd = s_whoosh(var)
            e = np.sqrt(np.convolve(snd.mean(axis=1) ** 2, np.ones(240) / 240, mode="same"))
            t = t - e.argmax() / SR  # loudest point lands exactly on the whip midpoint
        snd = np.atleast_2d(snd.T).T if snd.ndim == 1 else snd
        snd = snd / np.abs(snd).max() * 10 ** (lvl[typ] / 20)
        place(sfx, snd, t)
        log.append({**ev, "peak_dbfs": round(lvl[typ], 2)})

    # intro riser: low smooth swell whose audible end lands exactly on riser_end_s
    riser = np.zeros((N, 2))
    dur = EDL["riser_dur_s"]
    n = int(dur * SR); tt = np.arange(n) / SR
    u = tt / dur
    f = midi(41) * 2 ** (u ** 1.7 * 7 / 12)          # F2 gliding up a fifth
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.18 * np.sin(3 * ph + 0.3))
    nz = rng.standard_normal(n)
    nzf = np.zeros(n)
    blk = 1024
    for i in range(0, n, blk):
        c = 250 + 2600 * (u[min(i + blk // 2, n - 1)] ** 2.2)
        nzf[i:i + blk] = lp(nz[max(0, i - 2048):i + blk], c)[-len(nz[i:i + blk]):]
    body = lp(tone, 900) * 0.9 + nzf * 0.55
    amp = u ** 2.4
    rel = int(0.012 * SR)
    amp[-rel:] *= np.linspace(1, 0, rel)          # audible end exactly at the cut
    r = body * amp
    r = np.stack([r, np.roll(r, int(0.0007 * SR))], 1)
    r = r / np.abs(r).max() * 10 ** ((ref - 14) / 20)
    place(riser, r, EDL["riser_end_s"] - dur)
    return sfx, riser, log


def write(name, x):
    sf.write(os.path.join(OUT, name), x.astype(np.float32), SR, subtype="PCM_24")


if __name__ == "__main__":
    voice = build_voice()
    vpk = db(np.abs(voice).max())
    print("voice lufs %.2f tp %.2f sample-peak %.2f" % (lufs(voice), true_peak(voice), vpk))
    music = build_music()
    print("music lufs %.2f tp %.2f" % (lufs(music), true_peak(music)))
    sfx, riser, log = build_sfx_and_riser(vpk)
    for nm, x in (("voice.wav", voice), ("sfx.wav", sfx), ("riser.wav", riser), ("music.wav", music)):
        assert len(x) == N
        write(nm, x)
    mix = voice + sfx + riser + music
    pre = lufs(mix)
    mix *= 10 ** ((-14.0 - pre) / 20)
    tp = true_peak(mix)
    if tp > -1.0:
        mix, g = limiter(mix, -1.1)
    mix *= 10 ** ((-14.0 - lufs(mix)) / 20)
    if true_peak(mix) > -1.0:
        mix, g = limiter(mix, -1.1)
    print("master pre-gain lufs %.2f -> lufs %.2f tp %.2f" % (pre, lufs(mix), true_peak(mix)))
    sf.write(os.path.join(ROOT, "work", "audio", "master.wav"), mix.astype(np.float32), SR, subtype="PCM_24")
    json.dump({"sfx": log, "voice_peak_dbfs": vpk, "master_gain_db": -14.0 - pre}, open(os.path.join(ROOT, "work", "audio", "audio_log.json"), "w"), indent=1)
