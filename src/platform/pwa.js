// @ts-check
// P11.1: the service worker (offline play, home screen app) and how long the game takes to start.

/**
 * Registers sw.js (built by vite.config.js). Only in a production build, and not under test
 * automation (a cached old build would confuse tests) unless the page asks for it with ?sw=1.
 * @param {{ onUpdate: () => void }} hooks
 * @returns {boolean} whether registration was started
 */
export function registerServiceWorker(hooks) {
  const params = new URLSearchParams(window.location.search);
  const allowed = import.meta.env.PROD && 'serviceWorker' in navigator && (!navigator.webdriver || params.get('sw') === '1');
  if (!allowed) return false;
  const hadController = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.register('./sw.js', { scope: './' }).catch(() => {});
  // A new version took over while an older one was running: it is used from the next start.
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (hadController) hooks.onUpdate();
  });
  return true;
}

/**
 * How long the start took (ms since the page was requested): the page itself, the scripts, and
 * the game ready to play (art built, world made).
 * @param {number} readyAt performance.now() when the game was ready
 */
export function loadTiming(readyAt) {
  const nav = /** @type {PerformanceNavigationTiming | undefined} */ (performance.getEntriesByType('navigation')[0]);
  return {
    pageMs: nav ? Math.round(nav.responseEnd) : null,
    scriptsMs: nav ? Math.round(nav.domContentLoadedEventEnd) : null,
    readyMs: Math.round(readyAt),
    transferKb: nav ? Math.round((nav.transferSize ?? 0) / 1024) : null,
    fromCache: nav ? nav.transferSize === 0 : null,
  };
}
