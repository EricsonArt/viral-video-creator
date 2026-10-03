import json, numpy as np, soundfile as sf
S="/tmp/claude-0/-home-user-viral-video-creator/132d3151-1488-52dc-983e-ad7d135ae2eb/scratchpad"
FPS=60
T0=2/30            # leading trim (2 source frames); first word onset ~0.100 s -> ~33 ms lead-in
SRC_END=39.80
END=SRC_END-T0     # 39.7333
END_F=round(END*FPS)   # 2384
tr=json.load(open(f"{S}/tr_large.json"))
words=[w for s in tr for w in s["words"]]
fix={"wiralowy":"viralowy","wiralowe":"viralowe"}
toks=[]
for w in words:
    t=w["w"].strip()
    toks.append({"w":fix.get(t,t),"s":w["s"],"e":w["e"]})
# merge "youtubetranscript" + ".com"
i=[k for k,t in enumerate(toks) if t["w"]==".com"][0]
toks[i-1]["w"]="youtubetranscript.com"; toks[i-1]["e"]=toks[i]["e"]; del toks[i]
# --- snap word starts to nearest energy valley (continuous speech => whisper boundaries are smooth)
x,sr=sf.read(f"{S}/voice16k.wav")
hop=int(0.005*sr)
env=np.array([20*np.log10(np.sqrt(np.mean(x[i*hop:(i+1)*hop]**2)+1e-12)) for i in range(len(x)//hop)])
env_s=np.convolve(env,np.ones(3)/3,mode="same")
def snap(t,rad=0.05):
    a=int((t-rad)/0.005); b=int((t+rad)/0.005)
    a=max(a,0); b=min(b,len(env_s)-1)
    seg=env_s[a:b+1]; k=int(np.argmin(seg))
    # only snap if valley is clearly lower than the surroundings
    if seg.max()-seg.min()>=5: return (a+k)*0.005+0.0025
    return t
for k,t in enumerate(toks):
    if k>0:
        ns=snap(t["s"]); 
        toks[k]["s"]=ns; toks[k-1]["e"]=ns
for k,t in enumerate(toks): t["i"]=k
print(len(toks),"tokens")
# ---- caption chunks (hand-curated, 1-3 words) ; hl = token indices highlighted in Instrument Serif
C=lambda a,b=None,hl=None:(a,a if b is None else b,hl or [])
chunks=[C(0,1),C(2,4),C(5,6,[6]),
 C(7,8),C(9,10,[9]),C(11,12),C(13,14),
 C(15,16),C(17,17,[17]),C(18),
 C(19,20),C(21,22),C(23),C(24,25,[25]),C(26,28,[27,28]),
 C(29),C(30,31),C(32,33,[33]),C(34,35),C(36),
 C(37,38),C(39,40,[40]),
 C(41,43),C(44,44,[44]),
 C(45,46),C(47,48,[48]),C(49,50),C(51),
 C(52),C(53,54),
 C(55,56),C(57,59),C(60,61),C(62,64,[63]),C(65,66),C(67),C(68,69),C(70,71),
 C(72,73),C(74,75),C(76),C(77,78,[77,78]),C(79,80),
 C(81,82),C(83,84),C(85,86),C(87),
 C(88,89),C(90,92),C(93),C(94,95),C(96,97),C(98,100),C(101),C(102,102,[102]),C(103,104),
 C(105,107),C(108),C(109),C(110,111),
 C(112,114),C(115,116,[115,116]),C(117,118),C(119),
 C(120,121),C(122,123),C(124,124,[124]),
 C(125,126),C(127),C(128,129,[128,129]),C(130,131),C(132,133),C(134,135),C(136,137),C(138),
 C(139),C(140,141,[141]),
 C(142,144),C(145,146),C(147,147,[147]),C(148,149)]


HL={2:[6],4:[9],8:[17],11:[22],14:[27,28],17:[33],21:[40],23:[44],25:[48],29:[54],33:[63],35:[67],41:[77,78],44:[84],48:[92],51:[97],54:[102],57:[108],61:[115,116],63:[119],66:[124],69:[128,129],72:[135],76:[141],79:[147]}
chunks=[(a,b,HL.get(k,[])) for k,(a,b,_) in enumerate(chunks)]
# ---- verify highlight cadence
flags=[1 if c[2] else 0 for c in chunks]
gaps=[];last=None
for k,f in enumerate(flags):
    if f:
        if last is not None: gaps.append(k-last-1)
        last=k
print("chunks",len(chunks),"highlighted",sum(flags),"normal-gaps between highlights:",gaps)
assert all(not(flags[k] and flags[k+1]) for k in range(len(flags)-1)), "consecutive highlights"
# ---- chunk timing in OUTPUT time
out=[]
for k,(a,b,hl) in enumerate(chunks):
    s=toks[a]["s"]-T0; e=toks[b]["e"]-T0
    out.append({"k":k,"text":" ".join(toks[j]["w"] for j in range(a,b+1)),"words":list(range(a,b+1)),"hl":hl,"t0":s,"t1":e})
# continuous display: extend end to next start when gap < 0.25s, else linger 80ms
for k,c in enumerate(out):
    nxt=out[k+1]["t0"] if k+1<len(out) else END
    c["t1"]=nxt if nxt-c["t1"]<0.25 else c["t1"]+0.08
out[0]["t0"]=1/FPS   # captions start ~17 ms; frame 0 stays clean
out[-1]["t1"]=END
# ---- runs (output frame indices)
cuts=[0,296,474,749,941,1187,1442,1787,2206,END_F]
names=[("R1","split"),("R2","cam"),("R3","visual"),("R4","split"),("R5","visual"),("R6","cam"),("R7","split"),("R8","visual"),("R9","cam")]
runs=[]
for k,(rid,lay) in enumerate(names):
    f0,f1=cuts[k],cuts[k+1]
    runs.append({"id":rid,"layout":lay,"f0":f0,"f1":f1,"t0":f0/FPS,"t1":f1/FPS,"dur":(f1-f0)/FPS,"src0":f0/FPS+T0,"src1":f1/FPS+T0})
plan={"fps":FPS,"T0":T0,"END":END,"END_F":END_F,"runs":runs,"words":toks,"chunks":out}
json.dump(plan,open("plan.json","w"),ensure_ascii=False,indent=1)
for r in runs: print(r["id"],r["layout"],f"{r['t0']:.3f}-{r['t1']:.3f} ({r['dur']:.3f}s) frames {r['f0']}-{r['f1']}  src {r['src0']:.3f}-{r['src1']:.3f}")
print("END",END,END_F)
for c in out[:12]: print(f"{c['t0']:.3f}-{c['t1']:.3f} {c['text']} {c['hl']}")
