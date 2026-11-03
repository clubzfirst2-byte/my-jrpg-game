// @ts-check
// Fixed-timestep loop with an accumulator (DESIGN.md 1.3).
// Logic always advances in 1/60 s steps, so game speed does not depend on the display frame rate.

export const STEP_MS = 1000 / 60;
export const STEP_SEC = 1 / 60;
/** Max logic steps per rendered frame; beyond this, time is dropped instead of "warping". */
export const MAX_STEPS_PER_FRAME = 4;
/** Frame deltas above this are clamped (e.g. after a long hitch). */
export const MAX_FRAME_MS = 250;

export class FixedStepLoop {
  constructor() {
    this.accumulator = 0;
    this.totalSteps = 0;
    this.droppedMs = 0;
  }

  /**
   * Advances logic by the elapsed real time.
   * @param {number} frameMs real time since the previous frame
   * @param {() => void} step called once per fixed step
   * @returns {{ steps: number, alpha: number }} alpha = interpolation factor between previous and current state
   */
  advance(frameMs, step) {
    const dt = Math.min(Math.max(0, frameMs), MAX_FRAME_MS);
    this.accumulator += dt;
    let steps = 0;
    // Small epsilon so 2 x 16.666.. ms reliably yields 2 steps despite float error.
    while (this.accumulator + 1e-6 >= STEP_MS && steps < MAX_STEPS_PER_FRAME) {
      step();
      this.accumulator -= STEP_MS;
      steps++;
    }
    if (this.accumulator < 0) this.accumulator = 0;
    if (this.accumulator >= STEP_MS) {
      this.droppedMs += this.accumulator;
      this.accumulator = 0;
    }
    this.totalSteps += steps;
    return { steps, alpha: this.accumulator / STEP_MS };
  }

  /** Discards pending time (used when resuming from pause / background). */
  reset() {
    this.accumulator = 0;
  }
}
