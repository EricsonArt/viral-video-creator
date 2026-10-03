---
name: talking-head-short-editor
description: Edit an ALREADY PREPARED talking-head short into a finished, ready-to-post 9:16 video (1080x1920, 60 fps) for Reels, TikTok and YouTube Shorts, fully autonomously in code (ffmpeg, Python, Node, HyperFrames). Cleans pacing, syncs clean audio if present, builds luxury-tech graphics, split/full-cam/full-visual layouts, captions, cover, CTA card, synthesized SFX, riser and music, then exports edit/final.mp4 plus stems and REPORT.md. Use when the user supplies a ready short video and asks to edit, finish, polish or "zmontuj" it. Never selects takes, reorders or rewrites the speech.
---

# Talking-head short -> finished 9:16 social video

You are editing my ALREADY PREPARED SHORT-FORM VIDEO into a finished, ready-to-post 9:16 short for Instagram Reels, TikTok and YouTube Shorts.

## IMPORTANT - the supplied short is the source of truth

The input video is ALREADY the short I want to publish.

DO NOT:

- search through the footage for a different short
- extract a short from a longer recording
- look for alternative takes
- choose between multiple recordings of the same sentence
- reorder my spoken lines
- rewrite the structure of what I say
- remove complete lines just because you think another structure would perform better
- turn this into a different video

Your job is to EDIT, CLEAN UP, ENHANCE and FINISH this exact short video.
Preserve the original spoken content and its order.
You may tighten pauses, remove accidental dead space, improve pacing, add graphics, visual storytelling, captions, music, SFX, layouts, screen captures and motion design - but the underlying short itself must remain the same video.

Do all of it yourself, end to end, in code:

- ffmpeg
- Python
- Node
- HyperFrames (`npx --yes hyperframes`)

No traditional video editor app.
Every sound effect and the music are synthesized by you in code. There are no pre-made audio files to use unless they are already provided in the project.
You may install what you need locally inside this project:

- npm packages inside the project folder
- Python packages inside a local virtual environment

Never install system-wide software. Do not ask for permission.

## Work fully autonomously

- Don't ask me anything after the task starts.
- Run every step from start to finish.
- Finish with `final.mp4` exported.
- Every judgement call is yours: graphic choice, layout choice, animation choice, visual source, pacing adjustment, SFX placement, caption placement, product UI reconstruction, factual-source selection.
- Make the best call, keep going and log important decisions in the report.
- If something fails, try another way: different tool, different method, local package, fallback implementation. A missing tool is not a reason to stop.
- If a real product UI is behind a login, rebuild it from public screenshots, public documentation or other reliable public references and note that in the report.
- If the cover title is not supplied, create one yourself based on the hook.
- Only stop early if the input video itself is missing or unreadable.

## Inputs

PRIMARY INPUT: one already-prepared short-form video in the project folder (find it by scanning for video files such as mp4/mov/mkv/webm, ignoring the `edit/` output folder). This is NOT a long source recording. Treat its spoken structure and chronological order as final.

OPTIONAL INPUT: a separate clean audio file in the project folder.

- If clean audio exists: sync it precisely to the short and use it instead of the camera audio.
- If not: use the audio embedded in the short and clean/process it as necessary.

Cover title: create one yourself from the hook unless one is explicitly supplied.

## Deliverables

Create a new folder `edit/` containing:

- `final.mp4` - 1080x1920, 60 fps, H.264, high quality, AAC 48 kHz stereo
- `stems/voice.wav`
- `stems/sfx.wav`
- `stems/riser.wav`
- `stems/music.wav`
- `REPORT.md`

All stems must be full-length so they can be remixed later.

---

## 1. Prepare, sync and transcribe

First inspect the supplied short video. DO NOT search it for alternative takes, DO NOT identify multiple versions of the same sentence, DO NOT reconstruct the short from separate takes. The timeline of the supplied short is already the intended video.

If a separate clean audio file exists:

- convert the camera audio and clean audio to 16 kHz mono for analysis
- cross-correlate them to find the exact synchronization offset
- confirm the offset using a clear correlation peak
- align the clean audio to the supplied short
- discard the original camera audio after successful synchronization

If no clean audio exists: use the embedded video audio.

Transcribe the FINAL usable voice audio with word-level timestamps using HyperFrames transcribe or Whisper. Detect the spoken language rather than forcing English, and make sure the caption fonts cover its diacritics. Keep accurate word timestamps because they drive captions, visual timing, graphics, UI actions and SFX.

## 2. The edit / pacing

Do NOT select takes, look for repeated recordings, replace one spoken sentence with another take, or reorder spoken material. The supplied short already contains the exact performance to use. Your job here is only to improve pacing and remove obvious editing imperfections.

You may:

- remove accidental dead air
- shorten unnecessarily long pauses
- remove tiny accidental empty gaps
- clean obvious non-speech noise between sentences
- tighten obvious edit joins
- remove accidental silence at the very beginning or end

Do NOT remove natural intentional pauses that help delivery.

- Leave approximately 40 ms before the first spoken word.
- Internal silence: if a clearly unnecessary quiet stretch exceeds approximately 250 ms, shorten it toward approximately 120 ms. Natural short pauses stay. Do not make the speech sound rushed or robotic.

Determine the real ending of each spoken phrase from the audio, not only from the transcript timestamp. Use approximately:

- last 10 ms RMS window at or above -35 dB
- if the signal stays below approximately -32 dB for over 150 ms, treat the earlier point as the practical end

Picture cuts are hard cuts exactly on the intended join.

IMPORTANT: no automatic punch-ins, digital zooms or camera moves on my raw talking-head footage. Do not add artificial zoom-ins to my face.

The J-cut exists in AUDIO only, when useful: the next spoken line may begin approximately 50 ms before its picture transition.

A voice tail should decay naturally toward the noise floor. If necessary, fade the tail over approximately 170 ms.
Never create an artificial silent hole between phrases. No join may contain an accidental quiet gap above approximately 150 ms. Fix bad joins by trimming better or allowing natural overlap - never by inserting silence.

END = the last frame containing intentional video/audio content. Every generated layer must end exactly on END.

## 3. Eye contact

Analyze the supplied short for eye contact. Sample approximately 8 frames throughout relevant talking-head sections. Around head turns or obvious gaze changes, inspect more densely, approximately every 100 ms.

My camera should primarily appear when I am visibly engaging the lens.

- If I clearly look away from the lens for part of a sentence: split the visual run near the closest natural word boundary and switch that portion to an appropriate visual or graphic instead of showing me looking away.
- If an entire section is clearly delivered while looking off-camera / reading: prefer a full visual for that section.

IMPORTANT: do not change or remove the underlying spoken content. This rule affects only what is visually displayed.

## 4. The three layouts

Canvas: 1080x1920. Every short rotates naturally through three layouts. Transitions between layouts are hard cuts unless a graphic animation itself requires movement.

### A) FULL CAM

My supplied footage cover-fitted into 1080x1920.

- For a landscape source: use the centre crop intelligently and keep my face correctly framed.
- Do not add artificial camera zooms to the raw footage.

### B) SPLIT - camera at the bottom with my head popping out

A full-frame 1080x1920 graphic sits behind everything.

- Main graphic content lives approximately inside y = 40-900.
- Main element bottom edge: approximately y = 880-900.

On top: a rounded camera card.

- x = -65
- y = 1200
- width = 1210
- height = 864
- corner radius ~ 200, squircle-style rounding
- the card may bleed off the left, right and bottom edges

For a 16:9 source: scale footage to approximately 1890x1063 and place around x = -405, y = 1008. The lower portion is visible through the camera card.

Above the card's top edge only my cut-out head and shoulders extend above the card.

- Create the cutout from THE SAME SOURCE FRAME used inside the card.
- Use HyperFrames remove-background or an equivalent background-removal / segmentation method.
- Feather approximately 40 px around the card's top transition where appropriate.
- The head and camera-card footage must remain pixel-aligned.
- The head must never visually detach or tear away from the body. Verify this specifically during quick head movements.

For portrait source footage: derive an equivalent crop and geometry while keeping my head correctly positioned above the card.

### C) FULL VISUAL

A full-frame visual / graphic fills the 1080x1920 composition.

### Layout rules

- The hook / opening sentence uses SPLIT unless the supplied footage makes that clearly worse.
- The outro / CTA section uses FULL CAM.
- Direct-to-camera opinions, punchlines and personal statements generally use FULL CAM.
- Screen recordings, product interfaces, websites, news pages and visuals requiring readable detail generally use FULL VISUAL.
- A single screenshot, floating card, simple logo arrangement or short compact visual may use SPLIT.
- Avoid any single visual run longer than approximately 8 seconds unless there is a strong reason.
- Two runs in a row should not normally use the same layout.
- Across a normal short, use all three layouts when the content supports it.

Before creating graphics, write a run plan that covers the entire interval [0, END]. Every millisecond of the finished video must belong to a planned visual run.

## 5. Graphics

Use HyperFrames. Use one composition per visual run. Use parallel subagents if available and useful.

### Style: luxury tech

One bright visual world made of clean near-white space, floating white cards, premium UI, smooth camera movement, restrained depth and elegant shadows. Nothing cheap, gamer-like, overly neon or cartoonish.

**Ground:** radial near-white background. Centre `#FFFFFF` around 50% / 36%, edges `#F3F3F0`. No grid, no glowing orbs, no random particles, no dark background, no unnecessary decoration.

**Shadows:** objects floating above the background get a three-layer shadow:

```
0 60px 120px rgba(24,24,32,.16)
0 24px 48px rgba(24,24,32,.10)
0 4px 10px rgba(24,24,32,.06)
```

**Radii (approx.):** media cards 3% of their width, documents 40 px, tiles 72 px, phones/devices 84 px.

**Typography:** Poppins throughout unless defined otherwise below.

- Headline: 96 px / weight 700
- Subhead: 52 px / weight 700
- Body: 30 px / weight 400
- Nothing smaller than 30 px where viewers are expected to read it.

**Colors:**

- Main ink `#111111`
- Accent Clay fill `#D97757`
- Clay text on white `#B25730`
- Highlight band `#FBEEE8`
- Success/check `#34C759`
- Error/stamp `#FF3B30`

### World camera

The graphics feel like one coherent spatial world. The virtual camera moves between elements.

- **GLIDE:** sine.inOut, scale change no more than ~0.04
- **STEP TO NEXT ITEM:** ~0.5 s, power3.inOut, begins ~0.25 s before the narration names the new item
- **PUSH INTO CARD:** ~1.2-2.0 s, power2.inOut, up to ~1.6x
- **PULL BACK:** ~1-2 s, reveals the larger visual context
- **WHIP:** maximum ONE whip per visual run; ~0.45 s outgoing (power3.in), ~0.6 s incoming (power3.out)

Frame 0 of every run is already the clean landing state: sharp, settled, readable, camera at rest.

### Depth of field

The element currently being discussed is in focus. Nearby cards may blur up to ~14 px and dim around 30%. When a new hero card becomes active, the previous card may fall back to ~9 px blur and ~40% opacity. Never blur text the viewer needs to read.

### Motion blur

Apply motion blur to the GRAPHIC WORLD CAMERA during movement, never to stationary frames.

- sigma = 0.29 x speed x 0.75 / 60
- cap around 40 px
- when practical: render animation at 240 fps and blend ~3 of every 4 frames when reducing to 60 fps
- blur only during actual movement; a blurred frame while the camera is stationary is a bug

### Show the action - do not label the action

Whenever possible, SHOW what the narration describes. Do NOT place text labels that repeat my spoken sentence. Avoid generic label pills, decorative step chips, and rows of words restating narration.

If I mention a real product, show its REAL UI whenever reasonably possible: real public screenshot, public product documentation, HyperFrames capture, headless-browser capture, or an accurate reconstruction from reliable references.

If demonstrating the product, show the action itself: typing, streaming, clicking, generation, opening, scrolling, confirmation, etc.

When a product window is the main subject, the WORLD camera stays still. Only a camera INSIDE the product window moves: ~1.15x-1.4x, 0.4-0.7 s, power2.inOut.

For a named-product introduction: show (1) the official product logo large and centred, then (2) reveal the actual UI.

"Claude Code" refers to the Claude desktop-app experience / relevant Claude Code product UI. Do not automatically show a generic terminal unless the narration specifically refers to terminal usage.

### Real events / facts / releases

If the narration mentions something that actually happened (release, announcement, quote, statistic, number, headline, pricing, benchmark, product update), show the REAL source page whenever practical.

- Verify factual claims against at least two reputable sources when they materially matter.
- If reliable sources disagree: do not silently invent certainty. Use the most defensible representation and note the disagreement in REPORT.md.

For real webpage/news/product captures, place the real capture sharp inside a fixed frame: x = 24, y = 200, width = 1032, height = 1040, radius = 36, white background, premium shadow.

Behind it: an enlarged blurred near-white duplicate of the same visual (blur 40 px, saturation 0.7, brightness 1.05, 72% white wash).

The outer frame stays stationary. The footage/page inside may pan or zoom.

### Safe visual zones

- FULL VISUAL: keep important content above ~y = 1230. Main visual bottom edge ~1200-1230.
- SPLIT: important graphic content at y = 40-900. Fade the graphic world out from ~y = 900 downward across ~160 px.

### Scene density

Keep every scene sparse: one dominant visual subject, at most one secondary/supporting cue. No clutter. Motion is smooth, eased, deliberate, premium - never frantic.

The duration of every generated composition must EXACTLY match its assigned run.

Before using a rendered graphic, generate / inspect a contact sheet and confirm the important states are visually correct.

## 6. Cover, captions and CTA

### Cover

Frame 0 only. Generate a short cover title based on the hook.

- Poppins Bold, 110 px, black text
- inside a white rounded rectangle, radius ~2.8%, soft premium shadow
- centre around y ~ 0.13 of the canvas (about y 262-603 for a two-line title)
- ~50 px horizontal padding

On frame 0 the underlying intro graphic keeps its important content below ~y = 620. The cover title must be immediately readable.

### Captions

Use FINAL voice-track word timings. Start captions around 17 ms. Frame 0 stays visually clean. Chunk length: 1-3 words.

Base style: Poppins Bold, size 74, white, black stroke 10, no caption box.

After approximately every 2-3 normal caption chunks, highlight one or two meaningful words (product name, important number, result, benefit, surprising keyword, CTA keyword). Highlighted words:

- Instrument Serif, bold italic
- pure yellow `#FFFF00`
- same general size
- same black stroke

Never highlight two chunks in a row. Do not highlight meaningless function words.

### Caption position

Captions must never cover my face, critical product UI, the top edge of the camera card, or important graphic information.

- SPLIT: centre in the gap, ~y = 941-1114
- FULL CAM: lower section, ~y = 1267-1536
- MOST FULL VISUALS: lower section, ~y = 1267-1536
- VISUAL WITH IMPORTANT LOWER CONTENT: move captions up, ~y = 365-634
- OUTRO: centre, ~y = 1037-1306

Choose intelligently per run.

### CTA card

Outro only. Lower-third region: x = 43, y = 1344, width = 994, height = 276.

Show only:

- one centred comment input box
- transparent surrounding canvas
- simple/default avatar
- the CTA keyword from my spoken CTA
- the keyword being typed
- blinking caret
- Post button being pressed

Do NOT add a social-platform dashboard, fake DM panel, "DM me", unnecessary platform branding, or any extra background panel.

## 7. Audio

SYNTHESIZE EVERYTHING, THEN MIX. Sound design is clean, modern, restrained, premium. Never childish, cartoony, or meme-like unless explicitly appropriate.

### Voice - `stems/voice.wav`

The final edited/synchronized voice track, normalized to approximately -14 LUFS integrated.

### SFX - `stems/sfx.wav`

Use one SFX only for a meaningful VISIBLE event.

- BUTTON PRESS / TAP: soft bubbly click
- TYPING: short soft key press
- LONGER TYPING / DATA STREAM: light tick stream
- CARD / TILE / DEVICE LANDING: dull soft pop
- ANSWER / MODAL / CONFIRMATION: gentle two-note notification chime
- WHIP: low airy filtered-noise whoosh. The whoosh's loudest point must land EXACTLY on the midpoint of the visual whip. Whooshes belong only to actual whips. Maximum ~one per run, ~three per short. Create 3-4 whoosh variants and never repeat the same variant twice consecutively.

NO SFX for: layout cuts, graphic camera steps, pushes, glides, ordinary zooms. A logo reveal / lockup may use one tasteful whoosh or no sound. The CTA may similarly use one subtle whoosh or none. No random UI beep merely because an element appeared.

SFX levels relative to voice peak:

- clicks / pops / chimes: ~-10 dB
- whooshes: ~-9 dB
- key presses / ticks: ~-16 dB

### Intro riser - `stems/riser.wav`

A low, smooth swelling riser, ~2-3 s. Its audible ending lands exactly at the transition between the hook and the first main point. This is the one sound allowed to rise into a visual cut. Peak ~14 dB below voice.

### Music - `stems/music.wav`

An ORIGINAL instrumental bed: modern, minimal, warm electronic, premium tech, ~100-120 BPM, no vocals, no distracting lead melody, must not compete with the voice.

- spans the full video
- beat 1 starts on frame 1
- no long fade-in; only ~5 ms of declicking at the start
- ends with a ~800 ms fade-out
- ONE flat level throughout the short: no automatic ducking, no volume automation following speech
- target ~10 LU below the voice, about -24 LUFS integrated

### Master

Sum voice + SFX + riser + music. Do not make additional arbitrary per-stem level changes after the specified mix is established.

- target ~-14 LUFS integrated
- true peak max ~-1 dBTP
- transparent limiter only if peaks exceed the target
- no pumping, clipping or obvious limiter distortion

If the plain sum lands more than ~0.5 LU away from -14 LUFS, correct it with a single global gain on the master sum - not per-stem changes.

Measure with ffmpeg `ebur128`. Report LUFS / true peak for voice, SFX, riser, music and master.

## 8. Assemble and render

Build the finished picture according to the visual-run plan.

- FULL CAM runs: my supplied footage.
- SPLIT runs: graphic + camera card + aligned cut-out head.
- FULL VISUAL runs: the generated visual composition.

Then add the cover on frame 0, captions, and the CTA card where appropriate.

Render 1080x1920 at 60 fps and mux the final master audio. Every layer ends EXACTLY on END. No white frame at the end, no frozen head, no frozen graphic, no black frame, no accidental silent tail.

## 9. QA before you finish

LOOK AT REAL FRAMES. Do not assume the render is correct.

**Edit joins:** inspect frames on BOTH sides of every meaningful cut. Confirm the previous visual ends cleanly, the next begins immediately, and there is no flash frame, duplicated frame or missing frame.

**Split layout:** check fast head movement. Confirm head and body stay aligned, cutout and card use matching source frames, the head never disconnects from the body, the cutout exists from the FIRST frame of the split, and the matte does not flicker badly.

**Whole-video contact sheet:** generate one covering the entire finished short and check that:

- captions never cover my face or important UI
- yellow-word cadence looks intentional
- important graphic content stays inside its safe zones
- no accidental grid appears and no dark visual world appears
- the overall visual cadence feels coherent
- frame 0 works as a clean cover

**Audio QA:** confirm that

- every SFX corresponds to an actual visible event
- whooshes occur only on whip movements, with the peak aligned to the whip midpoint
- the intro riser ends precisely on the intended intro transition
- no join gap exceeds ~150 ms
- the master does not clip
- audio targets are within ~0.5 LU where practical

**Content QA (most important):** confirm that the finished video still represents THE SAME SHORT that was provided. Do NOT accidentally replace sentences, reorder statements, reconstruct the short from imagined alternate takes, remove major spoken ideas, or create a different narrative.

Fix anything that fails. Re-render. Inspect again. Do not hand it back until it passes.

## REPORT.md

Create `edit/REPORT.md` containing:

1. **Final length** - END in milliseconds and in seconds.
2. **Input handling** - source video used; whether separate clean audio existed; synchronization offset if applicable.
3. **Pacing edits** - meaningful timeline trims: shortened pauses, removed dead air, repaired joins. Do NOT list "take selection" - none should occur.
4. **Layout runs** - table with start time, end time, duration, layout, visual shown, reason for layout choice.
5. **Graphics** - for every generated visual: what it shows, what source/reference was used, and whether it is a real capture, reconstruction or custom graphic.
6. **Fact checking** - for each claim that needed verification: the claim, sources checked, result, any disagreement between sources.
7. **SFX** - timestamp, sound type, and the visual event it corresponds to.
8. **Audio measurements** - integrated LUFS and true peak for voice, SFX, riser, music and master.
9. **Fallbacks / issues** - unavailable tools, unavailable real UIs, failed approaches, fallbacks used, reconstructions used instead of real capture, any other meaningful compromise.
10. **Final QA** - briefly confirm final resolution, frame rate, duration, audio sync, caption placement, split-layout alignment, final loudness, no accidental silent tail, no accidental frozen/blank final frame, and that the supplied short's original spoken structure was preserved.

## FINAL RULE

DO NOT TURN MY VIDEO INTO A DIFFERENT SHORT.

I have already prepared the short. The supplied short is the editorial foundation. Your job is to make THAT video look and sound professionally edited, visually dynamic, premium and ready to publish.

Do not search for another story inside the footage. Do not select alternate takes. Do not reconstruct my speech. Do not rearrange the narration. EDIT THE SHORT I GAVE YOU.
