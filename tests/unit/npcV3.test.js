import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { NPC_ANIM, npcFrameKey } from '../../src/view/npcAnim.js';
import { NPC_V3_MIRROR_LEFT, NPC_V3_PEOPLE, NPC_V3_REGION, npcCoveredByV3, npcV3Bundle, npcV3BundleWho, npcV3Parts, npcV3People, npcWhoOf } from '../../src/view/assets/npcV3.js';
import { opaqueBox, atlasSizeFor } from '../../src/view/assets/placeholderPack.js';
import { decodePng, opaqueRect } from '../../tools/release-art-pack.mjs';
import { REGIONS } from '../../src/game/world/maps/regions.js';

// Graphics v3: the villagers at density 4 (docs/art-release-v3/NAMES.md 6, STYLE.md 10.2): the approved
// villagers' keys at twice the size; the princess's and the smith's left = right mirrored (no left files),
// the other 7 store their left frames; a trimmed bundle per person, 8.7 MB for the 9.

const dir3 = new URL('../../src/art-release-v3/npc/', import.meta.url);
const dir1 = new URL('../../src/art-release/npc/', import.meta.url);
const V3 = readdirSync(dir3).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
const V1 = readdirSync(dir1).filter((f) => f.endsWith('.png')).map((f) => f.slice(0, -4));
const png = (dir, k) => decodePng(readFileSync(new URL(`${k}.png`, dir)));
const DIRS = ['down', 'right', 'up', 'left'];
const SOURCES = JSON.parse(readFileSync(new URL('../../tools/art_v3/npc_v3_sources.json', import.meta.url), 'utf8')).people;

/** A person's atlas as main.js packs it (trimmed, tallest first, exact height, tight width). */
const atlasOf = (who, opts = { exactHeight: true, tight: true }) => {
  const entries = npcV3Parts(V3, who).keys.map((k) => {
    const img = png(dir3, k);
    return { rows: [], trim: opaqueBox(img.data, img.width, img.height), image: { width: img.width, height: img.height } };
  });
  entries.sort((a, b) => b.trim.h - a.trim.h);
  return { entries, ...atlasSizeFor(entries, opts) };
};

describe('v3 villagers', () => {
  it('340 stored frames: the 9 approved people, every idle and walk frame; left files for 7, none for the princess and the smith', () => {
    expect(V3.length).toBe(340);
    expect(npcV3People(V3)).toEqual([...NPC_V3_PEOPLE]);
    expect(npcV3People(V1)).toEqual([...NPC_V3_PEOPLE]);
    for (const who of NPC_V3_PEOPLE) {
      for (const [action, a] of Object.entries(NPC_ANIM)) {
        for (const dir of DIRS) {
          for (let n = 0; n < a.frames; n++) {
            const key = `npc.${who}.${action}.${dir}.${n}`;
            expect(V3.includes(key), key).toBe(dir !== 'left' || !NPC_V3_MIRROR_LEFT.includes(who));
            expect(V1.includes(key), key).toBe(true); // (the v3 keys are the approved keys)
          }
        }
      }
    }
    // no other file
    for (const k of V3) expect(V1.includes(k), k).toBe(true);
  });
  it('64×112: twice the approved frame (feet on the bottom row\'s centre, the same anchor)', () => {
    for (const k of V3) {
      const a = png(dir3, k);
      const b = png(dir1, k);
      expect([a.width, a.height], k).toEqual([64, 112]);
      expect([a.width, a.height], k).toEqual([b.width * 2, b.height * 2]);
    }
  });
  it('the feet: the lowest opaque row is the approved frame\'s (× 2), the opaque box within 2 game px of it on the other sides', () => {
    for (const k of V3) {
      const a = png(dir3, k);
      const b = png(dir1, k);
      const A = opaqueBox(a.data, a.width, a.height);
      const B = opaqueBox(b.data, b.width, b.height);
      expect(A.y + A.h, k).toBe((B.y + B.h) * 2);
      expect(Math.abs(A.y - B.y * 2), k).toBeLessThanOrEqual(8);
      expect(Math.abs(A.x - B.x * 2), k).toBeLessThanOrEqual(8);
      expect(Math.abs(A.x + A.w - (B.x + B.w) * 2), k).toBeLessThanOrEqual(8);
    }
  });
  it('the frames are not the approved frames blown up (v3 art, not a copy)', () => {
    for (const who of NPC_V3_PEOPLE) {
      const a = png(dir3, `npc.${who}.idle.down.0`);
      const b = png(dir1, `npc.${who}.idle.down.0`);
      let same = true;
      for (let y = 0; y < a.height && same; y++) for (let x = 0; x < a.width && same; x++) for (let c = 0; c < 4; c++) if (a.data[(y * a.width + x) * 4 + c] !== b.data[((y >> 1) * b.width + (x >> 1)) * 4 + c]) same = false;
      expect(same, who).toBe(false);
    }
  });
  it('a bundle per person; the princess and the smith: every left frame is its right frame mirrored; the others: none', () => {
    expect(npcWhoOf('npc.guard.walk.left.5')).toBe('guard');
    expect(npcWhoOf('npc.3.walk.down.0')).toBe(null); // (a placeholder look)
    expect(npcWhoOf('hero.idle.down.0')).toBe(null);
    expect(npcV3Bundle('elder')).toBe('v3:npc:elder');
    expect(npcV3BundleWho('v3:npc:elder')).toBe('elder');
    expect(npcV3BundleWho('v3:enemy:slime')).toBe(null);
    let stored = 0;
    for (const who of NPC_V3_PEOPLE) {
      const { keys, mirrorOf } = npcV3Parts(V3, who);
      stored += keys.length;
      expect(keys.every((k) => npcWhoOf(k) === who)).toBe(true);
      if (NPC_V3_MIRROR_LEFT.includes(who)) {
        expect(keys.length, who).toBe(30);
        expect(mirrorOf.size, who).toBe(10); // idle 4 + walk 6
        for (const [left, right] of mirrorOf) {
          expect(left).toBe(right.replace('.right.', '.left.'));
          expect(keys).toContain(right);
          expect(keys).not.toContain(left);
        }
        expect(mirrorOf.get(`npc.${who}.walk.left.5`)).toBe(`npc.${who}.walk.right.5`);
      } else {
        expect(keys.length, who).toBe(40);
        expect(mirrorOf.size, who).toBe(0);
      }
      // every approved frame of the person is drawn by its bundle (stored or mirrored)
      const drawn = new Set([...keys, ...mirrorOf.keys()]);
      for (const k of V1.filter((x) => npcWhoOf(x) === who)) expect(drawn.has(k), k).toBe(true);
    }
    expect(stored).toBe(340);
    // a missing left frame of anyone else is not mirrored (a missing file must show)
    expect(npcV3Parts(['npc.guard.idle.right.0'], 'guard').mirrorOf.size).toBe(0);
    expect(npcV3Parts(['npc.smith.idle.right.0'], 'smith').mirrorOf.get('npc.smith.idle.left.0')).toBe('npc.smith.idle.right.0');
  });
  it('the base bundle keeps no frame of a person drawn by v3 (never an approved left frame beside v3 frames)', () => {
    const people = npcV3People(V3);
    for (const k of V1) expect(npcCoveredByV3(k, people), k).toBe(true);
    expect(npcCoveredByV3('npc.princess.idle.left.0', ['smith'])).toBe(false);
    expect(npcCoveredByV3('npc.3.walk.down.0', people)).toBe(false);
    expect(npcCoveredByV3('hero.idle.left.0', people)).toBe(false);
  });
  it('npcFrameKey: a mirrored left frame is asked for by its left key; no frame while the person\'s bundle is not in; without v3 as before', () => {
    const own = (art) => NPC_V3_PEOPLE.includes(art);
    const npc = (o) => ({ id: 'smith', look: 3, facing: 'left', moving: false, walkTime: 0, ...o });
    for (const who of NPC_V3_PEOPLE) {
      const { keys, mirrorOf } = npcV3Parts(V3, who);
      const loaded = new Set([...keys, ...mirrorOf.keys()]); // what the bundle answers for (placeholderPack mirrorOf)
      const has = (k) => loaded.has(k);
      for (const facing of DIRS) {
        const idle = npcFrameKey(npc({ id: who, facing }), 1.3, has, own);
        const walk = npcFrameKey(npc({ id: who, facing, moving: true, walkTime: 0.3 }), 0, has, own);
        expect(idle, `${who} ${facing}`).toMatch(new RegExp(`^npc\\.${who}\\.idle\\.${facing}\\.[0-3]$`));
        expect(walk, `${who} ${facing}`).toMatch(new RegExp(`^npc\\.${who}\\.walk\\.${facing}\\.[0-5]$`));
        for (const k of [idle, walk]) {
          expect(has(k)).toBe(true);
          const mirrored = facing === 'left' && NPC_V3_MIRROR_LEFT.includes(who);
          expect(mirrorOf.has(k), k).toBe(mirrored);
          expect(keys.includes(k), k).toBe(!mirrored);
        }
      }
    }
    // every walk frame of the smith's left is a mirror of the same-numbered right frame
    const smith = npcV3Parts(V3, 'smith');
    const hasSmith = (k) => smith.keys.includes(k) || smith.mirrorOf.has(k);
    for (let f = 0; f < 6; f++) {
      const k = npcFrameKey(npc({ moving: true, walkTime: (f + 0.5) / NPC_ANIM.walk.fps }), 0, hasSmith, own);
      expect(k).toBe(`npc.smith.walk.left.${f}`);
      expect(smith.mirrorOf.get(k)).toBe(`npc.smith.walk.right.${f}`);
    }
    // the bundle not in yet: no frame (never the placeholder look), whatever else is loaded
    const onlyPlaceholders = (k) => /^npc\.\d\./.test(k);
    expect(npcFrameKey(npc({}), 0, onlyPlaceholders, own)).toBe(null);
    expect(npcFrameKey(npc({ id: 'princess_forest', art: 'princess' }), 0, onlyPlaceholders, own)).toBe(null);
    // someone without v3 art, and the game without v3 (no `own`): the placeholder as before
    expect(npcFrameKey(npc({ id: 'stranger', facing: 'down' }), 0, onlyPlaceholders, own)).toBe('npc.3.walk.down.0');
    expect(npcFrameKey(npc({ facing: 'down' }), 0, onlyPlaceholders)).toBe('npc.3.walk.down.0');
    // without v3 the approved left frame (a stored file) is used as before
    const v1 = new Set(V1);
    expect(npcFrameKey(npc({}), 0, (k) => v1.has(k))).toMatch(/^npc\.smith\.idle\.left\./);
  });
  it('memory (STYLE.md 10.2): the 9 trimmed bundles together under 8.7 MB (1 MB = 1,000,000 bytes); the tight width never worse than the power of two', () => {
    let total = 0;
    for (const who of NPC_V3_PEOPLE) {
      const tight = atlasOf(who);
      const pow2 = atlasOf(who, { exactHeight: true });
      const bytes = tight.width * tight.height * 4;
      expect(bytes, who).toBeLessThanOrEqual(pow2.width * pow2.height * 4);
      expect(tight.width % 4).toBe(0);
      expect(tight.height % 4).toBe(0);
      expect(tight.width).toBeLessThanOrEqual(2048);
      expect(tight.height).toBeLessThanOrEqual(2048);
      // the shelves fit: packed as packAtlas does (1 px between frames)
      let x = 0;
      let y = 0;
      let shelf = 0;
      for (const e of tight.entries) {
        if (x + e.trim.w > tight.width) {
          x = 0;
          y += shelf + 1;
          shelf = 0;
        }
        expect(x + e.trim.w).toBeLessThanOrEqual(tight.width);
        x += e.trim.w + 1;
        shelf = Math.max(shelf, e.trim.h);
      }
      expect(y + shelf).toBeLessThanOrEqual(tight.height);
      expect(bytes, who).toBeLessThan(1.2e6);
      total += bytes;
    }
    expect(total).toBeLessThanOrEqual(8.7e6);
  });
  it('atlasSizeFor tight: only when asked (the other bundles keep their layout)', () => {
    const e = Array.from({ length: 40 }, () => ({ rows: [], image: { width: 56, height: 110 } }));
    expect(atlasSizeFor(e, { exactHeight: true })).toEqual({ width: 1024, height: 332 });
    const t = atlasSizeFor(e, { exactHeight: true, tight: true });
    expect(t.width * t.height).toBeLessThan(1024 * 332 * 0.8);
    expect(atlasSizeFor([], { tight: true })).toEqual(atlasSizeFor([]));
  });
  it('the build\'s opaque box of each frame is the box the game would read from the pixels', () => {
    for (const k of V3) {
      const img = png(dir3, k);
      expect(opaqueRect(img), k).toEqual(opaqueBox(img.data, img.width, img.height));
    }
  });
  it('all 9 people live in the plains region (the bundles are held with its chunks)', () => {
    const plains = REGIONS.find((r) => r.id === NPC_V3_REGION);
    const here = new Set((plains.npcs ?? []).map((n) => n.art ?? n.id));
    for (const who of NPC_V3_PEOPLE) expect(here.has(who), who).toBe(true);
    // elsewhere only the princess stands (loaded while she is on a loaded chunk)
    for (const r of REGIONS) if (r.id !== NPC_V3_REGION) for (const n of r.npcs ?? []) expect(n.art ?? n.id).toBe('princess');
  });
  it('the source table (tools/art_v3/npc_v3_sources.json) names every person once, with its left rule and file count', () => {
    expect(Object.keys(SOURCES).sort()).toEqual([...NPC_V3_PEOPLE]);
    for (const [who, s] of Object.entries(SOURCES)) {
      expect(s.commit, who).toMatch(/^[0-9a-f]{40}$/);
      expect(['final', 'provisional']).toContain(s.state);
      expect(s.left, who).toBe(NPC_V3_MIRROR_LEFT.includes(who) ? 'mirror' : 'stored');
      expect(s.files, who).toBe(V3.filter((k) => npcWhoOf(k) === who).length);
    }
  });
});
