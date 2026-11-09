import { describe, it, expect } from 'vitest';
import { RenderTexture, Sprite } from 'pixi.js';
import { createLightMap, warningLights, WARNING_LIGHT, LIGHT_MAP_RESOLUTION } from '../../src/view/weatherView.js';
import { ENEMY_KINDS } from '../../src/game/entities/enemies.js';
import { BOSS_KINDS } from '../../src/game/entities/bosses.js';

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
});
