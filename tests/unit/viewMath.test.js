import { describe, it, expect } from 'vitest';
import { Camera, CAMERA_DEFAULTS } from '../../src/view/camera.js';
import { computeResolution, nextCandidate, RESOLUTION_CANDIDATES } from '../../src/view/resolution.js';
import { PALETTE, playerFrames, grassTile, pathTile, waterTile, rockSprite, treeSprite, gliderSprite, swimFrames, beastFrames, archerFrames, slashSprite, arrowSprite, orbSprite, shieldSprite, bowSprite, mirror } from '../../src/view/assets/placeholderArt.js';

function cam(opts = {}) {
  const c = new Camera(opts);
  c.setViewport(200, 100);
  c.setBounds({ x: 0, y: 0, width: 1000, height: 1000 });
  return c;
}

describe('Camera', () => {
  it('starts on the target and centers it', () => {
    const c = cam();
    c.follow(500, 300, 1 / 60);
    expect(c.origin()).toEqual({ x: 400, y: 250 });
  });

  it('follows smoothly: closes ~63% of the gap after one smoothTime', () => {
    const c = cam();
    c.snapTo(500, 500);
    for (let i = 0; i < 60; i++) c.follow(600, 500, CAMERA_DEFAULTS.smoothTime / 60);
    expect(c.x).toBeCloseTo(500 + 100 * (1 - Math.exp(-1)), 6);
  });

  it('is frame-rate independent (30fps and 60fps reach the same point)', () => {
    const a = cam();
    const b = cam();
    a.snapTo(500, 500);
    b.snapTo(500, 500);
    for (let i = 0; i < 30; i++) a.follow(700, 400, 1 / 60);
    for (let i = 0; i < 15; i++) b.follow(700, 400, 1 / 30);
    expect(b.x).toBeCloseTo(a.x, 9);
    expect(b.y).toBeCloseTo(a.y, 9);
  });

  it('never shows outside the bounds', () => {
    const c = cam();
    c.snapTo(10, 10);
    expect(c.origin()).toEqual({ x: 0, y: 0 });
    c.snapTo(990, 990);
    expect(c.origin()).toEqual({ x: 800, y: 900 });
  });

  it('centers an area smaller than the view (small rooms)', () => {
    const c = cam();
    c.setBounds({ x: 100, y: 100, width: 120, height: 60 });
    c.snapTo(130, 120);
    expect(c.origin()).toEqual({ x: 100 + (120 - 200) / 2, y: 100 + (60 - 100) / 2 });
  });

  it('bounds can be swapped for rooms, caves and dungeons', () => {
    const c = cam();
    c.setBounds({ x: 2000, y: 0, width: 300, height: 300 });
    c.snapTo(2290, 10);
    expect(c.origin()).toEqual({ x: 2100, y: 0 });
  });

  it('cuts instead of gliding across large distances (respawn, area change)', () => {
    const c = cam();
    c.snapTo(100, 100);
    c.follow(900, 900, 1 / 60);
    expect(c.x).toBe(900);
    expect(c.y).toBe(900);
  });

  it('zoom shrinks the visible area and keeps the origin on whole screen pixels', () => {
    const c = cam({ zoom: 2 });
    expect(c.viewWidth).toBe(100);
    expect(c.viewHeight).toBe(50);
    c.snapTo(500.37, 300.81);
    const o = c.origin();
    expect(Number.isInteger(o.x * 2)).toBe(true);
    expect(Number.isInteger(o.y * 2)).toBe(true);
  });

  it('returns whole pixels at zoom 1', () => {
    const c = cam();
    c.snapTo(500.4, 300.6);
    const o = c.origin();
    expect(Number.isInteger(o.x) && Number.isInteger(o.y)).toBe(true);
  });

  it('clamps zoom to the allowed range', () => {
    const c = cam();
    c.setZoom(0.2);
    expect(c.zoom).toBe(CAMERA_DEFAULTS.minZoom);
    c.setZoom(99);
    expect(c.zoom).toBe(CAMERA_DEFAULTS.maxZoom);
  });
});

describe('computeResolution', () => {
  // iPhone 15 Pro landscape: 852x393 CSS px at DPR 3
  for (const target of RESOLUTION_CANDIDATES) {
    it(`iPhone 15 Pro landscape, target ${target}: integer scale, covers the screen, height near target`, () => {
      const r = computeResolution(852, 393, 3, target);
      expect(Number.isInteger(r.scale)).toBe(true);
      expect(r.width * r.scale).toBeGreaterThanOrEqual(852 * 3);
      expect(r.height * r.scale).toBeGreaterThanOrEqual(393 * 3);
      // Overshoot is less than one game pixel.
      expect(r.width * r.scale - 852 * 3).toBeLessThan(r.scale);
      expect(Math.abs(r.height - target) / target).toBeLessThan(0.2);
    });
  }
  it('gives a wider view for a taller target', () => {
    const a = computeResolution(852, 393, 3, 180);
    const c = computeResolution(852, 393, 3, 270);
    expect(c.width).toBeGreaterThan(a.width);
  });
  it('P11.5: with 2 art pixels per game pixel the canvas has twice the pixels, the game view stays near the target', () => {
    for (const target of RESOLUTION_CANDIDATES) {
      const r = computeResolution(852, 393, 3, target, 2);
      expect(Number.isInteger(r.scale)).toBe(true);
      expect(r.artDensity).toBe(2);
      expect(r.height * r.scale).toBeGreaterThanOrEqual(393 * 3);
      // Game pixels across the short side: within a quarter of the target (even device scales only).
      expect(Math.abs(r.gameHeight - target) / target).toBeLessThan(0.25);
    }
    // iPhone 15 Pro, target 216: 3 device px per canvas px, 6 per game px → 196 game px tall.
    const r = computeResolution(852, 393, 3, 216, 2);
    expect(r.scale).toBe(3);
    expect(Math.round(r.gameHeight)).toBe(197);
    // Without real art nothing changes.
    expect(computeResolution(852, 393, 3, 216)).toMatchObject({ scale: 5, height: 236, artDensity: 1 });
  });
  it('never scales below 1', () => {
    expect(computeResolution(100, 50, 1, 270).scale).toBe(1);
  });
  it('cycles candidates', () => {
    expect(nextCandidate(180)).toBe(216);
    expect(nextCandidate(270)).toBe(180);
  });
});

describe('placeholder art', () => {
  const all = {
    ...playerFrames(),
    grass: grassTile(1),
    path: pathTile(),
    water0: waterTile(0),
    water1: waterTile(1),
    rock: rockSprite(),
    tree: treeSprite(),
    glider: gliderSprite(),
    ...swimFrames(),
    ...beastFrames(),
    ...archerFrames(),
    slash: slashSprite(),
    arrow: arrowSprite(),
    orb: orbSprite(),
    shield: shieldSprite(),
    bow: bowSprite(),
  };
  for (const [key, rows] of Object.entries(all)) {
    it(`${key}: rectangular and uses only palette colors`, () => {
      const w = rows[0].length;
      expect(rows.every((r) => r.length === w)).toBe(true);
      for (const r of rows) for (const c of r) expect(c === '.' || c in PALETTE).toBe(true);
    });
  }
  it('player frames are 16x16 with 3 frames per direction', () => {
    const f = playerFrames();
    expect(Object.keys(f)).toHaveLength(12);
    for (const rows of Object.values(f)) {
      expect(rows).toHaveLength(16);
      expect(rows[0]).toHaveLength(16);
    }
  });
  it('left frames mirror right frames', () => {
    const f = playerFrames();
    expect(f['player.walk.left.0']).toEqual(mirror(f['player.walk.right.0']));
  });
  it('tiles are deterministic', () => {
    expect(grassTile(7)).toEqual(grassTile(7));
  });
});
