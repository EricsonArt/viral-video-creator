import soundfile as sf, numpy as np, sys
from faster_whisper import WhisperModel
x, sr = sf.read("work/src16k.wav")
def clip(a,b): return x[int(a*sr):int(b*sr)].astype(np.float32)
windows = {"cta1 43.6-45.7": (43.6,45.7), "cta2 49.5-52.0": (49.5,52.0), "sec 29.3-34.6": (29.3,34.6), "tail 53.9-59.7":(53.9,59.7), "fd 11.4-14.0": (11.4,14.0)}
for name in ("medium","large-v3"):
    m = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=4)
    for wname,(a,b) in windows.items():
        for prompt in (None, "Wbij na systemskala.pl i wpisz swój nick konta. Wpisz programista, a je dostaniesz."):
            segs,_ = m.transcribe(clip(a,b), language="pl", beam_size=5, temperature=0.0, initial_prompt=prompt, condition_on_previous_text=False)
            t = " ".join(s.text.strip() for s in segs)
            print(f"[{name}][{wname}][prompt={'Y' if prompt else 'N'}] {t}", flush=True)
