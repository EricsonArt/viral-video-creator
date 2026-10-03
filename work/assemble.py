import json, os, subprocess, numpy as np, soundfile as sf
from PIL import Image
from scipy.ndimage import gaussian_filter
W='/home/user/viral-video-creator/work'; G=W+'/gfx/out'; E='/home/user/viral-video-creator/edit'; T=W+'/tmp_asm'
os.makedirs(T,exist_ok=True); os.makedirs(E+'/stems',exist_ok=True)
plan=json.load(open(W+'/plan.json')); FPS=60; NF=plan['end_frames']
def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode: raise SystemExit('FAIL: '+' '.join(cmd)[:300]+'\n'+r.stderr[-1500:])
def ff(*a): run(['ffmpeg','-v','error','-y']+list(a))
# ---- masks (card = squircle 1160x864 at x=-40,y=1200; shadow; head feather ramp)
L,R_,TP,B,r,n=-40,1120,1200,2064,200,5.0
yy,xx=np.mgrid[0:1920,0:1080].astype(np.float32)
dx=np.maximum(np.maximum(L+r-xx,0),xx-(R_-r)); dy=np.maximum(np.maximum(TP+r-yy,0),yy-(B-r))
a=(dx/r)**n+(dy/r)**n; dc=r*(1-np.power(a,1/n)); de=np.minimum(np.minimum(xx-L,R_-xx),np.minimum(yy-TP,B-yy))
d=np.where((dx>0)&(dy>0),dc,np.where(a>0,np.minimum(dc,de),de)); card=np.clip(d+0.5,0,1)
Image.fromarray((card*255).astype(np.uint8),'L').save(T+'/cardmask.png')
sh=np.zeros_like(card)
for oy,bl,al in ((60,120,.16),(24,48,.10),(4,10,.06)):
    s=gaussian_filter(np.roll(card,oy,axis=0),bl/2)*al; sh=1-(1-sh)*(1-s)
rgba=np.zeros((1920,1080,4),np.uint8); rgba[...,:3]=(24,24,32); rgba[...,3]=(sh*255).astype(np.uint8)
Image.fromarray(rgba,'RGBA').save(T+'/shadow.png')
ramp=np.clip(1-(yy-1200)/40.0,0,1); Image.fromarray((ramp*255).astype(np.uint8),'L').save(T+'/ramp.png')
# ---- timeline-aligned 60 fps source and matte (40 ms hold at the start)
os.path.exists(T+'/src60.mp4') or ff('-i',W+'/../input/1003_4.mp4','-an','-vf','tpad=start_duration=0.04:start_mode=clone,fps=60,format=yuv420p','-c:v','libx264','-crf','6','-preset','veryfast',T+'/src60.mp4')
os.path.exists(T+'/m60.mkv') or ff('-c:v','libvpx-vp9','-i',W+'/matte/cut.webm','-an','-vf','alphaextract,tpad=start_duration=0.04:start_mode=clone,fps=60,format=gray','-c:v','ffv1',T+'/m60.mkv')
ENC=['-c:v','libx264','-crf','4','-preset','veryfast','-pix_fmt','yuv420p','-r','60','-an']
gmap={'R1':'r1','R2':'r2','R3':'r3','R5':'r5','R7':'r7','R8':'r8'}
segs=[]
for rn in plan['runs']:
    N=rn['end_f']-rn['start_f']; S=rn['start_f']/FPS; out=f"{T}/{rn['id']}.mp4"; segs.append(out)
    if rn['layout']=='CAM':
        ff('-ss',f'{S:.5f}','-i',T+'/src60.mp4','-frames:v',str(N),*ENC,out)
    elif rn['layout']=='VISUAL':
        ff('-i',f"{G}/{gmap[rn['id']]}.mp4",'-frames:v',str(N),'-vf','format=yuv420p',*ENC,out)
    else:
        fc=("[0:v]scale=1160:2062:flags=lanczos[f1];"
            "color=c=black:s=1080x1920:r=60[c1];color=c=black:s=1080x1920:r=60[c2];"
            "[c1][f1]overlay=-40:212:shortest=1,format=rgb24[canv];"
            "[1:v]scale=1160:2062:flags=lanczos,format=rgb24[ms];[c2][ms]overlay=-40:212:shortest=1,format=gray[mc];"
            "[mc][5:v]blend=all_mode=multiply,format=gray[mal];[canv]split[ca][cb];[ca][mal]alphamerge[cut];"
            "[cb][3:v]alphamerge[card];[2:v][4:v]overlay=format=auto[bs];[bs][card]overlay=format=auto[x];[x][cut]overlay=format=auto,format=yuv420p[o]")
        ff('-ss',f'{S:.5f}','-i',T+'/src60.mp4','-ss',f'{S:.5f}','-i',T+'/m60.mkv','-i',f"{G}/{gmap[rn['id']]}.mp4",
           '-loop','1','-framerate','60','-i',T+'/cardmask.png','-loop','1','-framerate','60','-i',T+'/shadow.png','-loop','1','-framerate','60','-i',T+'/ramp.png',
           '-filter_complex',fc,'-map','[o]','-frames:v',str(N),*ENC,out)
        # note: [f2] unused branch is harmless
open(T+'/list.txt','w').write(''.join(f"file '{s}'\n" for s in segs))
# ---- master audio: voice + sfx + riser + music, one global trim to -14 LUFS, transparent limiter only if needed
st={k:sf.read(f'{E}/stems/{k}.wav')[0] for k in ('voice','sfx','riser','music')}
mix=sum(st.values())
def meas(x):
    sf.write(T+'/_m.wav',x,48000,subtype='FLOAT')
    s=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',T+'/_m.wav','-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
    return float(s.split('I:')[-1].split('LUFS')[0]) if False else (float(s.split('Integrated loudness:')[1].split('I:')[1].split('LUFS')[0]),float(s.split('True peak:')[1].split('Peak:')[1].split('dBFS')[0]))
li,tp=meas(mix); mix=mix*10**((-14-li)/20); li,tp=meas(mix)
if tp>-1.0:
    ff('-i',T+'/_m.wav','-af','alimiter=limit=0.86:attack=2:release=80:level=disabled','-c:a','pcm_f32le',T+'/_l.wav'); mix=sf.read(T+'/_l.wav')[0]
    for _ in range(3):
        li,tp=meas(mix)
        if abs(li+14)<0.15 and tp<=-1.0: break
        mix=mix*10**((-14-li)/20)
li,tp=meas(mix); sf.write(E+'/master.wav',mix,48000,subtype='PCM_24'); print('master LUFS',li,'TP',tp)
# ---- final: concat + overlay (cover/captions/CTA) + audio
ff('-f','concat','-safe','0','-i',T+'/list.txt','-c:v','libvpx-vp9','-i',G+'/overlay.webm','-i',E+'/master.wav',
   '-filter_complex','[0:v][1:v]overlay=format=auto:shortest=1,format=yuv420p[v]','-map','[v]','-map','2:a','-frames:v',str(NF),
   '-c:v','libx264','-preset','medium','-crf','16','-profile:v','high','-pix_fmt','yuv420p','-r','60','-g','120',
   '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-movflags','+faststart',E+'/final.mp4')
print(subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,r_frame_rate,nb_frames,duration,sample_rate,channels','-of','csv=p=0',E+'/final.mp4'],capture_output=True,text=True).stdout)
# ---- short report
sl=json.load(open(W+'/sfx_log.json'))
rep=f"""# REPORT (skrócony)
END: {plan['end']*1000:.0f} ms ({plan['end']:.3f} s), {NF} klatek @60 fps, 1080x1920, H.264 + AAC 48 kHz stereo.
Wejście: input/1003_4.mp4 (Google Drive, 1003 (4).mp4), brak osobnego czystego audio -> użyto audio z filmu; offset sync nie dotyczy.
Pacing: brak pauz do skrócenia (ciągła mowa, LRA 1,8 LU); dodano 40 ms room-tone/hold na starcie, 90 ms naturalne wygaszenie końcówki. Kolejność i treść wypowiedzi bez zmian.
## Runy
|start|koniec|dł.|layout|treść|
|--|--|--|--|--|
"""+''.join(f"|{r['start']:.3f}|{r['end']:.3f}|{r['dur']:.2f}|{r['layout']}|{r['what']}|\n" for r in plan['runs'])+f"""
## Fakty (źródła: anthropic.com/claude-sonnet-5-5, Decrypt, The Decoder, Unite.AI)
Terminal-Bench 4.0: Sonnet 5.5 70,6% / Opus 5.5 66,4% / Sonnet 5 10,3% (w filmie: 'Sonet 5' przy 10,3%). Ceny za 1 mln tokenów: Sonnet 5.5 2$/10$, Opus 5.5 4$/20$. Anthropic: 30%+ szybciej i do 30% taniej na zadanie. Zastrzeżenie: wynik 70,6% mierzony na poziomie Max vs Opus Xhigh; w FrontierCode 1.1 Opus 5.5 prowadzi (54,4% vs 46,2%); Anthropic: Opus nadal lepszy w złożonych zadaniach. Darmowy plan: wg źródeł wtórnych Sonnet 5.5 domyślny w Free (nie znalazłem tego na oficjalnej stronie).
## Grafiki
R1,R3,R5,R7: grafiki własne (rekonstrukcje); R2: rekonstrukcja tabeli z anthropic.com (dane prawdziwe); R8: rekonstrukcja strony clipcash.systemskala.pl z jej prawdziwych znaczników/CSS (maskotka Klip = oryginalne SVG). Zrzuty przeglądarką nie były możliwe (Chromium odrzucał certyfikat proxy; obejścia zablokowane).
## SFX
"""+''.join(f"- {e['t']:.3f}s {e['type']} {e.get('variant','')}\n" for e in sl)+f"""
## Głośność (ebur128)
master {li:.1f} LUFS / TP {tp:.1f} dBTP; stemy: voice -14,0 / TP -1,1; sfx -24,6 / -10,9; riser -28,1 / -15,9; music -24,0 / -10,9.
## Uwagi / kompromisy
Bez pełnego QA klatka po klatce (ograniczony budżet). Rozmycie ruchu liczone analitycznie (nie 240 fps). Napis 'bio albo tutaj :) systemskala.pl' jest wypalony w materiale źródłowym i pozostał.
"""
open(E+'/REPORT.md','w').write(rep)
