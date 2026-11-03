import { describe, it, expect } from 'vitest';
import { FrameStats, summarize, percentile } from '../../src/debug/frameStats.js';

describe('percentile', () => {
  it('returns 0 for empty input', () => {
    expect(percentile([], 0.95)).toBe(0);
  });
  it('uses nearest rank', () => {
    const values = Array.from({ length: 100 }, (_, i) => i + 1); // 1..100
    expect(percentile(values, 0.95)).toBe(95);
    expect(percentile(values, 1)).toBe(100);
    expect(percentile([5], 0.95)).toBe(5);
  });
  it('does not mutate input', () => {
    const v = [3, 1, 2];
    percentile(v, 0.5);
    expect(v).toEqual([3, 1, 2]);
  });
});

describe('summarize', () => {
  it('handles empty input', () => {
    expect(summarize([]).fps).toBe(0);
  });
  it('computes fps and frame time stats for a steady 60fps run', () => {
    const s = summarize(Array(60).fill(1000 / 60), Array(60).fill(2));
    expect(s.fps).toBeCloseTo(60, 5);
    expect(s.avgMs).toBeCloseTo(16.667, 2);
    expect(s.p95Ms).toBeCloseTo(16.667, 2);
    expect(s.avgCpuMs).toBe(2);
    expect(s.over33Pct).toBe(0);
  });
  it('treats a steady 30fps run as not below 30fps', () => {
    const s = summarize(Array(30).fill(1000 / 30));
    expect(s.fps).toBeCloseTo(30, 5);
    expect(s.over33Pct).toBe(0);
  });
  it('counts frames slower than 30fps', () => {
    const s = summarize([16, 16, 50, 16]);
    expect(s.over33Pct).toBe(25);
    expect(s.maxMs).toBe(50);
  });
});

describe('FrameStats ring buffer', () => {
  it('keeps only the latest samples', () => {
    const fs = new FrameStats(4);
    [10, 10, 10, 10, 20, 20].forEach((v) => fs.push(v));
    const s = fs.summary();
    expect(s.frames).toBe(4);
    expect(s.avgMs).toBe(15);
  });
  it('ignores invalid samples and resets', () => {
    const fs = new FrameStats(4);
    fs.push(0);
    fs.push(-5);
    fs.push(NaN);
    expect(fs.summary().frames).toBe(0);
    fs.push(16);
    fs.reset();
    expect(fs.summary().frames).toBe(0);
  });
});
