import json, numpy as np, soundfile as sf
x, sr = sf.read('audio/src_48k_stereo.wav'); m = x.mean(axis=1)
print('sr',sr,'dur',len(m)/sr)
win = int(0.010*sr)
n = len(m)//win
rms = np.sqrt((m[:n*win].reshape(n,win)**2).mean(axis=1)+1e-12)
db = 20*np.log10(rms+1e-9)
np.save('audio/rms10ms_db.npy', db)
print('noise floor p10/p25/p50 dB:', np.percentile(db,[10,25,50]).round(1), ' max', db.max().round(1))
T = json.load(open('transcript_large-v3.json'))
words=[w for s in T['segments'] for w in s['words']]
print(len(words),'words')
for i,w in enumerate(words):
    print(f"{i:3d} {w['s']:6.2f}-{w['e']:6.2f} p={w['p']:.2f} {w['w']}")
