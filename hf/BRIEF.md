# BRIEF – visual-run compositions (HyperFrames) for the 9:16 short "Claude Code plugins"

You build **one standalone HyperFrames composition per assigned run**. Everything is rendered locally, in code, 1080x1920 @ 60 fps.
Work ONLY inside `/home/user/viral-video-creator/hf/` (read-only: `kit/`, `fonts/`, `vendor/`, `../assets/`, `specs/`, `BRIEF.md`).
Your files: `hf/runs/<id>.html`, `hf/runs/<id>.events.json`, `hf/renders/<id>.mp4`, `hf/renders/<id>_sheet.png`, optional own assets `hf/assets_<id>/…`.
Never touch another agent's run files. Never `git commit`. Do not install system packages. No network at render time (only deterministic code).

## 0. Setup / commands

```bash
cd /home/user/viral-video-creator/hf && source env.sh
npx --no-install hyperframes lint runs/<id>.html           # fix every *error*; warnings: judge
npx --no-install hyperframes render . -c runs/<id>.html -o renders/<id>.mp4 -f 60 -q high -w 2   # ~20 fps with 4 workers; use -w 2 (other agents share 4 cores)
npx --no-install hyperframes snapshot --help               # key-frame PNGs for quick visual checks (cheap) – prefer this while iterating
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height,r_frame_rate -of csv=p=0 renders/<id>.mp4
```
Skills `hyperframes-core`, `hyperframes-animation`, `hyperframes-keyframes` exist (Skill tool) – read hyperframes-core first if you have not authored HyperFrames before.
Contract in one breath: standalone root `<div id="root" data-composition-id="<id>" data-start="0" data-duration="<seconds>" data-width="1080" data-height="1920">` directly in `<body>` (NO `<template>`);
ONE `gsap.timeline({paused:true})` registered at `window.__timelines["<id>"]`; deterministic only (no Date/Math.random/network/timers); GSAP from `../vendor/gsap.min.js`;
never tween a `.clip`; never pair a CSS initial `transform` with a GSAP tween of the same prop (use `gsap.set`/`fromTo`, or `xPercent`).
`data-duration` = the spec `duration_s` EXACTLY (e.g. 3.566667). The render MUST have exactly `frames` frames (check with ffprobe; if it is off by one, nudge duration by ±0.002 s and re-render).

## 1. Look ("luxury tech")  – non-negotiable
* One bright world: clean near-white space, floating white cards, premium UI, smooth camera, restrained depth, elegant shadows. Never cheap/gamer/neon/cartoon.
* Ground = radial near-white (center `#FFFFFF` at 50%/36%, edges `#F3F3F0`) – already in `kit/kit.css` (`#stage`). NO grid, NO glowing orbs, NO particles, NO dark background, no decorative noise.
* Floating objects get the 3-layer shadow: `.float` / `var(--shadow)` = `0 60px 120px rgba(24,24,32,.16), 0 24px 48px rgba(24,24,32,.10), 0 4px 10px rgba(24,24,32,.06)`.
* Radii: media cards 3% of their width; documents 40 px; tiles 72 px; phones/devices 84 px.
* Poppins everywhere (loaded in kit.css). Headline 96/700, subhead 52/700, body 30/400. **Nothing smaller than 30 px where a viewer must read it** (tiny decorative UI chrome that is NOT meant to be read may be smaller, but keep it to a minimum). Ink `#111111`; Clay fill `#D97757`; clay text on white `#B25730`; highlight band `#FBEEE8`; success `#34C759`; error/stamp `#FF3B30`.
* SHOW the action, do not label the narration. No generic label pills, no step chips, no rows of words restating the voice-over. Real UI > mock-up. Numbers the narrator says may be shown as big typographic counters.
* Scene density: sparse. ONE dominant subject + at most ONE secondary cue. Smooth, eased, deliberate motion – never frantic.
* No captions, no cover title, no logos of social platforms. (Captions/cover/CTA are added later by the assembler; keep your own text to what the visual needs.)

## 2. Canvas, layouts, safe zones
* **FULLVISUAL** (`layout:"FULLVISUAL"`): full-frame world. Keep ALL important content above **y = 1230**; main visual bottom edge ≈ 1200–1230. Captions will sit at y≈1267–1536 – never put important things there.
* **SPLIT** (`layout:"SPLIT"`): the assembler adds a rounded camera card (top edge y=1200) with the speaker's head popping up to y≈1110 over your graphic. Important graphic content only in **y = 40…900**, main element bottom edge ≈ 880–900. Add `class="split-fade"` to `<body>` and wrap `#world` in `<div id="world-mask">` so the world fades out from y=900 over ~160 px (see kit.css). Captions sit in y≈941–1114 – nothing important there.
* **Frame 0 of every run is already the clean landing state**: sharp, settled, readable, camera at rest. Hero element present at t=0 (its internal counter/typing may start later).
* r01 only: the cover title (white card, y≈262–603) is drawn over frame 0 → keep r01's important content BELOW y≈620 on frame 0 (it can move up afterwards).
* Hard cuts between runs: your first/last frames must be complete scenes (no fade from/to white).

## 3. World camera (kit/world.js)
```html
<link rel="stylesheet" href="../kit/kit.css"><script src="../vendor/gsap.min.js"></script><script src="../kit/world.js"></script>
<div id="stage"><div id="world"> …everything the camera moves… </div></div>
<script>
const tl = gsap.timeline({paused:true});
const cam = WorldKit.Camera(tl, {cx:540, cy:960, s:1});    // look-at point in world coords + zoom; screen centre = (540,960)
cam.glide(t, dur, {cx,cy,s});   // sine.inOut, scale change <= ~0.04
cam.step (t, {cx,cy,s});        // 0.5 s power3.inOut – begin ~0.25 s BEFORE the narrator names the next item
cam.push (t, dur, {cx,cy,s});   // 1.2–2.0 s power2.inOut, up to 1.6x
cam.pull (t, dur, {cx,cy,s});   // 1–2 s power2.inOut (reveal context)
cam.whip (t, {cx,cy,s});        // MAX ONE PER RUN: 0.45 s power3.in out + 0.6 s power3.out in; returns the midpoint time (peak speed)
WorldKit.dof(tl, '#card', 'focus'|'near'|'back'|'hidden', t, dur);  // focus: sharp/opaque; near: 14px/70%; back: 9px/40%
window.__timelines['<id>'] = tl;
</script>
```
* Motion blur on the WORLD is automatic and baked from the analytic camera speed (`sigma = 0.29·speed·0.75/60`, cap 40 px) and is exactly 0 on stationary frames – a blurred stationary frame is a bug. Do not add your own blur to #world.
* Depth of field: the element being discussed is sharp; neighbours may blur ≤14 px / dim ~30%; the previous hero falls back to ~9 px / 40% opacity. NEVER blur text the viewer needs to read.
* When a **product window is the main subject** the WORLD camera stays still; only a camera INSIDE the window moves (scale 1.15–1.4x, 0.4–0.7 s, power2.inOut – implement as transform on an inner wrapper).
* Named product introduction: official logo large and centred first, then reveal the actual UI.
* For things that are not world-camera moves (UI micro-animation, counters, typing, check draws) use plain GSAP tweens on your elements. Counters: tween a plain object's value and write textContent from an `onUpdate` – BUT note HyperFrames seeks the timeline, so `onUpdate` may not fire on seeks; the robust way is to pre-build each displayed value as stacked spans toggled with `tl.set(..., {opacity})` at exact times (or use `tl.call` + also set initial state). Verify with `snapshot`.

## 4. Assets you may use
`../assets/logos/claude_mark.svg` (official Claude spark), `claude_code_lockup.svg` (official "Claude Code" wordmark lockup, viewBox ~ 187x28.6 → use as `<img>`), `../assets/captures/*` (real screenshots).
github.com is BLOCKED in this environment (egress policy) – do not try to bypass. GitHub-style repo cards must be clearly **reconstructions** (custom graphic in our luxury style, generic repo/star glyph, no Octocat). Octicon star-fill path (MIT): `M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z`.
Other reachable public sites: code.claude.com, claude.com, anthropic.com, clipcash.systemskala.pl (use `node scripts/shot.mjs <url> <out.png> <w> <h>`; playwright-core is installed).

## 5. Events sidecar (for sound design) – REQUIRED
Write `runs/<id>.events.json` (times in seconds from run start, matching your timeline EXACTLY):
```json
{"run":"r02","events":[
 {"t":0.9,"type":"pop","note":"repo card lands"},            // pop = card/tile/device LANDING (dull soft pop) – only for a card that visibly lands/arrives with a settle
 {"t":1.4,"type":"click","note":"tap on Install"},          // click = button press / tap
 {"t0":2.0,"t1":2.8,"type":"typing","note":"keyword typed"}, // typing = key presses (soft), one per visible character burst
 {"t0":1.0,"t1":2.5,"type":"ticks","note":"data stream"},    // ticks = light tick stream for longer typing / data streaming
 {"t":3.1,"type":"chime","note":"confirmation check"},       // chime = answer / modal / confirmation
 {"t":2.2,"type":"whip","note":"midpoint of the whip = cam.whip() return value"}   // whoosh peak lands here. ONLY real whips.
]}
```
Rules: one SFX only for a meaningful VISIBLE event. No sounds for camera steps/pushes/glides, layout cuts, ordinary zooms, or merely because something appeared. At most 1 whip per run (whips allowed ONLY where your run spec says so).

## 6. QA you must do before reporting
1. `lint` clean (errors = 0).  2. Render, ffprobe: `nb_read_frames == frames`, 1080x1920, 60 fps.
3. Build a contact sheet: ≥12 frames incl. frame 0, every landing/hero state, mid-move frames (to see motion blur), last frame: e.g.
   `ffmpeg -v error -y -i renders/<id>.mp4 -vf "fps=4,scale=270:480,tile=8x3" -frames:v 1 renders/<id>_sheet.png` and LOOK at it (Read the PNG). Also view 2–3 frames at full res (readable text? shadows? safe zones? stationary frames sharp?).
4. Check: frame 0 = clean landing state; no frame blurred while the camera is stationary; text ≥30 px & unblurred when it matters; content inside the safe zone; timing hits the spoken words (see spec word times; the visual event should land on/just before the narrated word); last frame is a complete scene.
5. Fix, re-render, re-inspect. Only then report.

## 7. Report back (≤25 lines)
Per run: what it shows; source (real capture / reconstruction / custom graphic) and reference URLs; camera moves used (kind, start, duration) + whip midpoint if any; events JSON path; render path + frame count; any compromise. Do not paste code.
