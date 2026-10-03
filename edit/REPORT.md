# REPORT - "Claude Code za darmo / OmniRoute" short

Deliverables (all in `edit/`): `final.mp4`, `stems/voice.wav`, `stems/sfx.wav`, `stems/riser.wav`, `REPORT.md`.
Extras: `stems/extras/whoosh_v1..v4.wav` (the 4 synthesized whoosh variants), `work/` (all scripts, plan, transcripts, QA images).
**No music was produced** - you asked for none ("nie dodawaj muzyki"), so `stems/music.wav` does not exist and the master is voice + SFX + riser only. The riser is an SFX item from the brief, not music; it is in `stems/riser.wav` and can be dropped from a remix.

## 1. Final length

| | |
|---|---|
| END | **41 200 ms** |
| END | **41.200 s** (2472 frames @ 60 fps) |

END = the last 10 ms RMS window >= -35 dB in the voice (41.19 s). Video, voice, SFX, riser and every generated layer end exactly on END (video 2472 frames, audio 41.200 s).

## 2. Input handling

- Source video: `input/src.mp4` (= "1003 (1)(1).mp4" from your Google Drive; 1080x1920 portrait, 30 fps, 41.267 s, H.264 + AAC 44.1 kHz stereo).
- Separate clean audio: **none existed** -> the audio embedded in the short was used (cleaned, see section 3). **Sync offset: n/a** (no cross-correlation needed).
- The supplied footage has a **burned-in white pill "tu też :) systemskala.pl" from 39.4 s to the end**. It is part of your short, so it was kept untouched; captions and the CTA card are placed so they do not cover it.
- Transcript: faster-whisper large-v3 (word timestamps), cross-checked with a second large-v3 pass (domain prompt) and medium. HyperFrames `transcribe` was not usable (needs whisper.cpp, not installed) - see section 10.

## 3. Pacing edits

The supplied short is already tightly cut, so almost nothing needed fixing. **No spoken line was removed, replaced or reordered.**

| Edit | Detail |
|---|---|
| Tail trimmed | Source video ended at 41.267 s (audio 41.285 s). Trimmed to END 41.200 s: removes 67 ms of decayed tail (voice already at about -37 dB there, last frames had closed eyes). A 12 ms declick fade sits on the last samples; the natural decay was kept. |
| Head | Nothing trimmed: first sound at about 40 ms in the processed voice (the source already starts on the word). |
| Pauses > 250 ms | **None exist.** Longest quiet run (RMS < -32 dB) is 100 ms (18.15 s and 38.07 s). The P3->P4 junction (10.19-10.36 s) holds about 210 ms of near-silence/breath, below the 250 ms threshold, so it stays as a natural pause. |
| Join repair | Click/step detector over every join: no discontinuities (peaks are fricatives, waveform continuous) -> no repair needed. No quiet gap > 150 ms anywhere. |
| J-cuts | At all 7 layout cuts the picture switches **50 ms after** the next phrase starts (audio leads). Picture cuts are hard cuts on the 60 fps grid. |
| Voice processing | High-pass 75 Hz, FFT denoise (9 dB), -1.2 dB @ 220 Hz, +1.6 dB @ 3.2 kHz, 2:1 gentle compression, look-ahead limiter, -14 LUFS. |
| Frame rate | 30 fps source -> 60 fps by frame doubling (no interpolation, so no ghosting). All graphics are native 60 fps. |

### Eye contact
Analysed **all 1238 frames** (MediaPipe face landmarker: iris position, gaze blendshapes, head pose) plus visual checks at 100 ms steps around the largest deviations (38.0-39.0 s and 11.6-12.1 s) and an 8-frame sample. You look at the lens throughout; the largest deviation is a 0.3 s head tilt at 38.4-38.6 s (yaw about 10 degrees) with the eyes still on the lens. Result: **no section was swapped for a visual because of gaze.**

## 4. Layout runs

Run plan covers [0, END] with no gap or overlap; no layout repeats back-to-back; longest run 6.6 s; all three layouts used.

| Start (s) | End (s) | Dur (s) | Layout | Visual shown | Reason |
|---|---|---|---|---|---|
| 0.000 | 3.967 | 3.967 | SPLIT | Claude Code logo -> Claude Code session UI (typing, tool steps) + infinity tile | Hook -> SPLIT; compact logo + one UI card |
| 3.967 | 10.417 | 6.450 | FULL VISUAL | GitHub repo card -> OmniRoute logo -> real OmniRoute dashboard in the capture frame | Named product + real UI with detail |
| 10.417 | 14.517 | 4.100 | FULL CAM | Talking head (stat line) | Punchline straight to camera; avoids a number on screen that the sources disagree on |
| 14.517 | 20.783 | 6.267 | FULL VISUAL | Claude usage hits LIMIT -> whip -> free provider session keeps streaming | Process must be shown; the short's single whip |
| 20.783 | 23.650 | 2.867 | SPLIT | Long prompt compresses -> short prompt -> model tile | Short compact visual |
| 23.650 | 28.500 | 4.850 | FULL CAM | Talking head (result claim) | Direct personal claim; rests the eye between graphics |
| 28.500 | 35.100 | 6.600 | FULL VISUAL | Rebuilt account-analysis page (typing handle, button press) | Product UI with readable text |
| 35.100 | 41.200 | 6.100 | FULL CAM | Talking head + CTA input card | Outro / CTA -> FULL CAM |

## 5. Graphics

| Run | What it shows | Source / reference | Type |
|---|---|---|---|
| R1 | "Claude Code" logo lockup | Official lockup from the Claude Code docs header (code.claude.com); the four letters "Docs" were removed from the SVG | Real brand asset (edited) |
| R1 | Claude Code session UI (prompt typing, Read/Write steps, diff) | Style taken from the public screenshots on claude.com/product/claude-code | **Reconstruction** |
| R1 | Infinity tile | - | Custom |
| R2 | GitHub repo card (diegosouzapw / OmniRoute, "Free MIT AI gateway") | Repo metadata (README, npm); GitHub mark from Simple Icons. **github.com is blocked (403) from this environment**, so no live page capture | **Reconstruction** |
| R2 | OmniRoute logo tile | Hub glyph + brand colour redrawn from the vector in the repo's own README diagram | Reconstruction of a real mark |
| R2 | OmniRoute dashboard (Providers page) | Real screenshot `docs/screenshots/MainOmniRoute.png` from the project's README (MIT), sharp inside the fixed frame x=24 y=200 1032x1040 r=36, with the blurred duplicate behind (blur 40, sat .7, brightness 1.05; white wash raised from 72% to 93% because the capture is dark) | **Real capture** |
| R4 | Claude usage meter 62% -> 100% + red LIMIT stamp | - | Custom |
| R4 | Free provider card: Gemini / DeepSeek / Mistral / Groq tiles, green check, streaming session | Providers shown are in OmniRoute's real free-tier list; logos from the LobeHub icon set | Custom + real logos |
| R5 | Long prompt compressing into a short one, sent to a model tile | Concept from the README's compression-pipeline diagram (that diagram is dark with sub-30 px text, so redrawn in the bright style) | Custom |
| R7 | "ANALIZA KONTA - ZA DARMO / 3 filmy na jutro..." card with typing + button press | Your screenshot; mascot redrawn as SVG; fonts approximated (Instrument Serif, Poppins, JetBrains Mono) | **Reconstruction** |
| R8 | CTA input card | Styled after the input in your screenshot | Custom |

All compositions are HyperFrames (one per run), 1080x1920, near-white radial ground (#FFF at 50%/36% to #F3F3F0), 3-layer shadows, Poppins. `hyperframes check`: **0 lint errors in every composition**; the only layout-audit findings are in R7, where the button and headline are deliberately cropped/faded by the camera moving inside the product window.

Motion blur: every graphic run is rendered at **240 fps** and 3 of every 4 sub-frames are blended into each 60 fps frame (270-degree shutter). Because the two big camera moves (R2 step 1100 px in 0.5 s, R4 whip) leave visible stepping between sub-frames, a thin directional Gaussian (sigma = 0.55 x px per sub-frame) is added only on frames where the world camera actually moves. Stationary frames are sharp; the blur never exceeds the 40 px cap.

## 6. Fact checking

| Claim in narration | Sources checked | Result |
|---|---|---|
| Someone on GitHub created a free tool called OmniRoute that works with Claude Code | GitHub README (raw.githubusercontent.com/diegosouzapw/OmniRoute); npm registry `omniroute`; nerdzap.com (1 Jul 2026); explainx.ai guide | **True** (MIT, works with Claude Code). **"Just created" is loose**: the npm package was first published 2026-02-14 and has 290 versions (latest 3.8.51, 2026-09-30) |
| Connects Claude Code to "200+ free providers of API keys" | README ("358 providers - 150+ free"; repo description "359 providers (150+ free)"); nerdzap ("236 providers", "over 50" free-tier); project wiki ("50 provider free-tier pools") | **Sources disagree.** 200+ providers in total: supported (236-359). 200+ *free* providers: **not supported** (about 50-150+ depending on how free tiers are counted). No provider count is shown on screen |
| Up to 1.5 billion free tokens per month | README (~1.62B steady, ~2.22B first month); nerdzap (~1.6B); a 1.51B figure in another summary; wiki (~1.94B recurring, 2.53B first month, "upper-bound estimates") | **Consistent but conservative**: documented figures range 1.5-1.94B and the project itself says free tiers change constantly. No number is shown on screen |
| When the Claude limit is hit it switches automatically to a free equivalent | README ("quota-aware auto-fallback", tier cascade Subscription -> API key -> Cheap -> Free), nerdzap | **True**, with the caveat that the fallback is a non-Claude free-tier model |
| Compresses prompts, saving "over 90%" of tokens with identical results | README (RTK + Caveman compression "15-95%, ~89% avg"); compression doc (avg 89.2%, range 78.4-94.6%, code/URLs/JSON preserved byte-perfect); nerdzap (15-95%) | **Partly.** Average is about 89%, slightly **below** "over 90%" (peak about 95%). "Exactly the same results" is not benchmarked anywhere I found |
| Account-analysis offer (CTA) | Your own screenshot | Copied from your page, not verified |

Terms-of-service note from the project's own docs: about 13-19 of the listed providers carry personal-use or proxy clauses, so "free via OmniRoute" depends on which providers a viewer enables.

## 7. SFX

Levels relative to the voice peak: pops/chimes/clicks -10 dB, whoosh -9 dB, ticks -16 dB, riser -14 dB. Nothing is attached to layout cuts, camera steps, pushes or glides.

| Time (s) | Sound | Visible event |
|---|---|---|
| 1.467 -> 3.967 | riser (2.5 s) | ends exactly on the hook -> first-point cut (R1 -> R2) |
| 1.450 | dull soft pop | R1 Claude Code UI card lands |
| 1.98-3.06 | 15 key ticks | R1 prompt typing |
| 2.980 | dull soft pop | R1 infinity tile lands |
| 7.587 | dull soft pop | R2 real OmniRoute UI frame lands |
| 15.817 | dull soft pop | R4 LIMIT stamp lands |
| 16.517 | whoosh (variant 1) | R4 whip; loudest point on the whip midpoint |
| 17.137 | dull soft pop | R4 free provider card lands |
| 17.717 | two-note chime | R4 green check confirms the connection |
| 18.07-20.17 | 6 key ticks | R4 session lines stream in |
| 22.843 | dull soft pop | R5 compressed prompt reaches the model tile |
| 31.45-32.38 | 14 key ticks | R7 handle typing |
| 32.480 | soft bubbly click | R7 button pressed |
| 39.560 | dull soft pop | CTA input card lands |
| 39.84-40.77 | 14 key ticks | CTA handle typing |
| 40.969 | soft bubbly click | CTA button pressed |

Only 1 whoosh is used (limit is 3, one per run); 4 variants were synthesized and exported to `stems/extras/`.

## 8. Audio measurements (ffmpeg ebur128, true peak)

| Stem | Integrated LUFS | True peak (dBTP) |
|---|---|---|
| voice | **-14.0** | -1.1 |
| SFX | -26.1 | -9.8 |
| riser | -28.2 | -15.9 |
| music | not produced (per your request) | - |
| master (voice + SFX + riser) | **-14.0** | -2.4 |
| master as decoded from `final.mp4` (AAC 256 kbps) | **-14.0** | **-2.3** |

Targets met within 0.1 LU. The master uses a true-peak look-ahead limiter (ceiling -2.4 dBTP before AAC: a first attempt at -1 dBTP overshot to +1.1 dBTP after AAC encoding, so the ceiling was lowered and re-measured). No clipping.

## 9. Fallbacks / issues

- **HyperFrames `transcribe`** needs whisper.cpp (not installed) -> used faster-whisper (large-v3, word timestamps). Whisper starts phrases late by up to about 200 ms (e.g. "Zapewnia" at 10.62 s vs real onset 10.36 s), so phrase-initial words were re-anchored to the energy onset measured on the 10 ms RMS envelope.
- **ASR text fixes in captions:** CloudCode -> Claude Code, OminiRoute -> OmniRoute, "zarzędzie" -> narzędzie, "kluczów" -> kluczy, "Clouda" -> Claude'a. Whisper's "jest" between "Zapewnia" and "nawet" was dropped (no sibilant in the audio there; probably "ci"); "jest z niemal" in the hook was kept (sibilant present). "od ponad 90%" is captioned as spoken.
- **MediaPipe 1.0.1** needed system libEGL -> installed MediaPipe 0.10.21 in a separate local venv (face/gaze analysis only).
- **Head cut-out:** `hyperframes remove-background` (u2net_human_seg) + guided-filter refinement against the real source frame. On the first 3 motion-blurred frames the matte grabbed wall, so those use an extra head-ellipse clamp.
- **github.com blocked (403)** -> GitHub card is a reconstruction. Logos from jsDelivr (Simple Icons, LobeHub).
- **Portrait selfie adaptations.** Your face fills y of about 820-1530, so the brief's landscape-footage geometry was adapted:
  - SPLIT: card at the specified x=-65, y=1200, 1210x864, r=200 (squircle) showing the source at **scale 1.0 (no zoom)**, source offset +360 px; the card edge falls at the forehead and the hair above it is the cut-out (40 px feather just under the edge). Graphic content ends at y of about 822 and SPLIT captions sit at y=868 (just above the hair) instead of 941-1114.
  - FULL CAM captions go to y=350 (above the head, clear of the burned-in pill) instead of 1267-1536, which would cover your mouth.
  - CTA card sits at y=1612 (212 px tall) instead of y=1344/276 px, which would cover your mouth and chin.
  - In a few frames (3-5% of SPLIT frames) the chin is cropped by up to 27 px by the canvas edge.
- **CTA content:** your spoken CTA has no comment keyword ("weź link w bio i wpisz nazwę swojego profilu"), so the card types a profile handle (`eryk_hajduczek`, the example from your page) and ends with the orange arrow button instead of "Post".
- **Cover:** "Claude Code / za darmo" (hook-based), frame 0 only; first caption starts on frame 1 (16.7 ms).
- **Caption highlights:** 16 of 60 chunks, never two in a row.
- **Source quirk left as is:** the first frames (0-6) are motion-blurred by a hand movement; that belongs to the supplied take (the closed-eye frame at the very end was trimmed with the tail).
- **Dashboard backdrop** is greyish at the top because the real UI is dark; the world itself stays bright.
- **Marketing wording:** "Claude Code za darmo" (hook and cover) is only true in the sense that the free fallback uses *non-Claude* free-tier models.

## 10. Final QA

- Resolution **1080x1920**, **60 fps**, H.264 High, yuv420p, BT.709, AAC 48 kHz stereo, 48.9 MB.
- Duration **41.200 s** (2472 frames); audio duration 41.200 s, both start at 0.0 s -> audio sync unchanged from the source (voice used 1:1, no offset).
- Captions: FULL CAM top zone (never over the face or the pill), FULL VISUAL lower zone below every graphic, SPLIT just under the graphic and above the hair; checked on a 1 fps contact sheet of the whole video.
- Split alignment: cut-out and card use the same source frame and transform; fast head moves checked at source frames 116 and 664-666 (fastest in the SPLIT spans) - hair and face stay connected, no tear, matte stable. Cut-out exists from the first frame of both SPLIT runs.
- Cuts: frame pairs inspected on both sides of all 7 cuts - clean hard cuts, no flash, no black frame, no duplicated or missing frame.
- Loudness: voice -14.0 LUFS, master -14.0 LUFS, true peak -2.3 dBTP after AAC; whoosh peak 0.0 ms from the whip midpoint (16.517 s); riser audible end 3.9666 s vs cut 3.9667 s; longest quiet run in the voice 100 ms.
- No silent tail, no frozen or blank final frame (last frames differ by the source's 30 fps steps, mean brightness 134), no accidental grid, no dark world.
- **Content QA:** the finished video is the same short - same sentences in the same order (10 phrases, 143 spoken words, captions follow the speech); no line removed or rearranged; no alternative takes were used.
