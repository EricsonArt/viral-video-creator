import numpy as np, soundfile as sf, subprocess, json, os
from scipy.signal import butter, sosfilt
plan = json.load(open('plan.json'))
SR = 48000
PAD = plan['pad']; END = plan['end']
x, sr = sf.read('audio/src_48k.wav'); m = x.mean(axis=1)
# 1) tone: HPF 70 Hz (rumble), gentle -1.5 dB @ 280 Hz (mud), +1.5 dB @ 3.2 kHz (presence) via ffmpeg
sf.write('audio/voice_raw.wav', m, SR, subtype='FLOAT')
subprocess.run(['ffmpeg','-v','error','-y','-i','audio/voice_raw.wav','-af',
    'highpass=f=70:poles=2,equalizer=f=280:t=q:w=1.0:g=-1.5,equalizer=f=3200:t=q:w=0.9:g=1.5',
    '-c:a','pcm_f32le','audio/voice_eq.wav'], check=True)
v, _ = sf.read('audio/voice_eq.wav')

# 2) the source starts mid-onset (sample 0 is already -9 dB) -> 6 ms raised-cosine declick at speech start
def fade_in(sig, ms):
    n = int(SR*ms/1000); sig[:n] *= 0.5*(1-np.cos(np.linspace(0, np.pi, n))); return sig
v = fade_in(v, 6.0)

# 3) lead-in: PAD seconds of room tone (shaped noise at the residual floor level of the source's quietest 200 ms)
pad_n = int(round(PAD*SR))
w = int(0.2*SR); best = None
for i in range(0, len(v)-w, int(0.02*SR)):
    r = np.sqrt((v[i:i+w]**2).mean())
    if best is None or r < best[0]: best = (r, i)
floor_rms = best[0]*0.5            # room tone sits a bit under the quietest speech tail
rng = np.random.default_rng(7)
nz = rng.standard_normal(pad_n); sos = butter(2, [120, 2500], btype='band', fs=SR, output='sos'); nz = sosfilt(sos, nz)
nz *= floor_rms/ (np.sqrt((nz**2).mean())+1e-12)
# fade the room tone out into the speech start so there is no step
nz *= np.linspace(1, 0.35, pad_n)
sig = np.concatenate([nz, v])

# 4) hard length = END exactly; natural decay of the last syllable over ~90 ms (source was cut at -23 dB)
n_end = int(round(END*SR))
sig = sig[:n_end] if len(sig) >= n_end else np.pad(sig, (0, n_end-len(sig)))
tail = int(0.090*SR)
sig[-tail:] *= 0.5*(1+np.cos(np.linspace(0, np.pi, tail)))
sf.write('audio/voice_pre.wav', sig, SR, subtype='FLOAT')

# 5) loudness -> -14 LUFS integrated measured on the STEREO (dual-mono) deliverable, then true-peak limiter at -1.5 dBTP
def st(sig_mono, fn):
    sf.write(fn, np.stack([sig_mono, sig_mono], axis=1), SR, subtype='FLOAT')
def lufs(fn):
    r = subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',fn,'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
    i = float(r.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0])
    tp = float(r.split('True peak:')[1].split('Peak:')[1].split('dBFS')[0])
    return i, tp
def limit(sig_mono, limit_lin=0.80):
    st(sig_mono, 'audio/_t_in.wav')
    subprocess.run(['ffmpeg','-v','error','-y','-i','audio/_t_in.wav','-af',f'alimiter=limit={limit_lin}:attack=2:release=80:asc=1:level=disabled','-c:a','pcm_f32le','audio/_t_out.wav'], check=True)
    o,_ = sf.read('audio/_t_out.wav'); return o[:,0]
st(sig, 'audio/voice_pre_st.wav')
i0, tp0 = lufs('audio/voice_pre_st.wav'); print('pre  LUFS', i0, 'TP', tp0)
cur = sig * 10**((-14.0 - i0)/20)
for k in range(4):
    cur = limit(cur, 0.80)                      # 0.80 = -1.9 dBFS ceiling before true-peak overshoot
    st(cur, 'audio/_t_m.wav'); i1, tp1 = lufs('audio/_t_m.wav'); print(f'iter{k}: LUFS {i1} TP {tp1}')
    if abs(i1 + 14.0) < 0.05 and tp1 <= -1.0: break
    cur = cur * 10**((-14.0 - i1)/20)
final = cur
os.makedirs('../edit/stems', exist_ok=True)
sf.write('../edit/stems/voice.wav', np.stack([final, final], axis=1), SR, subtype='PCM_24')
st(final, 'audio/_t_m.wav'); i1, tp1 = lufs('audio/_t_m.wav')
print('voice.wav', len(final)/SR, 's  LUFS', i1, 'TP', tp1)
json.dump(dict(lufs=i1, tp=tp1), open('audio/voice_meas.json','w'))
