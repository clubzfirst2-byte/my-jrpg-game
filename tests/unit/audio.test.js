import { describe, it, expect } from 'vitest';
import { EVENT_SFX, sfxFor, chooseTrack, TRACKS, barNotes, freq } from '../../src/audio/cues.js';
import { AudioEngine } from '../../src/audio/audioEngine.js';

// P11.2: what sounds when, and that every sound is really made (with a stand-in for Web Audio).

/** A tiny fake of the Web Audio graph: counts what gets made and started. */
function fakeContext() {
  const made = { osc: 0, gain: 0, filter: 0, source: 0, started: 0 };
  const param = () => ({ value: 1, setValueAtTime() {}, linearRampToValueAtTime() {}, exponentialRampToValueAtTime() {}, setTargetAtTime() {} });
  const node = (extra = {}) => ({ connect: (n) => n, disconnect() {}, ...extra });
  const ctx = {
    state: 'running',
    currentTime: 0,
    sampleRate: 8000,
    destination: node(),
    createGain: () => (made.gain++, node({ gain: param() })),
    createOscillator: () => (made.osc++, node({ type: 'sine', frequency: param(), start: () => made.started++, stop() {} })),
    createBiquadFilter: () => (made.filter++, node({ type: 'lowpass', frequency: param() })),
    createBufferSource: () => (made.source++, node({ buffer: null, start: () => made.started++, stop() {} })),
    createBuffer: (_c, n) => ({ getChannelData: () => new Float32Array(n) }),
    resume: async () => {},
    suspend: async () => {},
  };
  return { ctx, made };
}
function engineWithFake() {
  const e = new AudioEngine();
  const { ctx, made } = fakeContext();
  e.ctx = /** @type {any} */ (ctx);
  e.sfxGain = ctx.createGain();
  e.musicGain = ctx.createGain();
  e.noiseBuf = ctx.createBuffer(1, 8000, 8000);
  return { e, ctx, made };
}

describe('sound effects', () => {
  it('game events map to sounds; unknown events are silent', () => {
    expect(sfxFor({ type: 'swing' })).toBe('swing');
    expect(sfxFor({ type: 'bossDown' })).toBe('fanfare');
    expect(sfxFor({ type: 'nothingLikeThis' })).toBe(null);
  });

  it('every event sound has a recipe that really makes sound', () => {
    for (const id of new Set(Object.values(EVENT_SFX))) {
      const { e, made } = engineWithFake();
      e.play(id);
      expect(made.started, id).toBeGreaterThan(0);
    }
  });

  it('the same sound is not stacked within 40 ms; nothing plays before sound is allowed', () => {
    const { e, ctx, made } = engineWithFake();
    e.play('hit');
    const once = made.started;
    e.play('hit');
    expect(made.started).toBe(once);
    ctx.currentTime = 0.1;
    e.play('hit');
    expect(made.started).toBeGreaterThan(once);
    const locked = new AudioEngine();
    locked.play('hit'); // no context yet (before the first touch): no error, counted only
    expect(locked.stats().unlocked).toBe(false);
    expect(locked.stats().sfxPlayed).toBe(1);
  });
});

describe('music', () => {
  const base = { inTitle: false, boss: false, area: null, region: 'plains', hour: 12 };
  it('fits where the player is: title, boss, houses, caves, night, desert, snow, fields', () => {
    expect(chooseTrack({ ...base, inTitle: true })).toBe('title');
    expect(chooseTrack({ ...base, boss: true, hour: 23 })).toBe('boss');
    expect(chooseTrack({ ...base, area: { id: 'inn', home: true } })).toBe('village');
    expect(chooseTrack({ ...base, area: { id: 'mine_1', dark: true } })).toBe('cave');
    expect(chooseTrack({ ...base, hour: 22 })).toBe('night');
    expect(chooseTrack({ ...base, hour: 3 })).toBe('night');
    expect(chooseTrack({ ...base, region: 'desert' })).toBe('desert');
    expect(chooseTrack({ ...base, region: 'mountains' })).toBe('snow');
    expect(chooseTrack({ ...base, region: 'forest' })).toBe('field');
  });

  it('every track plays the same notes every time, in a sensible range', () => {
    for (const id of Object.keys(TRACKS)) {
      for (let bar = 0; bar < 16; bar++) {
        const a = barNotes(id, bar);
        expect(barNotes(id, bar)).toEqual(a);
        expect(a.arp).toHaveLength(8);
        for (const n of [a.bass, ...a.arp, ...a.lead].filter((x) => x !== null)) {
          expect(freq(n)).toBeGreaterThan(40);
          expect(freq(n)).toBeLessThan(4200);
        }
      }
    }
    expect(freq(69)).toBe(440);
  });

  it('switching tracks crossfades: the old one fades, the new one plays; the same track is not restarted', () => {
    const { e, ctx, made } = engineWithFake();
    e.setTrack('field');
    e.setTrack('field');
    expect(e.tracks).toHaveLength(1);
    ctx.currentTime = 0.5;
    e.schedule();
    expect(made.started).toBeGreaterThan(0);
    e.setTrack('boss');
    expect(e.stats().playing).toEqual(['boss']);
    expect(e.tracks.filter((t) => t.fading).map((t) => t.id)).toEqual(['field']);
  });

  it('volumes and pausing', () => {
    const { e } = engineWithFake();
    e.setVolumes({ bgm: 0.25 });
    expect(e.stats().volumes).toEqual({ bgm: 0.25, sfx: 0.8 });
    e.suspend();
    expect(e.suspended).toBe(true);
    e.resume();
    expect(e.suspended).toBe(false);
  });
});
