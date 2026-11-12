// @ts-check
// Graphics v3 (?v3=1): the hero at density 4 (src/art-release-v3/hero, docs/art-release-v3/NAMES.md 5;
// the same keys, frame counts, fps and feet as the approved hero, twice the pixels).
//   - Left: only attack1–3, bow and guard have `left` files; every other action's left frame is its
//     right frame mirrored (scale.x = −1 about the frame's centre, the feet stay put).
//   - Memory (STYLE.md 10.2, decision 2026-11-12): the hero has two bundles of his own, packed without
//     the frames' transparent margins (placeholderPack opaqueBox / Texture orig + trim: a frame keeps its
//     size and its feet). "v3:hero" holds every action but climb, swim and glide and is kept for the whole
//     game (under 6.0 MB); "v3:hero:move" holds climb, swim and glide and is loaded when one of them starts
//     (gameView.updateHeroMove), let go a while after the last use. Until it is in, those actions are drawn
//     with the approved hero's frames, kept in the base bundle under "v1.<key>" (blown up 2×2 like the
//     rest of the density-2 art): the hero never stops or vanishes while it loads.
// Pure (no PixiJS): the unit tests read it.

/** The actions loaded only when used. */
export const HERO_V3_LAZY = Object.freeze(['climb', 'swim', 'glide']);

/** The actions with real left frames (a held prop). */
export const HERO_V3_OWN_LEFT = Object.freeze(['attack1', 'attack2', 'attack3', 'bow', 'guard']);

/** The bundle kept all the time, and the one loaded on use. */
export const HERO_V3_BUNDLE = 'v3:hero';
export const HERO_V3_MOVE_BUNDLE = 'v3:hero:move';

/** How long the move bundle stays after its last use (ms of real time). */
export const HERO_V3_MOVE_KEEP_MS = 20_000;

/** The key of an approved (v1) frame kept as the stand-in while the move bundle loads. @param {string} key */
export const heroFallbackKey = (key) => `v1.${key}`;

const HERO_KEY = /^hero\.([a-z0-9]+)\.(down|up|right|left)\.(\d+)$/;

/** A hero frame key's action, or null. @param {string} key */
export function heroActionOf(key) {
  return HERO_KEY.exec(key)?.[1] ?? null;
}

/** Which v3 hero bundle a frame goes in. @param {string} key @returns {string | null} */
export function heroV3BundleOf(key) {
  const a = heroActionOf(key);
  if (!a) return null;
  return HERO_V3_LAZY.includes(a) ? HERO_V3_MOVE_BUNDLE : HERO_V3_BUNDLE;
}

/**
 * The v3 hero's frames and the left frames drawn mirrored, for one bundle.
 * @param {Iterable<string>} v3Keys the hero keys that have v3 art (density 4)
 * @param {string} bundle HERO_V3_BUNDLE or HERO_V3_MOVE_BUNDLE
 * @returns {{ keys: string[], mirrorOf: Map<string, string> }} keys: stored frames (sorted); mirrorOf: left key → right key
 */
export function heroV3Parts(v3Keys, bundle) {
  const all = new Set([...v3Keys].filter((k) => heroV3BundleOf(k) === bundle));
  const keys = [...all].sort();
  /** @type {Map<string, string>} */
  const mirrorOf = new Map();
  for (const k of keys) {
    if (!k.includes('.right.')) continue;
    const left = k.replace('.right.', '.left.');
    const action = /** @type {string} */ (heroActionOf(k));
    // (attack1–3, bow and guard keep their own left frames: NAMES.md 5)
    if (all.has(left) || HERO_V3_OWN_LEFT.includes(action)) continue;
    mirrorOf.set(left, k);
  }
  return { keys, mirrorOf };
}

/**
 * Whether a hero frame key is drawn by the v3 hero (it is a v3 frame, or a left frame mirroring one), so
 * the base bundle need not keep the approved frame of that name.
 * @param {string} key @param {Set<string>} v3Keys
 */
export function heroCoveredByV3(key, v3Keys) {
  if (v3Keys.has(key)) return true;
  const a = heroActionOf(key);
  return !!a && key.includes('.left.') && !HERO_V3_OWN_LEFT.includes(a) && v3Keys.has(key.replace('.left.', '.right.'));
}

/**
 * The frame to draw for a hero key: the key itself when loaded, else its approved stand-in (the move
 * bundle not in yet), else null. @param {string} key @param {(k: string) => boolean} has
 */
export function heroDrawKey(key, has) {
  if (has(key)) return key;
  const f = heroFallbackKey(key);
  return has(f) ? f : null;
}
