import { describe, it, expect } from 'vitest';
import { createGameState, stepGame } from '../../src/game/state.js';
import { FixedStepLoop } from '../../src/game/core/fixedStep.js';
import { PLAYER_MOVE, facingFrom } from '../../src/game/entities/player.js';
import { normalizeStick, STICK_DEADZONE } from '../../src/game/input.js';

// Open 20x5 field with walls around, spawn on the left.
const FIELD = [
  '####################',
  '#..................#',
  '#P.................#',
  '#..................#',
  '####################',
];

const right = { moveX: 1, moveY: 0, dash: false };

/** Simulates `seconds` of real time at a given display frame rate. */
function simulate(fps, seconds, input) {
  const state = createGameState(FIELD);
  const loop = new FixedStepLoop();
  const frameMs = 1000 / fps;
  for (let i = 0; i < Math.round(seconds * fps); i++) loop.advance(frameMs, () => stepGame(state, input));
  return state;
}

describe('player movement', () => {
  it('reaches walk speed and moves right', () => {
    const s = simulate(60, 1, right);
    expect(s.player.facing).toBe('right');
    // ~1s at 72 px/s minus a short acceleration ramp
    expect(s.player.x - 24).toBeGreaterThan(PLAYER_MOVE.walkSpeed * 0.9);
    expect(s.player.x - 24).toBeLessThan(PLAYER_MOVE.walkSpeed * 1.01);
  });

  it('moves the same distance at 30fps and 60fps (game speed independent of frame rate)', () => {
    const a = simulate(60, 1.5, right).player;
    const b = simulate(30, 1.5, right).player;
    const c = simulate(120, 1.5, right).player;
    expect(b.x).toBeCloseTo(a.x, 6);
    expect(c.x).toBeCloseTo(a.x, 6);
    expect(b.y).toBeCloseTo(a.y, 6);
  });

  it('dashes faster than walking', () => {
    const start = createGameState(FIELD).player.x;
    const walk = simulate(60, 0.8, right).player.x - start;
    const dash = simulate(60, 0.8, { ...right, dash: true }).player.x - start;
    expect(dash).toBeGreaterThan(walk * 1.5);
  });

  it('dash button alone does not move or flag dashing', () => {
    const s = simulate(60, 0.5, { moveX: 0, moveY: 0, dash: true });
    expect(s.player.dashing).toBe(false);
    expect(s.player.moving).toBe(false);
  });

  it('a light stick tilt walks slower than a full tilt', () => {
    const slow = simulate(60, 1, { moveX: 0.4, moveY: 0, dash: false }).player.x;
    const fast = simulate(60, 1, right).player.x;
    expect(slow).toBeLessThan(fast);
    expect(slow).toBeGreaterThan(24);
  });

  it('decelerates to a stop after input is released', () => {
    const state = createGameState(FIELD);
    for (let i = 0; i < 60; i++) stepGame(state, right);
    for (let i = 0; i < 30; i++) stepGame(state, { moveX: 0, moveY: 0, dash: false });
    expect(state.player.vx).toBe(0);
    expect(state.player.moving).toBe(false);
  });

  it('is stopped by the wall and records previous position for interpolation', () => {
    const s = simulate(60, 6, { ...right, dash: true });
    expect(s.player.x).toBe(19 * 16 - s.player.halfWidth);
    expect(s.player.prevX).toBe(s.player.x);
  });
});

describe('facingFrom', () => {
  it('uses the dominant axis', () => {
    expect(facingFrom(1, 0.2, 'down')).toBe('right');
    expect(facingFrom(-0.1, -1, 'down')).toBe('up');
  });
  it('keeps the current facing on exact diagonals when it matches', () => {
    expect(facingFrom(1, 1, 'right')).toBe('right');
    expect(facingFrom(1, 1, 'down')).toBe('down');
    expect(facingFrom(1, 1, 'up')).toBe('down');
  });
  it('keeps facing with no input', () => {
    expect(facingFrom(0, 0, 'left')).toBe('left');
  });
});

describe('normalizeStick', () => {
  it('ignores input inside the dead zone', () => {
    expect(normalizeStick(STICK_DEADZONE * 0.9, 0)).toEqual({ x: 0, y: 0 });
  });
  it('clamps to the unit circle', () => {
    const v = normalizeStick(3, 4);
    expect(Math.hypot(v.x, v.y)).toBeCloseTo(1, 6);
  });
  it('ramps smoothly from the dead zone edge', () => {
    const v = normalizeStick(STICK_DEADZONE + 0.01, 0);
    expect(v.x).toBeGreaterThan(0);
    expect(v.x).toBeLessThan(0.05);
  });
});
