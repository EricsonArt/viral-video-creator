import json, numpy as np, soundfile as sf, sys
sys.path.insert(0, "tools"); import captions as cap
SR=48000
plan=json.load(open("work/plan.json")); N=plan["END_F"]*SR//60
print("END_F",plan["END_F"],"=",plan["END_F"]/60,"s ; expected samples",N)
st={k:sf.read(f"edit/stems/{k}.wav")[0] for k in ("voice","sfx","riser","music")}
mst,_=sf.read("edit/master_mix.wav")
for k,v in list(st.items())+[("master",mst)]: print(f"{k:7s} len {len(v)} {'OK' if len(v)==N else 'MISMATCH'}  ({len(v)/SR:.4f}s) ch={v.shape[1]}")
# --- voice gaps (RMS 10 ms windows < -35 dBFS) longer than 100 ms, excluding the lead-in
v=st["voice"].mean(axis=1); w=480; n=len(v)//w
rms=20*np.log10(np.sqrt((v[:n*w].reshape(n,w)**2).mean(axis=1))+1e-12)
low=rms<-35; runs=[];i=0
while i<n:
    if low[i]:
        j=i
        while j<n and low[j]: j+=1
        runs.append((i*0.01,(j-i)*10)); i=j
    else: i+=1
print("voice quiet runs (<-35 dB):",[(round(a,2),d) for a,d in runs if a>0.05], " longest (excl. lead-in/tail):", max([d for a,d in runs if 0.05<a<59.6] or [0]),"ms")
print("first 4 windows (lead-in 33 ms then speech):", np.round(rms[:5],1))
print("last 12 windows:", np.round(rms[-12:],1))
# --- riser end vs cut
r=st["riser"].max(axis=1); nz=np.nonzero(np.abs(r)>1e-6)[0]; cut=plan["runs"][1]["out_f0"]/60
print(f"riser audible {nz[0]/SR:.4f} -> {nz[-1]/SR:.4f}s ; hook->first-point cut at {cut:.4f}s ; riser dur {(nz[-1]-nz[0])/SR:.2f}s")
# --- whoosh peak vs whip midpoint
log=json.load(open("work/sfx_log.json")); wh=[l for l in log if l["type"].startswith("whoosh")]
s=np.abs(st["sfx"]).max(axis=1)
for l in wh:
    a=int((l["t"]-0.6)*SR); b=int((l["t"]+0.6)*SR); seg=np.sqrt(np.convolve(s[a:b]**2,np.ones(1440)/1440,mode="same"))
    print(f"whoosh at declared midpoint {l['t']:.3f}s -> measured envelope peak {(a+np.argmax(seg))/SR:.3f}s")
# --- captions
words=json.load(open("work/words.json")); ch=cap.make_chunks(words,plan["END_S"])
hl=[k for k,c in enumerate(ch) if any(w["hl"] for w in c["words"])]
print("caption chunks",len(ch),"highlighted",len(hl),"max words/chunk",max(len(c["words"]) for c in ch),"consecutive highlights:",sum(1 for a,b in zip(hl,hl[1:]) if b==a+1),"first caption starts at",ch[0]["t0"],"s")
gaps=[hl[0]]+[b-a-1 for a,b in zip(hl,hl[1:])]; print("normal chunks between highlights:",gaps)
