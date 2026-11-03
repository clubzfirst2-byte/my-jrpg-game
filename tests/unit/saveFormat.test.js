import { describe, it, expect } from 'vitest';
import {
  SCHEMA_VERSION,
  makeEnvelope,
  isIntact,
  migrate,
  chooseSave,
  classifyError,
  failureMessage,
  fnv1a,
} from '../../src/save/saveFormat.js';

const data = { openedChests: ['cave'], checkpoints: ['hill'], checkpoint: 'hill', landmarks: ['tower'], treasures: 1, maxHp: 16 };

describe('envelope', () => {
  it('records versions and verifies with its checksum', () => {
    const e = makeEnvelope(data, '0.0.1', 3, 1000);
    expect(e.schemaVersion).toBe(SCHEMA_VERSION);
    expect(e.gameVersion).toBe('0.0.1');
    expect(isIntact(e)).toBe(true);
  });

  it('detects any change to the data (corruption)', () => {
    const e = makeEnvelope(data, '0.0.1', 3, 1000);
    const tampered = { ...e, data: { ...e.data, treasures: 99 } };
    expect(isIntact(tampered)).toBe(false);
    expect(isIntact(null)).toBe(false);
    expect(isIntact({})).toBe(false);
  });

  it('fnv1a is stable', () => {
    expect(fnv1a('abc')).toBe(fnv1a('abc'));
    expect(fnv1a('abc')).not.toBe(fnv1a('abd'));
  });
});

describe('choosing a generation', () => {
  const older = makeEnvelope({ ...data, treasures: 1 }, '0.0.1', 4, 1000);
  const newer = makeEnvelope({ ...data, treasures: 2 }, '0.0.1', 5, 2000);

  it('empty when nothing was saved', () => {
    expect(chooseSave(null, null)).toEqual({ status: 'empty' });
  });

  it('loads the newest intact generation', () => {
    const r = chooseSave(older, newer);
    expect(r.status).toBe('ok');
    expect(r.data.treasures).toBe(2);
    expect(r.recovered).toBe(false);
  });

  it('falls back to the other generation when the newest is damaged (and says so)', () => {
    const damaged = { ...newer, data: { ...newer.data, treasures: 7 } };
    const r = chooseSave(older, damaged);
    expect(r.status).toBe('ok');
    expect(r.data.treasures).toBe(1);
    expect(r.recovered).toBe(true);
  });

  it('reports corruption when nothing is intact', () => {
    expect(chooseSave({ seq: 1 }, { seq: 2, checksum: 'x' }).status).toBe('corrupt');
  });

  it('refuses a save from a newer game version (and does not destroy it)', () => {
    // An intact envelope (valid checksum) written by a newer schema.
    const f = { schemaVersion: SCHEMA_VERSION + 1, gameVersion: '9.9.9', savedAt: 3000, seq: 9, data };
    const future = { ...f, checksum: fnv1a(JSON.stringify([f.schemaVersion, f.gameVersion, f.savedAt, f.seq, f.data])) };
    expect(isIntact(future)).toBe(true);
    expect(chooseSave(null, future).status).toBe('newer');
  });
});

describe('migrations', () => {
  it('applies each step in order from an older schema', () => {
    const env = { ...makeEnvelope({ hearts: 3 }, '0.0.1', 1, 0), schemaVersion: SCHEMA_VERSION - 2 };
    const steps = {
      [SCHEMA_VERSION - 2]: (d) => ({ ...d, step1: true }),
      [SCHEMA_VERSION - 1]: (d) => ({ maxHp: d.hearts * 4, step1: d.step1 }),
    };
    const r = migrate(env, steps);
    expect(r).toEqual({ ok: true, data: { maxHp: 12, step1: true } });
  });

  it('fails clearly when a step is missing', () => {
    const env = { ...makeEnvelope({}, '0.0.1', 1, 0), schemaVersion: SCHEMA_VERSION - 1 };
    expect(migrate(env, {})).toEqual({ ok: false, reason: 'missingMigration' });
  });

  it('current saves need no migration', () => {
    expect(migrate(makeEnvelope(data, '0.0.1', 1, 0))).toEqual({ ok: true, data });
  });
});

describe('errors', () => {
  it('classifies storage errors into user-facing reasons', () => {
    expect(classifyError({ name: 'QuotaExceededError' })).toBe('quota');
    expect(classifyError({ name: 'InvalidStateError' })).toBe('unavailable');
    expect(classifyError(new Error('boom'))).toBe('unknown');
    for (const r of ['quota', 'unavailable', 'unknown']) expect(failureMessage(r)).toMatch(/保存できませんでした/);
  });
});
