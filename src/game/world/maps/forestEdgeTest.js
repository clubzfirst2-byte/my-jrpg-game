// @ts-check
// Graphics v3 test map (?map=forestedge): the plains and the forest side by side, 224×96 tiles (7×3 chunks).
// In the world the two regions are in different columns (x 0-111 and 128-239) and never meet; this map is
// where their border (FOREST.md 1, the winter exchange of NAMES.md 2.1) and the plains pine rule (FOREST.md 4)
// are seen and tested. Plains on the west, forest east of a wavy border (each row's split is its own pair of
// 1-row region rectangles), a road across both, a pond, scattered plains trees, the wood dense with clearings.
// Like ?map=height and ?map=field it skips the title and never touches the save.

const W = 224;
const H = 96;

/** A small integer hash (deterministic). @param {number} x @param {number} y @param {number} s */
const h = (x, y, s) => {
  let v = (Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(s | 0, 2147483647)) >>> 0;
  v = Math.imul(v ^ (v >>> 13), 1274126177) >>> 0;
  return ((v ^ (v >>> 16)) >>> 0) / 2 ** 32;
};

/** The first forest column of row y (the border wanders 156-164: the plains pine only west of x 64, FOREST.md 4). @param {number} y */
export const forestEdgeBorder = (y) => Math.round(160 + 3 * Math.sin(y * 0.21) + 1.5 * Math.sin(y * 0.57 + 1));

function build() {
  const rows = [];
  for (let y = 0; y < H; y++) {
    const b = forestEdgeBorder(y);
    let r = '';
    for (let x = 0; x < W; x++) {
      let c;
      const edge = x < 2 || y < 2 || x >= W - 2 || y >= H - 2;
      const road = y === 48 || y === 49 || (x === 30 && y > 49);
      const pond = (x - 20) ** 2 / 36 + (y - 22) ** 2 / 16 < 1;
      const clearing = (x - 190) ** 2 / 64 + (y - 30) ** 2 / 36 < 1 || (x - 200) ** 2 / 49 + (y - 72) ** 2 / 25 < 1 || (x - b - 6) ** 2 / 25 + (y - 70) ** 2 / 16 < 1;
      if (edge) c = 'T';
      else if (road) c = '=';
      else if (pond) c = '~';
      else if (x >= b) {
        // the wood: dense, open along the road and its border, clearings
        const open = clearing || Math.abs(y - 48.5) < 4 || x < b + 2;
        c = !open && h(x, y, 7) < 0.82 ? 'T' : open && h(x, y, 8) < 0.04 ? 'T' : '.';
      } else c = h(x, y, 9) < (h(x >> 3, y >> 3, 10) < 0.3 ? 0.18 : 0.035) ? 'T' : '.';
      if (x === 150 && y === 48) c = 'P';
      r += c;
    }
    rows.push(r);
  }
  return rows;
}

/** @type {any} */
export const FOREST_EDGE_TEST = {
  ground: build(),
  regions: Array.from({ length: H }, (_, y) => [
    { id: 'plains', name: '草原', tx: 0, ty: y, tw: forestEdgeBorder(y), th: 1, climate: 'temperate', bundle: 'region:plains' },
    { id: 'forest', name: '森', tx: forestEdgeBorder(y), ty: y, tw: W - forestEdgeBorder(y), th: 1, climate: 'temperate', bundle: 'region:forest' },
  ]).flat(),
  outdoor: { id: 'outdoor', tx: 0, ty: 0, tw: W, th: H },
};
