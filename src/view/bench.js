// @ts-check
// Load test for measurement only (not gameplay): N bouncing sprites to probe draw throughput.
import { Container, Graphics, Sprite } from 'pixi.js';

export const MAX_BENCH_SPRITES = 20000;

export class Bench {
  /** @param {import('pixi.js').Application} app */
  constructor(app) {
    this.app = app;
    this.layer = new Container();
    this.layer.label = 'bench';
    app.stage.addChild(this.layer);

    const g = new Graphics();
    // 16x16 placeholder "character" in the shared palette.
    g.rect(4, 0, 8, 6).fill(0xf2d3ab);
    g.rect(2, 6, 12, 7).fill(0x3d7dca);
    g.rect(3, 13, 4, 3).fill(0x5a3a29);
    g.rect(9, 13, 4, 3).fill(0x5a3a29);
    this.texture = app.renderer.generateTexture({ target: g, resolution: 1 });
    this.texture.source.scaleMode = 'nearest';
    g.destroy();

    /** @type {Sprite[]} */
    this.sprites = [];
    this.vx = new Float32Array(MAX_BENCH_SPRITES);
    this.vy = new Float32Array(MAX_BENCH_SPRITES);
  }

  get count() {
    return this.sprites.length;
  }

  /** @param {number} n */
  setCount(n) {
    const target = Math.max(0, Math.min(MAX_BENCH_SPRITES, Math.round(n)));
    const { width, height } = this.app.screen;
    while (this.sprites.length < target) {
      const i = this.sprites.length;
      const s = new Sprite(this.texture);
      s.x = Math.random() * (width - 16);
      s.y = Math.random() * (height - 16);
      const angle = Math.random() * Math.PI * 2;
      const speed = 30 + Math.random() * 90; // px per second
      this.vx[i] = Math.cos(angle) * speed;
      this.vy[i] = Math.sin(angle) * speed;
      this.layer.addChild(s);
      this.sprites.push(s);
    }
    while (this.sprites.length > target) {
      this.sprites.pop()?.destroy();
    }
  }

  /** @param {number} dtSec */
  update(dtSec) {
    const dt = Math.min(dtSec, 0.1);
    const maxX = this.app.screen.width - 16;
    const maxY = this.app.screen.height - 16;
    const { vx, vy, sprites } = this;
    for (let i = 0; i < sprites.length; i++) {
      const s = sprites[i];
      let x = s.x + vx[i] * dt;
      let y = s.y + vy[i] * dt;
      if (x < 0 || x > maxX) {
        vx[i] = -vx[i];
        x = Math.max(0, Math.min(maxX, x));
      }
      if (y < 0 || y > maxY) {
        vy[i] = -vy[i];
        y = Math.max(0, Math.min(maxY, y));
      }
      s.x = x;
      s.y = y;
    }
  }
}
