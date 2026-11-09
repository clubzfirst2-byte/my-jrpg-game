import { describe, it, expect } from 'vitest';
import { Container, Sprite, Texture } from 'pixi.js';
import { WeatherView } from '../../src/view/weatherView.js';
import { CLOCK } from '../../src/game/env/weather.js';

// v1.0 iPhone perf: at night in the rain the view must not redo work that did not change.
// Counts what WeatherView does per frame with a fake renderer (no GPU in unit tests).

function setup({ hour = 23, weather = 'rain', objects = /** @type {[number, any][]} */ ([]) } = {}) {
  /** @type {any[]} */
  const renders = [];
  const app = /** @type {any} */ ({ renderer: { render: (/** @type {any} */ o) => renders.push(o) }, screen: { width: 1024, height: 472 } });
  const view = new WeatherView(app, () => new Sprite(Texture.WHITE), new Container());
  view.lightTex = Texture.WHITE; // the radial texture needs a DOM canvas
  const W = 8;
  const state = /** @type {any} */ ({
    events: [],
    enemies: [],
    orb: null,
    player: { x: 64, y: 64, z: 0 },
    map: { tileSize: 16, width: W, height: W, elev: new Array(W * W).fill(0) },
    env: { seed: 1, now: hour * CLOCK.hourMs, weatherOverride: weather, dry: [], cold: [], burning: [], objectAt: new Map(objects), strike: null, sparks: null },
  });
  let t = 0;
  const frame = (dt = 1 / 60) => {
    t += dt;
    view.update(state, { x: 0, y: 0 }, 2, null, t, dt);
  };
  return { view, state, renders, frame };
}

describe('weather view work per frame', () => {
  it('a still night in the rain draws the light map once, then reuses it', () => {
    const { view, renders, frame } = setup();
    for (let i = 0; i < 60; i++) frame();
    expect(view.lightOn).toBe(true);
    expect(view.rain.visible).toBe(true);
    expect(renders).toHaveLength(1);
    expect(view.stats).toMatchObject({ lightRenders: 1, lightSkips: 59 });
  });

  it('redraws the light map when the player moves, the hour changes or the screen resizes', () => {
    const { view, state, renders, frame } = setup();
    frame();
    state.player.x += 3;
    frame();
    expect(renders).toHaveLength(2);
    state.env.now = 19 * CLOCK.hourMs; // dusk: another ambient colour
    frame();
    expect(renders).toHaveLength(3);
    view.app.screen.width = 852;
    frame();
    expect(renders).toHaveLength(4);
    frame();
    expect(renders).toHaveLength(4);
  });

  it('a flickering campfire in view redraws every frame (the flicker is kept)', () => {
    const { renders, frame } = setup({ objects: [[2 * 8 + 3, { type: 'campfire' }]] });
    for (let i = 0; i < 10; i++) frame();
    expect(renders).toHaveLength(10);
  });

  it('a clear day uses no light map at all, and the map is redrawn when night returns', () => {
    const { view, state, renders, frame } = setup({ hour: 12, weather: 'clear' });
    frame();
    expect(view.lightOn).toBe(false);
    expect(renders).toHaveLength(0);
    state.env.now = 23 * CLOCK.hourMs;
    frame();
    frame();
    expect(renders).toHaveLength(1);
    state.env.now = 12 * CLOCK.hourMs;
    frame();
    state.env.now = 23 * CLOCK.hourMs;
    frame();
    expect(renders).toHaveLength(2);
  });

  it('rain moves its drops without re-rotating them or rebuilding the flash each frame', () => {
    const { view, frame } = setup();
    frame();
    const drops = view.drops.filter((d) => d.s.visible);
    expect(drops.length).toBe(Math.round(((1024 * 472) / 900) * 0.6));
    const y0 = drops.map((d) => d.y);
    let rotationWrites = 0;
    for (const d of drops) {
      let r = d.s.rotation;
      Object.defineProperty(d.s, 'rotation', {
        get: () => r,
        set: (v) => {
          rotationWrites++;
          r = v;
        },
        configurable: true,
      });
    }
    for (let i = 0; i < 30; i++) frame();
    expect(rotationWrites).toBe(0);
    expect(drops.some((d, i) => d.y !== y0[i])).toBe(true);
    expect(view.flash.visible).toBe(false);
    expect(view.stats.flashRebuilds).toBe(0);
  });

  it('a lightning flash builds its rect once and fades it by alpha', () => {
    const { view, state, frame } = setup({ weather: 'storm' });
    state.events.push({ type: 'lightning', tick: 1, x: 40, y: 40 });
    frame();
    const a0 = view.flash.alpha;
    frame();
    frame();
    expect(view.flash.visible).toBe(true);
    expect(view.flash.alpha).toBeLessThan(a0);
    expect(view.stats.flashRebuilds).toBe(1);
    for (let i = 0; i < 30; i++) frame();
    expect(view.flash.visible).toBe(false);
  });
});
