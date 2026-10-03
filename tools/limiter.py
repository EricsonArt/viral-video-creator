"""True-peak-aware look-ahead limiter (offline): 4x oversampled peak detection, gain curve = running-min over the look-ahead
window, then smoothed with a Hann window of the same length, so gain <= required gain at every sample (no overshoot) and the
gain reduction is gradual (transparent for isolated plosive peaks)."""
import numpy as np
from scipy.signal import resample_poly
from scipy.ndimage import minimum_filter1d

def tp_limit(x, ceil_db=-1.2, look_ms=10.0, sr=48000):
    x = np.asarray(x, np.float64)
    if x.ndim == 1: x = x[:, None]
    ceil = 10 ** (ceil_db / 20)
    os4 = resample_poly(x, 4, 1, axis=0)
    pk = np.abs(os4).max(axis=1)
    g_req = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    n = len(x)
    g = g_req[: 4 * n].reshape(n, 4).min(axis=1)
    L = int(look_ms * 1e-3 * sr)
    gmin = minimum_filter1d(g, size=2 * L + 1, mode="nearest")
    w = np.hanning(2 * L + 1); w /= w.sum()
    gs = np.convolve(np.pad(gmin, (L, L), mode="edge"), w, mode="valid")
    gs = np.minimum(gs, 1.0)
    return x * gs[:, None], gs
