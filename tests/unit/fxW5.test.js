import { describe, it, expect } from 'vitest';
import { Texture } from 'pixi.js';
import { objectShadow, characterShadow, SHADOW } from '../../src/view/shadows.js';
import { HOUSE_WINDOWS, HOUSE_SIZE, windowGlow, hasWindows } from '../../src/view/houseWindows.js';
import { ambientKinds, AmbientParticles, AMBIENT, MIST_DAWN, MIST_ALPHA } from '../../src/view/ambientParticles.js';
import { HitFx, fxFor, FX_POOL } from '../../src/view/hitFx.js';
import { RAIN, rainLayer } from '../../src/view/weatherView.js';
import { fxVersion } from '../../src/view/fxSwitch.js';
import { ambientAt, CLOCK } from '../../src/game/env/weather.js';

// gfx W5: light, shadow and effects — the pure parts and the pools.

describe('cast shadows (light from the upper left)', () => {
  it('lean to the lower right of what casts them; tall things cast longer ones', () => {
    const tree = objectShadow('tree', 32, 48);
    const rock = objectShadow('rock', 16, 12);
    expect(tree.dx).toBeGreaterThan(0);
    expect(rock.dx).toBeGreaterThan(0);
    expect(tree.w).toBeGreaterThan(32);
    expect(tree.w / 32).toBeGreaterThan(rock.w / 16);
    expect(tree.h).toBeLessThan(tree.w); // flat on the ground
    expect(tree.alpha).toBe(SHADOW.tall);
  });
  it('flat things cast none', () => {
    for (const t of ['mat', 'stairs', 'door', 'plate']) expect(objectShadow(t, 16, 16)).toBe(null);
  });
  it('characters: a small one under the feet, at least 8 px wide', () => {
    const c = characterShadow(4);
    expect(c.w).toBe(8);
    expect(characterShadow(32).w).toBeLessThan(32);
    expect(characterShadow(32).dx).toBeGreaterThan(0);
    expect(characterShadow(16).dy).toBeGreaterThan(0); // (below the feet: a slime's squat body does not hide it)
  });
});

describe('lit windows', () => {
  it('two panes inside the release house, above its feet', () => {
    for (const w of HOUSE_WINDOWS) {
      expect(w.x).toBeGreaterThanOrEqual(-HOUSE_SIZE.w / 2);
      expect(w.x + w.w).toBeLessThanOrEqual(HOUSE_SIZE.w / 2);
      expect(w.y).toBeLessThan(0);
      expect(-w.y).toBeLessThanOrEqual(HOUSE_SIZE.h);
    }
    expect(hasWindows({ width: 48, height: 56 })).toBe(true);
    expect(hasWindows({ width: 16, height: 16 })).toBe(false); // (the placeholder house has none)
  });
  it('off by day, on at night, coming on at dusk', () => {
    const at = (h) => windowGlow(ambientAt(h * CLOCK.hourMs, 'clear'));
    expect(at(12)).toBe(0);
    expect(at(23)).toBe(1);
    expect(at(19)).toBeGreaterThan(0);
  });
});

describe('ambient particles', () => {
  const base = { region: 'plains', season: 'summer', dark: false, day: true, weather: 'clear', indoor: false, nearWater: false, snowGround: false };
  it('leaves in the forest and in autumn; not in rain or winter', () => {
    expect(ambientKinds({ ...base, region: 'forest' }).leaves).toBe(AMBIENT.leaves);
    expect(ambientKinds({ ...base, season: 'autumn' }).leaves).toBe(AMBIENT.leaves);
    expect(ambientKinds(base).leaves).toBe(0);
    expect(ambientKinds({ ...base, region: 'forest', weather: 'rain' }).leaves).toBe(0);
    expect(ambientKinds({ ...base, region: 'forest', season: 'winter' }).leaves).toBe(0);
  });
  it('dust motes in clear daylight; fireflies at night by water; sparkles on snow; nothing indoors', () => {
    expect(ambientKinds(base).motes).toBe(AMBIENT.motes);
    expect(ambientKinds({ ...base, day: false }).motes).toBe(0);
    expect(ambientKinds({ ...base, day: false, dark: true, nearWater: true }).fireflies).toBe(AMBIENT.fireflies);
    expect(ambientKinds({ ...base, day: false, dark: true, nearWater: false }).fireflies).toBe(0);
    expect(ambientKinds({ ...base, season: 'winter' }).sparkles).toBe(AMBIENT.sparkles);
    expect(ambientKinds({ ...base, snowGround: true }).sparkles).toBe(AMBIENT.sparkles);
    const inside = ambientKinds({ ...base, indoor: true, region: 'forest' });
    expect(inside.leaves + inside.motes + inside.fireflies + inside.sparkles).toBe(0);
  });
  it('a fixed pool: never more sprites than made at the start, however long it runs', () => {
    const p = new AmbientParticles(Texture.WHITE);
    const sprites = p.under.children.length + p.glow.children.length;
    const kinds = ambientKinds({ ...base, region: 'forest', season: 'autumn' });
    const view = { x: 0, y: 0, w: 400, h: 200 };
    for (let i = 0; i < 600; i++) p.update({ ...kinds, fireflies: AMBIENT.fireflies, sparkles: AMBIENT.sparkles }, view, () => true, i / 60, 1 / 60);
    expect(p.under.children.length + p.glow.children.length).toBe(sprites);
    expect(p.visible).toBeLessThanOrEqual(AMBIENT.max + AMBIENT.fireflies);
    // everything shown is in (or near) the view
    for (const m of p.pool) if (m.s.visible) expect(m.x).toBeGreaterThan(-30);
  });
});

describe('hit effects', () => {
  it('a burst of sparks (and a ring) for a hit, a parry, a defeat; nothing for other events', () => {
    expect(fxFor({ type: 'hitEnemy' }).sparks).toBeGreaterThan(3);
    expect(fxFor({ type: 'parry' }).ring).toBeGreaterThan(fxFor({ type: 'hitEnemy' }).ring);
    expect(fxFor({ type: 'swing' })).toBe(null);
  });
  it('plays over several frames from a fixed pool, then goes out', () => {
    const fx = new HitFx(Texture.WHITE);
    const sprites = fx.layer.children.length;
    expect(sprites).toBe(FX_POOL.sparks + FX_POOL.rings);
    fx.takeEvents({ tick: 5, events: [{ type: 'hitEnemy', tick: 5, x: 50, y: 50 }, { type: 'swing', tick: 5 }] });
    fx.update(1 / 60);
    const lit = fx.active;
    expect(lit).toBe(fxFor({ type: 'hitEnemy' }).sparks + 1);
    // the same events are not shown twice
    fx.takeEvents({ tick: 6, events: [{ type: 'hitEnemy', tick: 5, x: 50, y: 50 }] });
    fx.update(1 / 60);
    expect(fx.active).toBe(lit);
    let frames = 1;
    while (fx.active > 0 && frames < 100) {
      fx.update(1 / 60);
      frames++;
    }
    expect(frames).toBeGreaterThan(5); // several frames, not 1–2
    expect(fx.active).toBe(0);
    // a storm of hits reuses the pool
    for (let t = 10; t < 60; t++) fx.takeEvents({ tick: t, events: [{ type: 'enemyDown', tick: t, x: 0, y: 0 }] });
    expect(fx.layer.children.length).toBe(sprites);
  });
});

describe('hit effects: where', () => {
  it('a boss stunned by a parry (the event names it, no place) bursts on the boss; an unknown one shows nothing', () => {
    const fx = new HitFx(Texture.WHITE);
    const enemies = [{ bossId: 'root', x: 300, y: 200 }];
    fx.takeEvents({ tick: 3, enemies, events: [{ type: 'bossStun', tick: 3, id: 'root' }] });
    fx.update(0);
    expect(fx.active).toBe(fxFor({ type: 'bossStun' }).sparks + 1);
    const ring = fx.rings.find((r) => r.s.visible);
    expect(ring.s.x).toBe(300);
    expect(ring.s.y).toBe(200 - fxFor({ type: 'bossStun' }).y);
    const none = new HitFx(Texture.WHITE);
    none.takeEvents({ tick: 3, enemies, events: [{ type: 'bossStun', tick: 3, id: 'gone' }] });
    none.takeEvents({ tick: 4, events: [{ type: 'bossStun', tick: 4, id: 'root' }] });
    none.update(0);
    expect(none.active).toBe(0);
  });
});

describe('rain', () => {
  it('two layers of streaks: near ones longer, brighter and faster than far ones', () => {
    expect(RAIN.near.h).toBeGreaterThan(RAIN.far.h);
    expect(RAIN.near.alpha).toBeGreaterThan(RAIN.far.alpha);
    expect(RAIN.near.speed).toBeGreaterThan(RAIN.far.speed);
    expect(RAIN.sky.r).toBeLessThan(1); // a darker sky
  });
});

describe('the switch back to the look before (fxSwitch.js)', () => {
  const p = (/** @type {string} */ q) => new URLSearchParams(q);
  it('on by default; ?fx=v1 or ?v2=0 turns every effect off; ?fx=v2 keeps them with ?v2=0', () => {
    expect(fxVersion(p(''))).toBe('v2');
    expect(fxVersion(p('map=world&time=21'))).toBe('v2');
    expect(fxVersion(p('fx=v1'))).toBe('v1');
    expect(fxVersion(p('v2=0'))).toBe('v1');
    expect(fxVersion(p('v2=0&fx=v2'))).toBe('v2');
    expect(fxVersion(p('fx=other'))).toBe('v2');
    expect(fxVersion(p('v2=1'))).toBe('v2');
  });
  it('v1 rain: every drop is the one old layer (5 px, one speed)', () => {
    for (let i = 0; i < 9; i++) expect(rainLayer(i, false)).toBe(RAIN.v1);
    expect(RAIN.v1).toEqual({ h: 5, alpha: 0.55, speed: 1, tint: 0xb8d0ff });
    expect(rainLayer(0, true)).toBe(RAIN.near);
    expect(rainLayer(1, true)).toBe(RAIN.far);
    // most drops are far ones
    let near = 0;
    for (let i = 0; i < 90; i++) if (rainLayer(i, true) === RAIN.near) near++;
    expect(near).toBe(90 / RAIN.nearEvery);
  });
});

describe('mist', () => {
  const base = { region: 'plains', season: 'summer', dark: false, day: true, weather: 'clear', indoor: false, nearWater: false, snowGround: false };
  it('in the rain and at dawn; not at noon, indoors, in snow or over the desert', () => {
    expect(ambientKinds({ ...base, weather: 'rain' }).mist).toBe(AMBIENT.mist);
    expect(ambientKinds({ ...base, weather: 'storm' }).mist).toBe(AMBIENT.mist);
    expect(ambientKinds({ ...base, hour: 6 }).mist).toBe(AMBIENT.mist);
    expect(ambientKinds({ ...base, hour: MIST_DAWN.to }).mist).toBe(0);
    expect(ambientKinds({ ...base, hour: 12 }).mist).toBe(0);
    expect(ambientKinds(base).mist).toBe(0);
    expect(ambientKinds({ ...base, hour: 6, weather: 'snow' }).mist).toBe(0);
    expect(ambientKinds({ ...base, hour: 6, region: 'desert' }).mist).toBe(0);
    expect(ambientKinds({ ...base, hour: 6, indoor: true }).mist).toBe(0);
  });
  it('a few faint patches from a fixed pool (the fill they cost is bounded)', () => {
    expect(AMBIENT.mist).toBeLessThanOrEqual(6);
    expect(MIST_ALPHA).toBeLessThanOrEqual(0.25);
    const p = new AmbientParticles(Texture.WHITE, Texture.WHITE);
    const sprites = p.under.children.length;
    expect(p.mistPool.length).toBe(AMBIENT.mist);
    const kinds = ambientKinds({ ...base, weather: 'rain' });
    const view = { x: 100, y: 50, w: 340, h: 160 };
    let area = 0;
    for (let i = 0; i < 900; i++) {
      p.update(kinds, view, () => false, i / 60, 1 / 60);
      for (const m of p.mistPool) {
        expect(m.s.alpha).toBeLessThanOrEqual(MIST_ALPHA);
        expect(m.s.alpha).toBeGreaterThanOrEqual(0);
      }
    }
    for (const m of p.mistPool) area += m.s.width * m.s.height;
    expect(area).toBeLessThan(view.w * view.h * 0.6); // well under one screen of extra fill
    expect(p.under.children.length).toBe(sprites);
    expect(p.visible).toBe(AMBIENT.mist); // (rain: no leaves, motes or sparkles)
    // it clears when the rain stops
    p.update(ambientKinds(base), view, () => false, 20, 1 / 60);
    for (const m of p.mistPool) expect(m.s.visible).toBe(false);
  });
});

describe('drawing only', () => {
  it('the effects read the game state and never change it (nothing to save)', () => {
    const state = { tick: 9, events: [{ type: 'hitEnemy', tick: 9, x: 10, y: 20 }, { type: 'parry', tick: 9, x: 1, y: 2 }, { type: 'hurt', tick: 8, x: 3, y: 4 }] };
    const before = JSON.stringify(state);
    const fx = new HitFx(Texture.WHITE);
    fx.takeEvents(state);
    for (let i = 0; i < 30; i++) fx.update(1 / 60);
    expect(JSON.stringify(state)).toBe(before);
  });
  it('pools are bounded: sparks, rings, particles, splashes', () => {
    expect(FX_POOL.sparks).toBeLessThanOrEqual(64);
    expect(FX_POOL.rings).toBeLessThanOrEqual(8);
    expect(AMBIENT.max + AMBIENT.fireflies + AMBIENT.mist).toBeLessThanOrEqual(64);
    expect(AMBIENT.leaves + AMBIENT.motes + AMBIENT.sparkles).toBeLessThanOrEqual(AMBIENT.max + 4);
    expect(RAIN.splashes).toBeLessThanOrEqual(32);
  });
});
