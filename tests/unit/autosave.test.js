import { describe, it, expect } from 'vitest';
import { Autosave, AUTOSAVE_INTERVAL_MS } from '../../src/save/autosave.js';

function fakeStore(results) {
  const saved = [];
  return {
    saved,
    async save(data) {
      saved.push(data);
      return results.shift() ?? { ok: true };
    },
  };
}

describe('autosave', () => {
  it('does nothing until enabled (title screen, test maps)', async () => {
    const store = fakeStore([]);
    const a = new Autosave(store, () => ({ n: 1 }), () => {});
    a.update({ saveRequested: true }, AUTOSAVE_INTERVAL_MS * 2);
    expect(await a.saveNow()).toBe(false);
    expect(store.saved).toHaveLength(0);
  });

  it('saves when the game asks, and every minute of play', async () => {
    const store = fakeStore([]);
    const a = new Autosave(store, () => ({ n: 1 }), () => {});
    a.enabled = true;
    const state = { saveRequested: true };
    a.update(state, 16);
    expect(state.saveRequested).toBe(false);
    await Promise.resolve();
    expect(store.saved).toHaveLength(1);
    a.update(state, AUTOSAVE_INTERVAL_MS - 100);
    expect(store.saved).toHaveLength(1);
    a.update(state, 200);
    expect(store.saved).toHaveLength(2);
  });

  it('tells the player once per kind of failure', async () => {
    const store = fakeStore([{ ok: false, reason: 'quota' }, { ok: false, reason: 'quota' }, { ok: true }, { ok: false, reason: 'quota' }]);
    const messages = [];
    const a = new Autosave(store, () => ({}), (m) => messages.push(m));
    a.enabled = true;
    expect(await a.saveNow()).toBe(false);
    expect(await a.saveNow()).toBe(false);
    expect(messages).toHaveLength(1);
    expect(messages[0]).toMatch(/空き容量/);
    expect(await a.saveNow()).toBe(true);
    expect(await a.saveNow()).toBe(false);
    expect(messages).toHaveLength(2); // a new failure after a success is reported again
    expect(a.failures).toBe(3);
  });
});
