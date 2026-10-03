"""Synthesis primitives. Everything is generated in code (numpy/scipy). SR=48000, float64."""
import numpy as np
from scipy import signal
SR=48000
def t_(n): return np.arange(n)/SR
def exp_env(n,tau,attack=0.001):
    t=t_(n); e=np.exp(-t/tau); a=np.minimum(1,t/max(attack,1e-5)); return e*a
def sos_filt(x,kind,f,order=2,fs=SR):
    sos=signal.butter(order,f,btype=kind,fs=fs,output="sos"); return signal.sosfilt(sos,x)
def bandpass(x,lo,hi,order=2): return sos_filt(x,"bandpass",[lo,hi],order)
def norm_peak(x,peak=1.0): m=np.max(np.abs(x))+1e-12; return x/m*peak
def pan(mono,p=0.0):
    """equal-power pan p in [-1,1] -> stereo (n,2)"""
    a=(p+1)*np.pi/4; return np.stack([mono*np.cos(a),mono*np.sin(a)],axis=1)
def bubble_click(rng):
    n=int(0.12*SR); t=t_(n)
    f=520+(900+rng.uniform(-60,60))*(1-np.exp(-t/0.011))
    ph=2*np.pi*np.cumsum(f)/SR
    s=np.sin(ph)+0.22*np.sin(2*ph)
    s*=exp_env(n,0.024,0.0012)
    tick=bandpass(rng.standard_normal(n),2500,6500)*np.exp(-t/0.0025)*0.25
    return sos_filt(s+tick,"lowpass",7500)
def key_press(rng,soft=1.0):
    n=int(0.04*SR); t=t_(n)
    c=rng.uniform(1800,3200); noise=bandpass(rng.standard_normal(n),c*0.6,c*1.8)*np.exp(-t/0.0042)
    thump=np.sin(2*np.pi*rng.uniform(140,200)*t)*np.exp(-t/0.011)*0.55
    return (noise+thump)*soft
def tick(rng):
    n=int(0.03*SR); t=t_(n)
    f=rng.uniform(2300,3600)
    s=np.sin(2*np.pi*f*t)*np.exp(-t/0.0055)*0.8+bandpass(rng.standard_normal(n),3500,8000)*np.exp(-t/0.0018)*0.4
    return s
def pop_dull(rng,deep=1.0):
    n=int(0.3*SR); t=t_(n)
    f=(110*deep)*np.exp(-t/0.05)+48*deep
    ph=2*np.pi*np.cumsum(f)/SR
    s=np.sin(ph)*exp_env(n,0.07,0.002)
    tr=sos_filt(rng.standard_normal(n),"lowpass",900)*np.exp(-t/0.006)*0.35
    return sos_filt(s+tr,"lowpass",1800)
def reverb_ir(rng,length=0.4,decay=0.09):
    n=int(length*SR); t=t_(n); ir=rng.standard_normal(n)*np.exp(-t/decay); ir=sos_filt(ir,"lowpass",5000); ir[0]=0; return ir/np.sqrt(np.sum(ir**2))
def chime(rng):
    notes=[(659.26,0.0),(987.77,0.125)]
    n=int(1.2*SR); out=np.zeros(n)
    for f,st in notes:
        i0=int(st*SR); m=n-i0; t=t_(m)
        s=np.zeros(m)
        for k,(mul,amp) in enumerate([(1,1.0),(2.0,0.28),(3.01,0.10),(4.2,0.04)]):
            s+=amp*np.sin(2*np.pi*f*mul*t+rng.uniform(0,6.28))*np.exp(-t/(0.30/(1+0.7*k)))
        s*=np.minimum(1,t/0.004)
        out[i0:]+=s*(0.8 if f>800 else 1.0)
    ir=reverb_ir(rng,0.5,0.12)
    wet=signal.fftconvolve(out,ir)[:n]
    return out+0.22*wet
def whoosh(rng,variant=0,total=1.05,t_peak=0.45):
    """low airy filtered-noise whoosh; loudest sample exactly at t_peak. returns (n,2)"""
    P=[dict(fp=2200,sg=0.85,f0=260,f1=520),dict(fp=1600,sg=1.0,f0=220,f1=420),dict(fp=2800,sg=0.8,f0=300,f1=600),dict(fp=1900,sg=1.1,f0=240,f1=480)][variant%4]
    n=int(total*SR); t=t_(n)
    cf=np.where(t<t_peak, P["f0"]*(P["fp"]/P["f0"])**(np.clip(t/t_peak,0,1)**1.4), P["fp"]*(P["f1"]/P["fp"])**(np.clip((t-t_peak)/(total-t_peak),0,1)**0.8))
    bands=np.geomspace(120,7000,18)
    out=np.zeros((n,2))
    for ch in range(2):
        acc=np.zeros(n)
        for fb in bands:
            nz=bandpass(rng.standard_normal(n),fb/1.25,fb*1.25,2)
            g=np.exp(-(np.log(fb/cf))**2/(2*P["sg"]**2*0.45))
            acc+=nz*g
        out[:,ch]=acc
    # asymmetric bell envelope with exact maximum at t_peak
    env=np.where(t<t_peak,(t/t_peak)**2.2,(1-(t-t_peak)/(total-t_peak))**1.6)
    env=np.clip(env,0,1); out*=env[:,None]
    out[:,0]=sos_filt(out[:,0],"lowpass",5500); out[:,1]=sos_filt(out[:,1],"lowpass",5500)
    # make the global amplitude maximum land on t_peak: rescale so the smoothed envelope peak is at t_peak
    return out
def riser(rng,dur=3.0):
    n=int(dur*SR); t=t_(n); u=t/dur
    f1=55*np.exp(np.log(2.2)*u**1.5); f2=110*np.exp(np.log(2.2)*u**1.5)
    s=0.8*np.sin(2*np.pi*np.cumsum(f1)/SR)+0.45*np.sin(2*np.pi*np.cumsum(f2)/SR+0.7)+0.15*np.sin(2*np.pi*np.cumsum(f2*1.5)/SR)
    # filtered-noise swell (cutoff rises 180 -> 2400 Hz)
    nz=rng.standard_normal(n)
    acc=np.zeros(n)
    bands=np.geomspace(150,3200,12)
    cf=180*np.exp(np.log(2400/180)*u**1.3)
    for fb in bands:
        acc+=bandpass(nz,fb/1.3,fb*1.3,2)*np.exp(-(np.log(fb/cf))**2/(2*0.5))
    sig=s*0.7+acc*0.12
    env=u**2.2
    sig*=env
    sig*=np.minimum(1,(dur-t)/0.02)       # ends exactly at dur
    L=sos_filt(sig,"lowpass",4000)
    return np.stack([L,np.roll(L,23)],axis=1)   # tiny inter-channel delay for width
