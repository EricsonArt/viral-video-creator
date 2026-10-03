#!/usr/bin/env python3
"""Master plan: single source of truth for timeline, runs, words, caption chunks.
All times in seconds on the FINAL timeline T (T = source_time + PAD)."""
import json, math
FPS = 60
PAD = 0.040                      # lead-in before the first spoken word (room tone + held frame 0)
SRC_VIDEO_FRAMES = 1228          # 30 fps source = 40.9333 s
END_FRAMES = 2458                # 40.9667 s  (<= PAD + 40.9333, so no frame is invented at the end)
END = END_FRAMES / FPS
JCUT = 0.050                     # picture transitions land ~50 ms AFTER the new line begins (audio leads)

valleys = json.load(open('valleys.json'))
al = json.load(open('words_aligned.json'))['words']
for i_, w in enumerate(al):
    if i_ == 25: w['w'] = '5'   # spoken 'Sonet 5' (Sonnet 5 = previous model, 10.3%)
    w['s'] = round(w['s'] + PAD, 3)
    w['e'] = round(w['e'] + PAD, 3)

def fr(t):  # snap to 60 fps frame
    return round(t * FPS) / FPS

cuts_src = [valleys['R1|R2'], valleys['R2|R3'], valleys['R3|R4'], valleys['R4|R5'],
            valleys['R5|R6'], valleys['R6|R7'], valleys['R7|R8'], valleys['R8|R9']]
cuts = [fr(c + PAD + JCUT) for c in cuts_src]

LAYOUTS = [
    ('R1', 'SPLIT',  'hook: Sonnet 5.5 vs Opus 5.5 (+ half price)'),
    ('R2', 'VISUAL', 'Terminal-Bench 4.0 table (70.6 / 66.4 / 10.3)'),
    ('R3', 'SPLIT',  'API price per 1M tokens: Sonnet 5.5 vs Opus 5.5'),
    ('R4', 'CAM',    'direct statement: 30% faster / 30% cheaper'),
    ('R5', 'VISUAL', 'strongest at: code, bugs, docs, slides, spreadsheets'),
    ('R6', 'CAM',    'Opus stays for heavy work; "nobody talks about it" + free test'),
    ('R7', 'SPLIT',  'Sonnet 5.5 on the Free plan (Claude app model picker)'),
    ('R8', 'VISUAL', 'ClipCash: account analysis, what blocks you, ready viral videos'),
    ('R9', 'CAM',    'outro / CTA: bio + type your nick'),
]
bounds = [0.0] + cuts + [END]
runs = []
for i, (rid, lay, what) in enumerate(LAYOUTS):
    runs.append(dict(id=rid, layout=lay, what=what, start=round(bounds[i], 4), end=round(bounds[i + 1], 4),
                     start_f=round(bounds[i] * FPS), end_f=round(bounds[i + 1] * FPS)))
    runs[-1]['dur'] = round(runs[-1]['end'] - runs[-1]['start'], 4)

# ---- caption chunks (word index ranges inclusive) + highlighted word index ----
CH = [
 (0,1,None),(2,3,None),(4,5,5),(6,8,None),(9,11,None),(12,12,None),
 (13,14,14),(15,17,None),(18,20,None),(21,21,21),
 (22,23,None),(24,25,None),(26,28,28),
 (29,31,None),(32,34,None),(35,37,35),
 (38,39,None),(40,42,None),(43,43,43),
 (44,46,None),(47,49,None),(50,52,52),(53,55,None),(56,57,None),(58,59,59),
 (60,61,None),(62,63,None),(64,64,None),(65,65,65),(66,68,None),
 (69,71,None),(72,73,None),(74,75,75),(76,78,None),(79,80,None),(81,83,None),(84,86,86),
 (87,89,None),(90,91,None),(92,93,92),
 (94,96,None),(97,98,None),(99,101,None),(102,103,None),(104,106,106),
 (107,109,None),(110,110,None),(111,111,111),
 (112,114,None),(115,117,None),(118,120,120),
 (121,123,None),(124,125,None),(126,128,128),(129,131,None),(132,133,None),
]
DISP = {  # caption text normalisation (display form)
}
chunks = []
for a, b, hl in CH:
    ws = al[a:b+1]
    chunks.append(dict(words=[dict(w=x['w'].strip('.,'), s=x['s'], e=x['e'], hl=(a+i == hl)) for i, x in enumerate(ws)],
                       s=ws[0]['s'], e=ws[-1]['e']))
# check cadence of highlights
seq = [any(w['hl'] for w in c['words']) for c in chunks]
gaps, g = [], 0
for h in seq:
    if h:
        gaps.append(g); g = 0
    else:
        g += 1
# chunk timing: start slightly before first word, end at next start (or last word end + 0.22)
for i, c in enumerate(chunks):
    c['start'] = max(0.017 if i == 0 else 0, c['s'] - 0.03)
for i, c in enumerate(chunks):
    nxt = chunks[i + 1]['start'] if i + 1 < len(chunks) else END
    c['end'] = min(nxt, c['e'] + 0.30) if i + 1 < len(chunks) else END
    # avoid micro flashes: ensure min 0.18 s
    c['end'] = max(c['end'], min(nxt, c['start'] + 0.18))
chunks[0]['start'] = 0.017

plan = dict(fps=FPS, pad=PAD, end=END, end_frames=END_FRAMES, jcut=JCUT, runs=runs, words=al, chunks=chunks,
            highlight_gaps=gaps)
json.dump(plan, open('plan.json', 'w'), ensure_ascii=False, indent=1)
print('END', END, 'frames', END_FRAMES)
for r in runs:
    print(f"{r['id']} {r['layout']:6s} {r['start']:7.3f}-{r['end']:7.3f} ({r['dur']:.2f}s) f{r['start_f']}-{r['end_f']}  {r['what']}")
print('highlight gaps (normal chunks between highlights):', gaps)
print(len(chunks), 'chunks')
for c in chunks:
    print(f"{c['start']:6.3f}-{c['end']:6.3f}  " + ' '.join(('[%s]' % w['w']) if w['hl'] else w['w'] for w in c['words']))
