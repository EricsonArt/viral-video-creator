import json, sys, time
from faster_whisper import WhisperModel
wav = "work/src16k.wav"
out = "work/transcript.json"
for name in ("large-v3", "medium"):
    try:
        t0 = time.time()
        model = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=4)
        print("loaded", name, round(time.time()-t0,1), "s", flush=True)
        segs, info = model.transcribe(wav, language="pl", word_timestamps=True,
                                      vad_filter=False, beam_size=5,
                                      condition_on_previous_text=False)
        words, segments = [], []
        for s in segs:
            segments.append({"start": s.start, "end": s.end, "text": s.text})
            for w in (s.words or []):
                words.append({"w": w.word, "start": w.start, "end": w.end, "p": w.probability})
        json.dump({"model": name, "duration": info.duration, "segments": segments, "words": words},
                  open(out, "w"), ensure_ascii=False, indent=1)
        print("DONE", name, len(words), "words", round(time.time()-t0,1), "s", flush=True)
        break
    except Exception as e:
        print("FAIL", name, repr(e), flush=True)
