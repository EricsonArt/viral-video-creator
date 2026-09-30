/* Shared helpers for the visual runs.
   Camera keys live in <script type="application/json" id="camkeys"> so the
   motion-blur pass (Python) reads the exact same camera path. */
(function () {
  const W = {};

  W.readCam = function () {
    return JSON.parse(document.getElementById("camkeys").textContent);
  };

  // Deterministic camera: fromTo tweens on CSS variables of .world (no callbacks).
  W.camera = function (tl, worldSel, cam) {
    const world = document.querySelector(worldSel);
    world.style.setProperty("--ax", cam.anchor[0]);
    world.style.setProperty("--ay", cam.anchor[1]);
    const k0 = cam.keys[0];
    gsap.set(world, { "--cx": k0.cx, "--cy": k0.cy, "--s": k0.s });
    tl.set(world, { "--cx": k0.cx, "--cy": k0.cy, "--s": k0.s }, 0);
    let prev = k0;
    for (let i = 1; i < cam.keys.length; i++) {
      const k = cam.keys[i];
      tl.fromTo(world,
        { "--cx": prev.cx, "--cy": prev.cy, "--s": prev.s },
        { "--cx": k.cx, "--cy": k.cy, "--s": k.s, duration: k.d, ease: k.ease, immediateRender: false },
        k.t);
      prev = k;
    }
  };

  // Depth of field: push a card back (blur + dim) or bring it into focus.
  W.defocus = function (tl, sel, t, blur, opacity, dur) {
    tl.fromTo(sel, { filter: "blur(0px)", opacity: 1 },
      { filter: "blur(" + blur + "px)", opacity: opacity, duration: dur || 0.5, ease: "power2.inOut", immediateRender: false }, t);
  };

  W.checkSVG = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>';

  // Polish thousands formatting: 1 246 870
  W.fmt = function (n) {
    return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  };

  window.W = W;
})();
