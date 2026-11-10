import { describe, it, expect } from 'vitest';
import { existsSync, readdirSync } from 'node:fs';
import { V2_ENABLED, artVersion, resolveArtGroups, parseGroupName, v2Name } from '../../src/view/assets/artV2.js';
import { onDemandReleaseGroup, preloadReleaseGroup, precacheFiles, releaseGroupOf } from '../../tools/precache.mjs';

// Graphics v2 infrastructure (src/view/assets/artV2.js): src/art-release-v2/<group> drawn instead of
// src/art-release/<group> when present and enabled; ?v2=0 and ?<group>=v1|v2 to compare.
const p = (q) => new URLSearchParams(q);

describe('graphics v2 art groups', () => {
  it('enables only the groups whose art passed inspection (the enemies, d900394)', () => {
    expect(V2_ENABLED).toEqual(['enemy']);
    // the enabled groups' art is really there, with its frame table
    for (const g of V2_ENABLED) expect(existsSync(`src/art-release-v2/${g}/frames.json`)).toBe(true);
  });

  it('the enemies: v2 by default, v1 with ?v2=0 or ?enemy=v1', () => {
    const opts = { available: ['enemy'] };
    expect(artVersion('enemy', p(''), opts)).toBe('v2');
    expect(artVersion('enemy', p('v2=0'), opts)).toBe('v1');
    expect(artVersion('enemy', p('enemy=v1'), opts)).toBe('v1');
    expect(resolveArtGroups(['hero', 'enemy'], p(''), { ...opts, v1Groups: ['hero', 'enemy'] })).toEqual(['hero', 'v2/enemy']);
    expect(resolveArtGroups(['hero', 'enemy'], p('v2=0'), { ...opts, v1Groups: ['hero', 'enemy'] })).toEqual(['hero', 'enemy']);
  });

  it('a v2 group is drawn when present and enabled; ?v2=0 turns every group back to v1; ?<group>= wins', () => {
    const opts = { available: ['terrain', 'enemy', 'ui'], enabled: ['terrain', 'ui'] };
    expect(artVersion('terrain', p(''), opts)).toBe('v2');
    expect(artVersion('enemy', p(''), opts)).toBe('v1'); // present, not enabled yet
    expect(artVersion('enemy', p('enemy=v2'), opts)).toBe('v2'); // asked for (review)
    expect(artVersion('terrain', p('v2=0'), opts)).toBe('v1');
    expect(artVersion('terrain', p('terrain=v1'), opts)).toBe('v1');
    expect(artVersion('terrain', p('v2=0&terrain=v2'), opts)).toBe('v2');
    expect(artVersion('hero', p('hero=v2'), opts)).toBe('v1'); // no v2 hero in the build
    // the existing switches of a group (?terrain=placeholder, ?enemy=release) are not v1/v2: the list decides
    expect(artVersion('terrain', p('terrain=release'), opts)).toBe('v2');
  });

  it('the groups to load: each v1 group the game wants, or its v2 group; v2-only groups when drawn', () => {
    const opts = { available: ['terrain', 'enemy', 'ui'], enabled: ['terrain', 'ui'], v1Groups: ['hero', 'npc', 'enemy', 'terrain', 'objects'] };
    expect(resolveArtGroups(['hero', 'npc', 'enemy', 'terrain', 'objects'], p(''), opts)).toEqual(['hero', 'npc', 'enemy', 'v2/terrain', 'objects', 'v2/ui']);
    expect(resolveArtGroups(['hero', 'npc', 'enemy', 'terrain', 'objects'], p('v2=0'), opts)).toEqual(['hero', 'npc', 'enemy', 'terrain', 'objects']);
    expect(resolveArtGroups(['hero', 'npc', 'enemy', 'terrain', 'objects'], p('enemy=v2&ui=v1'), opts)).toEqual(['hero', 'npc', 'v2/enemy', 'v2/terrain', 'objects']);
    // a v1 group the game does not load now (?terrain=placeholder) does not come back as v2
    expect(resolveArtGroups(['hero', 'npc', 'enemy', 'objects'], p(''), opts)).toEqual(['hero', 'npc', 'enemy', 'objects', 'v2/ui']);
    // a group whose v2 art is not enabled: exactly the v1 group
    expect(resolveArtGroups(['hero', 'terrain'], p(''), { available: ['terrain'] })).toEqual(['hero', 'terrain']);
  });

  it('preload: only what normal play draws — the enabled v2 group, not the v1 group it replaces (kept offline)', () => {
    expect(preloadReleaseGroup('v2-enemy')).toBe(true);
    expect(preloadReleaseGroup('enemy')).toBe(false); // (an unused preload is a console warning)
    expect(onDemandReleaseGroup('enemy')).toBe(false); // still precached: ?v2=0 / ?enemy=v1 work offline
    for (const g of ['hero', 'npc', 'terrain', 'objects']) expect(preloadReleaseGroup(g)).toBe(!V2_ENABLED.includes(g));
    expect(preloadReleaseGroup('v2-terrain')).toBe(V2_ENABLED.includes('terrain'));
    expect(preloadReleaseGroup('npc-revision-b2')).toBe(false);
  });

  it('names: "v2/<group>" in the game, release-v2-<group>.png|json when built', () => {
    expect(v2Name('terrain')).toBe('v2/terrain');
    expect(parseGroupName('v2/enemy')).toEqual({ group: 'enemy', v2: true });
    expect(parseGroupName('enemy')).toEqual({ group: 'enemy', v2: false });
    expect(releaseGroupOf('release-v2-terrain.png')).toBe('v2-terrain');
  });

  it('offline: a v2 group is precached once enabled; until then it loads on demand; v1 groups stay', () => {
    expect(onDemandReleaseGroup('v2-terrain')).toBe(!V2_ENABLED.includes('terrain'));
    expect(onDemandReleaseGroup('terrain')).toBe(false);
    const asset = (fileName, name) => [fileName, { type: 'asset', fileName, names: [name] }];
    const files = precacheFiles(/** @type {any} */ (Object.fromEntries([asset('a/t.png', 'release-terrain.png'), asset('a/v.png', 'release-v2-terrain.png')])));
    expect(files).toContain('a/t.png');
    expect(files.includes('a/v.png')).toBe(V2_ENABLED.includes('terrain'));
  });

  it('the approved v1 folders are separate from the v2 folders', () => {
    const v2 = new URL('../../src/art-release-v2/', import.meta.url);
    if (!existsSync(v2)) return;
    for (const g of readdirSync(v2)) expect(g, 'a v2 folder is a plain group name').toMatch(/^[a-z][a-z0-9-]*$/);
  });
});
