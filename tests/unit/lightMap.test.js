import { describe, it, expect } from 'vitest';
import { RenderTexture, Sprite } from 'pixi.js';
import { createLightMap, warningLights, WARNING_LIGHT, LIGHT_MAP_RESOLUTION, lightFalloff } from '../../src/view/weatherView.js';
import { ENEMY_KINDS } from '../../src/game/entities/enemies.js';
import { BOSS_KINDS } from '../../src/game/entities/bosses.js';
import { FINAL_BOSS } from '../../src/game/entities/finalBoss.js';

// Final QA A-1: started from the title, nights and dark rooms were never dark. The app draws frames
// while boot waits for the save; the light map was drawn then at its starting size (8×8) and its
// sprite never followed the later resize to the screen.

describe('the light map follows its resize to the screen', () => {
  it('reproduces the bug: a sprite on a non-dynamic render texture keeps the size it was first drawn at', () => {
    const rt = RenderTexture.create({ width: 8, height: 8 });
    const s = new Sprite(rt);
    s.getLocalBounds(); // a frame drawn before the first resize (as during the title's save load)
    rt.resize(852, 393);
    expect(s.getLocalBounds().width).toBe(8); // still a dot in the corner: the world is never darkened
  });

  it('createLightMap: drawn early or late, the overlay covers the whole screen after the resize', () => {
    const { rt, overlay } = createLightMap();
    overlay.getLocalBounds(); // drawn early
    // Drawn at half resolution, an odd size rounds up by one map pixel (2 screen px) at most.
    const covers = (/** @type {number} */ w, /** @type {number} */ h) => {
      rt.resize(w, h, LIGHT_MAP_RESOLUTION);
      const b = overlay.getLocalBounds();
      expect(b.width).toBeGreaterThanOrEqual(w);
      expect(b.height).toBeGreaterThanOrEqual(h);
      expect(b.width - w).toBeLessThan(1 / LIGHT_MAP_RESOLUTION);
      expect(b.height - h).toBeLessThan(1 / LIGHT_MAP_RESOLUTION);
    };
    covers(852, 393);
    covers(734, 343); // (the screen size changes: rotation, the Safari bar)
    covers(1024, 472);
  });

  it('is hidden (not drawn) until it is first filled, and multiplies the world', () => {
    const { overlay } = createLightMap();
    expect(overlay.visible).toBe(false);
    expect(overlay.blendMode).toBe('multiply');
  });

  it('is drawn at half resolution with linear filtering (a soft map, a quarter of the pixels)', () => {
    const { rt } = createLightMap();
    rt.resize(1024, 472, LIGHT_MAP_RESOLUTION);
    expect(LIGHT_MAP_RESOLUTION).toBe(0.5);
    expect([rt.source.pixelWidth, rt.source.pixelHeight]).toEqual([512, 236]);
    expect(rt.source.scaleMode).toBe('linear');
  });
});

describe('warning lights (final QA B-1: the wind-up warning stays in the world, lit in the dark)', () => {
  it('only enemies winding up light their spot', () => {
    const enemies = ['idle', 'windup', 'attack', 'recover', 'stun', 'dead'].map((state, i) => ({ id: i + 1, kind: 'beast', state, x: 10 * i, y: 50, z: 0 }));
    const lights = warningLights(enemies);
    expect(lights).toHaveLength(1);
    expect(lights[0]).toMatchObject({ x: 10, r: WARNING_LIGHT.enemyRadius });
    expect(lights[0].y).toBeLessThan(50); // on its body, above its feet
  });

  it('a slam lights its whole ring (sentinel, and a core winding up a slam)', () => {
    const [sentinel] = warningLights([{ kind: 'sentinel', state: 'windup', x: 0, y: 0, z: 0 }]);
    expect(sentinel.r).toBeGreaterThan(ENEMY_KINDS.sentinel.slamRadius);
    const [slam] = warningLights([{ boss: true, bossKind: 'frost', kind: 'boss_frost', pattern: 'slam', state: 'windup', x: 0, y: 0, z: 0 }]);
    expect(slam.r).toBeGreaterThan(BOSS_KINDS.frost.slamRadius);
    const [ring] = warningLights([{ boss: true, bossKind: 'frost', kind: 'boss_frost', pattern: 'ring', state: 'windup', x: 0, y: 0, z: 0 }]);
    expect(ring.r).toBe(WARNING_LIGHT.bossRadius);
  });

  it('the far edge of every slam ring still gets at least 20% of its light (the smooth falloff)', () => {
    const slams = [
      [{ kind: 'sentinel', state: 'windup', x: 0, y: 0, z: 0 }, ENEMY_KINDS.sentinel.slamRadius],
      ...Object.keys(BOSS_KINDS).filter((k) => BOSS_KINDS[k].slamRadius).map((k) => [{ boss: true, bossKind: k, kind: `boss_${k}`, pattern: 'slam', state: 'windup', x: 0, y: 0, z: 4 }, BOSS_KINDS[k].slamRadius]),
    ];
    for (const [e, r] of slams) {
      const [l] = warningLights([e]);
      // the ring is drawn around (x, y - z): its farthest point from the light
      let worst = 1;
      for (let a = 0; a < 360; a += 5) {
        const px = e.x + r * Math.cos((a * Math.PI) / 180);
        const py = e.y - e.z + r * Math.sin((a * Math.PI) / 180);
        worst = Math.min(worst, lightFalloff(Math.hypot(px - l.x, py - l.y) / l.r));
      }
      expect(worst, e.kind).toBeGreaterThanOrEqual(0.2);
      expect(l.r, e.kind).toBeLessThan(r * 1.5); // not much wider than the ring
    }
    // 淀みの源's ring light (ringCover) too
    for (const [pattern, reach] of [['slam', FINAL_BOSS.slamRadius], ['wave', FINAL_BOSS.waveRadius]]) {
      const ground = warningLights([{ final: true, kind: 'boss_source', pattern, state: 'windup', x: 0, y: 0, z: 0 }]).find((l) => l.y === 0);
      expect(lightFalloff(reach / ground.r), pattern).toBeGreaterThanOrEqual(0.2);
    }
  });
});

describe('the final boss lights its slam ring and its wave (v1.0 final)', () => {
  const at = { final: true, kind: 'boss_source', x: 100, y: 200, z: 0 };
  it('winding up a slam or a wave: a ground light centred on the ring covers all of it, plus its body light', () => {
    for (const [pattern, reach] of [['slam', FINAL_BOSS.slamRadius], ['wave', FINAL_BOSS.waveRadius]]) {
      const lights = warningLights([{ ...at, pattern, state: 'windup' }]);
      const ground = lights.find((l) => l.y === at.y - at.z);
      expect(ground, pattern).toBeTruthy();
      expect(ground.x).toBe(at.x);
      // the ring sits well inside the light (where its falloff still adds about 40%)
      expect(reach / ground.r).toBeLessThanOrEqual(WARNING_LIGHT.ringCover);
      expect(lights.some((l) => l.r === WARNING_LIGHT.bossRadius)).toBe(true);
    }
  });

  it('the shockwave itself stays lit; the orb attacks and resting get no ring light', () => {
    expect(warningLights([{ ...at, pattern: 'wave', state: 'attack' }])).toHaveLength(1);
    expect(warningLights([{ ...at, pattern: 'slam', state: 'recover' }])).toHaveLength(0);
    const volley = warningLights([{ ...at, pattern: 'volley', state: 'windup' }]);
    expect(volley).toHaveLength(1);
    expect(volley[0].r).toBe(WARNING_LIGHT.bossRadius);
  });
});

// Final QA L-1: lights in rooms looked like blotchy patches. The old disc was a straight cone
// (1 - t) with creases at its peak and edge; the new falloff is a smooth bell with the same total light.
describe('lightFalloff', () => {
  it('is 1 at the centre, 0 at and beyond the edge, and falls steadily', () => {
    expect(lightFalloff(0)).toBe(1);
    expect(lightFalloff(1)).toBe(0);
    expect(lightFalloff(1.5)).toBe(0);
    for (let t = 0; t < 1; t += 0.05) expect(lightFalloff(t + 0.05)).toBeLessThan(lightFalloff(t));
  });

  it('has no crease: flat at the centre and at the edge, and the slope changes smoothly', () => {
    const h = 0.01;
    expect(Math.abs(lightFalloff(h) - 1)).toBeLessThan(0.001);
    expect(lightFalloff(1 - h)).toBeLessThan(0.001);
    const slope = (/** @type {number} */ t) => (lightFalloff(t + h) - lightFalloff(t)) / h;
    for (let t = 0; t < 0.98; t += h) expect(Math.abs(slope(t + h) - slope(t))).toBeLessThan(0.1);
  });

  it('gives the same total light as the old disc (1 → 0.55 at 45% → 0), so nights stay as lit', () => {
    const old = (/** @type {number} */ t) => 1 - t; // the old stops 1, 0.55 at 0.45, 0
    let a = 0;
    let b = 0;
    const n = 10000;
    for (let k = 0; k < n; k++) {
      const t = (k + 0.5) / n;
      a += old(t) * t;
      b += lightFalloff(t) * t;
    }
    expect(Math.abs(b / a - 1)).toBeLessThan(0.01);
  });
});
