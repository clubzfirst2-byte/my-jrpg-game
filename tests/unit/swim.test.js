import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { FixedStepLoop } from '../../src/game/core/fixedStep.js';
import { SWIM } from '../../src/game/entities/swimming.js';
import { PLAYER_MAX_HP, PLAYER_MOVE } from '../../src/game/entities/player.js';

const none = { moveX: 0, moveY: 0, dash: false, jump: false };
const right = { ...none, moveX: 1 };
const left = { ...none, moveX: -1 };

/**
 * 1-row corridor: `ground` chars ('.' land, '~' water, 'u' ruin) and `heights` (4px units),
 * spawn at column 1.
 */
function corridor(ground, heights) {
  const w = ground.length + 2;
  const wall = '#'.repeat(w);
  return {
    ground: [wall, '#P' + ground.slice(1) + '#', wall],
    height: ['0'.repeat(w), '0' + (heights ?? '0'.repeat(ground.length)) + '0', '0'.repeat(w)],
  };
}

function run(s, input, steps) {
  for (let i = 0; i < steps; i++) stepGame(s, typeof input === 'function' ? input(i) : input);
  return s.player;
}

/** Walk right until the player is swimming. */
function wadeIn(s) {
  for (let i = 0; i < 200 && !s.player.swimming; i++) stepGame(s, right);
  if (!s.player.swimming) throw new Error('never entered the water');
}

describe('entering and leaving water', () => {
  it('walking into water starts swimming at the surface', () => {
    const s = createGameState(corridor('...~~~~~~~...'));
    wadeIn(s);
    expect(s.player.swimming).toBe(true);
    expect(s.player.grounded).toBe(false);
    expect(s.player.z).toBe(0);
  });

  it('swimming is slower than walking', () => {
    const s = createGameState(corridor('..~~~~~~~~~~~~~~~~...'));
    wadeIn(s);
    run(s, right, 30); // reach full swim speed
    const x0 = s.player.x;
    run(s, right, 60);
    expect(s.player.x - x0).toBeCloseTo(SWIM.speed, 0);
    expect(SWIM.speed).toBeLessThan(PLAYER_MOVE.walkSpeed);
  });

  it('dash swims faster but costs more stamina', () => {
    const s = createGameState(corridor('..~~~~~~~~~~~~~~~~~~~~~~...'));
    wadeIn(s);
    run(s, right, 30);
    const x0 = s.player.x;
    const st0 = s.player.stamina;
    run(s, { ...right, dash: true }, 60);
    expect(s.player.x - x0).toBeGreaterThan(SWIM.speed * 1.4);
    expect(st0 - s.player.stamina).toBeCloseTo(SWIM.dashCost, 0);
  });

  it('cannot jump while swimming', () => {
    const s = createGameState(corridor('..~~~~~~~...'));
    wadeIn(s);
    let maxZ = 0;
    run(s, () => {
      maxZ = Math.max(maxZ, s.player.z);
      return { ...none, jump: true };
    }, 30);
    expect(maxZ).toBe(0);
    expect(s.player.swimming).toBe(true);
  });

  it('swims across and walks out onto a low shore', () => {
    const s = createGameState(corridor('..~~~~.....'));
    wadeIn(s);
    run(s, right, 120);
    expect(s.player.swimming).toBe(false);
    expect(s.player.grounded).toBe(true);
    expect(s.player.x).toBeGreaterThan(7 * 16);
  });

  it('a 1-level ruin bank blocks swimming out', () => {
    const s = createGameState(corridor('..~~~~uuuuu', '000000444440'.slice(0, 11)));
    wadeIn(s);
    run(s, right, 200);
    expect(s.player.swimming).toBe(true);
    expect(s.player.x).toBeLessThan(7 * 16);
  });

  it('a climbable bank can be grabbed from the water', () => {
    const s = createGameState(corridor('..~~~~.....', '00000088888'));
    wadeIn(s);
    let grabbed = false;
    run(s, () => {
      if (s.player.climbing) grabbed = true;
      return right;
    }, 200);
    expect(grabbed).toBe(true);
  });
});

describe('ledge above water (regression)', () => {
  it('standing on a high ledge with toes over the water does not start swimming in mid-air', () => {
    const s = createGameState(corridor('...~~~~~~~...', 'ggg0000000000'));
    for (let i = 0; i < 200 && s.player.grounded; i++) {
      stepGame(s, right);
      if (s.player.swimming) expect(s.player.z).toBe(0); // only ever swims at the water surface
    }
    run(s, right, 60);
    expect(s.player.swimming).toBe(true);
    expect(s.player.z).toBe(0);
  });
});

describe('stamina and drowning', () => {
  it('swimming drains stamina, more while moving than treading water', () => {
    const a = createGameState(corridor('..~~~~~~~~~~~~~~~~...'));
    const b = createGameState(corridor('..~~~~~~~~~~~~~~~~...'));
    wadeIn(a);
    wadeIn(b);
    run(b, none, 40); // let the drift stop: from here b is treading water
    const a0 = a.player.stamina;
    const b0 = b.player.stamina;
    run(a, right, 60);
    run(b, none, 60);
    expect(a0 - a.player.stamina).toBeGreaterThan(b0 - b.player.stamina);
    expect(b0 - b.player.stamina).toBeCloseTo(SWIM.idleCost, 0);
  });

  it('running out of stamina drowns: back to the last dry ground with half a heart lost', () => {
    const s = createGameState(corridor('...~~~~~~~~~~...'));
    wadeIn(s);
    run(s, right, 30);
    s.player.stamina = 1;
    let drowned = false;
    run(s, () => {
      if (s.player.lastEvent?.type === 'drown') drowned = true;
      return drowned ? none : right;
    }, 60);
    const p = s.player;
    expect(drowned).toBe(true);
    expect(p.swimming).toBe(false);
    expect(p.grounded).toBe(true);
    expect(p.hp).toBe(PLAYER_MAX_HP - SWIM.drownDamage);
    expect(p.x).toBeLessThan(4 * 16); // on the shore we came from
  });

  it('an exhausted player recovers stamina after drowning (standing on land)', () => {
    const s = createGameState(corridor('...~~~~~~~~~~...'));
    wadeIn(s);
    s.player.stamina = 0.5;
    run(s, none, 15);
    expect(s.player.exhausted).toBe(true);
    expect(s.player.swimming).toBe(false);
    run(s, none, 200);
    expect(s.player.stamina).toBeGreaterThan(50);
  });
});

describe('falling and gliding into water', () => {
  it('falling into water from high up never hurts', () => {
    const s = createGameState(corridor('.....~~~~~~~~~~...', 'ggggg0000000000000'));
    run(s, right, 200);
    expect(s.player.hp).toBe(PLAYER_MAX_HP);
    expect(s.player.swimming).toBe(true);
  });

  it('gliding down onto water closes the glider and swims', () => {
    const s = createGameState(corridor('...~~~~~~~~~~~~~~~~~~~~~~~...', 'ggg00000000000000000000000000'));
    let left = -1;
    let glided = false;
    run(s, (i) => {
      if (left < 0 && !s.player.grounded) left = i;
      if (s.player.gliding) glided = true;
      return { ...right, jump: left >= 0 && i === left + 6 };
    }, 400);
    expect(glided).toBe(true);
    expect(s.player.gliding).toBe(false);
    expect(s.player.hp).toBe(PLAYER_MAX_HP);
  });

  it('swimming is the same at 30fps and 60fps', () => {
    const sim = (fps) => {
      const s = createGameState(corridor('..~~~~~~~~~~~~~~~~...'));
      const loop = new FixedStepLoop();
      for (let f = 0; f < fps * 2; f++) loop.advance(1000 / fps, () => stepGame(s, right));
      return s.player;
    };
    const a = sim(60);
    const b = sim(30);
    expect(b.x).toBeCloseTo(a.x, 6);
    expect(b.stamina).toBeCloseTo(a.stamina, 6);
  });

  it('walking back out the way you came works too', () => {
    const s = createGameState(corridor('.....~~~~~~~~...'));
    wadeIn(s);
    run(s, left, 90);
    expect(s.player.swimming).toBe(false);
    expect(s.player.grounded).toBe(true);
  });
});
