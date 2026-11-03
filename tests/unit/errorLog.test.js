import { describe, it, expect } from 'vitest';
import { ErrorLog, describe as describeErr } from '../../src/debug/errorLog.js';

describe('ErrorLog', () => {
  it('records entries and notifies listeners', () => {
    const log = new ErrorLog();
    const seen = [];
    log.onAdd((e) => seen.push(e));
    log.add('error', new Error('boom'), 12);
    expect(log.total).toBe(1);
    expect(log.entries[0].kind).toBe('error');
    expect(log.entries[0].message).toContain('boom');
    expect(seen).toHaveLength(1);
  });

  it('caps stored entries but keeps the total count', () => {
    const log = new ErrorLog(3);
    for (let i = 0; i < 5; i++) log.add('console', `e${i}`, i);
    expect(log.entries.map((e) => e.message)).toEqual(['e2', 'e3', 'e4']);
    expect(log.total).toBe(5);
  });
});

describe('describe()', () => {
  it('stringifies objects and handles circular values', () => {
    expect(describeErr({ a: 1 })).toBe('{"a":1}');
    const circular = {};
    circular.self = circular;
    expect(describeErr(circular)).toBe('[object Object]');
  });
});
