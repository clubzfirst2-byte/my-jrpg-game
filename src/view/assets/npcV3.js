// @ts-check
// Graphics v3 (?v3=1): the villagers at density 4 (src/art-release-v3/npc, docs/art-release-v3/NAMES.md 6;
// the same 9 people, keys, frame counts, fps and feet as the approved villagers, twice the pixels). Where
// each person's frames come from (branch, commit, final or provisional): tools/art_v3/npc_v3_sources.json.
//   - Left (NAMES.md 6, decision 2026-11-12): the princess and the smith store no `left` frame; theirs is
//     the `right` frame mirrored (scale.x = −1 about the frame's centre, the feet stay put). The other 7
//     use their stored left frames (a held thing changes hands: not a mirror).
//   - Memory (STYLE.md 10.2: 8.7 MB for the 9 people, 1 MB = 1,000,000 bytes): each person is a bundle of
//     its own, "v3:npc:<who>", packed without the frames' transparent margins (placeholderPack trim, the
//     build's opaque boxes). All 9 live in the plains region, so all 9 bundles are held while a loaded
//     chunk has a part of it, and let go away from it; elsewhere a person's bundle is held only while that
//     villager stands on a loaded chunk (the princess by the other regions' record stones). The base
//     bundle keeps no frame of a person drawn by v3.
//   - Until a person's bundle is in, that villager is not drawn (never the placeholder, never the approved
//     frames beside the v3 ones): npcAnim.npcFrameKey with `own`.
// Pure (no PixiJS): the unit tests read it.

/** The villagers' art names (v1.0: 9 people). */
export const NPC_V3_PEOPLE = Object.freeze(['child', 'cook', 'elder', 'guard', 'merchant', 'princess', 'smith', 'traveller', 'woman']);

/** The people whose left frames are their right frames mirrored (no `left` files: NAMES.md 6). */
export const NPC_V3_MIRROR_LEFT = Object.freeze(['princess', 'smith']);

/** The region all 9 live in (src/game/world/maps/regions.js): its chunks hold every person's bundle. */
export const NPC_V3_REGION = 'plains';

/** A person's bundle. @param {string} who */
export const npcV3Bundle = (who) => `v3:npc:${who}`;

const NPC_KEY = /^npc\.([a-z]+)\.(idle|walk)\.(down|up|right|left)\.(\d+)$/;

/** A villager frame key's person (art name), or null. @param {string} key */
export function npcWhoOf(key) {
  return NPC_KEY.exec(key)?.[1] ?? null;
}

/** The people who have v3 frames, sorted. @param {Iterable<string>} v3Keys the villager keys that have v3 art (density 4) */
export function npcV3People(v3Keys) {
  /** @type {Set<string>} */
  const out = new Set();
  for (const k of v3Keys) {
    const who = npcWhoOf(k);
    if (who) out.add(who);
  }
  return [...out].sort();
}

/**
 * One person's v3 frames and the left frames drawn mirrored.
 * @param {Iterable<string>} v3Keys the villager keys that have v3 art (density 4)
 * @param {string} who
 * @returns {{ keys: string[], mirrorOf: Map<string, string> }} keys: stored frames (sorted); mirrorOf: left key → right key
 */
export function npcV3Parts(v3Keys, who) {
  const all = new Set([...v3Keys].filter((k) => npcWhoOf(k) === who));
  const keys = [...all].sort();
  /** @type {Map<string, string>} */
  const mirrorOf = new Map();
  // (only the people NAMES.md 6 names: anyone else's missing left frame is a missing file, not a mirror)
  if (NPC_V3_MIRROR_LEFT.includes(who)) {
    for (const k of keys) {
      if (!k.includes('.right.')) continue;
      const left = k.replace('.right.', '.left.');
      if (!all.has(left)) mirrorOf.set(left, k);
    }
  }
  return { keys, mirrorOf };
}

/**
 * Whether a villager frame key belongs to a person drawn by v3, so the base bundle need not keep the
 * approved frame of that name (a person is drawn all v3 or not at all: an approved left frame never
 * stands beside v3 frames). @param {string} key @param {readonly string[]} people the people with v3 frames
 */
export function npcCoveredByV3(key, people) {
  const who = npcWhoOf(key);
  return !!who && people.includes(who);
}

/** A bundle name's person, or null. @param {string} bundle */
export function npcV3BundleWho(bundle) {
  return /^v3:npc:([a-z]+)$/.exec(bundle)?.[1] ?? null;
}
