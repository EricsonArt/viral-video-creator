import numpy as np, soundfile as sf, json
x, sr = sf.read("work/src48k.wav")
m = x.mean(axis=1) if x.ndim>1 else x
win = int(0.010*sr)
n = len(m)//win
rms = np.sqrt((m[:n*win].reshape(n,win)**2).mean(axis=1)+1e-12)
db = 20*np.log10(rms+1e-12)
print("duration", len(m)/sr, "frames10ms", n)
print("percentiles dB: p5 %.1f p25 %.1f p50 %.1f p75 %.1f p95 %.1f max %.1f" % tuple(np.percentile(db,[5,25,50,75,95,100])))
# gaps below threshold
for thr in (-35,-40,-45):
    low = db < thr
    runs=[]; i=0
    while i<n:
        if low[i]:
            j=i
            while j<n and low[j]: j+=1
            if (j-i)*10>=100: runs.append((i*0.01,j*0.01,(j-i)*10))
            i=j
        else: i+=1
    print(f"\n< {thr} dB runs >=100ms:")
    for a,b,d in runs: print(f"  {a:6.2f}-{b:6.2f}  {d} ms")
np.save("work/rms_db.npy", db)
