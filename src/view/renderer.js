// @ts-check
// Rendering layer bootstrap. PixiJS is used only inside src/view (DESIGN.md 1.1, 1.5).
import { Application } from 'pixi.js';
import { computeView } from './resolution.js';

/**
 * Creates the PixiJS application with WebGL fixed as the backend.
 * The canvas is rendered at a small internal resolution and scaled up by an integer factor.
 * @param {HTMLElement} host
 * @param {number} targetHeight internal height candidate (DESIGN.md 2.1)
 * @param {number} [artDensity] canvas (art) pixels per game pixel (P11.5; see computeResolution)
 * @param {ViewOptions} [opts] scale mode ('fit' | 'int') and the art densities on screen (computeView)
 */
export async function createRenderer(host, targetHeight, artDensity = 1, opts = {}) {
  const app = new Application();
  const res = currentResolution(targetHeight, artDensity, opts);
  await app.init({
    preference: 'webgl', // WebGPU / Canvas fallback are intentionally not managed (DESIGN.md 1.5)
    width: res.width,
    height: res.height,
    background: '#16202c',
    antialias: false,
    resolution: 1,
    autoDensity: false,
    roundPixels: true,
    powerPreference: 'high-performance',
  });
  if (app.renderer.name !== 'webgl') {
    throw new Error(`WebGL renderer required, got "${app.renderer.name}"`);
  }
  app.canvas.id = 'game-canvas';
  host.appendChild(app.canvas);
  applyCanvasSize(app, res);
  return app;
}

/** @typedef {{ mode?: import('./resolution.js').ScaleMode, artDensities?: readonly number[] }} ViewOptions */

/** @param {number} targetHeight @param {number} [artDensity] @param {ViewOptions} [opts] */
export function currentResolution(targetHeight, artDensity = 1, opts = {}) {
  const vv = window.visualViewport;
  const w = vv ? vv.width : window.innerWidth;
  const h = vv ? vv.height : window.innerHeight;
  return computeView(w, h, window.devicePixelRatio || 1, targetHeight, { ...opts, canvasDensity: artDensity });
}

/**
 * Re-applies the internal resolution (after rotation, resize or switching candidates).
 * @param {Application} app @param {number} targetHeight @param {number} [artDensity] @param {ViewOptions} [opts]
 */
export function resizeRenderer(app, targetHeight, artDensity = 1, opts = {}) {
  const res = currentResolution(targetHeight, artDensity, opts);
  if (app.renderer.width !== res.width || app.renderer.height !== res.height) {
    app.renderer.resize(res.width, res.height);
  }
  applyCanvasSize(app, res);
  return res;
}

/**
 * @param {Application} app
 * @param {ReturnType<typeof computeView>} res
 */
function applyCanvasSize(app, res) {
  const style = app.canvas.style;
  style.width = `${res.cssCanvasWidth}px`;
  style.height = `${res.cssCanvasHeight}px`;
  if (res.cssLeft === null || res.cssTop === null) {
    // 'fit': centred by the stylesheet (translate(-50%, -50%)), exactly as before
    style.left = style.top = style.transform = '';
    app.canvas.dataset.scale = 'fit';
  } else {
    // 'int': placed on whole device pixels so every canvas pixel lands on the device grid
    style.left = `${res.cssLeft}px`;
    style.top = `${res.cssTop}px`;
    style.transform = 'none';
    app.canvas.dataset.scale = 'int';
  }
}
