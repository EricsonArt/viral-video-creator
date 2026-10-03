#!/usr/bin/env python3
"""Builds plan.json: corrected word timings, caption chunks, visual-run plan, cut points.

Source of truth: the supplied short (input/src.mp4). Nothing is re-ordered or replaced.
Word timings come from Whisper large-v3 (transcript_large-v3.json); phrase-initial words are
re-anchored to the energy onset measured on the 10 ms RMS envelope (Whisper starts phrases late).
"""
import json, math

FPS = 60
END_S = 41.200                      # last 10 ms RMS window >= -35 dB is 41.19 s -> END = 41.200 s
END_F = round(END_S * FPS)          # 2472 frames @ 60 fps

T = json.load(open('transcript_large-v3.json'))
raw = [w for s in T['segments'] for w in s['words']]

def W(i):
    return raw[i]

tok = []   # (text, start, end)
def add(text, s, e):
    tok.append([text, round(s, 3), round(e, 3)])

# --- phrase 1 (hook)
for i, txt in [(0, 'Możesz'), (1, 'korzystać'), (2, 'teraz'), (3, 'z')]:
    add(txt, W(i)['s'], W(i)['e'])
mid = (W(4)['s'] + W(4)['e']) / 2 - 0.02
add('Claude', W(4)['s'], mid); add('Code', mid, W(4)['e'])
for i, txt in [(5, 'całkowicie'), (6, 'za'), (7, 'darmo,'), (8, 'jest'), (9, 'z'), (10, 'niemal'), (11, 'nieograniczonym'), (12, 'limitem.')]:
    add(txt, W(i)['s'], W(i)['e'])
# --- phrase 2
ON = {'P2': 3.92, 'P3': 7.10, 'P4': 10.36, 'P5': 14.43, 'P6': 18.72, 'P7': 20.71, 'P8': 23.58, 'P9': 28.42, 'P10': 39.38}
add('Ktoś', ON['P2'] - 0.02, W(13)['e'])
for i, txt in [(14, 'na'), (15, 'GitHubie'), (16, 'właśnie'), (17, 'stworzył'), (18, 'darmowe'), (19, 'narzędzie'), (20, 'o'), (21, 'nazwie'), (22, 'OmniRoute,')]:
    add(txt, W(i)['s'], W(i)['e'])
# --- phrase 3
add('który', ON['P3'] - 0.02, W(23)['e'])
add('łączy', W(24)['s'], W(24)['e'])
mid = (W(25)['s'] + W(25)['e']) / 2 - 0.02
add('Claude', W(25)['s'], mid); add('Code', mid, W(25)['e'])
for i, txt in [(26, 'z'), (27, 'ponad'), (28, '200'), (29, 'darmowymi'), (30, 'dostawcami'), (31, 'kluczy'), (32, 'API.')]:
    add(txt, W(i)['s'], W(i)['e'])
# --- phrase 4 ("jest" at 11.08-11.14 dropped: no sibilant in the audio there, most likely "ci")
add('Zapewnia', ON['P4'] - 0.02, 11.05)
add('nawet', W(35)['s'], W(35)['e'])
add('1,5', W(36)['s'], W(37)['e'])
for i, txt in [(38, 'miliarda'), (39, 'darmowych'), (40, 'tokenów'), (41, 'każdego'), (42, 'miesiąca.')]:
    add(txt, W(i)['s'], W(i)['e'])
# --- phrase 5
add('Więc', ON['P5'] - 0.02, W(43)['e'])
for i, txt in [(44, 'gdy'), (45, 'tylko'), (46, 'przekroczysz'), (47, 'limit'), (48, "Claude'a,"), (49, 'to'), (50, 'narzędzie'), (51, 'przełączy'), (52, 'cię'), (53, 'automatycznie'), (54, 'na'), (55, 'darmowy'), (56, 'odpowiednik.')]:
    add(txt, W(i)['s'], W(i)['e'])
# --- phrase 6
add('Dzięki', ON['P6'] - 0.02, W(57)['e'])
for i, txt in [(58, 'czemu'), (59, 'twoja'), (60, 'sesja'), (61, 'będzie'), (62, 'trwała'), (63, 'bez'), (64, 'przerw.')]:
    add(txt, W(i)['s'], W(i)['e'])
# --- phrase 7
add('Dodatkowo', ON['P7'] - 0.02, W(65)['e'])
for i, txt in [(66, 'kompresuje'), (67, 'to'), (68, 'prompty,'), (69, 'zanim'), (70, 'dotrą'), (71, 'do'), (72, 'modelu'), (73, 'AI.')]:
    add(txt, W(i)['s'], W(i)['e'])
# --- phrase 8
add('Zmniejszając', ON['P8'] - 0.02, W(74)['e'])
for i, txt in [(75, 'przy'), (76, 'tym'), (77, 'zużycie'), (78, 'tokenów'), (79, 'od'), (80, 'ponad')]:
    add(txt, W(i)['s'], W(i)['e'])
add('90%', W(81)['s'], W(82)['e'])   # "90 procent"
for i, txt in [(83, 'przy'), (84, 'zachowaniu'), (85, 'dokładnie'), (86, 'tych'), (87, 'samych'), (88, 'wyników.')]:
    add(txt, W(i)['s'], W(i)['e'])
# --- phrase 9
add('A', ON['P9'] - 0.02, W(89)['e'])
for i, txt in [(90, 'jeśli'), (91, 'chcesz'), (92, 'darmową,'), (93, 'pełną'), (94, 'analizę'), (95, 'twojego'), (96, 'całego'), (97, 'profilu,'), (98, 'chcesz'), (99, 'wiedzieć'), (100, 'co'), (101, 'cię'), (102, 'blokuje'), (103, 'i'), (104, 'chcesz'), (105, 'mieć'), (106, 'gotowe'), (107, 'trzy'), (108, 'viralowe'), (109, 'filmiki'), (110, 'do'), (111, 'nagrania'), (112, 'na'), (113, 'następny'), (114, 'dzień,'), (115, 'na'), (116, 'podstawie'), (117, 'filmików,'), (118, 'które'), (119, 'już'), (120, 'się'), (121, 'wybiły'), (122, 'u'), (123, 'ciebie'), (124, 'albo'), (125, 'w'), (126, 'twojej'), (127, 'niszy,'), (128, 'tak'), (129, 'żeby'), (130, 'mieć'), (131, 'pewnego'), (132, 'virala,')]:
    add(txt, W(i)['s'], W(i)['e'])
# --- phrase 10 (CTA)
add('to', ON['P10'] - 0.02, W(133)['e'])
for i, txt in [(134, 'weź'), (135, 'link'), (136, 'w'), (137, 'bio'), (138, 'i'), (139, 'wpisz'), (140, 'nazwę'), (141, 'swojego'), (142, 'profilu.')]:
    add(txt, W(i)['s'], W(i)['e'])

# make sure starts are monotonic and every token has positive length
for k in range(1, len(tok)):
    if tok[k][1] < tok[k - 1][1] + 0.02:
        tok[k][1] = tok[k - 1][1] + 0.02
for k in range(len(tok)):
    if tok[k][2] <= tok[k][1] + 0.03:
        tok[k][2] = tok[k][1] + 0.03

# caption chunks: (first token, last token, highlighted token indices)
CH = [
 (0,1,[]),(2,3,[]),(4,5,[4,5]),(6,8,[]),(9,11,[]),(12,13,[12]),
 (14,16,[]),(17,18,[]),(19,20,[]),(21,23,[23]),
 (24,25,[]),(26,28,[]),(29,30,[29,30]),(31,32,[]),(33,34,[]),
 (35,36,[]),(37,38,[37,38]),(39,40,[]),(41,42,[]),
 (43,45,[]),(46,47,[47]),(48,49,[]),(50,52,[]),(53,53,[53]),(54,56,[]),
 (57,59,[]),(60,62,[]),(63,64,[63,64]),
 (65,66,[]),(67,68,[68]),(69,70,[]),(71,73,[]),
 (74,76,[]),(77,78,[]),(79,81,[80,81]),(82,83,[]),(84,85,[]),(86,87,[]),
 (88,90,[]),(91,92,[91]),(93,94,[]),(95,96,[]),(97,98,[]),(99,101,[101]),(102,104,[]),(105,106,[]),(107,108,[107,108]),(109,110,[]),
 (111,113,[]),(114,115,[]),(116,117,[]),(118,120,[120]),(121,123,[]),(124,126,[]),(127,129,[]),(130,131,[131]),
 (132,134,[]),(135,136,[135,136]),(137,139,[]),(140,141,[]),
]
# sanity: contiguous coverage of all tokens, no two highlighted chunks in a row
cov = [i for a, b, _ in CH for i in range(a, b + 1)]
assert cov == list(range(len(tok))), (len(cov), len(tok))
prev = False
for a, b, h in CH:
    assert not (prev and h), f'two highlights in a row at chunk {a}'
    prev = bool(h)

# cut points: next phrase onset + 50 ms (J-cut: audio leads the picture), snapped to the 60 fps grid
CUT_ONSETS = {'C1': 3.92, 'C2': 10.36, 'C3': 14.46, 'C4': 20.73, 'C5': 23.60, 'C6': 28.45, 'C7': 35.05}
cuts = {k: round((v + 0.05) * FPS) for k, v in CUT_ONSETS.items()}

SRC_FPS = 30
runs = [
  dict(id='R1', layout='SPLIT',  a=0,            b=cuts['C1'], visual='Claude Code logo lockup -> Claude Code session UI (typing, tool steps)', why='Hook / opening sentence -> SPLIT. Compact logo + one UI card fits the graphic zone.'),
  dict(id='R2', layout='VISUAL', a=cuts['C1'],   b=cuts['C2'], visual='GitHub repo card -> OmniRoute logo -> real OmniRoute dashboard (providers grid) in capture frame', why='Named product + real UI needs readable detail -> FULL VISUAL.'),
  dict(id='R3', layout='CAM',    a=cuts['C2'],   b=cuts['C3'], visual='Talking head (stat line, yellow caption on 1,5 miliarda)', why='Punchline / stat delivered straight to camera -> FULL CAM. Avoids putting a number on screen that conflicts between sources.'),
  dict(id='R4', layout='VISUAL', a=cuts['C3'],   b=cuts['C4'], visual='Claude session hits limit -> whip -> free provider takes over, session keeps streaming', why='Process that must be shown (limit -> automatic fallback) -> FULL VISUAL with the single whip of the short.'),
  dict(id='R5', layout='SPLIT',  a=cuts['C4'],   b=cuts['C5'], visual='Long prompt card compresses into short prompt, then reaches model tile', why='Short compact visual (prompt compression) fits SPLIT graphic zone.'),
  dict(id='R6', layout='CAM',    a=cuts['C5'],   b=cuts['C6'], visual='Talking head (result claim, 90%)', why='Direct personal claim to camera -> FULL CAM; breaks the run of graphics.'),
  dict(id='R7', layout='VISUAL', a=cuts['C6'],   b=cuts['C7'], visual="Reconstruction of the user's account-analysis page (typing handle, pressing button)", why='Product UI with readable text -> FULL VISUAL.'),
  dict(id='R8', layout='CAM',    a=cuts['C7'],   b=END_F,      visual='Talking head + CTA input card (typing handle, button press)', why='Outro / CTA -> FULL CAM with CTA card in the lower third.'),
]
# validate: continuous cover of [0, END], no same layout twice in a row, no run > 8 s
assert runs[0]['a'] == 0 and runs[-1]['b'] == END_F
for i, r in enumerate(runs):
    r['dur_f'] = r['b'] - r['a']; r['start_s'] = round(r['a'] / FPS, 4); r['end_s'] = round(r['b'] / FPS, 4); r['dur_s'] = round(r['dur_f'] / FPS, 4)
    assert r['dur_s'] <= 8.0, r
    if i:
        assert runs[i - 1]['b'] == r['a']
        assert runs[i - 1]['layout'] != r['layout'], (runs[i - 1]['id'], r['id'])

def run_at(t):
    f = t * FPS
    for r in runs:
        if r['a'] <= f < r['b']:
            return r
    return runs[-1]

# caption zones per layout (centre y); see REPORT for the portrait-selfie adaptation
ZONE = {'CAM': 350, 'VISUAL': 1400, 'SPLIT': 868}
chunks = []
for n, (a, b, h) in enumerate(CH):
    start = tok[a][1]
    last_end = tok[b][2]
    chunks.append(dict(n=n, a=a, b=b, hl=h, text=' '.join(tok[i][0] for i in range(a, b + 1)), start=start, last_end=last_end))
for n, c in enumerate(chunks):
    nxt = chunks[n + 1]['start'] if n + 1 < len(chunks) else END_S
    c['end'] = round(min(nxt, c['last_end'] + 0.35) if n + 1 < len(chunks) else END_S, 3)
    c['start'] = max(round(c['start'], 3), 0.017) if n == 0 else round(c['start'], 3)
    r = run_at(c['start'] + 0.02)
    c['run'] = r['id']; c['layout'] = r['layout']; c['y'] = ZONE[r['layout']]

plan = dict(fps=FPS, end_s=END_S, end_f=END_F, src_fps=SRC_FPS, tokens=tok, chunks=chunks, runs=runs, cuts=cuts,
            cut_onsets=CUT_ONSETS, onsets=ON)
json.dump(plan, open('plan.json', 'w'), ensure_ascii=False, indent=1)
print('END', END_S, END_F, 'frames; tokens', len(tok), 'chunks', len(chunks))
for r in runs:
    print(f"{r['id']} {r['layout']:6s} {r['start_s']:7.3f}-{r['end_s']:7.3f} ({r['dur_s']:.3f}s)  frames {r['a']}-{r['b']}")
print('highlighted chunks:', [c['n'] for c in chunks if c['hl']])
