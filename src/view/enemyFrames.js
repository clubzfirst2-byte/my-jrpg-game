// @ts-check
// gfx W3/W5: how many frames each enemy / boss action has, and how fast it plays — read from the
// art's own frame table (frames.json), never assumed. Pure (no Pixi), unit-tested.
//
//   v1  docs/art-release/enemy/frames.json         (the approved release art: 1–6 frames an action)
//   v2  src/art-release-v2/enemy/frames.json        (the new art, 4–8 frames an action; or the same
//       docs/art-release-v2/enemy/frames.json        file under docs/)
// Which table is used follows the art that is loaded (tableForArt): whatever switch picked the
// art (?v2=0, ?enemy=v1|v2, the list of approved v2 groups), the frames played are that art's.
//
// A table: { kinds: { <kind>: { actions: { <action>: { frames, fps? } } } }, fps?: { <action>: fps },
//   fps_hint_ms?: { <action>: ms a frame } } — the v2 art ships its timings as `fps_hint_ms`
//   (docs/art-release-v2/enemy/PRODUCTION.md: idle 180 ms, move 90, attack 80, hurt 90, stagger
//   120 …; non-numbers such as the wind-up's "split evenly" are ignored: wind-ups always split).
// Timing per action:
//   loops    idle / idle2 / move / stagger / tendril: `fps` (looping by real time)
//   windup   spread over the wind-up by its progress (whatever the frame count)
//   attack   plays at `fps` from the moment it strikes, through the recovery, holding the last frame
//   hurt     plays at `fps` once, holding the last frame
//   defeat / transform   spread over the time the game gives them
// An action's fps comes from the table (per action, or the table's `fps` by action name), else
// from the defaults of its version: v1's own timings (docs/art-release/enemy/PRODUCTION.md 2.3), and
// for v2 the gfx plan's (idle 6, move 10, attack 14 …).
import V1_JSON from '../../docs/art-release/enemy/frames.json';

const V2_FILES = /** @type {Record<string, any>} */ (
  import.meta.glob(['../art-release-v2/enemy/frames.json', '../../docs/art-release-v2/enemy/frames.json'], { eager: true, import: 'default' })
);

/** v1 timings (PRODUCTION.md 2.3: idle 400 ms a frame, move 140, attack 120, hurt 200). */
export const V1_FPS = Object.freeze({ idle: 2.5, idle2: 2.5, move: 1000 / 140, attack: 1000 / 120, hurt: 5, stagger: 5, tendril: 4 });
/** v2 defaults (gfx plan: idle 6 fps, move 10, attack fast). */
export const V2_FPS = Object.freeze({ idle: 6, idle2: 6, move: 10, attack: 14, hurt: 10, stagger: 8, tendril: 8 });

/** The fps family of an action name (attack_slam → attack, windup_ring → windup). @param {string} action */
export const actionFamily = (action) => action.replace(/_[a-z0-9]+$/, '');

/**
 * @typedef {{ version: string, frames: Map<string, number>, fps: Map<string, number>, defaults: Record<string, number> }} FrameTable
 */

/**
 * @param {any} json a frames.json @param {string} version @param {Record<string, number>} defaults
 * @returns {FrameTable}
 */
export function frameTable(json, version, defaults) {
  /** @type {Map<string, number>} */
  const frames = new Map();
  /** @type {Map<string, number>} */
  const fps = new Map();
  for (const [kind, k] of Object.entries(json?.kinds ?? {})) {
    for (const [action, a] of Object.entries(/** @type {any} */ (k).actions ?? {})) {
      const base = `enemy.${kind}.${action}`;
      frames.set(base, Number(/** @type {any} */ (a).frames) || 0);
      const hint = (/** @type {string} */ name) => {
        const ms = json.fps_hint_ms?.[name];
        return typeof ms === 'number' && ms > 0 ? 1000 / ms : undefined;
      };
      const f = /** @type {any} */ (a).fps ?? json.fps?.[action] ?? json.fps?.[actionFamily(action)] ?? hint(action) ?? hint(actionFamily(action));
      if (f) fps.set(base, Number(f));
    }
  }
  return { version, frames, fps, defaults };
}

export const V1_TABLE = frameTable(V1_JSON, 'v1', V1_FPS);
const v2Json = Object.values(V2_FILES)[0] ?? null;
/** The v2 table when the new art's frames.json is in the tree, else null. */
export const V2_TABLE = v2Json ? frameTable(v2Json, 'v2', V2_FPS) : null;

/**
 * Whether a table describes the art that is loaded: (nearly) every action it lists has exactly its
 * number of frames there (the last one present, none after it).
 * @param {FrameTable} table @param {(key: string) => boolean} has
 */
export function tableFits(table, has) {
  let ok = 0;
  let all = 0;
  for (const [base, n] of table.frames) {
    if (n <= 0) continue;
    all++;
    if (has(`${base}.${n - 1}`) && !has(`${base}.${n}`)) ok++;
  }
  return all > 0 && ok >= all * 0.9;
}

/**
 * The table of the enemy art that is loaded: v2 when the loaded frames are the v2 art's, else v1.
 * @param {(key: string) => boolean} has @param {FrameTable | null} [v2]
 */
export const tableForArt = (has, v2 = V2_TABLE) => (v2 && tableFits(v2, has) ? v2 : V1_TABLE);

/** The table the view uses now (main.js picks it by the art loaded: tableForArt). */
let active = V1_TABLE;
/** @param {FrameTable} table */
export function useEnemyFrameTable(table) {
  active = table;
}
export const activeEnemyFrameTable = () => active;

/**
 * Frame count and speed of one action (`base` = enemy.<kind>.<action>), checked against the art
 * that is loaded: the table's count when its last frame is there; otherwise the frames actually
 * loaded (counted), at the v1 timings (the table describes art that is not the one loaded). With
 * `cache`, each answer is remembered (the caller clears it when the loaded art changes).
 * @param {string} base @param {(key: string) => boolean} has
 * @param {Map<string, { n: number, fps: number }>} [cache] @param {FrameTable} [table]
 * @returns {{ n: number, fps: number }}
 */
export function actionInfo(base, has, cache, table = active) {
  const known = cache?.get(base);
  if (known) return known;
  const fam = actionFamily(base.slice(base.lastIndexOf('.') + 1));
  const listed = table.frames.get(base) ?? 0;
  /** @type {{ n: number, fps: number }} */
  let info;
  if (listed > 0 && has(`${base}.${listed - 1}`) && has(`${base}.0`)) {
    info = { n: listed, fps: table.fps.get(base) ?? table.defaults[fam] ?? table.defaults.attack };
  } else {
    let n = 0;
    while (n < 64 && has(`${base}.${n}`)) n++;
    info = { n, fps: /** @type {Record<string, number>} */ (V1_FPS)[fam] ?? V1_FPS.attack };
  }
  cache?.set(base, info);
  return info;
}

/** Looping frame by real time. @param {number} timeSec @param {{ n: number, fps: number }} a @param {number} [offset] in frames */
export const loopFrame = (timeSec, a, offset = 0) => Math.floor(timeSec * a.fps + offset) % a.n;
/** Once-through frame `ms` in, holding the last. @param {number} ms @param {{ n: number, fps: number }} a */
export const onceFrame = (ms, a) => Math.max(0, Math.min(a.n - 1, Math.floor((ms * a.fps) / 1000)));
/** A frame spread over a span (0..1 of it). @param {number} k @param {number} n */
export const spreadFrame = (k, n) => Math.max(0, Math.min(n - 1, Math.floor(k * n)));
