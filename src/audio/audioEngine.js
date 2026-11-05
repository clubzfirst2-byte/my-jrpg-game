// @ts-check
// P11.2: sound effects and music, synthesized with Web Audio (no audio files: nothing to download,
// and it works offline). iOS only lets a page make sound after a touch, so the engine starts on
// the first tap / key press. The game never calls this directly: main.js plays the sound of each
// game event (cues.js) and picks the music for where the player is.
import { TRACKS, barNotes, freq } from './cues.js';

const STEPS_PER_BAR = 8;
const LOOKAHEAD_S = 0.25;

export class AudioEngine {
  constructor() {
    /** @type {AudioContext | null} */
    this.ctx = null;
    /** @type {GainNode | null} */
    this.sfxGain = null;
    /** @type {GainNode | null} */
    this.musicGain = null;
    /** @type {AudioBuffer | null} */
    this.noiseBuf = null;
    this.volumes = { bgm: 0.5, sfx: 0.8 };
    /** @type {{ id: string, gain: GainNode, next: number, step: number, bar: number, fading: boolean }[]} */
    this.tracks = [];
    /** The track that should be playing (set even before sound is unlocked). */
    this.wanted = '';
    /** @type {Map<string, number>} */
    this.lastPlayed = new Map();
    this.sfxPlayed = 0;
    this.lastSfx = '';
    this.suspended = false;
    /** @type {ReturnType<typeof setInterval> | null} */
    this.timer = null;
  }

  /** Starts sound (call from a user gesture). Safe to call again. */
  unlock() {
    if (!this.ctx) {
      const AC = window.AudioContext ?? /** @type {any} */ (window).webkitAudioContext;
      if (!AC) return;
      this.ctx = new AC();
      const ctx = /** @type {AudioContext} */ (this.ctx);
      this.sfxGain = ctx.createGain();
      this.musicGain = ctx.createGain();
      this.sfxGain.connect(ctx.destination);
      this.musicGain.connect(ctx.destination);
      this.applyVolumes();
      // One second of white noise, reused by every noisy sound.
      this.noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
      const d = this.noiseBuf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
      this.timer = setInterval(() => this.schedule(), 50);
      if (this.wanted) this.setTrack(this.wanted, true);
    }
    if (!this.suspended && this.ctx.state === 'suspended') void this.ctx.resume();
  }

  get unlocked() {
    return !!this.ctx && this.ctx.state === 'running';
  }

  /** @param {{ bgm?: number, sfx?: number }} v 0..1 */
  setVolumes(v) {
    this.volumes = { ...this.volumes, ...v };
    this.applyVolumes();
  }

  applyVolumes() {
    if (!this.ctx || !this.sfxGain || !this.musicGain) return;
    const t = this.ctx.currentTime;
    this.sfxGain.gain.setTargetAtTime(this.volumes.sfx * 0.5, t, 0.02);
    this.musicGain.gain.setTargetAtTime(this.volumes.bgm * 0.22, t, 0.05);
  }

  /** Paused / in the background: silence everything. */
  suspend() {
    this.suspended = true;
    if (this.ctx && this.ctx.state === 'running') void this.ctx.suspend();
  }

  resume() {
    this.suspended = false;
    if (this.ctx && this.ctx.state === 'suspended') void this.ctx.resume();
  }

  // ---------------------------------------------------------------- music

  /** Crossfades to a track (no-op if it is already playing). @param {string} id @param {boolean} [force] */
  setTrack(id, force = false) {
    if (id === this.wanted && !force) return;
    this.wanted = id;
    const ctx = this.ctx;
    if (!ctx || !this.musicGain || !TRACKS[id]) return;
    const t = ctx.currentTime;
    for (const tr of this.tracks) {
      if (tr.fading) continue;
      tr.fading = true;
      tr.gain.gain.setTargetAtTime(0, t, 0.4);
    }
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0, t);
    gain.gain.setTargetAtTime(TRACKS[id].gain, t + 0.3, 0.6);
    gain.connect(this.musicGain);
    this.tracks.push({ id, gain, next: t + 0.35, step: 0, bar: 0, fading: false });
  }

  /** Schedules the notes of the next moments (a lookahead keeps timing tight despite timers). */
  schedule() {
    const ctx = this.ctx;
    if (!ctx || ctx.state !== 'running') return;
    const horizon = ctx.currentTime + LOOKAHEAD_S;
    for (const tr of this.tracks) {
      const def = TRACKS[tr.id];
      const stepS = 60 / def.bpm / 2;
      while (tr.next < horizon) {
        if (!tr.fading || tr.gain.gain.value > 0.002) this.playStep(tr, def, stepS);
        tr.next += stepS;
        tr.step++;
        if (tr.step % STEPS_PER_BAR === 0) tr.bar++;
      }
    }
    // Faded-out tracks are dropped.
    this.tracks = this.tracks.filter((tr) => {
      const gone = tr.fading && tr.gain.gain.value < 0.002 && ctx.currentTime > tr.next - 1;
      if (gone) tr.gain.disconnect();
      return !gone;
    });
  }

  /** @param {any} tr @param {typeof TRACKS.field} def @param {number} stepS */
  playStep(tr, def, stepS) {
    const notes = barNotes(tr.id, tr.bar);
    const i = tr.step % STEPS_PER_BAR;
    const t = tr.next;
    if (i % 4 === 0) this.note(tr.gain, 'triangle', freq(notes.bass), t, stepS * 3.6, 0.5);
    const a = notes.arp[i];
    if (a !== null) this.note(tr.gain, def.pad, freq(a), t, stepS * 0.9, 0.16);
    const l = notes.lead[i];
    if (l !== null) this.note(tr.gain, def.lead, freq(l), t, stepS * 1.6, 0.12);
    if (tr.id === 'boss' && i % 2 === 0) this.drum(tr.gain, t, i % 4 === 0);
  }

  /** @param {AudioNode} out @param {OscillatorType} type @param {number} f @param {number} t @param {number} dur @param {number} vol */
  note(out, type, f, t, dur, vol) {
    const ctx = /** @type {AudioContext} */ (this.ctx);
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f, t);
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(vol, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(out);
    o.start(t);
    o.stop(t + dur + 0.02);
  }

  /** @param {AudioNode} out @param {number} t @param {boolean} kick */
  drum(out, t, kick) {
    if (kick) this.sweep(out, 'sine', 140, 40, t, 0.18, 0.7);
    else this.noise(out, t, 0.06, 0.25, 5000, 'highpass');
  }

  // ---------------------------------------------------------------- sound effects

  /** Plays a sound effect (the same one at most every 40 ms). @param {string | null} id */
  play(id) {
    if (!id) return;
    const ctx = this.ctx;
    this.lastSfx = id;
    this.sfxPlayed++;
    if (!ctx || !this.sfxGain || ctx.state !== 'running') return;
    const now = ctx.currentTime;
    if (now - (this.lastPlayed.get(id) ?? -1) < 0.04) return;
    this.lastPlayed.set(id, now);
    const out = this.sfxGain;
    const t = now + 0.005;
    const S = this;
    const recipe = /** @type {Record<string, () => void>} */ ({
      swing: () => S.noise(out, t, 0.09, 0.35, 2600, 'bandpass', 900),
      hit: () => (S.sweep(out, 'square', 320, 90, t, 0.08, 0.35), S.noise(out, t, 0.05, 0.3, 1800, 'lowpass')),
      defeat: () => [523, 392, 262].forEach((f, k) => S.sweep(out, 'square', f, f * 0.7, t + k * 0.06, 0.09, 0.25)),
      hurt: () => S.sweep(out, 'sawtooth', 300, 80, t, 0.22, 0.4),
      perfect: () => [784, 1047, 1568].forEach((f, k) => S.sweep(out, 'triangle', f, f, t + k * 0.05, 0.12, 0.3)),
      parry: () => (S.sweep(out, 'square', 1400, 1100, t, 0.12, 0.3), S.noise(out, t, 0.08, 0.25, 4000, 'highpass')),
      block: () => S.noise(out, t, 0.07, 0.35, 1200, 'lowpass'),
      dodge: () => S.noise(out, t, 0.12, 0.2, 1500, 'bandpass', 3000),
      land: () => S.sweep(out, 'sine', 120, 60, t, 0.07, 0.25),
      bow: () => S.sweep(out, 'triangle', 700, 300, t, 0.1, 0.25),
      ignite: () => S.noise(out, t, 0.35, 0.3, 600, 'lowpass', 2400),
      enemyShot: () => S.sweep(out, 'sine', 500, 900, t, 0.12, 0.15),
      pickup: () => [880, 1320].forEach((f, k) => S.sweep(out, 'square', f, f, t + k * 0.05, 0.06, 0.18)),
      chest: () => [523, 659, 784, 1047].forEach((f, k) => S.sweep(out, 'triangle', f, f, t + k * 0.08, 0.16, 0.3)),
      checkpoint: () => [659, 988].forEach((f, k) => S.sweep(out, 'sine', f, f, t + k * 0.12, 0.4, 0.3)),
      discover: () => [587, 784, 1175].forEach((f, k) => S.sweep(out, 'triangle', f, f, t + k * 0.1, 0.3, 0.25)),
      gate: () => (S.sweep(out, 'sawtooth', 90, 60, t, 0.6, 0.25), S.noise(out, t, 0.6, 0.2, 400, 'lowpass')),
      switch: () => S.sweep(out, 'square', 660, 990, t, 0.08, 0.2),
      thud: () => S.sweep(out, 'sine', 160, 70, t, 0.12, 0.35),
      ability: () => [440, 660, 880].forEach((f, k) => S.sweep(out, 'sine', f, f * 1.5, t + k * 0.04, 0.2, 0.2)),
      deny: () => S.sweep(out, 'square', 180, 160, t, 0.12, 0.2),
      quest: () => [523, 784].forEach((f, k) => S.sweep(out, 'triangle', f, f, t + k * 0.1, 0.25, 0.3)),
      fanfare: () => [523, 659, 784, 1047, 784, 1047].forEach((f, k) => S.sweep(out, 'square', f, f, t + k * 0.09, k === 5 ? 0.5 : 0.1, 0.25)),
      talk: () => S.sweep(out, 'square', 600, 620, t, 0.04, 0.12),
      door: () => S.noise(out, t, 0.25, 0.25, 700, 'bandpass', 300),
      thunder: () => S.noise(out, t, 1.2, 0.6, 300, 'lowpass', 1200),
      warn: () => S.sweep(out, 'square', 1200, 1200, t, 0.05, 0.12),
      fall: () => S.sweep(out, 'sine', 600, 100, t, 0.5, 0.3),
      splash: () => S.noise(out, t, 0.4, 0.35, 1400, 'bandpass', 600),
      death: () => [392, 330, 262, 196].forEach((f, k) => S.sweep(out, 'triangle', f, f, t + k * 0.18, 0.3, 0.3)),
      sleep: () => [392, 330, 294, 262].forEach((f, k) => S.sweep(out, 'sine', f, f, t + k * 0.25, 0.5, 0.25)),
      chime: () => [1047, 1319, 1568, 2093].forEach((f, k) => S.sweep(out, 'sine', f, f, t + k * 0.12, 0.6, 0.18)),
      bossRoar: () => (S.sweep(out, 'sawtooth', 110, 55, t, 0.9, 0.45), S.noise(out, t, 0.8, 0.3, 500, 'lowpass')),
      break: () => S.noise(out, t, 0.25, 0.4, 3000, 'highpass'),
    })[id];
    recipe?.();
  }

  /** A tone sliding from f0 to f1. @param {AudioNode} out @param {OscillatorType} type @param {number} f0 @param {number} f1 @param {number} t @param {number} dur @param {number} vol */
  sweep(out, type, f0, f1, t, dur, vol) {
    const ctx = /** @type {AudioContext} */ (this.ctx);
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f0, t);
    if (f1 !== f0) o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur);
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(out);
    o.start(t);
    o.stop(t + dur + 0.02);
  }

  /**
   * Filtered noise (swishes, hits, fire, thunder); the filter can glide to `to`.
   * @param {AudioNode} out @param {number} t @param {number} dur @param {number} vol @param {number} cutoff @param {BiquadFilterType} type @param {number} [to]
   */
  noise(out, t, dur, vol, cutoff, type, to) {
    const ctx = /** @type {AudioContext} */ (this.ctx);
    const src = ctx.createBufferSource();
    src.buffer = this.noiseBuf;
    const f = ctx.createBiquadFilter();
    f.type = type;
    f.frequency.setValueAtTime(cutoff, t);
    if (to) f.frequency.exponentialRampToValueAtTime(to, t + dur);
    const g = ctx.createGain();
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.connect(f).connect(g).connect(out);
    src.start(t, Math.random() * 0.5);
    src.stop(t + dur + 0.02);
  }

  /** For the debug overlay and tests. */
  stats() {
    return {
      unlocked: this.unlocked,
      state: this.ctx?.state ?? 'none',
      track: this.wanted,
      playing: this.tracks.filter((t) => !t.fading).map((t) => t.id),
      sfxPlayed: this.sfxPlayed,
      lastSfx: this.lastSfx,
      volumes: { ...this.volumes },
    };
  }
}
