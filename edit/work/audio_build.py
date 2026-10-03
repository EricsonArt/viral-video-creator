import json, subprocess, re, numpy as np, soundfile as sf, os, sys
from scipy import signal
from audio_synth import *
from music_synth import render_music
S="/tmp/claude-0/-home-user-viral-video-creator/132d3151-1488-52dc-983e-ad7d135ae2eb/scratchpad"
OUT="/home/user/viral-video-creator/edit/stems"; os.makedirs(OUT,exist_ok=True)
plan=json.load(open("plan.json")); T0=plan["T0"]; END=plan["END"]; N=int(round(END*SR)); assert N==1907200,N
W=plan["words"]; RUN={r["id"]:r for r in plan["runs"]}
ws=lambda i: W[i]["s"]-T0
we=lambda i: W[i]["e"]-T0
def measure(path):
    r=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",path,"-af","ebur128=peak=true","-f","null","-"],capture_output=True,text=True).stderr
    tail=r[r.rfind("Summary:"):]
    I=float(re.search(r"I:\s+(-?[\d.]+|-inf)\s+LUFS",tail).group(1)) if re.search(r"I:\s+(-?[\d.]+)\s+LUFS",tail) else float("-inf")
    tp=re.search(r"Peak:\s+(-?[\d.]+|-inf)\s+dBFS",tail)
    return I,(float(tp.group(1)) if tp else float("-inf"))
def write(path,x): sf.write(path,x.astype(np.float32),SR,subtype="PCM_24")
# ------------------------------------------------------------------ VOICE
if not os.path.exists("voice_pre.wav"):
    subprocess.run(["ffmpeg","-y","-v","error","-i",f"{S}/cam48.wav","-af",
      "pan=mono|c0=0.5*c0+0.5*c1,highpass=f=75,equalizer=f=300:t=q:w=1:g=-1.2,equalizer=f=3200:t=q:w=1.1:g=1.6,highshelf=f=9500:g=0.8",
      "-ar","48000","voice_pre.wav"],check=True)
v,_=sf.read("voice_pre.wav"); s0=int(round(T0*SR)); v=v[s0:s0+N]
assert len(v)==N,len(v)
f=int(0.005*SR); v[:f]*=np.linspace(0,1,f)          # 5 ms declick at the head
f=int(0.060*SR); v[-f:]*=np.linspace(1,0,f)**1.5    # natural tail decay into the end
voice=np.stack([v,v],axis=1)
tmp=np.stack([v,v],axis=1); write("tmp_v.wav",tmp); I,_=measure("tmp_v.wav")
g=10**((-14.0-I)/20); voice*=g
VPEAK=np.max(np.abs(voice)); print(f"voice: pre {I:.2f} LUFS -> gain {20*np.log10(g):+.2f} dB, sample peak {20*np.log10(VPEAK):.2f} dBFS")
db=lambda x: 10**(x/20)
# ------------------------------------------------------------------ SFX events
rng=np.random.default_rng(20261003)
ev=[]   # (time_out, kind, level_db_rel_voice_peak, extra)
def typed_times(items):
    """items: (t0,t1,text) -> reveal time of every non-space char, sequential like typedWords()"""
    times=[]; prev_end=-1e9
    for (t0,t1,text) in items:
        n=len(text)
        for j in range(1,n+1):
            tj=max(t0+j/n*(t1-t0),prev_end)
            times.append(tj)
        prev_end=max(t1,prev_end)
    return times
# R1  (SPLIT hook)
r=RUN["R1"]["t0"]
ev.append((r+1.25,"pop",-10,{}))
it1=[]
for k,i in enumerate([7,8,9,10,11,12,13,14]):
    nxt=ws([7,8,9,10,11,12,13,14][k+1]) if k<7 else we(i); it1.append((ws(i),min(nxt,ws(i)+0.5),W[i]["w"]))
for k,tm in enumerate(typed_times(it1)):
    if k%2==0: ev.append((tm,"tick",-16,{}))
ev.append((r+3.70,"click",-10,{}))
for i in range(4): ev.append((r+3.70+0.25+i*0.15+0.06,"tick",-16,{}))
ev.append((r+4.12,"pop",-10,{"deep":0.8}))
# R3  (FULL VISUAL: YouTube -> transcript site)
r=RUN["R3"]["t0"]
ev.append((r+0.90,"pop",-10,{}))
ev.append((r+1.95,"click",-10,{})); ev.append((r+2.03,"chime",-10,{}))
ev.append((r+2.40,"click",-10,{}))
WHIP_MID=r+2.50+0.45
ev.append((WHIP_MID,"whoosh",-9,{"variant":1}))
ev.append((r+4.30,"click",-10,{}))
# R4  (SPLIT transcript)
r=RUN["R4"]["t0"]
for tm in np.arange(0.34,1.86,0.16): ev.append((r+tm,"tick",-16,{}))
ev.append((r+2.86,"click",-10,{}))
# R5  (FULL VISUAL: ChatGPT paste + prompt)
r=RUN["R5"]["t0"]
ev.append((r+0.45,"pop",-10,{"deep":1.1}))
it5=[(ws(61),we(61),"Daj"),(ws(61)+0.12,we(61),"mi"),(ws(63),we(63),"5"),(ws(64),we(64),"pomysłów"),(ws(65),we(65),"na"),(ws(66),we(66),"viralowe"),(ws(67),we(67),"filmiki"),(ws(68),we(68),"na"),(ws(69),ws(69)+0.34,"podstawie"),(ws(70),we(70),"tego"),(ws(71),we(71)-0.05,"filmu")]
for k,tm in enumerate(typed_times(it5)):
    if k%2==0: ev.append((tm,"tick",-16,{}))
ev.append((r+3.86,"click",-10,{}))
# R7  (SPLIT: pick idea -> script)
r=RUN["R7"]["t0"]
ev.append((r+1.00,"click",-10,{}))
it7=[(ws(95),ws(95)+0.28,"Napisz"),(ws(101)-0.05,we(101),"kompletny"),(ws(102),we(102),"scenariusz"),(ws(103),we(103),"na"),(ws(104),we(104)-0.04,"filmik")]
for k,tm in enumerate(typed_times(it7)):
    if k%2==0: ev.append((tm,"tick",-16,{}))
ev.append((r+4.30,"click",-10,{}))
ev.append((r+4.52,"pop",-10,{"deep":1.0})); ev.append((r+4.60,"chime",-10,{}))
# R9  (outro CTA card)
r=RUN["R9"]["t0"]
ev.append((r+1.15,"pop",-10,{"deep":1.1}))
for j in range(1,15): ev.append((r+1.62+j/14*0.50,"key",-16,{}))
ev.append((r+2.62,"click",-10,{}))
ev.sort(key=lambda e:e[0])
# ---- render events
sfx=np.zeros((N,2))
def place(wave,t,peak_lin,p=0.0):
    st=wave.ndim==2
    w=wave if st else pan(wave,p)
    w=w/ (np.max(np.abs(w))+1e-12)*peak_lin
    i0=int(round(t*SR)); m=min(len(w),N-i0)
    if m>0: sfx[i0:i0+m]+=w[:m]
LOG=[]
for (t,kind,lvl,x) in ev:
    pk=VPEAK*db(lvl)
    pp=rng.uniform(-0.15,0.15)
    if kind=="click": place(bubble_click(rng),t,pk,pp)
    elif kind=="tick": place(tick(rng),t,pk,pp)
    elif kind=="key": place(key_press(rng),t,pk,pp)
    elif kind=="pop": place(pop_dull(rng,x.get("deep",1.0)),t,pk,0)
    elif kind=="chime": place(chime(rng),t,pk,0)
    elif kind=="whoosh":
        w=whoosh(rng,x["variant"])
        # find the true loudest instant (10 ms RMS) and align it exactly to the whip midpoint
        mono=np.sqrt((w**2).sum(axis=1)); k=int(0.010*SR); sm=np.sqrt(np.convolve(mono**2,np.ones(k)/k,mode="same"))
        imax=int(np.argmax(sm)); t_place=t-imax/SR
        place(w,t_place,pk); LOG.append(("whoosh peak offset in wave (s)",imax/SR,"placed at",t_place,"loudest lands at",t_place+imax/SR))
    LOG.append((round(t,4),kind,lvl))
json.dump([ [round(a,4),b,c] for a,b,c,_ in ev],open("sfx_events.json","w"))
write(f"{OUT}/sfx.wav",sfx)
# ------------------------------------------------------------------ RISER (ends exactly at the R3 cut)
rs=np.zeros((N,2)); T_END=RUN["R3"]["t0"]; rr=riser(rng,3.0); rr=rr/np.max(np.abs(rr))*VPEAK*db(-14)
i0=int(round((T_END-3.0)*SR)); rs[i0:i0+len(rr)]=rr[:N-i0]; assert i0+len(rr)==int(round(T_END*SR))
write(f"{OUT}/riser.wav",rs)
# ------------------------------------------------------------------ MUSIC
mu=render_music(N,np.random.default_rng(7))
f=int(0.005*SR); mu[:f]*=np.linspace(0,1,f)[:,None]               # 5 ms declick
fo=int(0.8*SR); mu[-fo:]*=np.linspace(1,0,fo)[:,None]**1.5          # 800 ms fade-out to END
write("tmp_m.wav",mu); I,_=measure("tmp_m.wav"); gm=10**((-24.0-I)/20); mu*=gm
print(f"music: pre {I:.2f} LUFS -> gain {20*np.log10(gm):+.2f} dB")
write(f"{OUT}/music.wav",mu)
write(f"{OUT}/voice.wav",voice)
# ------------------------------------------------------------------ MASTER
mix=voice+sfx+rs+mu
write("tmp_mix.wav",mix); I,tp=measure("tmp_mix.wav"); print(f"raw mix: {I:.2f} LUFS, TP {tp:.2f}")
trim=-14.0-I+0.4; print(f"master trim {trim:+.2f} dB (includes +0.4 dB to compensate limiter loss)"); mix*=db(trim)
np.save("mix_pre_limit.npy",mix)
write("tmp_mix2.wav",mix)
lim="alimiter=limit=0.80:attack=5:release=80:level=disabled"
subprocess.run(["ffmpeg","-y","-v","error","-i","tmp_mix2.wav","-af",lim,"-c:a","pcm_s24le","master.wav"],check=True)
for name,p in (("voice",f"{OUT}/voice.wav"),("sfx",f"{OUT}/sfx.wav"),("riser",f"{OUT}/riser.wav"),("music",f"{OUT}/music.wav"),("master","master.wav")):
    I,tp=measure(p); print(f"{name:7s} integrated {I:7.2f} LUFS   true peak {tp:6.2f} dBTP")
json.dump(LOG,open("sfx_log.json","w"),default=float)
