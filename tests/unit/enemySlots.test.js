import { describe, it, expect } from 'vitest';
import { createGameState, spawnEnemies } from '../../src/game/state.js';
import { HEIGHT_TEST } from '../../src/game/world/maps/heightTest.js';
import { EnemySlots } from '../../src/view/enemySlots.js';

// The E2E flake in v1-enemies.spec (a slime's view entry showing "enemy.beast.idle.1"): enemy ids
// are places in the spawn list, so clearing the enemies and spawning new ones reuses the ids of the
// map's own beast and archer. The view kept sprites by id alone, so until the next draw it still
// listed the beast's sprite under the slime's id, and on that draw reused the beast's sprite for
// the slime. EnemySlots ties each sprite to the enemy object it was made for.

/** A stand-in for a Pixi sprite. */
const sprite = (kind) => ({ kind, destroyed: false });

/** One draw, as gameView.renderCombat does it. */
function draw(slots, state) {
  const seen = new Set();
  for (const e of state.enemies) {
    seen.add(e.id);
    let s = slots.get(e);
    if (!s) {
      s = sprite(e.kind);
      slots.set(e, s);
    }
  }
  slots.sweep(seen);
}

/** The debug hooks clearEnemies and spawnEnemy (src/main.js). */
function clearAndSpawn(state, spawns) {
  state.enemySpawns = [];
  state.enemies = [];
  for (const s of spawns) {
    state.enemySpawns.push(s);
    spawnEnemies(state);
  }
}

describe('enemy sprites when ids are reused (respawn, spawnEnemy)', () => {
  it('reproduces the collision: new enemies of another kind get the ids of the old ones', () => {
    const s = createGameState(HEIGHT_TEST);
    const before = s.enemies.map((e) => [e.id, e.kind]);
    expect(before).toEqual([[1, 'beast'], [2, 'archer']]);
    clearAndSpawn(s, [{ kind: 'slime', tx: 12, ty: 26 }, { kind: 'sentinel', tx: 14, ty: 26 }]);
    expect(s.enemies.map((e) => [e.id, e.kind])).toEqual([[1, 'slime'], [2, 'sentinel']]);
  });

  it('before the next draw, the debug view lists none of the old sprites (no stale beast under the slime id)', () => {
    const s = createGameState(HEIGHT_TEST);
    const slots = new EnemySlots(() => {});
    draw(slots, s);
    expect(slots.live(s.enemies).map((x) => x.sprite.kind)).toEqual(['beast', 'archer']);
    clearAndSpawn(s, [{ kind: 'slime', tx: 12, ty: 26 }, { kind: 'sentinel', tx: 14, ty: 26 }]);
    // Two sprites are still kept (ids 1 and 2) — the old check "two entries" passed here — but they
    // belong to enemies that are gone, so they are not listed.
    expect(slots.size).toBe(2);
    expect(slots.live(s.enemies)).toEqual([]);
    draw(slots, s);
    const live = slots.live(s.enemies);
    expect(live.map((x) => [x.id, x.owner.kind, x.sprite.kind])).toEqual([[1, 'slime', 'slime'], [2, 'sentinel', 'sentinel']]);
  });

  it("on the next draw, the old enemy's sprite is released, not reused for the new one", () => {
    const s = createGameState(HEIGHT_TEST);
    const dropped = [];
    const slots = new EnemySlots((id, spr) => {
      spr.destroyed = true;
      dropped.push([id, spr.kind]);
    });
    draw(slots, s);
    const beastSprite = slots.byId(1);
    clearAndSpawn(s, [{ kind: 'slime', tx: 12, ty: 26 }]);
    draw(slots, s);
    expect(beastSprite.destroyed).toBe(true);
    expect(slots.byId(1)).not.toBe(beastSprite);
    expect(slots.byId(1).kind).toBe('slime');
    // id 1 was taken over (dropped on sight), id 2 is gone (swept).
    expect(dropped.sort()).toEqual([[1, 'beast'], [2, 'archer']]);
  });

  it('the same enemy keeps its sprite from frame to frame (respawn after death included: new objects, new sprites)', () => {
    const s = createGameState(HEIGHT_TEST);
    const slots = new EnemySlots(() => {});
    draw(slots, s);
    const first = slots.byId(1);
    draw(slots, s);
    expect(slots.byId(1)).toBe(first);
    spawnEnemies(s); // (as after the player's death or a new season: the same spawns, new objects)
    draw(slots, s);
    expect(slots.byId(1)).not.toBe(first);
    expect(slots.byId(1).kind).toBe('beast');
  });
});
