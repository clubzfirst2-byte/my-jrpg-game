import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { CLIMB } from '../../src/game/entities/climbing.js';
import { PLAYER_STAMINA, PLAYER_MAX_HP } from '../../src/game/entities/player.js';
import { LEVEL_PX } from '../../src/game/world/tilemap.js';

const none = { moveX: 0, moveY: 0, dash: false, jump: false };
const right = { ...none, moveX: 1 };
const left = { ...none, moveX: -1 };
const up = { ...none, moveY: -1 };

/** 1-row corridor; spawn at the left; `ground` optionally sets ground chars ('u' = ruin). */
function corridor(heights, ground) {
  const w = heights.length + 2;
  const wall = '#'.repeat(w);
  return {
    ground: [wall, '#P' + (ground ?? '.'.repeat(heights.length - 1)) + '#', wall],
    height: ['0'.repeat(w), '0' + heights + '0', '0'.repeat(w)],
  };
}

/** A plateau to the north (columns 1-4, 1 level) with open ground south of it. */
const NORTH_WALL = {
  ground: ['#########', '#.......#', '#.......#', '#.......#', '#.P.....#', '#########'],
  height: ['000000000', '044440000', '044440000', '000000000', '000000000', '000000000'],
};

function run(state, input, steps) {
  for (let i = 0; i < steps; i++) stepGame(state, typeof input === 'function' ? input(i) : input);
  return state.player;
}

/** Walk into the wall until the player grabs it. Returns the step count it took. */
function grab(state, input, max = 200) {
  for (let i = 0; i < max; i++) {
    stepGame(state, input);
    if (state.player.climbing) return i;
  }
  throw new Error('never grabbed the wall');
}

describe('grabbing walls', () => {
  it('pushing into a climbable wall grabs it after a short deliberate push', () => {
    const s = createGameState(corridor('00444444'));
    grab(s, right);
    expect(s.player.climbing).toBe(true);
    expect(s.player.climbDir).toBe('right');
  });

  it('brushing a wall briefly does not grab it', () => {
    const s = createGameState(corridor('00444444'));
    // Walk until blocked, then push for less than the grab delay and let go.
    let blockedAt = -1;
    run(s, (i) => {
      if (blockedAt < 0 && s.player.x === 3 * 16 - s.player.halfWidth) blockedAt = i;
      const pushFor = Math.floor((CLIMB.grabDelay * 60) / 2);
      return blockedAt < 0 || i < blockedAt + pushFor ? right : none;
    }, 90);
    expect(s.player.climbing).toBe(false);
  });

  it('ruin walls cannot be climbed', () => {
    const s = createGameState(corridor('00888888', '.uuuuuu'));
    run(s, right, 200);
    expect(s.player.climbing).toBe(false);
    expect(s.player.z).toBe(0);
  });

  it('a wall low enough to step up is walked over, not climbed', () => {
    const s = createGameState(corridor('00222222'));
    run(s, right, 120);
    expect(s.player.climbing).toBe(false);
    expect(s.player.z).toBe(8);
  });

  it('a wall can be grabbed in mid-air (jump at a 2-level wall)', () => {
    const s = createGameState(corridor('00888888'));
    let grabbed = false;
    run(s, (i) => {
      if (s.player.climbing && !grabbed) grabbed = true;
      return { ...right, jump: i > 10 && i < 14 };
    }, 60);
    expect(grabbed).toBe(true);
  });
});

describe('climbing', () => {
  it('climbs up and pulls onto the ledge at the top', () => {
    const s = createGameState(corridor('00444444'));
    grab(s, right);
    const p = run(s, right, 90);
    expect(p.climbing).toBe(false);
    expect(p.grounded).toBe(true);
    expect(p.z).toBe(LEVEL_PX);
    expect(p.x).toBeGreaterThan(3 * 16);
  });

  it('climbs at the configured speed', () => {
    const s = createGameState(corridor('00888888'));
    grab(s, right);
    const z0 = s.player.z;
    run(s, right, 30);
    expect(s.player.z - z0).toBeCloseTo(CLIMB.speed * 0.5, 5);
  });

  it('pulling away climbs down and steps off at the bottom', () => {
    const s = createGameState(corridor('00888888'));
    grab(s, right);
    run(s, right, 20);
    expect(s.player.z).toBeGreaterThan(0);
    const p = run(s, left, 60);
    expect(p.climbing).toBe(false);
    expect(p.grounded).toBe(true);
    expect(p.z).toBe(0);
  });

  it('jump lets go of the wall and the player falls', () => {
    const s = createGameState(corridor('00888888'));
    grab(s, right);
    run(s, right, 40);
    expect(s.player.z).toBeGreaterThan(10);
    run(s, { ...none, jump: true }, 1);
    expect(s.player.climbing).toBe(false);
    run(s, none, 60);
    expect(s.player.grounded).toBe(true);
    expect(s.player.z).toBe(0);
  });

  it('after letting go, holding toward the wall does not instantly re-grab it', () => {
    const s = createGameState(corridor('00888888'));
    grab(s, right);
    run(s, right, 30);
    run(s, { ...right, jump: true }, 1);
    let regrabbedAt = -1;
    run(s, (i) => {
      if (regrabbedAt < 0 && s.player.climbing) regrabbedAt = i;
      return right;
    }, Math.round(CLIMB.regrabCooldown * 60) - 2);
    expect(regrabbedAt).toBe(-1);
  });

  it('letting go high up causes fall damage like any fall', () => {
    const s = createGameState(corridor('00vvvvvv'));
    grab(s, right);
    run(s, right, Math.ceil((60 / CLIMB.speed) * 60)); // climb to ~60px (> 3 levels)
    run(s, { ...none, jump: true }, 1);
    run(s, none, 90);
    expect(s.player.hp).toBe(PLAYER_MAX_HP - 2);
  });

  it('moves along a north wall and stops where the wall ends', () => {
    const s = createGameState(NORTH_WALL);
    grab(s, up);
    expect(s.player.climbDir).toBe('up');
    run(s, up, 6); // a little off the ground
    run(s, right, 120);
    const p = s.player;
    expect(p.climbing).toBe(true);
    expect(p.x).toBeGreaterThan(4 * 16); // moved along the wall
    expect(p.x).toBeLessThan(5 * 16); // but not past its end
  });

  it('climbs a north wall onto the plateau', () => {
    const s = createGameState(NORTH_WALL);
    grab(s, up);
    const p = run(s, up, 90);
    expect(p.grounded).toBe(true);
    expect(p.z).toBe(LEVEL_PX);
    expect(p.y).toBeLessThan(3 * 16);
  });
});

describe('stamina', () => {
  it('climbing drains stamina; running out makes the player fall', () => {
    const s = createGameState(corridor('00vvvvvv'));
    grab(s, right);
    s.player.stamina = 10;
    run(s, right, Math.ceil((10 / CLIMB.moveCost) * 60) + 2);
    expect(s.player.exhausted).toBe(true);
    expect(s.player.climbing).toBe(false);
    run(s, none, 60);
    expect(s.player.grounded).toBe(true);
  });

  it('an exhausted player cannot grab walls', () => {
    const s = createGameState(corridor('00444444'));
    s.player.stamina = 0;
    s.player.exhausted = true;
    run(s, right, 40);
    expect(s.player.climbing).toBe(false);
  });

  it('dashing drains stamina', () => {
    const s = createGameState(corridor('0000000000000000000000'));
    run(s, { ...right, dash: true }, 60);
    expect(s.player.stamina).toBeCloseTo(PLAYER_STAMINA.max - PLAYER_STAMINA.dashCost, 0);
  });

  it('exhausted: no dash, slower walking, back to normal only when the wheel is full again', () => {
    const s = createGameState(corridor('0000000000000000000000'));
    const p = s.player;
    p.stamina = 0;
    p.exhausted = true;
    const x0 = p.x;
    run(s, { ...right, dash: true }, 30);
    expect(p.dashing).toBe(false);
    const tired = p.x - x0;
    expect(tired).toBeLessThan(0.5 * 72 * PLAYER_STAMINA.exhaustedSpeed + 2);
    run(s, none, Math.ceil((PLAYER_STAMINA.regenDelay + PLAYER_STAMINA.max / PLAYER_STAMINA.regen) * 60) + 10);
    expect(p.stamina).toBe(PLAYER_STAMINA.max);
    expect(p.exhausted).toBe(false);
  });

  it('stamina recovers after a short rest', () => {
    const s = createGameState(corridor('0000000000000000000000'));
    s.player.stamina = 50;
    run(s, none, Math.round(PLAYER_STAMINA.regenDelay * 60) - 2);
    expect(s.player.stamina).toBe(50);
    run(s, none, 60);
    expect(s.player.stamina).toBeGreaterThan(50 + PLAYER_STAMINA.regen * 0.8);
  });
});
