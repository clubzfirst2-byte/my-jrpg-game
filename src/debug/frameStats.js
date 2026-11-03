// @ts-check
// Rolling frame statistics. Pure: no browser APIs, so it can be unit tested in Node.

/**
 * @typedef {object} StatsSummary
 * @property {number} frames      samples in the window
 * @property {number} fps         average frames per second
 * @property {number} avgMs       average frame interval (ms)
 * @property {number} p95Ms       95th percentile frame interval (ms) = the slow 5%
 * @property {number} maxMs       slowest frame interval (ms)
 * @property {number} avgCpuMs    average JS time spent per frame (update + render submit)
 * @property {number} over33Pct   % of frames slower than 33.3ms (below 30fps)
 */

export class FrameStats {
  /** @param {number} capacity number of frames kept (ring buffer) */
  constructor(capacity = 240) {
    this.capacity = capacity;
    this.intervals = new Float64Array(capacity);
    this.cpu = new Float64Array(capacity);
    this.count = 0;
    this.head = 0;
  }

  /**
   * @param {number} intervalMs time since previous frame
   * @param {number} [cpuMs] JS work time for this frame
   */
  push(intervalMs, cpuMs = 0) {
    if (!Number.isFinite(intervalMs) || intervalMs <= 0) return;
    this.intervals[this.head] = intervalMs;
    this.cpu[this.head] = cpuMs;
    this.head = (this.head + 1) % this.capacity;
    if (this.count < this.capacity) this.count++;
  }

  reset() {
    this.count = 0;
    this.head = 0;
  }

  /** @returns {StatsSummary} */
  summary() {
    return summarize(Array.from(this.intervals.subarray(0, this.count)), Array.from(this.cpu.subarray(0, this.count)));
  }
}

/**
 * @param {number[]} intervals
 * @param {number[]} [cpu]
 * @returns {StatsSummary}
 */
export function summarize(intervals, cpu = []) {
  const n = intervals.length;
  if (n === 0) return { frames: 0, fps: 0, avgMs: 0, p95Ms: 0, maxMs: 0, avgCpuMs: 0, over33Pct: 0 };
  let sum = 0;
  let max = 0;
  let over = 0;
  for (const v of intervals) {
    sum += v;
    if (v > max) max = v;
    if (v > 1000 / 30 + 0.5) over++;
  }
  const cpuSum = cpu.reduce((a, b) => a + b, 0);
  const avg = sum / n;
  return {
    frames: n,
    fps: 1000 / avg,
    avgMs: avg,
    p95Ms: percentile(intervals, 0.95),
    maxMs: max,
    avgCpuMs: cpu.length ? cpuSum / cpu.length : 0,
    over33Pct: (over / n) * 100,
  };
}

/**
 * Nearest-rank percentile.
 * @param {number[]} values
 * @param {number} p 0..1
 */
export function percentile(values, p) {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const rank = Math.ceil(p * sorted.length) - 1;
  return sorted[Math.min(sorted.length - 1, Math.max(0, rank))];
}
