// @ts-check
// Rendering layer bootstrap. PixiJS is used only inside src/view (DESIGN.md 1.1, 1.5).
import { Application, Graphics, TilingSprite } from 'pixi.js';

/**
 * Creates the PixiJS application with WebGL fixed as the backend.
 * @param {HTMLElement} host
 */
export async function createRenderer(host) {
  const app = new Application();
  await app.init({
    preference: 'webgl', // WebGPU / Canvas fallback are intentionally not managed (DESIGN.md 1.5)
    resizeTo: window,
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
  return app;
}

/**
 * P0 test pattern: a tiled checker floor so scaling and texture upload can be eyeballed.
 * @param {Application} app
 */
export function addTestFloor(app) {
  const g = new Graphics();
  g.rect(0, 0, 16, 16).fill(0x2c3e50);
  g.rect(16, 0, 16, 16).fill(0x34495e);
  g.rect(0, 16, 16, 16).fill(0x34495e);
  g.rect(16, 16, 16, 16).fill(0x2c3e50);
  const texture = app.renderer.generateTexture({ target: g, resolution: 1 });
  texture.source.scaleMode = 'nearest';
  g.destroy();
  const floor = new TilingSprite({ texture, width: app.screen.width, height: app.screen.height });
  floor.label = 'test-floor';
  app.stage.addChild(floor);
  app.renderer.on('resize', (w, h) => {
    floor.width = w;
    floor.height = h;
  });
  return floor;
}
