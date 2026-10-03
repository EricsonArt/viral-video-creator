import json, sys, time
from faster_whisper import WhisperModel
t=time.time()
size = sys.argv[1] if len(sys.argv)>1 else "large-v3"
model = WhisperModel(size, device="cpu", compute_type="int8", cpu_threads=4)
print("loaded", size, round(time.time()-t,1), flush=True)
segs, info = model.transcribe("audio/src_16k_mono.wav", language="pl", word_timestamps=True, vad_filter=False, beam_size=5, condition_on_previous_text=False)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end,"p":w.probability} for w in (s.words or [])]})
json.dump({"language":info.language,"segments":out}, open(f"transcript_{size}.json","w"), ensure_ascii=False, indent=1)
print("done", round(time.time()-t,1))
for s in out: print(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}")
