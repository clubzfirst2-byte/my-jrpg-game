import { describe, it, expect } from 'vitest';
import { parseMap, isSolidTile, Ground, TILE_SIZE } from '../../src/game/world/tilemap.js';
import { moveAndCollide, overlapsSolid } from '../../src/game/physics/collision.js';
import { TEST_FIELD } from '../../src/game/world/maps/testField.js';

// 5x5 room: walls around, one rock in the middle.
const ROOM = ['#####', '#...#', '#.#.#', '#...#', '#####'];
const body = (x, y) => ({ x, y, halfWidth: 5, height: 6 });

describe('parseMap', () => {
  it('parses ground, solids, objects and spawn', () => {
    const m = parseMap(['.=~', 'T#P']);
    expect(m.width).toBe(3);
    expect(m.height).toBe(2);
    expect(m.ground[1]).toBe(Ground.PATH);
    expect(m.ground[2]).toBe(Ground.WATER);
    expect(isSolidTile(m, 2, 0)).toBe(false); // water is swimmable since P2.3
    expect(isSolidTile(m, 0, 1)).toBe(true);
    expect(isSolidTile(m, 1, 1)).toBe(true);
    expect(isSolidTile(m, 0, 0)).toBe(false);
    expect(m.objects).toEqual([
      { type: 'tree', tx: 0, ty: 1 },
      { type: 'rock', tx: 1, ty: 1 },
    ]);
    expect(m.spawn).toEqual({ x: 2 * TILE_SIZE + 8, y: 2 * TILE_SIZE - 2 });
  });

  it('treats outside the map as solid', () => {
    const m = parseMap(['.']);
    expect(isSolidTile(m, -1, 0)).toBe(true);
    expect(isSolidTile(m, 1, 0)).toBe(true);
  });

  it('rejects ragged rows and unknown characters', () => {
    expect(() => parseMap(['..', '.'])).toThrow();
    expect(() => parseMap(['.x'])).toThrow(/Unknown/);
  });

  it('the P1 test field is valid and the spawn point is free', () => {
    const m = parseMap(TEST_FIELD);
    expect(m.width).toBe(48);
    expect(m.height).toBe(32);
    expect(overlapsSolid(body(m.spawn.x, m.spawn.y), m)).toBe(false);
  });
});

describe('moveAndCollide', () => {
  const map = parseMap(ROOM);

  it('moves freely in open space', () => {
    const b = body(24, 30);
    const hit = moveAndCollide(b, map, 3, 0);
    expect(hit).toEqual({ hitX: false, hitY: false });
    expect(b.x).toBe(27);
  });

  it('stops flush against a wall on the right', () => {
    const b = body(58, 30); // tile column 3, wall at column 4 (x >= 64)
    const hit = moveAndCollide(b, map, 20, 0);
    expect(hit.hitX).toBe(true);
    expect(b.x).toBe(64 - 5);
    expect(overlapsSolid(b, map)).toBe(false);
  });

  it('stops flush against a wall on the left', () => {
    const b = body(24, 30);
    moveAndCollide(b, map, -20, 0);
    expect(b.x).toBe(16 + 5);
  });

  it('stops feet on top of a solid tile when moving down', () => {
    const b = body(40, 28); // above the middle rock (tile 2,2 => y 32..48)
    const hit = moveAndCollide(b, map, 0, 10);
    expect(hit.hitY).toBe(true);
    expect(b.y).toBe(32);
  });

  it('stops body below a solid tile when moving up', () => {
    const b = body(40, 60);
    moveAndCollide(b, map, 0, -20);
    expect(b.y).toBe(48 + 6);
  });

  it('slides along a wall when moving diagonally', () => {
    const b = body(58, 30);
    const hit = moveAndCollide(b, map, 10, 4);
    expect(hit.hitX).toBe(true);
    expect(hit.hitY).toBe(false);
    expect(b.y).toBe(34);
  });

  it('never pushes a body backwards out of a tile it already overlaps', () => {
    const b = body(60, 30); // overlaps the wall column (e.g. after a teleport)
    moveAndCollide(b, map, -3, 0);
    expect(b.x).toBe(57);
  });

  it('does not tunnel through a 1-tile wall at high speed', () => {
    const b = body(21, 46); // row 2: the middle rock occupies x 32..48
    moveAndCollide(b, map, 200, 0);
    expect(b.x).toBe(32 - 5);
    expect(overlapsSolid(b, map)).toBe(false);
  });

  it('never ends inside a solid tile under random movement', () => {
    let seed = 1;
    const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647) * 2 - 1;
    const b = body(24, 30);
    for (let i = 0; i < 2000; i++) {
      moveAndCollide(b, map, rand() * 6, rand() * 6);
      expect(overlapsSolid(b, map)).toBe(false);
    }
  });
});
