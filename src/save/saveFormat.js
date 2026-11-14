// @ts-check
// Save data format (DESIGN.md 2.6): versioned envelope with a checksum, a migration chain, and the
// rule for picking which of the two alternating generations (A / B) to load. Pure: unit-tested.
import { nameIndexedDiff } from '../game/world/worldDiff.js';

/**
 * The object lists of P8-P10.2 (src/save/legacyObjects.js, 31 KB) are only needed to read saves of
 * those versions, so they are loaded on demand (P11.4): saveStore loads them before migrating an
 * old save; tests register them directly.
 * @type {string[][] | null}
 */
let legacyLists = null;
/** @param {Record<string, string>} objects */
export function useLegacyObjects(objects) {
  legacyLists = Object.values(objects).map((l) => l.split(' '));
}
/** Whether a stored envelope needs the old object lists to be read. @param {any} e */
export const needsLegacyObjects = (e) => !!e && typeof e.schemaVersion === 'number' && e.schemaVersion < 3;

/** Bump when the shape of `data` changes, and add a migration from the previous version. */
export const SCHEMA_VERSION = 4;

/**
 * Migrations from version N to N+1, applied in order when loading an older save.
 * @type {Record<number, (data: any) => any>}
 */
export const MIGRATIONS = {
  // v1 -> v2 (P6): "treasures" became money (星貨) and an inventory. Each old treasure is worth 50.
  1: (data) => {
    const { treasures = 0, ...rest } = data ?? {};
    return { ...rest, inv: { ...(rest.inv ?? {}), money: (rest.inv?.money ?? 0) + treasures * 50 } };
  },
  // v2 -> v3 (P10.3): changed world objects are named "type@tx,ty" instead of by list index (which
  // shifts whenever the map gains objects). See nameIndexedDiff.
  2: (data) => ({ ...data, worldDiff: nameIndexedDiff(data?.worldDiff, legacyLists ?? []) }),
  // v3 -> v4 (volume phase 1): the map. `surveyed` lists the regions drawn on it (survey stones
  // touched); a save from before has none. Nothing else changes: every id, flag, chest, checkpoint
  // and world difference of a v3 save means the same in v4 (no coordinate of an old region moved).
  3: (data) => ({ ...data, surveyed: Array.isArray(data?.surveyed) ? data.surveyed : [] }),
};

/**
 * @typedef {object} Envelope
 * @property {number} schemaVersion
 * @property {string} gameVersion
 * @property {number} savedAt      ms since epoch
 * @property {number} seq          increases with every save (picks the newer generation)
 * @property {any} data
 * @property {string} checksum
 */

/** FNV-1a (32 bit) over a string, as 8 hex digits. @param {string} s */
export function fnv1a(s) {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h.toString(16).padStart(8, '0');
}

/** @param {Omit<Envelope, 'checksum'>} e */
function checksumOf(e) {
  return fnv1a(JSON.stringify([e.schemaVersion, e.gameVersion, e.savedAt, e.seq, e.data]));
}

/**
 * @param {any} data @param {string} gameVersion @param {number} seq @param {number} now
 * @returns {Envelope}
 */
export function makeEnvelope(data, gameVersion, seq, now) {
  const e = { schemaVersion: SCHEMA_VERSION, gameVersion, savedAt: now, seq, data };
  return { ...e, checksum: checksumOf(e) };
}

/** @param {any} e @returns {e is Envelope} */
export function isIntact(e) {
  return !!e && typeof e === 'object' && typeof e.checksum === 'string' && e.checksum === checksumOf(e);
}

/**
 * Brings an intact envelope's data up to the current schema.
 * @param {Envelope} e @param {Record<number, (data: any) => any>} [migrations]
 * @returns {{ ok: true, data: any } | { ok: false, reason: 'newer' | 'missingMigration' }}
 */
export function migrate(e, migrations = MIGRATIONS) {
  if (e.schemaVersion > SCHEMA_VERSION) return { ok: false, reason: 'newer' };
  let data = e.data;
  for (let v = e.schemaVersion; v < SCHEMA_VERSION; v++) {
    const step = migrations[v];
    if (!step) return { ok: false, reason: 'missingMigration' };
    data = step(data);
  }
  return { ok: true, data };
}

/**
 * Chooses what to load from the two generations. The newest intact one wins; if the newest is
 * damaged the other is used and `recovered` is set (the player is told).
 * @param {any} a @param {any} b
 * @returns {{ status: 'empty' } | { status: 'ok', data: any, recovered: boolean, envelope: Envelope } |
 *   { status: 'newer' } | { status: 'corrupt' }}
 */
export function chooseSave(a, b) {
  const present = [a, b].filter((x) => x != null);
  if (present.length === 0) return { status: 'empty' };
  const intact = present.filter(isIntact).sort((x, y) => y.seq - x.seq);
  if (intact.length === 0) return { status: 'corrupt' };
  const newestSeq = Math.max(...present.map((x) => (typeof x.seq === 'number' ? x.seq : -1)));
  const best = intact[0];
  const m = migrate(best);
  if (m.ok === false) return m.reason === 'newer' ? { status: 'newer' } : { status: 'corrupt' };
  return { status: 'ok', data: m.data, recovered: best.seq < newestSeq, envelope: best };
}

/**
 * Turns a storage error into a user-facing reason (DESIGN.md 2.6: different messages per cause).
 * @param {unknown} err @returns {'quota' | 'unavailable' | 'unknown'}
 */
export function classifyError(err) {
  const name = err && typeof err === 'object' && 'name' in err ? String(err.name) : '';
  if (name === 'QuotaExceededError' || /quota/i.test(String(err))) return 'quota';
  if (name === 'SecurityError' || name === 'InvalidStateError' || name === 'NotAllowedError' || /indexeddb/i.test(String(err))) {
    return 'unavailable';
  }
  return 'unknown';
}

/** @param {'quota' | 'unavailable' | 'unknown'} reason */
export function failureMessage(reason) {
  switch (reason) {
    case 'quota':
      return '保存できませんでした：端末の空き容量が足りません。前回の保存データは残っています。';
    case 'unavailable':
      return '保存できませんでした：このブラウザの設定（プライベートブラウズなど）では保存できません。';
    default:
      return '保存できませんでした。前回の保存データは残っています。次の保存で再試行します。';
  }
}
