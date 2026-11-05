import { describe, it, expect, vi, afterEach } from 'vitest';

// P11.5: the real art (src/art/<name>.png) replaces placeholder sprites by name.
vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));
const { withOverrides, atlasSizeFor, mustKeepSize, placeholderEntries } = await import('../../src/view/assets/placeholderPack.js');

/** A stand-in for the browser's Image: "loads" with the size written in its URL (w x h), or fails. */
class FakeImage {
  set src(url) {
    const m = /(\d+)x(\d+)/.exec(url);
    setTimeout(() => {
      if (!m) return this.onerror?.();
      this.width = Number(m[1]);
      this.height = Number(m[2]);
      this.onload?.();
    });
  }
}

describe('art overrides', () => {
  afterEach(() => vi.unstubAllGlobals());
  const entries = placeholderEntries().filter((e) => ['tile.path', 'obj.rock', 'obj.tree', 'tile.sand'].includes(e.key));

  it('only tiles (top-left anchored) must keep their size', () => {
    expect(mustKeepSize([0, 0])).toBe(true);
    expect(mustKeepSize([0.5, 1])).toBe(false);
    expect(mustKeepSize([0.5, 0.5])).toBe(false);
  });

  it('a PNG replaces its sprite; a tile of the wrong size or a broken file keeps the placeholder', async () => {
    vi.stubGlobal('Image', FakeImage);
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const out = await withOverrides(
      entries,
      new Map([
        ['tile.path', 'path-16x16.png'],
        ['obj.rock', 'rock-40x36.png'],
        ['tile.sand', 'sand-10x10.png'],
        ['obj.tree', 'broken.png'],
      ]),
    );
    const by = Object.fromEntries(out.map((e) => [e.key, e]));
    expect(by['tile.path'].image).toMatchObject({ width: 16, height: 16 });
    expect(by['obj.rock'].image).toMatchObject({ width: 40, height: 36 });
    expect(by['tile.sand'].image).toBeUndefined();
    expect(by['obj.tree'].image).toBeUndefined();
    expect(warn).toHaveBeenCalledTimes(2);
    warn.mockRestore();
  });

  it('no art at all: the entries are used as they are', async () => {
    expect(await withOverrides(entries, new Map())).toBe(entries);
  });

  it('the atlas grows to fit bigger art', () => {
    const big = entries.map((e) => ({ ...e, image: { width: 200, height: 200 } }));
    expect(atlasSizeFor(big)).toBeGreaterThan(atlasSizeFor(entries));
  });
});
