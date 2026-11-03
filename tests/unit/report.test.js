import { describe, it, expect } from 'vitest';
import { buildReport } from '../../src/debug/report.js';

const base = {
  version: '0.0.1',
  commit: 'abc1234',
  dateIso: '2026-11-03T00:00:00.000Z',
  durationSec: 1,
  cpu: [],
  drawCalls: [3, 5],
  sprites: 1000,
  textures: 4,
  errors: 0,
  device: { GPU: 'Apple GPU', UserAgent: 'a|b' },
};

describe('buildReport', () => {
  it('produces a markdown table with key metrics', () => {
    const md = buildReport({ ...base, intervals: Array(60).fill(1000 / 60) });
    expect(md).toContain('### 計測レポート');
    expect(md).toContain('| 平均 FPS | 60.0 |');
    expect(md).toContain('| 描画呼び出し数（平均） | 4.0 |');
    expect(md).toContain('60fps 目標を達成');
    expect(md).toContain('| GPU | Apple GPU |');
  });

  it('escapes pipes in device values so the table stays valid', () => {
    const md = buildReport({ ...base, intervals: [16] });
    expect(md).toContain('| UserAgent | a/b |');
  });

  it('grades 30fps and below', () => {
    expect(buildReport({ ...base, intervals: Array(30).fill(1000 / 30) })).toContain('30fps 以上');
    expect(buildReport({ ...base, intervals: Array(20).fill(50) })).toContain('30fps 未満');
  });
});
