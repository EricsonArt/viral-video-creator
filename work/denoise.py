import numpy as np, soundfile as sf
from scipy.signal import stft, istft
from scipy.ndimage import uniform_filter1d, minimum_filter1d

def spectral_denoise(x, sr, max_att_db=10.0, n_fft=2048, hop=512, over=1.4):
    f, t, X = stft(x, sr, nperseg=n_fft, noverlap=n_fft-hop, window='hann', boundary='zeros')
    P = np.abs(X)**2
    # noise PSD per bin: low percentile over time (speech is nearly continuous so use 8th percentile)
    npsd = np.percentile(P, 8, axis=1)
    npsd = uniform_filter1d(npsd, 5)
    snr = P / (npsd[:, None] * over + 1e-14)
    G = np.clip(1.0 - 1.0/np.maximum(snr, 1e-6), 0, 1)       # Wiener-like
    G = np.sqrt(G)
    gmin = 10**(-max_att_db/20)
    G = np.maximum(G, gmin)
    # smooth over time (fast attack, slower release) and a bit over frequency to limit musical noise
    G = uniform_filter1d(G, 3, axis=1)
    G = uniform_filter1d(G, 5, axis=0)
    # release smoothing
    Gs = G.copy()
    rel = 0.6
    for i in range(1, Gs.shape[1]):
        Gs[:, i] = np.maximum(G[:, i], rel*Gs[:, i-1] + (1-rel)*G[:, i])
    _, y = istft(X*Gs, sr, nperseg=n_fft, noverlap=n_fft-hop, window='hann', boundary=True)
    return y[:len(x)]

if __name__ == '__main__':
    x, sr = sf.read('audio/test/mono.wav')
    for att in (8, 12):
        y = spectral_denoise(x, sr, att)
        sf.write(f'audio/test/sd{att}.wav', y, sr, subtype='FLOAT')
        w = int(0.01*sr); n = len(y)//w
        db = 20*np.log10(np.sqrt((y[:n*w].reshape(n, w)**2).mean(axis=1))+1e-9)
        print(att, 'pct 2/5/10/25:', np.percentile(db,[2,5,10,25]).round(1), 'median/75/90', np.percentile(db,[50,75,90]).round(1))
