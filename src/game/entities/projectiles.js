// @ts-check
// Arrows (player) and orbs (enemy). They fly at their launch height and stop at walls, trees and
// rocks. A parried orb flies back as the player's.
import { isSolidTile, terrainHeightAt } from '../world/tilemap.js';
import { overlaps } from '../combat/hitbox.js';
import { hitEnemy, hitPlayer } from '../combat/damage.js';
import { arrowEnv, fireArrowHitsEnemy } from '../env/envActions.js';

/**
 * @param {any} state @param {number} dt seconds (already scaled by slow motion)
 */
export function updateProjectiles(state, dt) {
  const map = state.map;
  const keep = [];
  for (const pr of state.projectiles) {
    pr.lifeMs -= dt * 1000;
    pr.x += pr.vx * dt;
    pr.y += pr.vy * dt;
    const tx = Math.floor(pr.x / map.tileSize);
    const ty = Math.floor(pr.y / map.tileSize);
    const blocked = isSolidTile(map, tx, ty) || terrainHeightAt(map, pr.x, pr.y) > pr.z + 4;
    // P4: arrows light up over fire, set things alight, hit crystals and jars.
    const env = state.env ? arrowEnv(state, pr, blocked, pr.lifeMs <= 0) : blocked || pr.lifeMs <= 0 ? 'stop' : 'fly';
    if (env === 'stop') continue;
    if (collide(state, pr)) continue;
    keep.push(pr);
  }
  state.projectiles = keep;
}

/** @returns {boolean} true if the projectile is used up */
function collide(state, pr) {
  const point = { x: pr.x, y: pr.y, z: pr.z, r: 2 };
  if (pr.owner === 'player') {
    for (const e of state.enemies) {
      if (e.state === 'dead') continue;
      if (overlaps(point, { x: e.x, y: e.y - 4, z: e.z, r: 7 })) {
        hitEnemy(state, e, { owner: 'player', id: pr.id, damage: pr.damage, knock: 0.5, from: { x: pr.x - pr.vx, y: pr.y - pr.vy }, kind: 'projectile' });
        if (state.env) fireArrowHitsEnemy(state, pr, e);
        return true;
      }
    }
    return false;
  }
  const p = state.player;
  if (!overlaps(point, { x: p.x, y: p.y - 4, z: p.z, r: 6 })) return false;
  const result = hitPlayer(state, { owner: 'enemy', id: pr.id, damage: pr.damage, from: { x: pr.x - pr.vx, y: pr.y - pr.vy }, kind: 'projectile' });
  if (result === 'parried') {
    // Perfect guard: send it back as the player's, a little faster.
    pr.owner = 'player';
    pr.vx = -pr.vx * 1.5;
    pr.vy = -pr.vy * 1.5;
    pr.lifeMs = 1500;
    pr.reflected = true;
    return false;
  }
  return result !== 'justDodge' && result !== 'dodged';
}
