import { describe, it, expect } from 'vitest';
import {
  computeView,
  computeResolution,
  chooseIntScale,
  crispUnit,
  parseScaleMode,
  DEFAULT_SCALE_MODE,
  RESOLUTION_CANDIDATES,
} from '../../src/view/resolution.js';

// [name, CSS width, CSS height, DPR, expected int scale (device px per game px) at target 216, density 2]
/** @type {[string, number, number, number, number][]} */
const SCREENS = [
  ['iPhone 15 Pro landscape', 852, 393, 3, 6],
  ['iPhone 15 Pro portrait', 393, 852, 3, 6],
  ['iPhone SE landscape', 667, 375, 2, 4],
  ['iPhone SE portrait', 375, 667, 2, 4],
  ['iPhone 15 Pro Max landscape', 932, 430, 3, 6],
  ['iPhone 15 Pro Max portrait', 430, 932, 3, 6],
  ['iPad 10th landscape', 1180, 820, 2, 8],
  ['iPad Pro 11 landscape', 1194, 834, 2, 8],
  ['iPad Pro 13 landscape', 1376, 1032, 2, 10],
  ['iPhone 15 (Safari bars, E2E)', 734, 343, 3, 4], // 1029 device px: 257 (×4) is closer to 216 than 171 (×6)
];

describe('scale mode', () => {
  it('defaults to fit; only "int" switches', () => {
    expect(DEFAULT_SCALE_MODE).toBe('fit');
    expect(parseScaleMode(null)).toBe('fit');
    expect(parseScaleMode('fit')).toBe('fit');
    expect(parseScaleMode('int')).toBe('int');
    expect(parseScaleMode('INT')).toBe('fit');
    expect(parseScaleMode('6')).toBe('fit');
  });

  it('fit is exactly the previous computeResolution', () => {
    for (const [, w, h, dpr] of SCREENS) {
      for (const t of RESOLUTION_CANDIDATES) {
        for (const d of [1, 2]) {
          const v = computeView(w, h, dpr, t, { canvasDensity: d });
          expect(v).toMatchObject(computeResolution(w, h, dpr, t, d));
          expect(v.mode).toBe('fit');
          expect(v.cssLeft).toBeNull();
        }
      }
    }
  });
});

describe('crispUnit / chooseIntScale', () => {
  it('lcm of the densities', () => {
    expect(crispUnit([2])).toBe(2);
    expect(crispUnit([2, 2])).toBe(2);
    expect(crispUnit([2, 4])).toBe(4);
    expect(crispUnit([2, 3])).toBe(6);
    expect(crispUnit([1])).toBe(1);
    expect(crispUnit([])).toBe(1);
  });
  it('multiple of the unit, closest to the target, never below the unit', () => {
    expect(chooseIntScale(1179, 216, 2)).toBe(6); // 5.46 → 6
    expect(chooseIntScale(750, 216, 2)).toBe(4); // 3.47 → 4
    expect(chooseIntScale(1179, 216, 4)).toBe(4); // 5.46 / 4 = 1.36 → 4
    expect(chooseIntScale(100, 216, 2)).toBe(2);
    expect(chooseIntScale(1179, 216, 1)).toBe(5);
  });
});

describe('int mode', () => {
  for (const [name, w, h, dpr, expScale] of SCREENS) {
    it(`${name}: whole device px per canvas and art pixel, covers the screen, no border`, () => {
      const v = computeView(w, h, dpr, 216, { mode: 'int', canvasDensity: 2 });
      const dw = Math.round(w * dpr);
      const dh = Math.round(h * dpr);
      expect(v.mode).toBe('int');
      expect(v.scale).toBe(expScale);
      expect(Number.isInteger(v.canvasScale)).toBe(true);
      expect(v.artPixel.every(Number.isInteger)).toBe(true);
      expect(v.scale % 2).toBe(0);
      // covers the whole screen, overshoot under one canvas pixel
      expect(v.width * v.canvasScale).toBeGreaterThanOrEqual(dw);
      expect(v.height * v.canvasScale).toBeGreaterThanOrEqual(dh);
      expect(v.width * v.canvasScale - dw).toBeLessThan(v.canvasScale);
      expect(v.height * v.canvasScale - dh).toBeLessThan(v.canvasScale);
      // placed on whole device pixels, cropped evenly (≤ 0)
      expect(Number.isInteger(Math.round(v.cssLeft * dpr * 1e6) / 1e6)).toBe(true);
      expect(Number.isInteger(Math.round(v.cssTop * dpr * 1e6) / 1e6)).toBe(true);
      expect(v.cssLeft).toBeLessThanOrEqual(0);
      expect(v.cssTop).toBeLessThanOrEqual(0);
      expect(v.cssLeft + v.cssCanvasWidth).toBeGreaterThanOrEqual(w - 1e-9);
      expect(v.cssTop + v.cssCanvasHeight).toBeGreaterThanOrEqual(h - 1e-9);
      // tiles add up
      expect(v.tilesX * 16 * 2).toBeCloseTo(v.width, 9);
      expect(v.tilesY * 16 * 2).toBeCloseTo(v.height, 9);
    });
  }

  it('iPhone 15 Pro / SE landscape: the audit numbers (案1)', () => {
    expect(computeView(852, 393, 3, 216, { mode: 'int', canvasDensity: 2 })).toMatchObject({
      scale: 6, canvasScale: 3, width: 852, height: 393, gameWidth: 426, cssLeft: -0, cssTop: -0,
    });
    const se = computeView(667, 375, 2, 216, { mode: 'int', canvasDensity: 2 });
    expect(se).toMatchObject({ scale: 4, canvasScale: 2, width: 667, height: 375 });
    expect(se.tilesX).toBeCloseTo(20.84, 2);
    expect(se.tilesY).toBeCloseTo(11.72, 2);
  });

  it('crops an odd remainder on a whole device pixel (734×343 @3, E2E viewport)', () => {
    const v = computeView(734, 343, 3, 216, { mode: 'int', canvasDensity: 2 });
    // 2202×1029 device px, 2 device px per canvas px → 1101×515 canvas px, 1 device px over at the bottom
    expect(v).toMatchObject({ scale: 4, canvasScale: 2, width: 1101, height: 515, cssLeft: -0, cssTop: -0 });
    // 15 Pro at ×6 (3 device px per canvas px), 2557 device px wide → 853 canvas px, 2 over → 1 px left
    const odd = computeView(2557 / 3, 393, 3, 216, { mode: 'int', canvasDensity: 2 });
    expect(odd.width).toBe(853);
    expect(odd.cssLeft * 3).toBeCloseTo(-1, 9);
    const odd2 = computeView(2558 / 3, 393, 3, 216, { mode: 'int', canvasDensity: 2 }); // 1 over → 0 px
    expect(odd2.cssLeft * 3).toBeCloseTo(0, 9);
  });

  it('a finer art set (density 4) is kept whole too, separately from the canvas density', () => {
    const v = computeView(852, 393, 3, 216, { mode: 'int', canvasDensity: 2, artDensities: [2, 4] });
    expect(v.scale % 4).toBe(0);
    expect(v.artPixel).toEqual([v.scale / 2, v.scale / 4]);
    expect(v.artPixel.every(Number.isInteger)).toBe(true);
    const v4 = computeView(852, 393, 3, 216, { mode: 'int', canvasDensity: 4, artDensities: [4] });
    expect(v4.scale % 4).toBe(0);
    expect(Number.isInteger(v4.canvasScale)).toBe(true);
    // fit mode ignores the art densities for the view (same area as before)
    const f = computeView(852, 393, 3, 216, { canvasDensity: 2, artDensities: [2, 4] });
    expect(f.gameHeight).toBe(computeResolution(852, 393, 3, 216, 2).gameHeight);
  });

  it('the other targets (?res=180/270) still pick a multiple of the density', () => {
    for (const t of RESOLUTION_CANDIDATES) {
      const v = computeView(852, 393, 3, t, { mode: 'int', canvasDensity: 2 });
      expect(v.scale % 2).toBe(0);
      expect(Number.isInteger(v.canvasScale)).toBe(true);
    }
  });

  it('placeholder art (density 1) gives any whole scale', () => {
    const v = computeView(852, 393, 3, 216, { mode: 'int', canvasDensity: 1 });
    expect(v.scale).toBe(5);
    expect(v.canvasScale).toBe(5);
  });
});
