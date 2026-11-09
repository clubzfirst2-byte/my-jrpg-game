// @ts-check
// P11.2: what sounds when (pure: no Web Audio here, unit-tested). The game never plays sounds
// itself: the audio layer listens to the game's events and to where the player is.

/** Game event -> sound effect. Events not listed are silent. */
export const EVENT_SFX = Object.freeze({
  swing: 'swing',
  hitEnemy: 'hit',
  enemyDown: 'defeat',
  hurt: 'hurt',
  justDodge: 'perfect',
  parry: 'parry',
  block: 'block',
  dodge: 'dodge',
  land: 'land',
  shoot: 'bow',
  fireArrow: 'ignite',
  ignite: 'ignite',
  enemyShoot: 'enemyShot',
  pickup: 'pickup',
  chest: 'chest',
  checkpoint: 'checkpoint',
  landmark: 'discover',
  gateOpen: 'gate',
  switchOn: 'switch',
  sconceLit: 'ignite',
  crateMoved: 'thud',
  ability: 'ability',
  noAbility: 'deny',
  full: 'deny',
  questStart: 'quest',
  questDone: 'fanfare',
  talk: 'talk',
  warp: 'door',
  lightning: 'thunder',
  strikeWarn: 'warn',
  fell: 'fall',
  drown: 'splash',
  death: 'death',
  slept: 'sleep',
  season: 'chime',
  bossAwake: 'bossRoar',
  bossPhase: 'bossRoar',
  bossStun: 'parry',
  bossDown: 'fanfare',
  // v1.0: 淀みの源 (sounds of the cores' fight).
  sourceAwake: 'bossRoar',
  sourcePhase: 'bossRoar',
  seatOn: 'switch',
  sourceStagger: 'gate',
  sourceGuard: 'block',
  sourceWave: 'warn',
  sourcePurified: 'fanfare',
  broke: 'break',
});

/** @param {{ type: string }} event @returns {string | null} */
export function sfxFor(event) {
  return /** @type {Record<string, string>} */ (EVENT_SFX)[event.type] ?? null;
}

/**
 * Which music fits where the player is.
 * @param {{ inTitle: boolean, boss: boolean, area: { id: string, dark?: boolean, home?: boolean } | null,
 *   region: string | null, hour: number }} where
 * @returns {'title' | 'boss' | 'village' | 'cave' | 'night' | 'desert' | 'snow' | 'field'}
 */
export function chooseTrack(where) {
  if (where.inTitle) return 'title';
  if (where.boss) return 'boss';
  if (where.area?.home) return 'village';
  if (where.area) return 'cave'; // caves, trials, the mine
  if (where.hour >= 20 || where.hour < 5) return 'night';
  if (where.region === 'desert') return 'desert';
  if (where.region === 'mountains') return 'snow';
  return 'field';
}

/**
 * The tracks: tempo, key, mode and the chord progression (scale degrees, 0-based); the music
 * engine plays a bass, an arpeggio over the chord and a light melody drawn from the chord.
 * @type {Record<string, { bpm: number, root: number, mode: number[], chords: number[], lead: OscillatorType, pad: OscillatorType, density: number, gain: number }>}
 */
export const TRACKS = {
  //            bpm   root(midi) mode                        chords (degrees)        lead        pad
  title: { bpm: 72, root: 57, mode: [0, 2, 4, 7, 9, 12, 14], chords: [0, 3, 4, 3], lead: 'triangle', pad: 'sine', density: 0.35, gain: 0.8 },
  field: { bpm: 96, root: 60, mode: [0, 2, 4, 5, 7, 9, 11], chords: [0, 4, 5, 3], lead: 'square', pad: 'triangle', density: 0.6, gain: 0.7 },
  desert: { bpm: 88, root: 62, mode: [0, 1, 4, 5, 7, 8, 10], chords: [0, 1, 0, 6], lead: 'sawtooth', pad: 'triangle', density: 0.5, gain: 0.55 },
  snow: { bpm: 76, root: 64, mode: [0, 2, 3, 5, 7, 9, 10], chords: [0, 5, 3, 4], lead: 'triangle', pad: 'sine', density: 0.4, gain: 0.75 },
  night: { bpm: 64, root: 57, mode: [0, 2, 3, 5, 7, 8, 10], chords: [0, 5, 3, 6], lead: 'sine', pad: 'sine', density: 0.25, gain: 0.8 },
  cave: { bpm: 56, root: 50, mode: [0, 1, 3, 5, 7, 8, 10], chords: [0, 0, 5, 6], lead: 'sine', pad: 'triangle', density: 0.2, gain: 0.8 },
  village: { bpm: 108, root: 65, mode: [0, 2, 4, 5, 7, 9, 11], chords: [0, 3, 4, 0], lead: 'square', pad: 'triangle', density: 0.7, gain: 0.6 },
  boss: { bpm: 144, root: 52, mode: [0, 2, 3, 5, 7, 8, 11], chords: [0, 5, 6, 4], lead: 'sawtooth', pad: 'square', density: 0.85, gain: 0.5 },
};

/**
 * The notes of one bar (deterministic: the same track always sounds the same). 8 steps per bar.
 * @param {string} trackId @param {number} bar
 * @returns {{ bass: number, arp: (number | null)[], lead: (number | null)[], chord: number[] }}
 */
export function barNotes(trackId, bar) {
  const t = TRACKS[trackId];
  const deg = t.chords[bar % t.chords.length];
  const note = (/** @type {number} */ d) => t.root + t.mode[d % 7] + 12 * Math.floor(d / 7);
  const chord = [note(deg), note(deg + 2), note(deg + 4)];
  const arp = [0, 1, 2, 1, 0, 1, 2, 1].map((k, i) => (i % 2 === 0 || t.density > 0.5 ? chord[k] + 12 : null));
  const lead = [];
  for (let i = 0; i < 8; i++) {
    const r = hash(bar * 31 + i * 7 + trackId.length);
    lead.push(r < t.density * 0.5 ? note(deg + [0, 2, 4, 7][Math.floor(hash(bar + i * 13) * 4)]) + 24 : null);
  }
  return { bass: chord[0] - 12, arp, lead, chord };
}

/** @param {number} n */
function hash(n) {
  const x = Math.sin(n * 12.9898) * 43758.5453;
  return x - Math.floor(x);
}

/** @param {number} midi */
export const freq = (midi) => 440 * Math.pow(2, (midi - 69) / 12);
