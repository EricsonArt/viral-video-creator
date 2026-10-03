import sys, json
from faster_whisper import WhisperModel
size = sys.argv[1]
m = WhisperModel(size, device="cpu", compute_type="int8", cpu_threads=4)
segs, info = m.transcribe(sys.argv[2], language="pl", word_timestamps=True, vad_filter=False, beam_size=5, condition_on_previous_text=False)
out=[]
for s in segs:
    out.append({"start":s.start,"end":s.end,"text":s.text,"words":[{"w":w.word,"s":w.start,"e":w.end,"p":w.probability} for w in s.words]})
json.dump(out, open(sys.argv[3],"w"), ensure_ascii=False, indent=1)
for s in out: print(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}")
