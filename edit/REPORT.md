# REPORT: 0930.mp4 → finished 9:16 short

Deliverables in `edit/`:

- `final.mp4`: 1080×1920, 60 fps, H.264 High (CRF 14, preset slow, BT.709), AAC-LC 48 kHz stereo 320 kb/s
- `stems/voice.wav`, `stems/sfx.wav`, `stems/riser.wav`, `stems/music.wav`: 48 kHz / 24-bit stereo. Every stem is exactly END long (2 268 800 samples).
- `qa/`: contact sheets used for the final QA

The pipeline that produced the video is in `work/` (compositions, compositor, audio synthesis, QA scripts). Heavy intermediates are git-ignored.

---

## 1. Final length

| | |
|---|---|
| **END** | **47 266.667 ms** (2836 frames @ 60 fps) |
| END in seconds | **47.2667 s** |

END is the last frame of the supplied short: source frame 1417 @ 30 fps, the last one containing picture. The source audio ran 9 ms past the last video frame; it is cut to END. Every generated layer ends exactly on END: graphics, captions, CTA, SFX, riser and music (with an 800 ms music fade that finishes on END).

## 2. Input handling

- **Source video:** `0930.mp4`. You gave a local Windows path; the file was fetched from your Google Drive through the temporary "anyone with link" share you enabled. Size 59 386 849 B. H.264 1080×1920 portrait, 30 fps, 1418 frames. AAC 44.1 kHz stereo, 47.28 s.
- **Separate clean audio:** none existed, so the audio embedded in the video was used. There was no sync step and no offset.
- **Transcription:** faster-whisper `large-v3` (CPU, int8) with word-level timestamps on the final voice timeline. Detected language: Polish, probability 0.999. The voice timeline is the untouched source timeline, so the word times drive captions, graphics and SFX 1:1.

## 3. Pacing edits

**No timeline trims were made.** The supplied short is already tightly cut: 17 jump cuts made by you, all on sentence boundaries. I measured it before deciding:

- **Internal quiet stretches.** Using 10 ms RMS windows, no quiet stretch (< −35 dB) anywhere in the voice exceeds 250 ms. The longest is 100 ms, and it sits inside a phrase. The "shorten > 250 ms pauses to ~120 ms" rule had nothing to act on. Tightening further would have made the delivery sound rushed.
- **Start.** The first word begins about 30–40 ms after frame 0, which already matches the ~40 ms target. Nothing added, nothing removed.
- **Existing joins.** I checked all 17 source joins. The longest quiet gap within ±250 ms of any join is 70 ms, well under the 150 ms limit. None needed repair.
- **J-cuts.** Your own joins already let the next line start 7–73 ms before its picture change. Every layout cut in the edit lands on one of your jump-cut frames, so voice and picture stay frame-accurate.
- **Voice tail.** The source stops inside the word "bio" (still at about −20 dB on the last sample). A 120 ms cos² fade lets it decay to the noise floor exactly at END instead of clicking off. I chose 120 ms rather than 170 ms because a 170 ms fade audibly swallowed "bi-o".
- **Voice processing.** 70 Hz high-pass (zero-phase), dual-mono, loudness normalisation to −14 LUFS, and a transparent look-ahead true-peak limiter at −1.5 dBTP. The source was hot and slightly clipped (+0.3 dBFS inter-sample overshoots in the AAC decode). No denoising was applied, because the room noise sits under the music bed and NR artifacts would have cost more than they saved.

## 4. Layout runs (covers every ms of [0, END])

| Run | Start (s) | End (s) | Dur (s) | Layout | Visual shown | Reason |
|---|---|---|---|---|---|---|
| R1 | 0.000 | 4.333 | 4.333 | **SPLIT** | Stats card (views ↗ 1,2 mln vs clients flat at 0) → account card, "Dostęp do konta" switch turns on → four tiles 1–4 (3 and 4 in clay) | Hook: SPLIT rule. A compact data card fits the 40–900 zone and stays below y 620 on the cover frame. |
| R2 | 4.333 | 9.033 | 4.700 | FULL CAM | You to camera | Teaser / open loop, a direct personal promise. The riser swells under it. |
| R3 | 9.033 | 13.167 | 4.133 | FULL VISUAL | Profile grid of your last 10 videos. A scan ring checks each one as its view count appears; the top 3 are selected, lift out and line up sorted (486 / 212 / 97 tys.). | Readable UI detail (10 tiles + counts) needs the full frame. |
| R4 | 13.167 | 16.667 | 3.500 | SPLIT | Comment sheet. Questions get marked; the 3 near-identical "ile razy w tygodniu…" questions get a clay bar and a ×3 badge, the rest fall back in depth. | Single floating card. |
| R5 | 16.667 | 18.000 | 1.333 | FULL CAM | You | Punchline "I tutaj masz już pomysł na filmik". |
| R6 | 18.000 | 22.300 | 4.300 | FULL VISUAL | The question flies from the comment into a phone as the on-screen hook; the first second of the timeline fills (0:01). **Whip** → a single answer card, "3 razy w tygodniu.", with a green check. | Demonstrates the action (record the question in second 1, then one answer). Needs the full frame. |
| R7 | 22.300 | 25.233 | 2.933 | FULL CAM | You | Opinion / payoff line. |
| R8 | 25.233 | 28.033 | 2.800 | SPLIT | Your most popular video card (486 tys.) with a #1 badge; anonymous audience avatars with "?" appear around it. | Single compact card, "Kto ogląda…?". |
| R9 | 28.033 | 31.967 | 3.933 | FULL VISUAL | The audience drifts toward the viral card, with curiosity reactions ("Ciekawe!", "Serio?!", "Nie wiedziałem", "Wow"). **Whip** → the next video; the same crowd and reactions form around it while its view counter climbs. | Several elements plus a whip need the full frame. |
| R10 | 31.967 | 33.333 | 1.367 | FULL CAM | You | Punchline "I nie da ci żadnych klientów". |
| R11 | 33.333 | 37.433 | 4.100 | FULL VISUAL | Three questions. The potential client's ("Mam salon beauty…") comes forward and gets checked, the others blur. Step down → it becomes the hook of the next video and record is pressed. | Readable multi-card detail. |
| R12 | 37.433 | 43.567 | 6.133 | SPLIT | "Analiza profilu" document with metrics filling in, a "Co cię blokuje" row, then a step to 3 ready script cards (Film 1–3). | Offer part of the outro: shows what you get while your face stays on screen. |
| R13 | 43.567 | 47.267 | 3.700 | FULL CAM + CTA | You; CTA comment box types "link w bio", then "Opublikuj" is pressed | Outro/CTA: FULL CAM rule. |

Rotation: 4× SPLIT, 5× FULL CAM, 4× FULL VISUAL. No two consecutive runs share a layout. The longest run is 6.13 s, so none exceeds 8 s.

**Eye contact.** MediaPipe FaceLandmarker (blendshape gaze + head pose) ran on all 1418 frames. I spot-checked 8 evenly spaced frames and sampled densely (every 100 ms) around the only candidate, a downward-gaze reading at 34.0–36.0 s. That reading turned out to be a blink at 36.0 s. You engage the lens for the whole short, so no visual run was changed because of gaze.

**Split geometry (portrait source).** The source is already 1080×1920, so the footage stays at scale 1.0 with no zoom and is only shifted down by 280 px:

- Hair top lands at y ≈ 1040–1110 and the card top edge (y 1200) crosses the forehead. This is equivalent to the 16:9 reference, where the footage top sits 192 px above the card.
- Camera card: x −65, y 1200, 1210×864, radius 200 superellipse (squircle), three-layer shadow.
- The head cutout uses the same source frame index as the card, with the same offset, so it is pixel-aligned. It is feathered over 40 px below the card edge.
- Graphic world fades out from y 900 to 1060.

## 5. Graphics

All visual runs are HyperFrames compositions, one per run, in `work/hf/viz/compositions/`. Each composition's duration equals its run exactly: 240 fps frame counts are 1040 / 992 / 840 / 1032 / 672 / 944 / 984 / 1472, which is 4× the run frames.

**Shared style.** Near-white radial ground (#FFF at 50%/36% → #F3F3F0), white floating cards with the three-layer shadow, Poppins 96/52/30, and the specified accent colours. There is no grid, no orbs and no dark world.

**World camera.** Camera keyframes live in each composition as JSON (glide / step / pull back / push / whip). Frame 0 of every run is the settled landing state.

**Motion blur.** Each graphic is rendered at 240 fps. For every 60 fps output frame the compositor computes the camera's screen displacement over a 270° shutter (0.75/60 s):

- Displacement under 1 px: the frame is the sharp centre subframe. Slow glides stay razor sharp, so there is no blur on a stationary camera.
- Otherwise: 3 of the 4 subframes are blended. Each is additionally integrated along the exact camera path (affine warps) so fast whips become a smooth streak instead of 3 ghosts.
- The streak length equals speed × 0.75/60 (σ = 0.29·L), capped at σ 40 px.

335 of 2836 frames received blur, all during camera moves.

| Run | What it shows | Source / reference | Type |
|---|---|---|---|
| R1 | Stats card, account card + access switch, tiles 1–4 | Custom | Custom graphic |
| R3 | Profile grid (10 videos, view counts, selection) | Generic short-video profile grid, platform-neutral; thumbnails are stills from your own footage | Reconstruction (no branding) |
| R4 | Comment sheet with repeated question | Generic comment UI, platform-neutral | Reconstruction |
| R6 | Comment → phone recording UI (REC, hook caption, 0:01 timeline) → answer card | Generic camera/recording UI | Reconstruction + custom |
| R8 / R9 | Most popular video + audience + reactions, next video | Your own stills; custom avatars (neutral silhouettes) | Custom graphic |
| R11 | Question cards → next-video card with record button | Generic UI | Reconstruction + custom |
| R12 | Profile analysis document, blocker row, 3 script cards | Custom | Custom graphic |
| CTA | Avatar, comment box, typed "link w bio", blinking caret, "Opublikuj" pressed | Custom | Custom graphic (rendered with alpha) |
| Cover | "Wyświetlenia / bez klientów?" (Poppins Bold 110, black on a white rounded box, y 262–603) | Written from your hook | Custom |

**No real product is named in the narration.** No Instagram, TikTok, Claude or other product is named, so no product logo or real UI capture was needed. The UIs are neutral reconstructions without platform branding.

**All numbers in the graphics are illustrative, not your real data:** 1,2 mln; 486 / 212 / 97 tys.; 38 / 41 / 12 %; "3 razy w tygodniu". If you want the graphics to carry proof, swap in real stats from your account.

Contact sheets for every composition were rendered and inspected before use. The final whole-video sheet is `qa/contact_all.jpg`.

## 6. Fact checking

The narration contains no external factual claim: no release, statistic, price, quote, benchmark or headline. It is advice and personal method, so there was nothing to verify against sources. The only numbers spoken are "10 filmów", "trzy" and "cztery rzeczy", which describe your own method. There are no disagreements to report.

## 7. SFX

Every sound corresponds to a visible event. Layout cuts, glides, steps and pushes have no sound.

- **Levels** (relative to the voice sample peak of −1.5 dBFS): clicks, pops and the chime at −10 dB; whooshes at −9 dB; key presses at −16 dB.
- **Whooshes:** 2 whips → 2 whooshes (limit is 3), using different variants (0 and 2). Each whoosh's loudest 5 ms window lands exactly on its whip midpoint (verified: 20.970 s and 30.483 s).

| Time (s) | Sound | Visual event |
|---|---|---|
| 1.800 | soft pop | R1: account card lands |
| 2.500 | bubbly click | R1: access switch flips on |
| 3.560 / 3.680 / 3.800 / 3.920 | soft pops | R1: tiles 1, 2, 3, 4 land |
| 10.953 / 11.133 / 11.313 | bubbly clicks | R3: top videos 1–3 selected (check badges) |
| 15.937 | soft pop | R4: ×3 badge lands |
| **20.970** | whoosh (variant 0) | R6: whip midpoint, phone → answer card |
| 21.650 | two-note chime | R6: answer confirmed (green check) |
| 26.943 | soft pop | R8: #1 badge lands |
| **30.483** | whoosh (variant 2) | R9: whip midpoint, viral video → next video |
| 35.473 | bubbly click | R11: client's question checked |
| 36.303 | bubbly click | R11: record button pressed |
| 41.543 / 41.683 / 41.823 | soft pops | R12: script cards 1–3 land |
| 46.550 → 46.955 (10×, 45 ms apart) | soft key presses | CTA: "link w bio" typed |
| 47.017 | bubbly click | CTA: "Opublikuj" pressed |

**Riser:** 6.533 → **9.033 s**. It is a low F2→C3 swell plus filtered noise, peaking 14 dB below the voice peak. Its audible end lands exactly on the hook → first-point cut ("Najpierw…", verified sample-accurate), which is also the downbeat of bar 5 of the music.

**Music:** original, synthesized in `work/audio/build_audio.py`.

- 106.27 BPM, so that 16 beats = 9.0333 s and the riser lands on a downbeat.
- F major colour: Fmaj9 | Am7 | Dm9 | B♭maj9. Soft sine kick, snap on 2 & 4 after the hook, hats and shaker, sub bass, warm detuned-saw pad, very quiet chord-tone pluck. No lead melody, no vocals.
- Beat 1 on the first frame with a 5 ms declick, one flat gain throughout (per-bar RMS −25.0 to −25.4 dB), no ducking, 800 ms fade to END.

## 8. Audio measurements (ffmpeg `ebur128=peak=true`)

| Stem | Integrated | True peak |
|---|---|---|
| voice.wav | **−14.0 LUFS** | −1.5 dBTP |
| sfx.wav | −23.6 LUFS | −9.9 dBTP |
| riser.wav | −25.9 LUFS | −15.5 dBTP |
| music.wav | **−24.0 LUFS** (10 LU under voice) | −10.8 dBTP |
| master (WAV, pre-AAC) | **−14.0 LUFS** | −1.1 dBTP |
| final.mp4 audio (AAC, as delivered) | **−14.0 LUFS** (−14.03) | **−1.0 dBTP** (−1.03) |

The mixing steps:

1. The stems summed to −13.5 LUFS.
2. One uniform master trim of −0.48 dB brought the master to −14.0 LUFS. This was not a per-stem change; to rebuild the master from the stems, sum them and apply −0.48 dB.
3. The master true peak was already −1.1 dBTP after the trim, so **the master limiter never engaged**. There is no pumping and no clipping.

## 9. Fallbacks / issues

- **Input location.** `C:\Users\cosmi\…\0930.mp4` is on your PC and this ran in a cloud container. The file came via Google Drive, which needed your temporary link share because the Drive connector caps downloads at 10 MB. **You can now switch that file back to "Restricted" if you haven't.**
- **No system ffmpeg.** Used a static ffmpeg 7.0.2 (via `imageio-ffmpeg` in the project venv) and ffprobe from the npm package `@ffprobe-installer`. Both are local to the project, nothing was installed system-wide. That ffmpeg has no `drawtext`, so all text overlays (captions, cover) are drawn with Pillow.
- **HyperFrames `transcribe` needs whisper.cpp,** which wasn't available. Used faster-whisper `large-v3` instead.
- **HyperFrames `remove-background`** (u2net_human_seg, CPU) worked and made all 4 split mattes (503 frames).
- **MediaPipe 1.0.1 needs libEGL** (not available without system installs), so the venv pins 0.10.21.
- **HyperFrames downloaded its own headless Chrome** into `~/.cache/hyperframes` (user cache, not a system install).
- **Motion blur:** the pure "blend 3 of 4 subframes" method leaves visible triple ghosts on whips (spacing up to 40 px). It was extended with camera-path warps; see §5.
- **Caption zones adapted to your framing.** In this portrait shot your face spans y ≈ 760–1560, so the default lower FULL CAM zone (1267–1536) and the outro centre (1037–1306) would cover your mouth.
  - FULL CAM captions sit above your head (y ≈ 618–719).
  - SPLIT captions sit in the gap above the popping head (≈ 925–1026).
  - FULL VISUAL captions use the standard lower zone (≈ 1314–1414).
- **CTA card moved.** The specified region (y 1344–1620) would cover your mouth and chin, so the same 994×276 card sits above your head at y 330–606.
- **CTA keyword.** Your spoken CTA is "link w bio", not a comment keyword, so the box types exactly that. Typing a different word would have invented a CTA you never said. The button reads "Opublikuj" (Polish UI), with no platform branding.
- **Transitional caption overlap.** During the two downward camera steps (R6 at ~19.0 s, R11 at ~36.0 s) the rising phone / video card passes under the caption for about 0.3 s while moving. Once settled, nothing important sits in the caption zone.
- **30 → 60 fps.** Each source frame is shown twice (no interpolation, so no warping artifacts on your face). Graphics are true 60 fps.

## 10. Final QA

| Check | Result |
|---|---|
| Resolution / fps / codec | 1080×1920, 60/1 fps, H.264 High yuv420p BT.709; AAC-LC 48 kHz stereo |
| Duration | 47.2667 s video (2836 frames), audio 47.266 s |
| Audio sync | Voice is the untouched source timeline, frame-locked to the source picture. All cuts are on your jump-cut frames. |
| Joins | All 12 layout cuts inspected on both sides (`qa/joins.jpg`): hard cuts, no flash or black frame, no missing or duplicated edit frame. |
| Split alignment | First frame of each split plus the two fastest head movements per split, checked at full resolution (`qa/split_heads.jpg`). Cutout present from frame 1 of every split; head always attached; matte stable. |
| Captions | Never over your face. They sit above the head in FULL CAM / outro, in the gap in SPLIT, and in the lower zone in FULL VISUAL. Highlight cadence is every 2–5 chunks and never two in a row. Frame 0 has no caption. |
| Frame 0 | Clean cover: title box at y 262–603, intro graphic content below y 620 (`qa/frame0_cover.png`). |
| Loudness | Master −14.0 LUFS / −1.1 dBTP (WAV); final AAC −14.03 LUFS / −1.03 dBTP |
| Tail | No silent tail: the voice decays into END, the music fade ends on END, and the last frame is you finishing "bio" with the CTA already posted (not blank, not frozen). |
| Content | Same short, same sentences, same order. See the transcript check below. |

**Transcript check.** The finished audio was re-transcribed with faster-whisper large-v3 and compared word by word with the source transcript (`qa/final_transcript.json`):

- **Word match:** 175 source words vs 174 final words, 98.6 % sequence similarity, same order.
- **The only differences are recognition noise:** "pokaże"↔"pokażę", "sprawdzam"↔"sprawdzę", and one dropped "w".
- **Waveform check:** the voice stem correlates at 0.997 with the high-passed source audio. It is your original performance, only filtered and levelled.

No sentence was replaced, removed or reordered, and no alternative takes were used.
