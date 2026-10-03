/* Shared "world camera" helpers for HyperFrames compositions (seek-safe: everything is a GSAP tween). */
const HFW = (function () {
  const K = 0.29 * 0.75 / 60;     // sigma = 0.29 * speed * 0.75 / 60   (speed in px/s)
  const CAP = 40;                 // motion-blur sigma cap (px)
  const OFF = 200;                // stage bleeds 200px beyond the canvas so blur has real pixels at the edges
  let tl, cx = 540, cy = 960, cur = { x: 540, y: 960, s: 1 };
  const tf = (c) => ({ x: cx + OFF - c.x * c.s, y: cy + OFF - c.y * c.s, scale: c.s });
  function init(timeline, o) {
    tl = timeline; cx = o.cx; cy = o.cy; cur = Object.assign({}, o.cam);
    gsap.set('#world', Object.assign({ transformOrigin: '0 0' }, tf(cur)));
    gsap.set('#mbf', { attr: { stdDeviation: '0.0001 0.0001' } });
  }
  function deriv(e) { return (p) => { const h = 1e-3, a = Math.max(0, p - h), b = Math.min(1, p + h); return (e(b) - e(a)) / (b - a); }; }
  function profile(easeName) {
    const e = gsap.parseEase(easeName), d = deriv(e); let mx = 0;
    for (let i = 0; i <= 400; i++) mx = Math.max(mx, d(i / 400));
    return { mx, bell: (p) => Math.max(0, d(p)) / mx };
  }
  /* camera move: world point (x,y) lands on screen centre (cx,cy) at scale s. */
  function cam(t0, dur, to, easeName) {
    const A = tf(cur), B = tf(to), pr = profile(easeName);
    const vx = Math.abs(B.x - A.x) / dur * pr.mx, vy = Math.abs(B.y - A.y) / dur * pr.mx;
    const vz = Math.abs(to.s - cur.s) * 650 / dur * pr.mx;       // zoom contributes radial motion
    const sx = Math.min(CAP, K * (vx + vz)), sy = Math.min(CAP, K * (vy + vz));
    tl.to('#world', { x: B.x, y: B.y, scale: B.scale, duration: dur, ease: easeName }, t0);
    tl.fromTo('#mbf', { attr: { stdDeviation: '0.0001 0.0001' } },
      { attr: { stdDeviation: sx.toFixed(3) + ' ' + sy.toFixed(3) }, duration: dur, ease: pr.bell, immediateRender: false }, t0);
    cur = Object.assign({}, to);
    return { sx, sy };
  }
  /* WHIP: 0.45s out (power3.in) + 0.6s in (power3.out). The world jumps at the midpoint, where blur is at its peak. */
  function whip(t0, dir, far, to) {
    const mid = { x: cur.x + dir[0] * far, y: cur.y + dir[1] * far, s: cur.s };
    cam(t0, 0.45, mid, 'power3.in');
    const start = { x: to.x - dir[0] * far, y: to.y - dir[1] * far, s: to.s };
    tl.set('#world', tf(start), t0 + 0.45);
    cur = start;
    cam(t0 + 0.45, 0.6, to, 'power3.out');
    return t0 + 0.45;      // whip midpoint
  }
  const STATE = { active: { blur: 0, opacity: 1 }, near: { blur: 10, opacity: 0.7 }, prev: { blur: 9, opacity: 0.4 }, far: { blur: 14, opacity: 0.7 } };
  function focus(sel, t, st, dur) {
    const s = STATE[st];
    tl.to(sel, { filter: 'blur(' + s.blur + 'px)', opacity: s.opacity, duration: dur == null ? 0.5 : dur, ease: 'sine.inOut' }, t);
  }
  function setFocus(sel, st) { const s = STATE[st]; gsap.set(sel, { filter: 'blur(' + s.blur + 'px)', opacity: s.opacity }); }
  function spark(size, fill) {
    const R = 50, lens = [1, .66, .92, .6, 1, .7, .94, .62, 1, .68, .9, .6], ang = [0, 31, 59, 91, 121, 150, 181, 211, 240, 271, 300, 330];
    let g = ''; for (let i = 0; i < 12; i++) { const L = lens[i] * R, w = 7.4; g += '<rect x="' + (-w) + '" y="' + (-L) + '" width="' + (2 * w) + '" height="' + L + '" rx="' + w + '" transform="rotate(' + ang[i] + ')"/>'; }
    return '<svg viewBox="-55 -55 110 110" width="' + size + '" height="' + size + '"><g fill="' + fill + '">' + g + '<circle r="9"/></g></svg>';
  }
  return { init, cam, whip, focus, setFocus, spark, tf, get cur() { return cur; } };
})();
