// @ts-check
// v1.0 (C5-C7): messages for the final boss's events, and test helpers for it on window.__debugApi
// (main.js adds these to the debug API). Flags (source_open is normally set by the princess's
// dialogue, C14), going into the antechamber / arena, waking the seats, and striking the source.
import { hitEnemy } from '../game/combat/damage.js';
import { allSeatsAwake } from '../game/entities/finalBoss.js';

/** @type {Record<string, string>} */
const SEAT_NAMES = { 'source-fire': '火の座', 'source-light': '光の座', 'source-weight': '重さの座', 'source-echo': '響きの座' };

/**
 * The toast for an event of the source, or null.
 * @param {{ type: string, id?: string }} ev @returns {{ text: string, ms: number } | null}
 */
export function finalBossToast(ev) {
  switch (ev.type) {
    case 'sourceAwake':
      return { text: '裏返った星環——淀みの源が目を開けた。まわりの 4 つの座を目覚めさせよう', ms: 4000 };
    case 'seatOn':
      return { text: `${SEAT_NAMES[ev.id ?? ''] ?? '座'}が目覚めた`, ms: 1500 };
    case 'sourceStagger':
      return { text: '輪がもとの向きに返った！ 今なら攻撃が通る', ms: 3000 };
    case 'sourceGuard':
      return { text: '裏返った輪には攻撃が通らない…', ms: 1500 };
    case 'sourceWave':
      return { text: '裏返しの波——座の光が消えた', ms: 2000 };
    case 'sourcePhase':
      return { text: '輪にひびが入った…！', ms: 2000 };
    case 'sourcePurified':
      return { text: '淀みの源を浄化した！ 輪がもとの向きに戻っていく…', ms: 5000 };
    default:
      return null;
  }
}

/**
 * Test helpers (E2E: tests/e2e/v1-final-boss.spec.js).
 * @param {any} state @param {(tx: number, ty: number) => void} teleport
 */
export function finalBossDebugApi(state, teleport) {
  const boss = () => state.enemies.find((/** @type {any} */ e) => e.final) ?? null;
  const arrival = (/** @type {string} */ id) => {
    const w = state.warps.find((/** @type {any} */ x) => x.id === id);
    return w ? { tx: w.toTx, ty: w.toTy } : null;
  };
  return {
    /** Progress flags (a copy). */
    flags: () => ({ ...state.progress.flags }),
    /** Sets (or with `on` false, clears) a progress flag, e.g. setFlag('source_open'). */
    setFlag: (/** @type {string} */ name, on = true) => {
      if (on) state.progress.flags[name] = true;
      else delete state.progress.flags[name];
    },
    /** Into the antechamber (where the beach ring leads). */
    enterSourceGate: () => {
      const a = arrival('source-gate');
      if (a) teleport(a.tx, a.ty);
      return a;
    },
    /** Into the arena (where the antechamber's opening leads). The source wakes on the next step. */
    enterSourceArena: () => {
      const a = arrival('source-arena-in');
      if (a) teleport(a.tx, a.ty);
      return a;
    },
    /** Where the beach ring and the arena are (tiles). */
    sourcePlaces: () => ({
      ring: state.warps.filter((/** @type {any} */ w) => w.id === 'source-gate').map((/** @type {any} */ w) => ({ tx: w.tx, ty: w.ty, facing: w.facing, if: w.if }))[0] ?? null,
      gate: arrival('source-gate'),
      arena: arrival('source-arena-in'),
      seats: state.switches.filter((/** @type {any} */ s) => s.seat).map((/** @type {any} */ s) => ({ id: s.id, kind: s.kind, tx: s.tx, ty: s.ty })),
    }),
    /** The source now, or null (it is placed when the player steps into its arena; gone once purified). */
    finalBoss: () => {
      const e = boss();
      if (!e) return null;
      return { id: e.bossId, name: e.name, hp: e.hp, maxHp: e.maxHp, phase: e.phase, awake: e.awake, state: e.state, pattern: e.pattern, staggers: e.staggers, seats: { ...e.seats }, allSeats: allSeatsAwake(e), x: e.x, y: e.y };
    },
    /** What each seat receives now (switch state) and whether the source counts it awake. */
    seats: () => {
      const e = boss();
      return Object.fromEntries(
        state.switches.filter((/** @type {any} */ s) => s.seat).map((/** @type {any} */ s) => [s.id, { active: !!state.switchActive[s.id], awake: !!e?.seats[s.id] }]),
      );
    },
    /** Wakes seats directly (all four by default): with all four the source staggers on its next step. */
    activateSeats: (/** @type {string[] | undefined} */ ids) => {
      const e = boss();
      if (!e || e.state === 'dead') return false;
      for (const id of ids ?? e.seatIds) if (id in e.seats) e.seats[id] = true;
      return true;
    },
    /** One blow to the source (lands only while it staggers). Returns whether it landed. */
    strikeFinalBoss: () => {
      const e = boss();
      if (!e) return false;
      return hitEnemy(state, e, { owner: 'player', id: `debug-source${state.tick}-${Math.random()}`, damage: 1, from: { x: e.x, y: e.y + 20 }, kind: 'melee' });
    },
  };
}
