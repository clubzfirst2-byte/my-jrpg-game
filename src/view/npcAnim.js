// @ts-check
// NPC batch 1: which frame a villager shows. A villager with release art (src/art-release/npc/,
// npc.<id>.<idle|walk>.<dir>.<n>) breathes while standing and walks with a 6-frame step; one
// without keeps the placeholder npc.<look>.walk.<dir>.<0..2>. Pure (no Pixi), unit-tested.
// Graphics v3 (assets/npcV3.js): a person with v3 art is in a bundle of its own. A left frame that has
// no file (the princess, the smith) is that bundle's right frame mirrored, under the left frame's key
// (placeholderPack mirrorOf: `has` answers for it like for a stored frame, the view mirrors the
// sprite). While the bundle is not in, such a villager has no frame (null), never the placeholder.

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
 * @param {(key: string) => boolean} has whether a texture exists (graphics v3: a mirrored left frame counts)
 * @param {(art: string) => boolean} [own] graphics v3: whether this person's art is a bundle of its own
 *   (loaded apart): then no frame while it is not in, instead of the placeholder
 * @returns {string | null} the sprite key (null: graphics v3, this person's own art is not loaded yet)
 */
export function npcFrameKey(n, timeSec, has, own) {
  const dir = n.facing;
  const art = n.art ?? n.id;
  // (graphics v3: a left frame is asked for by its own key whether it is stored or its right frame mirrored)
  if (own?.(art) && !has(`npc.${art}.idle.${dir}.0`)) return null;
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
