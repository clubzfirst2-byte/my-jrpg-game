// @ts-check
// Rendering layer bootstrap. PixiJS is used only inside src/view (DESIGN.md 1.1, 1.5).
import { Application } from 'pixi.js';
import { computeResolution } from './resolution.js';

/**
 * Creates the PixiJS application with WebGL fixed as the backend.
 * The canvas is rendered at a small internal resolution and scaled up by an integer factor.
 * @param {HTMLElement} host
 * @param {number} targetHeight internal height candidate (DESIGN.md 2.1)
 */
export async function createRenderer(host, targetHeight) {
  const app = new Application();
  const res = currentResolution(targetHeight);
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

/** @param {number} targetHeight */
export function currentResolution(targetHeight) {
  const vv = window.visualViewport;
  const w = vv ? vv.width : window.innerWidth;
  const h = vv ? vv.height : window.innerHeight;
  return computeResolution(w, h, window.devicePixelRatio || 1, targetHeight);
}

/**
 * Re-applies the internal resolution (after rotation, resize or switching candidates).
 * @param {Application} app @param {number} targetHeight
 */
export function resizeRenderer(app, targetHeight) {
  const res = currentResolution(targetHeight);
  if (app.renderer.width !== res.width || app.renderer.height !== res.height) {
    app.renderer.resize(res.width, res.height);
  }
  applyCanvasSize(app, res);
  return res;
}

/**
 * @param {Application} app
 * @param {ReturnType<typeof computeResolution>} res
 */
function applyCanvasSize(app, res) {
  const style = app.canvas.style;
  style.width = `${res.cssCanvasWidth}px`;
  style.height = `${res.cssCanvasHeight}px`;
}
