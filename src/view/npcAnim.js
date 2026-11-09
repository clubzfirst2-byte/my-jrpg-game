// @ts-check
// NPC batch 1: which frame a villager shows. A villager with release art (src/art-release/npc/,
// npc.<id>.<idle|walk>.<dir>.<n>) breathes while standing and walks with a 6-frame step; one
// without keeps the placeholder npc.<look>.walk.<dir>.<0..2>. Pure (no Pixi), unit-tested.

export const NPC_ANIM = Object.freeze({
  /** standing: 4 frames, a slow breath */
  idle: { frames: 4, fps: 3 },
  /** walking (speed 24 px/s): 6 frames, by the time spent walking so the feet keep step */
  walk: { frames: 6, fps: 8 },
});

const PLACEHOLDER_FPS = 6;
const PLACEHOLDER_CYCLE = [1, 0, 2, 0];

/** A fixed offset per villager, so two of them never breathe in step. @param {string} id */
export function idleOffset(id) {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return (h % 997) / 997;
}

/**
 * The release frames are npc.<art>.* (art: the villager's art name, v1.0; its id when not given).
 * @param {{ id: string, art?: string, look: number, facing: string, moving: boolean, walkTime: number }} n
 * @param {number} timeSec real time (the breathing loop)
 * @param {(key: string) => boolean} has whether a texture exists
 * @returns {string} the sprite key
 */
export function npcFrameKey(n, timeSec, has) {
  const dir = n.facing;
  const art = n.art ?? n.id;
  if (has(`npc.${art}.idle.${dir}.0`)) {
    if (n.moving) {
      const f = Math.floor(n.walkTime * NPC_ANIM.walk.fps) % NPC_ANIM.walk.frames;
      return `npc.${art}.walk.${dir}.${f}`;
    }
    const f = Math.floor(timeSec * NPC_ANIM.idle.fps + idleOffset(n.id) * NPC_ANIM.idle.frames) % NPC_ANIM.idle.frames;
    return `npc.${art}.idle.${dir}.${f}`;
  }
  const frame = n.moving ? PLACEHOLDER_CYCLE[Math.floor(n.walkTime * PLACEHOLDER_FPS) % PLACEHOLDER_CYCLE.length] : 0;
  return `npc.${n.look}.walk.${dir}.${frame}`;
}
