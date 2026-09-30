import soundfile as sf, numpy as np
x,sr=sf.read("work/audio/src48k.wav"); 
m=x.mean(1) if x.ndim>1 else x
print("sr",sr,"dur",len(m)/sr,"peak dBFS",20*np.log10(np.abs(m).max()))
w=int(0.01*sr)
n=len(m)//w
r=np.sqrt(np.mean(m[:n*w].reshape(n,w)**2,axis=1))+1e-12
db=20*np.log10(r)
np.save("work/rms10ms.npy",db)
print("noise floor p5",np.percentile(db,5),"p10",np.percentile(db,10),"median",np.median(db),"p95",np.percentile(db,95))
# silent stretches below -35 dB longer than 150ms
th=-35
sil=db<th
runs=[];s=None
for i,v in enumerate(sil):
    if v and s is None: s=i
    if not v and s is not None:
        runs.append((s,i)); s=None
if s is not None: runs.append((s,len(sil)))
for a,b in runs:
    if (b-a)>=12: print(f"silence {a/100:.2f}-{b/100:.2f} dur {(b-a)*10}ms")
