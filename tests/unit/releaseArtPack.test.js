import { describe, it, expect, vi, afterEach } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { deflateSync, inflateSync } from 'node:zlib';
import { decodePng, encodePng, packGroup, packSheet, cutFrame, layoutSheet, releaseGroups, SHEET_PAD, MAX_SHEET, COLOUR_SPACE_CHUNKS } from '../../tools/release-art-pack.mjs';

// Release art packing (docs/perf/release-art-packing.md): each src/art-release/<group> becomes one
// sheet PNG + one frame table at build time, drawn exactly as the frame files were.
vi.mock('pixi.js', () => ({ Rectangle: class {}, Texture: class {} }));

const ROOT = fileURLToPath(new URL('../../src/art-release/', import.meta.url));
const HERO = `${ROOT}hero`;
const heroFiles = readdirSync(HERO).filter((f) => f.endsWith('.png')).sort();
const hero = packGroup(HERO);
const sheet = decodePng(hero.png);

describe('release art packer', () => {
  it('finds the groups (the folders under src/art-release)', () => {
    expect(releaseGroups(ROOT)).toContain('hero');
    expect(releaseGroups(`${ROOT}no-such-folder`)).toEqual([]);
  });

  it('the table names every frame file once, with its own size', () => {
    const names = Object.keys(hero.table.frames);
    expect(names).toEqual(heroFiles.map((f) => f.replace(/\.png$/, '')));
    for (const f of heroFiles) {
      const img = decodePng(readFileSync(`${HERO}/${f}`));
      expect(hero.table.frames[f.replace(/\.png$/, '')], f).toMatchObject({ w: img.width, h: img.height });
    }
    expect([sheet.width, sheet.height]).toEqual([hero.table.width, hero.table.height]);
  });

  it('frames lie inside the sheet and never overlap (with a gap between them)', () => {
    const rects = Object.values(hero.table.frames);
    for (const r of rects) {
      expect(r.x >= 0 && r.y >= 0 && r.x + r.w <= sheet.width && r.y + r.h <= sheet.height).toBe(true);
    }
    for (let i = 0; i < rects.length; i++) {
      for (let j = i + 1; j < rects.length; j++) {
        const [a, b] = [rects[i], rects[j]];
        const apart = a.x + a.w + SHEET_PAD <= b.x || b.x + b.w + SHEET_PAD <= a.x || a.y + a.h + SHEET_PAD <= b.y || b.y + b.h + SHEET_PAD <= a.y;
        expect(apart).toBe(true);
      }
    }
  });

  it('every frame cut back out of the sheet is the frame file, pixel for pixel', () => {
    for (const f of heroFiles) {
      const original = decodePng(readFileSync(`${HERO}/${f}`));
      const cut = cutFrame(sheet, hero.table.frames[f.replace(/\.png$/, '')]);
      expect(cut.width).toBe(original.width);
      expect(cut.height).toBe(original.height);
      expect(Buffer.from(cut.data).equals(Buffer.from(original.data)), f).toBe(true);
    }
  });

  it('the same frames always give the same sheet and table (byte for byte)', () => {
    const again = packGroup(HERO);
    expect(again.png.equals(hero.png)).toBe(true);
    expect(JSON.stringify(again.table)).toBe(JSON.stringify(hero.table));
    // and the insertion order of the frames does not matter
    const frames = new Map(heroFiles.map((f) => [f.replace(/\.png$/, ''), decodePng(readFileSync(`${HERO}/${f}`))]));
    const reversed = new Map([...frames].reverse());
    const a = packSheet(frames);
    const b = packSheet(reversed);
    expect(encodePng(a.image).equals(encodePng(b.image))).toBe(true);
    expect(JSON.stringify(a.frames)).toBe(JSON.stringify(b.frames));
  });

  it('encode → decode keeps every pixel (also semi-transparent ones)', () => {
    const data = new Uint8Array(5 * 3 * 4).map((_, i) => (i * 37) & 255);
    const back = decodePng(encodePng({ width: 5, height: 3, data }));
    expect([back.width, back.height]).toEqual([5, 3]);
    expect(Buffer.from(back.data).equals(Buffer.from(data))).toBe(true);
  });

  it('decodes every PNG row filter (None, Sub, Up, Average, Paeth) and the frame files as stored', () => {
    const [w, h] = [6, 5];
    const data = new Uint8Array(w * h * 4).map((_, i) => (i * 53 + (i >> 3) * 11) & 255);
    const ref = encodePng({ width: w, height: h, data });
    const stride = w * 4;
    const raw = Buffer.alloc((stride + 1) * h);
    const at = (x, y) => (x < 0 || y < 0 ? 0 : data[y * stride + x]);
    for (let y = 0; y < h; y++) {
      const f = y % 5;
      raw[y * (stride + 1)] = f;
      for (let x = 0; x < stride; x++) {
        const [a, b, c] = [at(x - 4, y), at(x, y - 1), at(x - 4, y - 1)];
        const p = a + b - c;
        const paeth = Math.abs(p - a) <= Math.abs(p - b) && Math.abs(p - a) <= Math.abs(p - c) ? a : Math.abs(p - b) <= Math.abs(p - c) ? b : c;
        const pred = [0, a, b, (a + b) >> 1, paeth][f];
        raw[y * (stride + 1) + 1 + x] = (data[y * stride + x] - pred) & 255;
      }
    }
    // swap the IDAT of the reference PNG for one with these filters
    const idat = deflateSync(raw);
    const len = Buffer.alloc(4);
    len.writeUInt32BE(idat.length);
    const png = Buffer.concat([ref.subarray(0, 33), len, Buffer.from('IDAT'), idat, Buffer.alloc(4), Buffer.from([0, 0, 0, 0, 0x49, 0x45, 0x4e, 0x44, 0xae, 0x42, 0x60, 0x82])]);
    expect(Buffer.from(decodePng(png).data).equals(Buffer.from(data))).toBe(true);

    // the frame files (filter None rows): decoded bytes are the stored bytes
    const file = readFileSync(`${HERO}/${heroFiles[0]}`);
    const img = decodePng(file);
    const rows = inflateSync(file.subarray(41, 41 + file.readUInt32BE(33)));
    for (let y = 0; y < img.height; y++) {
      if (rows[y * (img.width * 4 + 1)] !== 0) continue;
      expect(Buffer.from(img.data.subarray(y * img.width * 4, (y + 1) * img.width * 4)).equals(rows.subarray(y * (img.width * 4 + 1) + 1, (y + 1) * (img.width * 4 + 1)))).toBe(true);
    }
  });

  it('the sheet stays small enough for a phone (at most 4096 wide, about square)', () => {
    expect(sheet.width).toBeLessThanOrEqual(4096);
    expect(sheet.height).toBeLessThanOrEqual(sheet.width);
    const one = layoutSheet([{ name: 'a', width: 10, height: 20 }]);
    expect(one).toMatchObject({ width: 64, frames: { a: { x: 0, y: 0, w: 10, h: 20 } } });
  });

  it('refuses PNGs whose colours the browser might change (colour-space chunks)', () => {
    const png = encodePng({ width: 1, height: 1, data: new Uint8Array([1, 2, 3, 4]) });
    // put a gAMA chunk after IHDR (8 signature + 25 IHDR)
    const gama = Buffer.from([0, 0, 0, 4, 0x67, 0x41, 0x4d, 0x41, 0, 0, 0xb1, 0x8f, 0, 0, 0, 0]);
    const bad = Buffer.concat([png.subarray(0, 33), gama, png.subarray(33)]);
    expect(() => decodePng(bad, 'x.png')).toThrow(/gAMA/);
    const cicp = Buffer.concat([png.subarray(0, 33), Buffer.from([0, 0, 0, 4]), Buffer.from('cICP'), Buffer.from([9, 16, 0, 1, 0, 0, 0, 0])]);
    expect(() => decodePng(Buffer.concat([cicp, png.subarray(33)]), 'x.png')).toThrow(/cICP/);
    expect(COLOUR_SPACE_CHUNKS).toEqual(expect.arrayContaining(['gAMA', 'iCCP', 'cHRM', 'cICP']));
  });

  it('refuses a broken PNG whose pixel data is short', () => {
    const png = encodePng({ width: 4, height: 4, data: new Uint8Array(64).fill(200) });
    const raw = deflateSync(Buffer.alloc(3 * (1 + 4 * 4)));
    const len = Buffer.alloc(4);
    len.writeUInt32BE(raw.length);
    const bad = Buffer.concat([png.subarray(0, 33), len, Buffer.from('IDAT'), raw, Buffer.alloc(4), png.subarray(png.length - 12)]);
    expect(() => decodePng(bad, 'short.png')).toThrow(/broken PNG/);
  });

  it('stops when a group needs a sheet larger than 4096×4096', () => {
    const many = Array.from({ length: 6500 }, (_, i) => ({ name: `f${i}`, width: 48, height: 56 }));
    expect(MAX_SHEET).toBe(4096);
    expect(() => layoutSheet(many)).toThrow(/4096×\d+ sheet/);
    expect(() => layoutSheet([{ name: 'wide', width: 5000, height: 10 }])).toThrow(/wider than 4096/);
  });
});

describe('sheet frames in the game', () => {
  afterEach(() => vi.unstubAllGlobals());

  /** A stand-in canvas that records how it was drawn. */
  class FakeCanvas {
    width = 0;
    height = 0;
    calls = [];
    getContext() {
      return { drawImage: (...args) => this.calls.push(args), imageSmoothingEnabled: true };
    }
  }

  it('withOverrides cuts a sheet frame into an image of its own size (no smoothing)', async () => {
    vi.stubGlobal('document', { createElement: () => new FakeCanvas() });
    const { withOverrides, placeholderEntries } = await import('../../src/view/assets/placeholderPack.js');
    const entries = placeholderEntries().filter((e) => e.key === 'obj.rock');
    const sheetImage = { width: 1024, height: 569 };
    const [out] = await withOverrides(entries, new Map([['obj.rock', { sheet: sheetImage, x: 49, y: 57, w: 48, h: 56 }]]));
    expect(out.image).toMatchObject({ width: 48, height: 56 });
    expect(out.image.calls).toEqual([[sheetImage, 49, 57, 48, 56, 0, 0, 48, 56]]);
  });

  it('releaseFrames reads the built sheet + table and keeps the frame names (sorted, as before)', async () => {
    class FakeImage {
      set src(url) {
        this.url = url;
        setTimeout(() => this.onload?.());
      }
    }
    vi.stubGlobal('Image', FakeImage);
    vi.stubGlobal('fetch', async (url) => ({ ok: url === 'hero.json', json: async () => hero.table }));
    const { releaseFrames } = await import('../../src/view/assets/heroPrototype.js');
    const frames = await releaseFrames('hero', { hero: { sheet: 'hero.png', table: 'hero.json' } });
    expect([...frames.keys()]).toEqual(heroFiles.map((f) => f.replace(/\.png$/, '')));
    const first = /** @type {any} */ (frames.get('hero.attack1.down.1'));
    expect(first.sheet.url).toBe('hero.png');
    expect(first).toMatchObject(hero.table.frames['hero.attack1.down.1']);
    // a group with no sheet (and no files in this test) gives nothing
    expect((await releaseFrames('no-such-group', { hero: { sheet: 'hero.png', table: 'hero.json' } })).size).toBe(0);
  });

  it('releaseFrames gives the file URLs of a group built frame by frame (the v2 UI): nothing fetched', async () => {
    vi.stubGlobal('fetch', async () => {
      throw new Error('no fetch');
    });
    const { releaseFrames } = await import('../../src/view/assets/heroPrototype.js');
    const frames = await releaseFrames('v2/ui', { 'v2/ui': { files: { 'panel.menu': 'https://x/a.png', 'heart.0': 'https://x/b.png' } } });
    expect([...frames]).toEqual([
      ['panel.menu', 'https://x/a.png'],
      ['heart.0', 'https://x/b.png'],
    ]);
  });

  it('a sheet that cannot load leaves the placeholders (no crash)', async () => {
    vi.stubGlobal('Image', class {
      set src(_url) {
        setTimeout(() => this.onerror?.());
      }
    });
    vi.stubGlobal('fetch', async () => ({ ok: false }));
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const { releaseFrames } = await import('../../src/view/assets/heroPrototype.js');
    expect((await releaseFrames('hero', { hero: { sheet: 'x.png', table: 'x.json' } })).size).toBe(0);
    expect(warn).toHaveBeenCalledTimes(1);
    warn.mockRestore();
  });
});
