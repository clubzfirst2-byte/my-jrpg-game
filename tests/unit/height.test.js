import { describe, it, expect } from 'vitest';
import { parseMap, terrainHeightAt, Shape, LEVEL_PX } from '../../src/game/world/tilemap.js';
import { createGameState, stepGame } from '../../src/game/state.js';
import { FixedStepLoop } from '../../src/game/core/fixedStep.js';
import { PLAYER_MOVE, PLAYER_MAX_HP, SAFE_FALL_PX, fallDamage, jumpVelocity } from '../../src/game/entities/player.js';
import { overlapsSolid } from '../../src/game/physics/collision.js';
import { HEIGHT_TEST } from '../../src/game/world/maps/heightTest.js';

const none = { moveX: 0, moveY: 0, dash: false, jump: false };
const right = { ...none, moveX: 1 };

/**
 * A 1-row corridor (plus wall rows) with the given height row; spawn at the left.
 * `ground` optionally gives the ground characters for the corridor ('u' = ruin: a wall that cannot be climbed).
 */
function corridor(heights, ground) {
  const w = heights.length + 2;
  const wall = '#'.repeat(w);
  const floor = ground ?? '.'.repeat(heights.length - 1);
  return {
    ground: [wall, '#P' + floor + '#', wall],
    height: ['0'.repeat(w), '0' + heights + '0', '0'.repeat(w)],
  };
}

function run(state, input, steps) {
  for (let i = 0; i < steps; i++) stepGame(state, typeof input === 'function' ? input(i) : input);
  return state.player;
}

describe('terrain height', () => {
  it('parses flat heights in 4px units', () => {
    const m = parseMap({ ground: ['...'], height: ['028'] });
    expect([...m.elev]).toEqual([0, 8, 32]);
  });

  it('ramps interpolate from the high north edge to the low south edge', () => {
    const m = parseMap({ ground: ['.', '.', '.'], height: ['4', '^', '0'] });
    expect(m.shape[1]).toBe(Shape.RAMP_N);
    expect(terrainHeightAt(m, 8, 16)).toBe(16); // north edge
    expect(terrainHeightAt(m, 8, 24)).toBe(8); // middle
    expect(terrainHeightAt(m, 8, 31.99)).toBeCloseTo(0, 1); // south edge
  });

  it('rejects ramps that do not rise exactly one level', () => {
    expect(() => parseMap({ ground: ['.', '.', '.'], height: ['2', '^', '0'] })).toThrow(/rise exactly/);
    expect(() => parseMap({ ground: ['.'], height: ['x'] })).toThrow(/Unknown height/);
  });

  it('the height verification map is valid and its spawn point is free', () => {
    const m = parseMap(HEIGHT_TEST);
    expect(m.width).toBe(40);
    expect(m.height).toBe(30);
    expect(overlapsSolid({ x: m.spawn.x, y: m.spawn.y, halfWidth: 5, height: 6 }, m)).toBe(false);
    expect(Math.max(...m.elev)).toBe(4 * LEVEL_PX);
  });
});

describe('walking on terrain', () => {
  it('walks up half-level (8px) steps without jumping', () => {
    const s = createGameState(corridor('0024600000'));
    const p = run(s, right, 120);
    expect(p.z).toBe(0); // walked up to 24 and back down again
    expect(p.x).toBeGreaterThan(10 * 16);
  });

  it('stands on a step: z follows the terrain', () => {
    const s = createGameState(corridor('00222222'));
    const p = run(s, right, 60);
    expect(p.grounded).toBe(true);
    expect(p.z).toBe(8);
  });

  it('is blocked by a 1-level cliff that cannot be climbed', () => {
    const s = createGameState(corridor('00444444', '.uuuuuu'));
    const p = run(s, right, 120);
    expect(p.z).toBe(0);
    expect(p.x).toBe(3 * 16 - p.halfWidth);
  });

  it('can jump onto a 1-level ledge', () => {
    const s = createGameState(corridor('00444444', '.uuuuuu'));
    // Walk to the wall, then hold jump while still pushing right.
    run(s, right, 60);
    const p = run(s, { ...right, jump: true }, 40);
    expect(p.z).toBe(LEVEL_PX);
    expect(p.x).toBeGreaterThan(3 * 16);
  });

  it('cannot jump onto a 2-level ledge', () => {
    const s = createGameState(corridor('00888888', '.uuuuuu'));
    run(s, right, 60);
    const p = run(s, (i) => ({ ...right, jump: i % 30 < 15 }), 120); // keep trying
    expect(p.x).toBe(3 * 16 - p.halfWidth);
    expect(p.z).toBe(0);
  });

  it('walks up a ramp and onto the plateau above', () => {
    const def = {
      ground: ['#####', '#...#', '#...#', '#.P.#', '#####'],
      height: ['00000', '04440', '04^40', '00000', '00000'],
    };
    const s = createGameState(def);
    const p = run(s, { ...none, moveY: -1 }, 60);
    expect(p.z).toBe(LEVEL_PX);
    expect(p.grounded).toBe(true);
    expect(p.y).toBeLessThan(2 * 16);
  });

  it('cannot enter the side of a ramp from below where it is too high', () => {
    const def = {
      ground: ['#####', '#...#', '#...#', '#...#', '#####'],
      height: ['00000', '04440', '00^40', '00000', '00000'],
    };
    const s = createGameState(def);
    const p = s.player;
    p.x = 16 + 8;
    p.y = 2 * 16 + 7; // box spans y 33..39: west of the ramp's north half (ramp is ~9..15px high there)
    run(s, right, 40);
    expect(p.x).toBe(2 * 16 - p.halfWidth);
  });
});

describe('jumping and falling', () => {
  it('a standing jump reaches the configured apex and lands back', () => {
    const s = createGameState(corridor('00000000'));
    let apex = 0;
    run(s, (i) => {
      apex = Math.max(apex, s.player.z);
      return { ...none, jump: i < 2 };
    }, 60);
    expect(apex).toBeGreaterThan(PLAYER_MOVE.jumpHeight - 0.5);
    expect(apex).toBeLessThanOrEqual(PLAYER_MOVE.jumpHeight + 0.01);
    expect(s.player.grounded).toBe(true);
    expect(s.player.z).toBe(0);
  });

  it('holding jump does not bounce repeatedly (press detection)', () => {
    const s = createGameState(corridor('00000000'));
    let jumps = 0;
    let wasGrounded = true;
    run(s, () => {
      if (wasGrounded && !s.player.grounded) jumps++;
      wasGrounded = s.player.grounded;
      return { ...none, jump: true };
    }, 120);
    expect(jumps).toBe(1);
  });

  it('jump arc is the same at 30fps and 60fps', () => {
    const sim = (fps) => {
      const s = createGameState(corridor('00000000'));
      const loop = new FixedStepLoop();
      let frame = 0;
      for (let i = 0; i < fps * 0.5; i++) {
        loop.advance(1000 / fps, () => stepGame(s, { ...right, jump: frame++ < 3 }));
      }
      return s.player;
    };
    const a = sim(60);
    const b = sim(30);
    expect(b.z).toBeCloseTo(a.z, 6);
    expect(b.x).toBeCloseTo(a.x, 6);
  });

  it('walking off a ledge falls and lands without damage from 1 level', () => {
    const s = createGameState(corridor('44444000'));
    const p = run(s, right, 90);
    expect(p.z).toBe(0);
    expect(p.hp).toBe(PLAYER_MAX_HP);
  });

  it('coyote time: a jump pressed just after leaving the ledge still works', () => {
    const s = createGameState(corridor('44400000'));
    let left = -1;
    let maxZ = 0;
    run(s, (i) => {
      if (left < 0 && !s.player.grounded) left = i;
      if (left >= 0) maxZ = Math.max(maxZ, s.player.z);
      return { ...right, jump: left >= 0 && i >= left + 2 && i <= left + 3 };
    }, 120);
    expect(left).toBeGreaterThan(0);
    expect(maxZ).toBeGreaterThan(LEVEL_PX + 8); // jumped from the ledge height
  });

  it('a jump pressed after coyote time (and too early to be buffered for landing) does nothing', () => {
    const s = createGameState(corridor('ccc00000')); // 3-level ledge: ~20 steps of falling
    let left = -1;
    let maxZ = 0;
    run(s, (i) => {
      if (left < 0 && !s.player.grounded) left = i;
      if (left >= 0) maxZ = Math.max(maxZ, s.player.z);
      return { ...right, jump: left >= 0 && i >= left + 6 && i <= left + 7 };
    }, 120);
    expect(maxZ).toBeLessThanOrEqual(3 * LEVEL_PX);
    expect(s.player.z).toBe(0);
  });

  it('jump buffer: pressing jump shortly before landing jumps again on landing', () => {
    const s = createGameState(corridor('00000000'));
    let landed = 0;
    let bounced = false;
    run(s, (i) => {
      const p = s.player;
      if (i > 5 && p.grounded) landed++;
      if (landed > 0 && !p.grounded) bounced = true;
      // First jump at i=0..1; press again while descending, just above the ground.
      const pressAgain = i > 5 && !p.grounded && p.vz < 0 && p.z < 3;
      return { ...none, jump: i < 2 || pressAgain };
    }, 90);
    expect(bounced).toBe(true);
  });
});

describe('fall damage', () => {
  it('is zero up to 3 levels and grows per level beyond', () => {
    expect(fallDamage(SAFE_FALL_PX)).toBe(0);
    expect(fallDamage(SAFE_FALL_PX + 1)).toBe(2);
    expect(fallDamage(4 * LEVEL_PX)).toBe(2);
    expect(fallDamage(4 * LEVEL_PX + 1)).toBe(4);
  });

  it('falling 4 levels off the tower edge hurts the player', () => {
    const s = createGameState(corridor('ggggg000'));
    expect(s.player.z).toBe(4 * LEVEL_PX); // spawns on top of the terrain
    const p = run(s, right, 120);
    expect(p.z).toBe(0);
    expect(p.hp).toBe(PLAYER_MAX_HP - 2);
  });

  it('returns to the spawn point with full health when health reaches zero (until P3)', () => {
    const s = createGameState(corridor('vvvvv000'));
    s.player.hp = 2;
    let respawned = false;
    run(s, () => {
      if (s.player.lastEvent?.type === 'respawn') respawned = true;
      return respawned ? none : right;
    }, 200);
    const p = s.player;
    expect(respawned).toBe(true);
    expect(p.hp).toBe(PLAYER_MAX_HP);
    expect(p.x).toBe(p.spawnX);
    expect(p.z).toBe(124); // back on top of the spawn tile, not inside it
  });

  it('jump velocity matches the apex formula', () => {
    expect(jumpVelocity() ** 2 / (2 * PLAYER_MOVE.gravity)).toBeCloseTo(PLAYER_MOVE.jumpHeight, 6);
  });
});
