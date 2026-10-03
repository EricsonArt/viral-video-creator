import numpy as np
from scipy import signal
from audio_synth import SR,t_,exp_env,sos_filt,bandpass
BPM=110; BEAT=60/BPM
def midi(m): return 440*2**((m-69)/12)
def saw_pad(f,dur,rng,detune=0.004):
    n=int(dur*SR); t=t_(n); out=np.zeros(n)
    for d in (-detune,0,detune):
        ph=2*np.pi*np.cumsum(np.full(n,f*(1+d)))/SR+rng.uniform(0,6.28)
        out+=signal.sawtooth(ph)*0.33
    return out
def adsr(n,a,d,s,r_samp,sus_level):
    e=np.ones(n); na=int(a*SR)
    e[:na]=np.linspace(0,1,max(na,1))
    return e
def pluck(f,dur,rng):
    n=int(dur*SR); t=t_(n)
    s=np.sin(2*np.pi*f*t)+0.35*np.sin(2*np.pi*2*f*t)*np.exp(-t/0.07)+0.12*signal.sawtooth(2*np.pi*f*t)
    return s*exp_env(n,0.16,0.003)
def kick(rng):
    n=int(0.5*SR); t=t_(n)
    f=46+70*np.exp(-t/0.035)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*exp_env(n,0.16,0.002)
def hat(rng):
    n=int(0.06*SR); t=t_(n)
    return sos_filt(rng.standard_normal(n),"highpass",7500)*np.exp(-t/0.014)
CH=[ (45,[57,60,64,67,71]),   # Am9
     (41,[57,60,64,65,69]),   # Fmaj7(9)
     (48,[55,59,62,64,67]),   # Cmaj7(9)
     (43,[55,59,62,64,69]) ]  # G6/9
ARP=[0,2,4,2,1,3,4,3]
def render_music(N,rng):
    out=np.zeros((N,2))
    dur=N/SR; bars=int(np.ceil(dur/(4*BEAT)))+1
    def add(x,start,gain=1.0,p=0.0):
        i0=int(round(start*SR)); 
        if i0>=N: return
        m=min(len(x),N-i0)
        a=(p+1)*np.pi/4
        out[i0:i0+m,0]+=x[:m]*gain*np.cos(a); out[i0:i0+m,1]+=x[:m]*gain*np.sin(a)
    for b in range(bars):
        bass,pad=CH[b%4]; t0=b*4*BEAT
        # pad: soft chord, slow attack baked (8 ms start so beat 1 is on time), lowpassed warm
        L=np.zeros(int((4*BEAT+0.4)*SR))
        for k,m in enumerate(pad):
            L[:]+=saw_pad(midi(m),4*BEAT+0.4,rng)[:len(L)]*(0.5 if k>=3 else 0.7)
        tt=t_(len(L)); env=np.minimum(1,tt/0.012)*np.minimum(1,(4*BEAT+0.4-tt)/0.35)
        L=sos_filt(L*env,"lowpass",900,2)
        add(L,t0,0.50,-0.1)
        # bass: sine, beat 1 (1.4 beats) + beat 3 (1.0 beat)
        for off,ln,amp in ((0,1.4*BEAT,1.0),(2*BEAT,1.0*BEAT,0.8)):
            n=int(ln*SR); tt=t_(n); s=np.sin(2*np.pi*midi(bass)*tt)+0.25*np.sin(2*np.pi*2*midi(bass)*tt)
            s*=np.minimum(1,tt/0.01)*np.minimum(1,(ln-tt)/0.08)
            add(s,t0+off,0.55*amp,0.0)
        # arp plucks (8ths), quiet, filtered
        for k,idx in enumerate(ARP):
            note=pad[idx]+(12 if k%4==3 else 0)
            x=sos_filt(pluck(midi(note),0.5,rng),"lowpass",1800,2)
            add(x,t0+k*BEAT/2,0.20,-0.5 if k%2==0 else 0.5)
        # kick on 1 and 3, hats on off-8ths
        add(kick(rng),t0,0.55,0.0); add(kick(rng),t0+2*BEAT,0.42,0.0)
        for k in range(4):
            add(hat(rng),t0+k*BEAT+BEAT/2,0.07,0.25*(1 if k%2 else -1))
    return out
