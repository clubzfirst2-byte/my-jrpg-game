import { describe, it, expect } from 'vitest';
import { RenderTexture, Sprite } from 'pixi.js';
import { createLightMap, warningLights, WARNING_LIGHT } from '../../src/view/weatherView.js';
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
    rt.resize(852, 393);
    const b = overlay.getLocalBounds();
    expect([b.width, b.height]).toEqual([852, 393]);
    rt.resize(734, 343); // (the screen size changes: rotation, the Safari bar)
    const c = overlay.getLocalBounds();
    expect([c.width, c.height]).toEqual([734, 343]);
  });

  it('is hidden (not drawn) until it is first filled, and multiplies the world', () => {
    const { overlay } = createLightMap();
    expect(overlay.visible).toBe(false);
    expect(overlay.blendMode).toBe('multiply');
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
