// P11.5: writes the art kit — every sprite the game draws, as a PNG of its exact size (the
// placeholder art, to draw over), sorted into one folder per bundle, plus docs/ART.md with the list.
// Run: node tools/export_art_kit.mjs
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { deflateSync } from 'node:zlib';
import { placeholderEntries, REGION_ENTRIES } from '../src/view/assets/placeholderPack.js';
import { PALETTE } from '../src/view/assets/placeholderArt.js';

const OUT = new URL('../docs/art-kit/', import.meta.url);

const CRC = new Int32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c;
});
const crc32 = (buf) => {
  let c = -1;
  for (const b of buf) c = CRC[(c ^ b) & 255] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
};
const chunk = (type, data) => {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(td));
  return Buffer.concat([len, td, crc]);
};
/** @param {string[]} rows @param {number} scale */
export function png(rows, scale = 1) {
  const w = rows[0].length * scale;
  const h = rows.length * scale;
  const raw = Buffer.alloc((w * 4 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 4 + 1)] = 0;
    for (let x = 0; x < w; x++) {
      const c = rows[Math.floor(y / scale)][Math.floor(x / scale)];
      if (c === '.') continue;
      const hex = PALETTE[c];
      const o = y * (w * 4 + 1) + 1 + x * 4;
      raw[o] = parseInt(hex.slice(1, 3), 16);
      raw[o + 1] = parseInt(hex.slice(3, 5), 16);
      raw[o + 2] = parseInt(hex.slice(5, 7), 16);
      raw[o + 3] = 255;
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

const BUNDLES = [['base', placeholderEntries()], ...Object.entries(REGION_ENTRIES).map(([name, make]) => [name.replace(':', '-'), make()])];
const ANCHOR = (a) => (a[0] === 0 && a[1] === 0 ? '左上（大きさ固定）' : a[1] === 1 ? '足元' : '中心');

rmSync(OUT, { recursive: true, force: true });
const lines = [];
let count = 0;
for (const [bundle, entries] of BUNDLES) {
  mkdirSync(new URL(`${bundle}/`, OUT), { recursive: true });
  lines.push(`\n### ${bundle}（${entries.length} 枚）\n`, '| 名前（ファイル名） | 大きさ | 基準点 |', '|---|---|---|');
  for (const e of entries) {
    writeFileSync(new URL(`${bundle}/${e.key}.png`, OUT), png(e.rows));
    lines.push(`| \`${e.key}\` | ${e.rows[0].length}×${e.rows.length} | ${ANCHOR(e.anchor)} |`);
    count++;
  }
}
writeFileSync(new URL('LIST.md', OUT), `# 絵の一覧（${count} 枚、tools/export_art_kit.mjs で作成）\n${lines.join('\n')}\n`);
console.log(`${count} sprites written to docs/art-kit/`);
