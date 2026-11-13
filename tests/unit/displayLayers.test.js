import { describe, it, expect } from 'vitest';
import { CORNERS, PRIORITY, displayLayers, landKey } from '../../src/view/groundV2.js';

// gfx v2 integration (start-up): displayLayers rewritten in plain loops gives exactly the layers of
// the version before (kept here as the reference), for every combination of 4 corners.
function reference({ cls, deep, waterVariant, edgeVariant, pick, macro }) {
  const out = [];
  const land = cls.filter((c) => c !== 'water');
  const rank = (c) => PRIORITY.indexOf(c);
  let lowest = null;
  if (land.length < 4) {
    const allDeep = cls.every((c, k) => c === 'water' && deep[k]);
    const v = waterVariant ? '.v1' : '';
    out.push({ key: `tile.water${allDeep ? '.deep' : ''}${v}`, anim: true });
    const deepMask = cls.reduce((m, c, k) => (c === 'water' && deep[k] ? m | CORNERS[k][2] : m), 0);
    if (deepMask && !allDeep) out.push({ key: `tile.water.deep.edge.${deepMask}`, anim: true });
    const landMask = cls.reduce((m, c, k) => (c !== 'water' ? m | CORNERS[k][2] : m), 0);
    if (landMask) out.push({ key: `tile.water.foam.${landMask}`, anim: true });
  } else {
    lowest = land.reduce((a, b) => (rank(b) < rank(a) ? b : a));
    const name = (new Set(cls).size === 1 ? macro() : null) ?? pick(lowest);
    out.push({ key: landKey(lowest, name), anim: false });
  }
  for (const t of [...new Set(land)].sort((a, b) => rank(a) - rank(b))) {
    if (t === lowest) continue;
    const mask = cls.reduce((m, c, k) => (c !== 'water' && rank(c) >= rank(t) ? m | CORNERS[k][2] : m), 0);
    out.push({ key: mask === 15 ? landKey(t, '0') : landKey(t, `edge.${mask}.${edgeVariant(t, mask)}`), anim: false });
  }
  return out;
}

describe('displayLayers (loops) = the version before', () => {
  it('every combination of 4 corners (9 lands and water), every deep pattern, both water variants, with and without a picture', () => {
    const kinds = ['water', ...PRIORITY];
    let n = 0;
    for (let a = 0; a < kinds.length; a++)
      for (let b = 0; b < kinds.length; b++)
        for (let c = 0; c < kinds.length; c++)
          for (let d = 0; d < kinds.length; d++) {
            const cls = [kinds[a], kinds[b], kinds[c], kinds[d]];
            const anyWater = cls.includes('water');
            for (let dm = 0; dm < (anyWater ? 16 : 1); dm++) {
              const deep = [0, 1, 2, 3].map((k) => !!(dm & (1 << k)));
              for (const waterVariant of [0, 1]) {
                for (const pic of [null, 'macro3.1']) {
                  const t = { cls, deep, waterVariant, edgeVariant: (s, m) => (m * 7 + s.length) % 4, pick: (s) => String(s.length * 3), macro: () => pic };
                  expect(displayLayers(t)).toEqual(reference(t));
                  n++;
                }
              }
            }
          }
    expect(n).toBeGreaterThan(100000);
  });
});
