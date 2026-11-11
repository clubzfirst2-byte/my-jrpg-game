import { describe, it, expect } from 'vitest';
import { Texture } from 'pixi.js';
import { objectShadow, characterShadow, shadowMask, weatherShadow, SHADOW, HOUSE_SHADOW } from '../../src/view/shadows.js';
import { HOUSE_WINDOWS, HOUSE_SIZE, PANE_AREA, WINDOW_GLOW, HOUSE_GLASS, windowGlow, hasWindows, glassKind, paneImage, paneImageFromTable, windowLightSpots } from '../../src/view/houseWindows.js';
import { readFileSync } from 'node:fs';
import { inflateSync } from 'node:zlib';
import { ambientKinds, AmbientParticles, AMBIENT, MIST_DAWN, MIST_ALPHA, MIST_BANDS, mistBand } from '../../src/view/ambientParticles.js';
import { HitFx, fxFor, FX_POOL, RING_FRAMES, SPARK_STEPS, ringPixels, ringPixelsInOrder, sparkStep } from '../../src/view/hitFx.js';
import { packShelf, ATLAS_SIZE } from '../../src/view/pixelAtlas.js';
import { rimAlpha, RIM_FLASH } from '../../src/view/flashOverlay.js';
import { RAIN, rainLayer, splashTexture } from '../../src/view/weatherView.js';
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
    const p = new AmbientParticles(Texture.WHITE, [Texture.WHITE]);
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
    expect(RAIN.splashes).toBeLessThanOrEqual(48);
  });
});

// --- inspection round 1 (pixel art, weather, windows, rings) ---

/** The widths of the runs of equal values along a row (a step narrower than 1 game px cannot exist on a 1-texel-per-px mask, but runs show the steps are flat). */
const runs = (/** @type {number[]} */ row) => {
  const out = [];
  let n = 1;
  for (let i = 1; i <= row.length; i++) {
    if (i < row.length && row[i] === row[i - 1]) n++;
    else {
      out.push(n);
      n = 1;
    }
  }
  return out;
};

describe('shadows as pixel art', () => {
  it('an oval in at most 3 flat steps, one texel per game px, darker inside', () => {
    for (const g of [objectShadow('tree', 32, 48), objectShadow('rock', 16, 12), characterShadow(16)]) {
      const m = shadowMask(g);
      expect(m.w).toBe(Math.round(g.w));
      expect(m.h).toBe(Math.round(g.h));
      expect(Math.max(...m.data)).toBeLessThanOrEqual(3);
      expect(new Set(m.data).size).toBeLessThanOrEqual(4); // none + 3 steps
      const mid = [...m.data.slice(Math.floor(m.h / 2) * m.w, Math.floor(m.h / 2) * m.w + m.w)];
      expect(mid[Math.floor(m.w / 2)]).toBe(3);
      // from the edge to the centre the steps only go up
      for (let x = 1; x <= m.w / 2; x++) expect(mid[x]).toBeGreaterThanOrEqual(mid[x - 1]);
      expect(runs(mid).length).toBeLessThanOrEqual(7);
    }
    expect(SHADOW.steps).toHaveLength(4);
  });
  it('the house: a band along its right wall under the eave (stepped top) and one along its foot; nothing over its walls', () => {
    const g = objectShadow('house', HOUSE_SIZE.w, HOUSE_SIZE.h);
    expect(g.shape).toBe('house');
    const m = shadowMask(g);
    const x0 = Math.round(g.dx - g.w / 2);
    const y0 = Math.round(g.dy - g.h / 2);
    const at = (/** @type {number} */ gx, /** @type {number} */ gy) => m.data[(gy - y0) * m.w + (gx - x0)];
    // right of the wall, under the eave: shadow; the eave's corner steps down to the right
    expect(at(HOUSE_SHADOW.wallRight, -HOUSE_SHADOW.eave)).toBeGreaterThan(0);
    expect(at(HOUSE_SHADOW.wallRight + 3, -HOUSE_SHADOW.eave)).toBe(0);
    expect(at(HOUSE_SHADOW.wallRight + 3, -HOUSE_SHADOW.eave + 2)).toBeGreaterThan(0);
    // along the foot, below the house
    expect(at(0, 0)).toBe(3);
    expect(at(0, HOUSE_SHADOW.foot - 1)).toBe(1);
    // none over the house's own wall (it is drawn there)
    expect(at(0, -10)).toBe(0);
    expect(at(HOUSE_SHADOW.wallRight - 1, -10)).toBe(0);
    // the other house art (a placeholder of another size): an oval
    expect(objectShadow('house', 16, 16).shape).toBe('oval');
  });
  it('softer under clouds, rain and snow; out in a lightning flash', () => {
    expect(weatherShadow('clear')).toBe(1);
    expect(weatherShadow('cloudy')).toBeLessThan(1);
    expect(weatherShadow('rain')).toBeLessThan(weatherShadow('cloudy'));
    expect(weatherShadow('storm')).toBeLessThanOrEqual(weatherShadow('rain'));
    expect(weatherShadow('snow')).toBeLessThanOrEqual(weatherShadow('rain'));
    expect(weatherShadow('clear', true)).toBe(0);
    expect(weatherShadow('storm', true)).toBe(0);
  });
});

describe('lit windows: only the glass', () => {
  // a fake house (48×56 game px at 2 art px per game px): wall, a glint, a frame and glass in the windows
  const scale = 2;
  const W = HOUSE_SIZE.w * scale;
  const H = HOUSE_SIZE.h * scale;
  const px = new Uint8ClampedArray(W * H * 4);
  const put = (/** @type {number} */ x, /** @type {number} */ y, /** @type {number[]} */ c) => px.set([...c, 255], (y * W + x) * 4);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) put(x, y, [0xdd, 0xd0, 0xb4]); // plaster
  const ox = (HOUSE_SIZE.w / 2 + HOUSE_WINDOWS[0].x) * scale;
  const oy = (HOUSE_SIZE.h + HOUSE_WINDOWS[0].y) * scale;
  put(ox, oy, [0x26, 0x42, 0x5e]); // glass
  put(ox + 1, oy, [0x10, 0x1a, 0x2c]); // dark glass
  put(ox + 2, oy, [0x78, 0xa8, 0xcc]); // a glint
  put(ox + 3, oy, [0x6e, 0x44, 0x24]); // the frame
  it('glass is lit, glints, frames, flowers and walls are not', () => {
    expect(glassKind(0x26, 0x42, 0x5e, 255)).toBe(1);
    expect(glassKind(0x10, 0x1a, 0x2c, 255)).toBe(2);
    expect(glassKind(0x78, 0xa8, 0xcc, 255)).toBe(0);
    expect(glassKind(0xd6, 0xee, 0xfa, 255)).toBe(0);
    expect(glassKind(0x6e, 0x44, 0x24, 255)).toBe(0);
    expect(glassKind(0x3c, 0x8a, 0x3a, 255)).toBe(0); // leaves in the flower box
    expect(glassKind(0x26, 0x42, 0x5e, 0)).toBe(0);
  });
  it('the pane image keeps only those pixels, warm', () => {
    const img = paneImage(px, W, scale);
    expect(img.w).toBe(PANE_AREA.w * scale);
    expect(img.glass).toBe(2);
    const a = (/** @type {number} */ x) => img.data[x * 4 + 3];
    expect(a(0)).toBe(255);
    expect(a(1)).toBe(255);
    expect(a(2)).toBe(0); // the glint stays as drawn
    expect(a(3)).toBe(0); // and the frame
    expect((img.data[0] << 16) | (img.data[1] << 8) | img.data[2]).toBe(WINDOW_GLOW.glass);
  });
  it('their light falls on the ground in front, below the house (not on its wall)', () => {
    const spots = windowLightSpots(100, 200);
    expect(spots).toHaveLength(HOUSE_WINDOWS.length);
    for (const s of spots) {
      expect(s.y).toBeGreaterThan(200);
      expect(s.y - WINDOW_GLOW.radius).toBeGreaterThan(200 + HOUSE_WINDOWS[0].y + HOUSE_WINDOWS[0].h); // never reaches the windows
    }
  });
});

describe('hit effects as pixel art', () => {
  it('the ring: a 1-px circle on the grid, 4 frames growing, white to yellow', () => {
    for (const r of [3, 6, 9, 14]) {
      const p = ringPixels(r);
      for (const [x, y] of p) expect(Math.abs(Math.hypot(x, y) - r)).toBeLessThan(1);
      expect(new Set(p.map(([x, y]) => `${x},${y}`)).size).toBe(p.length);
      // closed: every pixel has a neighbour on the ring
      const has = new Set(p.map(([x, y]) => `${x},${y}`));
      for (const [x, y] of p) {
        let n = 0;
        for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) if ((dx || dy) && has.has(`${x + dx},${y + dy}`)) n++;
        expect(n).toBeGreaterThanOrEqual(2);
      }
    }
    expect(RING_FRAMES).toHaveLength(4);
    for (let i = 1; i < RING_FRAMES.length; i++) expect(RING_FRAMES[i].r).toBeGreaterThan(RING_FRAMES[i - 1].r);
    expect(RING_FRAMES[0].warm).toBe(0xffffff);
    expect(RING_FRAMES[3].warm & 0xff).toBeLessThan(0x80); // yellow at the end, not grey
  });
  it('sparks stay opaque white → yellow → orange until they go out', () => {
    expect(sparkStep(0).color).toBe(0xffffff);
    expect(sparkStep(0.99).color).toBe(SPARK_STEPS[2].color);
    const fx = new HitFx(Texture.WHITE);
    fx.takeEvents({ tick: 1, events: [{ type: 'hitEnemy', tick: 1, x: 10, y: 10 }] });
    for (let i = 0; i < 30; i++) {
      fx.update(1 / 60);
      for (const p of fx.sparks) if (p.s.visible) expect(p.s.alpha).toBe(1);
    }
  });
});

describe('mist as drawn bands', () => {
  it('long low bands in at most 3 flat steps, even sizes (on the pixel grid with a centred anchor)', () => {
    for (const { w, h } of MIST_BANDS) {
      expect(w % 2).toBe(0);
      expect(h % 2).toBe(0);
      expect(w).toBeGreaterThan(h * 5);
      const m = mistBand(w, h);
      expect(Math.max(...m)).toBe(3);
      expect(new Set(m).size).toBeLessThanOrEqual(4);
    }
  });
});

describe('the wind-up overlay as a rim (gfx W5)', () => {
  it('strong on a 1-game-px outline, faint inside, nothing outside', () => {
    const w = 8;
    const h = 8;
    const a = new Uint8ClampedArray(w * h);
    for (let y = 1; y < 7; y++) for (let x = 1; x < 7; x++) a[y * w + x] = 255;
    const r = rimAlpha(a, w, h, 2);
    expect(r[0]).toBe(0);
    expect(r[1 * w + 1]).toBe(Math.round(255 * RIM_FLASH.edge));
    expect(r[2 * w + 2]).toBe(Math.round(255 * RIM_FLASH.edge)); // (2 art px = 1 game px)
    expect(r[3 * w + 3]).toBe(Math.round(255 * RIM_FLASH.inside));
    expect(RIM_FLASH.inside).toBeLessThan(0.5);
  });
});

/** A minimal PNG reader (8-bit RGBA, not interlaced: the release art) for checking tables against the art. @param {string} path */
function readPng(path) {
  const buf = readFileSync(path);
  let pos = 8;
  let width = 0;
  let height = 0;
  const idat = [];
  while (pos < buf.length) {
    const len = buf.readUInt32BE(pos);
    const type = buf.toString('ascii', pos + 4, pos + 8);
    const body = buf.subarray(pos + 8, pos + 8 + len);
    if (type === 'IHDR') {
      width = body.readUInt32BE(0);
      height = body.readUInt32BE(4);
      expect([body[8], body[9], body[12]]).toEqual([8, 6, 0]); // 8-bit RGBA, no interlace
    } else if (type === 'IDAT') idat.push(body);
    pos += 12 + len;
  }
  const raw = inflateSync(Buffer.concat(idat));
  const bpp = 4;
  const stride = width * bpp;
  const out = new Uint8ClampedArray(width * height * 4);
  for (let y = 0; y < height; y++) {
    const f = raw[y * (stride + 1)];
    for (let x = 0; x < stride; x++) {
      const v = raw[y * (stride + 1) + 1 + x];
      const a = x >= bpp ? out[y * stride + x - bpp] : 0;
      const b = y > 0 ? out[(y - 1) * stride + x] : 0;
      const c = x >= bpp && y > 0 ? out[(y - 1) * stride + x - bpp] : 0;
      const p = a + b - c;
      const pr = Math.abs(p - a) <= Math.abs(p - b) && Math.abs(p - a) <= Math.abs(p - c) ? a : Math.abs(p - b) <= Math.abs(p - c) ? b : c;
      out[y * stride + x] = (v + [0, a, b, (a + b) >> 1, pr][f]) & 255;
    }
  }
  return { width, height, data: out };
}

describe('lit windows: the glass table matches the house art', () => {
  it('HOUSE_GLASS is what glassKind reads off src/art-release/objects/obj.house.png', () => {
    const png = readPng('src/art-release/objects/obj.house.png');
    expect([png.width, png.height]).toEqual([HOUSE_SIZE.w * 2, HOUSE_SIZE.h * 2]);
    const fromArt = paneImage(png.data, png.width, 2);
    const fromTable = paneImageFromTable();
    expect(fromTable.glass).toBe(fromArt.glass);
    expect(fromTable.glass).toBeGreaterThan(100);
    expect([...fromTable.data]).toEqual([...fromArt.data]);
    for (const t of HOUSE_GLASS) for (const row of t) expect(row).toMatch(/^[.gd]{14}$/);
  });
});

// --- inspection round 2 (finishing): rings on dirt, crown splashes, orange pools, one atlas ---

describe('finishing touches', () => {
  it('the ring stays fully opaque in every frame; the last is dotted (every other pixel, around it)', () => {
    for (const f of RING_FRAMES) expect(f.alpha).toBe(1);
    expect(RING_FRAMES.map((f) => f.dotted)).toEqual([false, false, false, true]);
    const r = 9;
    const all = ringPixels(r);
    const ordered = ringPixelsInOrder(r);
    expect(ordered).toHaveLength(all.length);
    // neighbours in the order are next to each other on the ring (so every other one is a dotted line)
    for (let i = 1; i < ordered.length; i++) {
      const [ax, ay] = ordered[i - 1];
      const [bx, by] = ordered[i];
      expect(Math.max(Math.abs(ax - bx), Math.abs(ay - by))).toBeLessThanOrEqual(1);
    }
    // the late frames are light on brown dirt (well brighter than a path's ~110 luminance)
    const lum = (c) => 0.299 * ((c >> 16) & 255) + 0.587 * ((c >> 8) & 255) + 0.114 * (c & 255);
    for (const f of RING_FRAMES) expect(lum(f.warm)).toBeGreaterThan(200);
  });
  it('a splash: a 2-px drop, then a crown 4 px wide with its ends 1 px up', () => {
    expect(RAIN.splash[0].rows).toEqual(['##']);
    expect(RAIN.splash[1].rows).toEqual(['#..#', '.##.']);
    expect(splashTexture(1)).toBe(Texture.WHITE); // (no canvas in unit tests)
  });
  it('the window pools are orange (red well over green)', () => {
    const c = WINDOW_GLOW.pool.color;
    expect((c >> 16) & 255).toBeGreaterThan(((c >> 8) & 255) * 1.2);
    expect((WINDOW_GLOW.light >> 16) & 255).toBeGreaterThan(((WINDOW_GLOW.light >> 8) & 255) * 1.2);
  });
  it('the effects atlas packs frames in shelves without overlap, and says when it is full', () => {
    const at = { x: 0, y: 0, shelf: 0 };
    const boxes = [];
    for (let i = 0; i < 200; i++) {
      const w = 8 + (i * 7) % 60;
      const h = 4 + (i * 5) % 40;
      const spot = packShelf(at, w, h);
      if (!spot) break;
      boxes.push({ ...spot, w, h });
      expect(spot.x + w).toBeLessThanOrEqual(ATLAS_SIZE);
      expect(spot.y + h).toBeLessThanOrEqual(ATLAS_SIZE);
    }
    expect(boxes.length).toBeGreaterThan(50);
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i];
        const b = boxes[j];
        expect(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y).toBe(true);
      }
    }
    expect(packShelf({ x: 0, y: 0, shelf: 0 }, ATLAS_SIZE + 1, 4)).toBe(null);
  });
});
