import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { FixedStepLoop } from '../../src/game/core/fixedStep.js';
import { GLIDE } from '../../src/game/entities/glider.js';
import { PLAYER_MAX_HP } from '../../src/game/entities/player.js';

const none = { moveX: 0, moveY: 0, dash: false, jump: false };
const right = { ...none, moveX: 1 };

/** Long corridor: a `ledge` of high ground on the left, then flat ground. */
function cliffCorridor(ledgeHeights, flatLength = 40) {
  const heights = ledgeHeights + '0'.repeat(flatLength);
  const w = heights.length + 2;
  const wall = '#'.repeat(w);
  return {
    ground: [wall, '#P' + '.'.repeat(heights.length - 1) + '#', wall],
    height: ['0'.repeat(w), '0' + heights + '0', '0'.repeat(w)],
  };
}

/**
 * Walks right off the ledge and presses jump `delay` steps after leaving it.
 * Returns info about the flight.
 */
function glideOff(def, { delay = 6, steps = 400, input = right, closeAfter = -1 } = {}) {
  const s = createGameState(def);
  let left = -1;
  let opened = -1;
  let leftX = 0;
  let landedX = null;
  let wasGrounded = true;
  for (let i = 0; i < steps; i++) {
    const p = s.player;
    if (left < 0 && !p.grounded) {
      left = i;
      leftX = p.x;
    }
    if (opened < 0 && p.gliding) opened = i;
    const press = left >= 0 && (i === left + delay || (closeAfter >= 0 && opened >= 0 && i === opened + closeAfter));
    stepGame(s, { ...input, jump: press });
    if (left >= 0 && !wasGrounded && p.grounded && landedX === null) landedX = p.x;
    wasGrounded = p.grounded;
  }
  return { s, p: s.player, left, opened, glideDistance: landedX === null ? null : landedX - leftX };
}

describe('opening and closing the glider', () => {
  it('jump in mid-air opens the glider and the player sinks slowly', () => {
    const { s, opened } = glideOff(cliffCorridor('gggg'), { steps: 60 });
    expect(opened).toBeGreaterThan(0);
    expect(s.player.gliding).toBe(true);
    expect(s.player.vz).toBe(-GLIDE.fallSpeed);
  });

  it('cannot open close to the ground (the press becomes a jump on landing instead)', () => {
    const { opened } = glideOff(cliffCorridor('2222'), { delay: 2, steps: 80 }); // 8px drop only
    expect(opened).toBe(-1);
  });

  it('a jump then a second press near the top of the jump opens the glider', () => {
    const s = createGameState(cliffCorridor('', 20));
    let opened = false;
    for (let i = 0; i < 60; i++) {
      stepGame(s, { ...none, jump: i < 2 || (i >= 14 && i < 16) });
      if (s.player.gliding) opened = true;
    }
    expect(opened).toBe(true);
  });

  it('jump again closes it and the player falls normally', () => {
    const s = createGameState(cliffCorridor('gggg'));
    let left = -1;
    let opened = -1;
    let closed = -1;
    let fastestFall = 0;
    for (let i = 0; i < 200; i++) {
      const p = s.player;
      if (left < 0 && !p.grounded) left = i;
      if (opened < 0 && p.gliding) opened = i;
      const press = left >= 0 && (i === left + 6 || (opened >= 0 && i === opened + 20));
      stepGame(s, { ...right, jump: press });
      if (opened >= 0 && closed < 0 && !p.gliding) closed = i;
      if (closed >= 0 && !p.grounded) fastestFall = Math.min(fastestFall, p.vz);
    }
    expect(opened).toBeGreaterThan(0);
    expect(closed).toBe(opened + 20);
    expect(fastestFall).toBeLessThan(-GLIDE.fallSpeed); // accelerating under gravity after closing
  });

  it('an exhausted player cannot open it', () => {
    const def = cliffCorridor('gggg');
    const s = createGameState(def);
    s.player.stamina = 0;
    s.player.exhausted = true;
    let left = -1;
    let opened = false;
    for (let i = 0; i < 120; i++) {
      if (left < 0 && !s.player.grounded) left = i;
      stepGame(s, { ...right, jump: left >= 0 && i === left + 6 });
      if (s.player.gliding) opened = true;
    }
    expect(opened).toBe(false);
  });
});

describe('flight', () => {
  it('glides about speed x (height / sink speed) across from a 4-level tower', () => {
    const { glideDistance, p } = glideOff(cliffCorridor('gggg', 40));
    const expected = GLIDE.speed * (64 / GLIDE.fallSpeed);
    expect(glideDistance).not.toBeNull();
    expect(glideDistance).toBeGreaterThan(expected * 0.85);
    expect(glideDistance).toBeLessThan(expected * 1.1);
    expect(p.grounded).toBe(true);
  });

  it('landing while gliding never hurts, even from high up', () => {
    const { p } = glideOff(cliffCorridor('vvvv', 60), { steps: 800 });
    expect(p.grounded).toBe(true);
    expect(p.hp).toBe(PLAYER_MAX_HP);
  });

  it('closing the glider high up measures fall damage from the closing height', () => {
    const { p } = glideOff(cliffCorridor('vvvv', 60), { closeAfter: 10, steps: 300 });
    expect(p.grounded).toBe(true);
    expect(p.hp).toBeLessThan(PLAYER_MAX_HP);
  });

  it('without input the glider slows to a drift but keeps sinking', () => {
    const s = createGameState(cliffCorridor('vvvv', 60));
    let left = -1;
    for (let i = 0; i < 400 && !(left >= 0 && i > left + 30); i++) {
      if (left < 0 && !s.player.grounded) left = i;
      stepGame(s, { ...right, jump: left >= 0 && i === left + 6 });
    }
    expect(s.player.gliding).toBe(true);
    for (let i = 0; i < 60; i++) stepGame(s, none); // let go of the stick
    expect(s.player.gliding).toBe(true);
    expect(Math.abs(s.player.vx)).toBeLessThan(1);
    expect(s.player.vz).toBe(-GLIDE.fallSpeed);
  });

  it('gliding drains stamina; running out closes the glider', () => {
    const def = cliffCorridor('vvvv', 60);
    const s = createGameState(def);
    let left = -1;
    let closedByStamina = false;
    for (let i = 0; i < 400; i++) {
      const p = s.player;
      if (left < 0 && !p.grounded) left = i;
      if (left >= 0 && i === left + 6) p.stamina = 3; // nearly empty when opening
      const was = p.gliding;
      stepGame(s, { ...right, jump: left >= 0 && i === left + 6 });
      if (was && !p.gliding && !p.grounded) closedByStamina = p.exhausted;
    }
    expect(closedByStamina).toBe(true);
  });

  it('gliding into a climbable wall grabs it', () => {
    // Ledge, a gap, then a tall wall to glide into.
    const s = createGameState(cliffCorridor('gggg00vvvv', 4));
    let left = -1;
    let grabbed = false;
    for (let i = 0; i < 200; i++) {
      if (left < 0 && !s.player.grounded) left = i;
      stepGame(s, { ...right, jump: left >= 0 && i === left + 4 });
      if (s.player.climbing) grabbed = true;
    }
    expect(grabbed).toBe(true);
  });

  it('flight is the same at 30fps and 60fps', () => {
    const sim = (fps) => {
      const s = createGameState(cliffCorridor('gggg', 40));
      const loop = new FixedStepLoop();
      let step = 0;
      let left = -1;
      for (let f = 0; f < fps * 2; f++) {
        loop.advance(1000 / fps, () => {
          if (left < 0 && !s.player.grounded) left = step;
          stepGame(s, { ...right, jump: left >= 0 && step === left + 6 });
          step++;
        });
      }
      return s.player;
    };
    const a = sim(60);
    const b = sim(30);
    expect(b.x).toBeCloseTo(a.x, 6);
    expect(b.z).toBeCloseTo(a.z, 6);
  });
});
