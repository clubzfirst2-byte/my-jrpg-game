// @ts-check
// The enemies' sprites, one per enemy on screen. Pure (no Pixi), unit-tested.
//
// An enemy's id is its place in the map's spawn list (state.js spawnEnemies), so ids are reused:
// every respawn (the player's death, a new season, the test hook spawnEnemy) makes NEW enemy objects
// under the same ids, possibly of another kind (spawn 1 was a beast, now it is a slime). A sprite
// kept by id alone would then carry over to a different enemy — still showing the old one's frame,
// warning overlay and fade until the next draw — and the debug view would list the old enemy. So
// each sprite remembers the enemy object it was made for, and is dropped when its id now belongs to
// another one.

/** @template S */
export class EnemySlots {
  /** @param {(id: number, sprite: S) => void} onDrop releases a sprite (and whatever goes with it) */
  constructor(onDrop) {
    /** @type {Map<number, { owner: any, sprite: S }>} */
    this.slots = new Map();
    this.onDrop = onDrop;
  }

  /**
   * The sprite of this enemy, or null when it needs a new one. A sprite left under its id by another
   * enemy (ids are reused on respawn) is dropped first.
   * @param {any} e @returns {S | null}
   */
  get(e) {
    const slot = this.slots.get(e.id);
    if (!slot) return null;
    if (slot.owner === e) return slot.sprite;
    this.drop(e.id);
    return null;
  }

  /** @param {any} e @param {S} sprite */
  set(e, sprite) {
    this.slots.set(e.id, { owner: e, sprite });
  }

  /** The sprite under an id, whoever it belongs to. @param {number} id */
  byId(id) {
    return this.slots.get(id)?.sprite ?? null;
  }

  /** @param {number} id */
  drop(id) {
    const slot = this.slots.get(id);
    if (!slot) return;
    this.slots.delete(id);
    this.onDrop(id, slot.sprite);
  }

  /** Drops every sprite whose id was not drawn this frame. @param {Set<number>} seen */
  sweep(seen) {
    for (const id of [...this.slots.keys()]) if (!seen.has(id)) this.drop(id);
  }

  /** Every id with a sprite. */
  ids() {
    return [...this.slots.keys()];
  }

  /**
   * The sprites that show an enemy still in the game (tests, ?debug): a sprite whose enemy is gone
   * (cleared or respawned, not yet redrawn) is left out.
   * @param {any[]} enemies the game's enemy list now
   * @returns {{ id: number, owner: any, sprite: S }[]}
   */
  live(enemies) {
    const now = new Set(enemies);
    return [...this.slots].filter(([, s]) => now.has(s.owner)).map(([id, s]) => ({ id, owner: s.owner, sprite: s.sprite }));
  }

  get size() {
    return this.slots.size;
  }
}
