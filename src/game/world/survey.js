// @ts-check
// Survey stones, the map and travel between record stones (volume phase 1; plan M1 / M2).
//
//   survey stone (測量石)  stands on high ground, one per region. Touching it draws that region on the
//                          map (progress.surveyed). Without it the map shows the region only as a
//                          dim outline with the record stones already touched.
//   travel                 from the map, to any record stone that has been touched. Never during a
//                          fight with a core or the source, a conversation, the opening or ending,
//                          in the air, in water, or while down.
// Pure logic: no DOM, no PixiJS.
import { tileFeet, areaAt } from './features.js';
import { regionAt } from './world.js';
import { groundHeightUnder } from '../physics/collision.js';

/** @typedef {{ id: string, region: string, tx: number, ty: number }} SurveyDef */

/** What the map calls each record stone (a stone not listed is called by its id's region). @type {Record<string, string>} */
export const CHECKPOINT_NAMES = {
  beach: '目覚めの浜',
  hill: '島の丘',
  camp: '島の野営地',
  plains: '風見の村',
  desert: '荒野の入口',
  mountains: '白嶺のふもと',
  forest: '森の小道',
  lake: '鏡湖の西岸',
  source: '星環の前室',
  terrace: '段丘の入口',
  terrace_east: '段丘・東の棚',
};
/** @param {string} id */
export const checkpointName = (id) => CHECKPOINT_NAMES[id] ?? '記録石';

/** How close (px) the player must be to touch a survey stone (the stone is solid: from beside it). */
const SURVEY_RANGE = 22;

/**
 * Touching a survey stone draws its region on the map.
 * @param {any} state
 */
export function touchSurveys(state) {
  const p = state.player;
  if (!p.grounded || !state.surveyDefs?.length) return;
  const pr = state.progress;
  for (const s of /** @type {SurveyDef[]} */ (state.surveyDefs)) {
    if (pr.surveyed.includes(s.region)) continue;
    const f = tileFeet(state.map, s.tx, s.ty);
    if (Math.hypot(f.x - p.x, f.y - p.y) > SURVEY_RANGE) continue;
    if (Math.abs(state.map.elev[s.ty * state.map.width + s.tx] - p.z) > 12) continue;
    pr.surveyed.push(s.region);
    state.events.push({ type: 'survey', tick: state.tick, id: s.region });
    state.saveRequested = true;
  }
}

/**
 * Why the player cannot travel now, or null when they can.
 * @param {any} state
 * @returns {null | 'dead' | 'busy' | 'air' | 'fight'}
 */
export function travelBlocked(state) {
  const p = state.player;
  if (p.dead) return 'dead';
  if (state.dialogue || state.shop || state.opening || state.ending) return 'busy';
  if (!p.grounded || p.swimming || p.climbing) return 'air';
  // A core that has woken, or the source: finish (or leave) the fight first.
  if (state.enemies.some((/** @type {any} */ e) => (e.boss || e.final) && e.awake && e.state !== 'dead')) return 'fight';
  return null;
}

/** @type {Record<string, string>} */
export const TRAVEL_BLOCKED_TEXT = {
  dead: '今は移れない',
  busy: '今は移れない',
  air: '地面に立っている時だけ移れる',
  fight: '戦いの間は移れない',
};

/**
 * Moves the player to a record stone already touched; it becomes the place to come back to life.
 * @param {any} state @param {string} id checkpoint id
 * @returns {boolean} whether the player moved
 */
export function travelTo(state, id) {
  if (travelBlocked(state)) return false;
  const pr = state.progress;
  if (!pr.checkpoints.includes(id)) return false;
  const c = state.checkpointDefs.find((/** @type {any} */ d) => d.id === id);
  if (!c) return false;
  const p = state.player;
  // Just south of the stone, as when coming back to life there.
  const f = tileFeet(state.map, c.tx, c.ty + 1);
  p.x = p.prevX = f.x;
  p.y = p.prevY = f.y;
  p.z = p.prevZ = p.groundZ = groundHeightUnder({ x: f.x, y: f.y, halfWidth: 5, height: 6 }, state.map);
  p.vx = p.vy = p.vz = 0;
  p.safeX = p.x;
  p.safeY = p.y;
  p.safeZ = p.z;
  p.gliding = false;
  p.facing = 'down';
  state.projectiles = [];
  state.orb = null;
  pr.checkpoint = id;
  state.events.push({ type: 'travel', tick: state.tick, id });
  state.saveRequested = true;
  return true;
}

/**
 * What the map shows: every region with whether it is surveyed, the record stones touched (travel
 * targets), the survey stones touched, the landmarks found, and where the player is. Rooms (the
 * strip east of each region) are not on the map: a player indoors is shown at the region's edge.
 * @param {any} state
 */
export function mapModel(state) {
  const pr = state.progress;
  const ts = state.map.tileSize;
  const p = state.player;
  const ptx = Math.floor(p.x / ts);
  const pty = Math.floor(p.y / ts);
  const here = regionAt(state.regions, ptx, pty);
  const indoors = !!areaAt(state, p.x, p.y);
  /** The outdoors of a region is its west 96 columns (its strip of rooms is east of that). */
  const OUT_W = 96;
  const regions = state.regions.map((/** @type {any} */ r) => {
    const inside = (/** @type {any} */ o) => o.tx >= r.tx && o.tx < r.tx + Math.min(r.tw, OUT_W) && o.ty >= r.ty && o.ty < r.ty + r.th;
    const inRegion = (/** @type {any} */ o) => o.tx >= r.tx && o.tx < r.tx + r.tw && o.ty >= r.ty && o.ty < r.ty + r.th;
    const surveyed = pr.surveyed.includes(r.id);
    return {
      id: r.id,
      name: r.name,
      tx: r.tx,
      ty: r.ty,
      tw: Math.min(r.tw, OUT_W),
      th: r.th,
      surveyed,
      hasSurvey: (state.surveyDefs ?? []).some((/** @type {SurveyDef} */ s) => s.region === r.id),
      current: here?.id === r.id,
      // Record stones touched are always shown (old saves travel at once); a stone in a room (the
      // source's antechamber) is listed with its region but has no place on the drawing.
      checkpoints: state.checkpointDefs
        .filter((/** @type {any} */ c) => inRegion(c) && pr.checkpoints.includes(c.id))
        .map((/** @type {any} */ c) => ({ id: c.id, tx: c.tx, ty: c.ty, outdoors: inside(c), active: pr.checkpoint === c.id })),
      // Landmarks found are drawn only on a surveyed region.
      landmarks: surveyed ? state.landmarks.filter((/** @type {any} */ l) => inside(l) && pr.landmarks.includes(l.id)).map((/** @type {any} */ l) => ({ id: l.id, name: l.name, tx: l.tx, ty: l.ty })) : [],
      surveys: (state.surveyDefs ?? []).filter((/** @type {SurveyDef} */ s) => s.region === r.id && surveyed).map((/** @type {SurveyDef} */ s) => ({ id: s.id, tx: s.tx, ty: s.ty })),
    };
  });
  return {
    regions,
    player: here ? { region: here.id, tx: indoors ? Math.min(ptx, here.tx + OUT_W - 1) : ptx, ty: pty, indoors } : null,
    blocked: travelBlocked(state),
  };
}
