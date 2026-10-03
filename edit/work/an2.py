import json, numpy as np, soundfile as sf
S="/tmp/claude-0/-home-user-viral-video-creator/132d3151-1488-52dc-983e-ad7d135ae2eb/scratchpad"
x,sr=sf.read(f"{S}/voice16k.wav")
w=int(0.010*sr); n=len(x)//w
db=np.array([20*np.log10(np.sqrt(np.mean(x[i*w:(i+1)*w]**2)+1e-12)) for i in range(n)])
np.save(f"{S}/db10.npy",db)
print("start db first 60 windows:",np.round(db[:60:5],1))
print("end db last 60 windows:",np.round(db[-60::5],1))
# low-energy stretches
for thr in (-35,-32,-30,-28):
    runs=[];st=None
    for i,v in enumerate(db):
        if v<thr and st is None: st=i
        if v>=thr and st is not None:
            runs.append((st,i)); st=None
    if st is not None: runs.append((st,n))
    print(f"thr {thr}: runs>=30ms:",[(a/100,b/100,(b-a)*10) for a,b in runs if (b-a)>=3])
