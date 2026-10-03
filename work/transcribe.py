import sys, json
from faster_whisper import WhisperModel
size = sys.argv[1] if len(sys.argv)>1 else "large-v3"
m = WhisperModel(size, device="cpu", compute_type="int8", cpu_threads=4)
segs, info = m.transcribe("audio/src_16k.wav", word_timestamps=True, vad_filter=False, beam_size=5, condition_on_previous_text=False)
print("lang", info.language, info.language_probability, flush=True)
out=[]
for s in segs:
    ws=[{"w":w.word,"s":round(w.start,3),"e":round(w.end,3),"p":round(w.probability,3)} for w in s.words]
    out.append({"s":round(s.start,3),"e":round(s.end,3),"text":s.text,"words":ws})
    print(round(s.start,2), round(s.end,2), s.text, flush=True)
json.dump({"lang":info.language,"segments":out}, open(f"transcript_{size}.json","w"), ensure_ascii=False, indent=1)
