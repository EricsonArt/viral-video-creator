import json, numpy as np, soundfile as sf
S="/tmp/claude-0/-home-user-viral-video-creator/132d3151-1488-52dc-983e-ad7d135ae2eb/scratchpad"
x,sr=sf.read(f"{S}/voice16k.wav"); print(sr,len(x)/sr)
w=int(0.010*sr)
n=len(x)//w
rms=np.array([np.sqrt(np.mean(x[i*w:(i+1)*w]**2)+1e-12) for i in range(n)])
db=20*np.log10(rms)
print("global noise floor guess (5th pct):",np.percentile(db,5),"median",np.median(db),"95th",np.percentile(db,95))
tr=json.load(open(f"{S}/tr_large.json"))
words=[w_ for s in tr for w_ in s["words"]]
print(len(words),"words")
prev_e=0
for i,wd in enumerate(words):
    gap=wd["s"]-prev_e
    # min db in the gap
    a=int(prev_e*100); b=int(wd["s"]*100)
    mn=db[a:b].max() if b>a else None
    print(f"{i:3d} {wd['s']:6.2f}-{wd['e']:6.2f} gap={gap*1000:5.0f}ms maxdb_in_gap={mn if mn is None else round(mn,1)} {wd['w']}")
    prev_e=wd["e"]
