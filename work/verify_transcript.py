import json, re, sys
from faster_whisper import WhisperModel
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=2)
segs, info = m.transcribe(sys.argv[1], language="pl", beam_size=5)
txt = " ".join(s.text.strip() for s in segs)
norm = lambda t: re.findall(r"\w+", t.lower())
a = norm(" ".join(s["text"] for s in json.load(open("work/transcript_large.json"))["segments"]))
b = norm(txt)
import difflib
sm = difflib.SequenceMatcher(a=a, b=b)
print("source words", len(a), "final words", len(b), "similarity %.4f" % sm.ratio())
for op in sm.get_opcodes():
    if op[0] != "equal":
        print(op[0], a[op[1]:op[2]], "->", b[op[3]:op[4]])
json.dump({"final_transcript": txt, "similarity": sm.ratio()}, open("work/qa/final_transcript.json", "w"), ensure_ascii=False, indent=1)
