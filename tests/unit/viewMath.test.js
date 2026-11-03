import { describe, it, expect } from 'vitest';
import { cameraOrigin } from '../../src/view/camera.js';
import { computeResolution, nextCandidate, RESOLUTION_CANDIDATES } from '../../src/view/resolution.js';
import { PALETTE, playerFrames, grassTile, pathTile, waterTile, rockSprite, treeSprite, mirror } from '../../src/view/assets/placeholderArt.js';

describe('cameraOrigin', () => {
  it('centers on the target', () => {
    expect(cameraOrigin(500, 300, 200, 100, 1000, 1000)).toEqual({ x: 400, y: 250 });
  });
  it('clamps to world edges', () => {
    expect(cameraOrigin(10, 10, 200, 100, 1000, 1000)).toEqual({ x: 0, y: 0 });
    expect(cameraOrigin(990, 990, 200, 100, 1000, 1000)).toEqual({ x: 800, y: 900 });
  });
  it('centers a world smaller than the view', () => {
    expect(cameraOrigin(50, 50, 200, 100, 100, 1000).x).toBe(-50);
  });
  it('returns whole pixels', () => {
    const c = cameraOrigin(500.4, 300.6, 200, 100, 1000, 1000);
    expect(Number.isInteger(c.x) && Number.isInteger(c.y)).toBe(true);
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
