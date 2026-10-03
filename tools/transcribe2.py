import json, time
from faster_whisper import WhisperModel
prompt = ("Jak w 5 minut zamienić Claude Code w zespół 6 programistów? Wtyczki: Superpowers, Frontend Design, "
          "Code Review, Security Review, gstack Garry'ego Tana. Anthropic, GitHub, klucze API, systemskala.pl, "
          "wpisz w komentarzu programista, nick konta, wiralowe filmiki.")
model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
segs, info = model.transcribe("work/src16k.wav", language="pl", word_timestamps=True, beam_size=8,
                              initial_prompt=prompt, condition_on_previous_text=False, temperature=0.0)
words, segments = [], []
for s in segs:
    segments.append({"start": s.start, "end": s.end, "text": s.text})
    for w in (s.words or []):
        words.append({"w": w.word, "start": w.start, "end": w.end, "p": w.probability})
json.dump({"segments": segments, "words": words}, open("work/transcript_prompted.json","w"), ensure_ascii=False, indent=1)
print("DONE2", len(words))
