// @ts-check
// Pause / resume around backgrounding, and WebGL context loss (DESIGN.md 2.3).

/**
 * @typedef {object} LifecycleHandlers
 * @property {(reason: 'background' | 'user') => void} onPause
 * @property {() => void} onContextLost
 * @property {() => void} onContextRestored
 * @property {() => void} onViewportChange
 */

/**
 * @param {HTMLCanvasElement} canvas
 * @param {LifecycleHandlers} h
 */
export function installLifecycle(canvas, h) {
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') h.onPause('background');
  });
  window.addEventListener('pagehide', () => h.onPause('background'));
  window.addEventListener('blur', () => h.onPause('background'));

  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault(); // allows the browser to restore the context
    h.onContextLost();
  });
  canvas.addEventListener('webglcontextrestored', () => h.onContextRestored());

  let pending = 0;
  const schedule = () => {
    cancelAnimationFrame(pending);
    pending = requestAnimationFrame(() => h.onViewportChange());
  };
  window.addEventListener('resize', schedule);
  window.addEventListener('orientationchange', schedule);
  window.visualViewport?.addEventListener('resize', schedule);
}
