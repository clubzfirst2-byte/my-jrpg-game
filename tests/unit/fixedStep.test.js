import { describe, it, expect } from 'vitest';
import { FixedStepLoop, STEP_MS, MAX_STEPS_PER_FRAME } from '../../src/game/core/fixedStep.js';

/** Runs `seconds` of real time split into frames of `frameMs`; returns the number of logic steps. */
function run(frameMs, seconds) {
  const loop = new FixedStepLoop();
  let steps = 0;
  const frames = Math.round((seconds * 1000) / frameMs);
  for (let i = 0; i < frames; i++) loop.advance(frameMs, () => steps++);
  return steps;
}

describe('FixedStepLoop', () => {
  it('runs 60 logic steps per second at 60fps, 30fps and 120fps', () => {
    expect(run(1000 / 60, 1)).toBe(60);
    expect(run(1000 / 30, 1)).toBe(60);
    expect(run(1000 / 120, 1)).toBe(60);
  });

  it('returns an interpolation factor between 0 and 1', () => {
    const loop = new FixedStepLoop();
    const { steps, alpha } = loop.advance(STEP_MS * 1.5, () => {});
    expect(steps).toBe(1);
    expect(alpha).toBeCloseTo(0.5, 5);
  });

  it('caps steps per frame and drops excess time instead of warping', () => {
    const loop = new FixedStepLoop();
    let steps = 0;
    const r = loop.advance(200, () => steps++);
    expect(r.steps).toBe(MAX_STEPS_PER_FRAME);
    expect(loop.accumulator).toBe(0);
    expect(loop.droppedMs).toBeGreaterThan(0);
  });

  it('clamps huge deltas (returning from background) and reset() discards pending time', () => {
    const loop = new FixedStepLoop();
    const r = loop.advance(60_000, () => {});
    expect(r.steps).toBe(MAX_STEPS_PER_FRAME);
    loop.advance(STEP_MS * 0.9, () => {});
    expect(loop.accumulator).toBeGreaterThan(0);
    loop.reset();
    expect(loop.accumulator).toBe(0);
  });

  it('accounts for every millisecond: simulated + dropped + pending == elapsed', () => {
    const loop = new FixedStepLoop();
    const frames = [16.7, 33.3, 400, 8, 120, 1000, 16.7, 50];
    for (const f of frames) loop.advance(f, () => {});
    const total = frames.reduce((a, b) => a + b, 0);
    expect(loop.elapsedMs).toBeCloseTo(total, 6);
    expect(loop.totalSteps * STEP_MS + loop.droppedMs + loop.accumulator).toBeCloseTo(total, 6);
  });

  it('ignores negative deltas', () => {
    const loop = new FixedStepLoop();
    expect(loop.advance(-50, () => {}).steps).toBe(0);
  });
});
