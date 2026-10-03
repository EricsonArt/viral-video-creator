/* World camera for HyperFrames compositions (deterministic - no Date/Math.random).
 *
 * The camera is stored in CSS variables on #world (--tx,--ty,--s) so every GSAP seek reproduces it exactly.
 * Motion blur is baked from the analytic speed of each camera move:
 *     sigma = 0.29 * speed * 0.75 / 60      (speed in screen px/s, capped at 40 px)
 * and is written to --mb only while the camera is actually moving (0 otherwise).
 *
 * Camera model: camera looks at world point (cx,cy) with zoom s; that point is drawn at the screen centre
 * (540,960) unless a different anchor is given.
 *
 *   const cam = Camera(tl, {cx:540, cy:700, s:1})      // landing state at t=0 (rest, sharp)
 *   cam.glide(t, dur, {cx,cy,s})                        // sine.inOut, |ds|<=0.04
 *   cam.step (t, {cx,cy,s})                             // 0.5 s power3.inOut (start ~0.25 s before the name is spoken)
 *   cam.push (t, dur, {cx,cy,s})                        // 1.2-2.0 s power2.inOut, up to 1.6x
 *   cam.pull (t, dur, {cx,cy,s})                        // 1-2 s power2.inOut
 *   cam.whip (t, {cx,cy,s}, {out:.45, in:.6, ...})     // power3.in out / power3.out in, ONE per run; returns midpoint time
 *   cam.moves                                           // log of every move (for the report / SFX alignment)
 */
(function () {
  const W = 1080, H = 1920;
  const SCREEN_CX = 540, SCREEN_CY = 960;
  const MB_CAP = 40;
  const SAMPLE_DT = 1 / 240;           // baked blur sampling (finer than the 60 fps frame grid)

  function Camera(tl, init, opts) {
    opts = opts || {};
    const ax = opts.ax == null ? SCREEN_CX : opts.ax;   // screen anchor
    const ay = opts.ay == null ? SCREEN_CY : opts.ay;
    const world = document.querySelector(opts.world || '#world');
    let cur = { cx: init.cx, cy: init.cy, s: init.s == null ? 1 : init.s };
    const moves = [];

    function toVars(c) {            // world->screen:  screen = (p - c) * s + anchor
      return { tx: ax - c.cx * c.s, ty: ay - c.cy * c.s, s: c.s };
    }
    function put(c) {
      const v = toVars(c);
      world.style.setProperty('--tx', v.tx.toFixed(3));
      world.style.setProperty('--ty', v.ty.toFixed(3));
      world.style.setProperty('--s', v.s.toFixed(5));
      world.style.setProperty('--mb', '0');
    }
    put(cur);

    function ease(name) { return gsap.parseEase(name); }

    // generic eased move cur -> to over [t, t+dur]
    function move(kind, t, dur, to, easeName) {
      const from = { cx: cur.cx, cy: cur.cy, s: cur.s };
      to = { cx: to.cx == null ? from.cx : to.cx, cy: to.cy == null ? from.cy : to.cy, s: to.s == null ? from.s : to.s };
      const e = ease(easeName);
      const fv = toVars(from), tv = toVars(to);
      // 1) the actual camera tween (GSAP property tween on CSS variables)
      tl.fromTo(world, { '--tx': fv.tx, '--ty': fv.ty, '--s': fv.s },
                       { '--tx': tv.tx, '--ty': tv.ty, '--s': tv.s, duration: dur, ease: easeName, immediateRender: false }, t);
      // 2) baked motion blur from analytic screen-space speed of the world centre point
      const pos = (p) => {            // screen position of the look-at target & of a corner -> max of both speeds
        const q = e(p);
        const c = { cx: from.cx + (to.cx - from.cx) * q, cy: from.cy + (to.cy - from.cy) * q, s: from.s + (to.s - from.s) * q };
        const v = toVars(c);
        return { x: v.tx, y: v.ty, s: v.s };
      };
      const n = Math.max(2, Math.ceil(dur / SAMPLE_DT));
      let peak = 0;
      for (let i = 0; i <= n; i++) {
        const p0 = Math.max(0, (i - 0.5) / n), p1 = Math.min(1, (i + 0.5) / n);
        const a = pos(p0), b = pos(p1);
        const dt = (p1 - p0) * dur;
        // translation speed + zoom speed (zoom moves the frame edge ~ (ds/s)*540px)
        const vt = Math.hypot(b.x - a.x, b.y - a.y) / dt;
        const vz = Math.abs(b.s - a.s) / dt * 540;
        const speed = vt + vz;
        let sigma = 0.29 * speed * 0.75 / 60;
        sigma = Math.min(MB_CAP, sigma);
        if (sigma < 0.15) sigma = 0;
        peak = Math.max(peak, sigma);
        const tt = t + (i / n) * dur;
        tl.set(world, { '--mb': sigma.toFixed(2) }, Math.max(0, tt - 1e-6));
      }
      tl.set(world, { '--mb': 0 }, t + dur + 1e-6);   // stationary frames are never blurred
      moves.push({ kind, t, dur, ease: easeName, from, to, peakBlurPx: +peak.toFixed(2) });
      cur = to;
    }

    const api = {
      moves,
      get state() { return { cx: cur.cx, cy: cur.cy, s: cur.s }; },
      glide(t, dur, to) { move('glide', t, dur, to, 'sine.inOut'); return t + dur; },
      step(t, to)       { move('step', t, 0.5, to, 'power3.inOut'); return t + 0.5; },
      push(t, dur, to)  { move('push', t, dur, to, 'power2.inOut'); return t + dur; },
      pull(t, dur, to)  { move('pull', t, dur, to, 'power2.inOut'); return t + dur; },
      // WHIP: outgoing power3.in to a far "overshoot" point, incoming power3.out onto the target. Max ONE per run.
      whip(t, to, o) {
        o = o || {};
        const dOut = o.out || 0.45, dIn = o.in || 0.6;
        const far = o.via || {
          cx: cur.cx + (to.cx - cur.cx) * 1.9, cy: cur.cy + (to.cy - cur.cy) * 1.9, s: cur.s };
        move('whip-out', t, dOut, far, 'power3.in');
        const mid = t + dOut;
        move('whip-in', mid, dIn, to, 'power3.out');
        api.lastWhipMid = mid;
        return mid;
      },
    };
    window.__camMoves = moves;
    return api;
  }

  // Depth of field helper: element in focus = sharp & opaque; background cards: up to 14px blur / 30% dim;
  // previous hero card falls back to 9px / 40% opacity.
  function dof(tl, el, state, t, dur) {
    const S = { focus: { b: 0, o: 1 }, near: { b: 14, o: 0.7 }, back: { b: 9, o: 0.4 }, hidden: { b: 0, o: 0 } }[state];
    tl.to(el, { filter: 'blur(' + S.b + 'px)', opacity: S.o, duration: dur == null ? 0.5 : dur, ease: 'sine.inOut' }, t);
  }

  window.WorldKit = { Camera, dof, W, H };
})();
