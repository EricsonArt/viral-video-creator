import json, sys, time
from faster_whisper import WhisperModel
size=sys.argv[1]; tag=sys.argv[2]; prompt=sys.argv[3] if len(sys.argv)>3 else None
model = WhisperModel(size, device="cpu", compute_type="int8", cpu_threads=4)
segs, info = model.transcribe("audio/src_16k_mono.wav", language="pl", word_timestamps=True, beam_size=10, best_of=5, temperature=0.0, condition_on_previous_text=False, initial_prompt=prompt, vad_filter=False)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end,"p":w.probability} for w in (s.words or [])]})
json.dump({"segments":out}, open(f"transcript_{tag}.json","w"), ensure_ascii=False, indent=1)
print("== ", tag)
for s in out: print(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}")
