// @ts-check
// P11.5: a SIZE-TEST hero (仮素材 — not the hero's art). Only with ?hero=test: frames of the new
// standard size (32×56, ART_SCALE 2) drawn from simple shapes in the approved colours, to check
// the hero against the tiles, camera and effects before the real art (P12) exists. It is never
// written to src/art and never shipped as the hero.

export const TEST_HERO_SIZE = /** @type {const} */ ({ w: 32, h: 56 });

const C = {
  line: '#1a1c2c',
  hair: '#7a4a2a',
  hairLight: '#a0683e',
  skin: '#f2c49b',
  eye: '#4aa0c8',
  cloak: '#739355',
  cloakLight: '#96b188',
  cloakDark: '#406a53',
  gold: '#f8d684',
  pendant: '#5cc8ff',
  pendantCore: '#d8f4ff',
  shirt: '#e8e4dc',
  leather: '#7a5a3a',
  trousers: '#3a3a48',
  boot: '#5a3e28',
  water: '#cfe8ff',
};

/**
 * @param {CanvasRenderingContext2D} g
 * @param {'down' | 'up' | 'right'} dir
 * @param {number} step -1, 0 or 1: which leg is forward
 * @param {number} top how far down the body starts (swimming sinks it)
 */
function drawHero(g, dir, step, top) {
  const r = (/** @type {string} */ c, /** @type {number} */ x, /** @type {number} */ y, /** @type {number} */ w, /** @type {number} */ h) => {
    g.fillStyle = c;
    g.fillRect(x, y + top, w, h);
  };
  // Legs and boots (rows 44..55).
  const legL = step < 0 ? -2 : 0;
  const legR = step > 0 ? -2 : 0;
  r(C.line, 10, 43 + legL, 6, 13 - legL);
  r(C.line, 17, 43 + legR, 6, 13 - legR);
  r(C.trousers, 11, 43 + legL, 4, 7);
  r(C.trousers, 18, 43 + legR, 4, 7);
  r(C.boot, 11, 50 + legL, 4, 5 - legL);
  r(C.boot, 18, 50 + legR, 4, 5 - legR);
  // Cloak (the silhouette): wide, to the knees, gold hem.
  r(C.line, 5, 22, 22, 25);
  r(dir === 'up' ? C.cloak : C.cloakDark, 6, 23, 20, 23);
  r(C.gold, 6, 45, 20, 1);
  if (dir === 'up') {
    // Back: the gold star on the cloak, the hood.
    r(C.cloakLight, 8, 23, 16, 4);
    r(C.gold, 15, 30, 2, 8);
    r(C.gold, 12, 33, 8, 2);
  } else {
    // Front / side: shirt, belt, the glowing star-ring pendant.
    const cx = dir === 'right' ? 14 : 11;
    r(C.shirt, cx, 24, 10, 20);
    r(C.leather, cx, 36, 10, 2);
    r(C.gold, cx + 4, 36, 2, 2);
    r(C.cloak, 6, 23, cx - 6, 23);
    if (dir === 'down') r(C.cloak, 21, 23, 5, 23);
    const px = dir === 'right' ? 20 : 15;
    r(C.gold, px - 1, 27, 4, 5);
    r(C.pendant, px, 28, 2, 3);
    r(C.pendantCore, px, 29, 1, 1);
  }
  // Head (rows 2..24): hair, face, eyes.
  r(C.line, 6, 3, 20, 21);
  r(C.line, 9, 1, 14, 3);
  r(C.hair, 7, 4, 18, 19);
  r(C.hair, 10, 2, 12, 2);
  r(C.hairLight, 10, 5, 10, 2);
  r(C.hair, 22, 0, 2, 3); // the cowlick
  if (dir === 'down') {
    r(C.skin, 9, 11, 14, 11);
    r(C.hair, 9, 10, 9, 3); // asymmetric fringe: longer on the left
    r(C.hair, 18, 10, 5, 2);
    r(C.line, 11, 15, 3, 1);
    r(C.eye, 11, 16, 3, 2);
    r(C.line, 18, 15, 3, 1);
    r(C.eye, 18, 16, 3, 2);
    r(C.line, 15, 20, 2, 1);
  } else if (dir === 'right') {
    r(C.skin, 15, 11, 9, 11);
    r(C.hair, 15, 10, 7, 3);
    r(C.line, 20, 15, 3, 1);
    r(C.eye, 21, 16, 2, 2);
    r(C.line, 22, 20, 2, 1);
  }
}

/**
 * The frames, by the same names as the placeholder hero (walk 3 × 4, swim 2 × 4).
 * @returns {Map<string, string>} name → PNG data URL
 */
export function testHeroFrames() {
  /** @type {Map<string, string>} */
  const out = new Map();
  const canvas = document.createElement('canvas');
  canvas.width = TEST_HERO_SIZE.w;
  canvas.height = TEST_HERO_SIZE.h;
  const g = /** @type {CanvasRenderingContext2D} */ (canvas.getContext('2d'));
  const frame = (/** @type {string} */ name, /** @type {(g: CanvasRenderingContext2D) => void} */ draw, /** @type {boolean} */ mirror) => {
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.clearRect(0, 0, canvas.width, canvas.height);
    if (mirror) g.setTransform(-1, 0, 0, 1, canvas.width, 0);
    draw(g);
    out.set(name, canvas.toDataURL('image/png'));
  };
  const steps = [0, -1, 1];
  for (const dir of /** @type {const} */ (['down', 'up', 'right', 'left'])) {
    const d = dir === 'left' ? 'right' : dir;
    const mirror = dir === 'left';
    steps.forEach((s, f) => frame(`player.walk.${dir}.${f}`, (gg) => drawHero(gg, d, s, 0), mirror));
    for (let f = 0; f < 2; f++) {
      frame(
        `player.swim.${dir}.${f}`,
        (gg) => {
          // Head and shoulders above the water, in the same 32×56 frame (feet line at the bottom).
          drawHero(gg, d, 0, 18);
          gg.clearRect(0, 47, 32, 9);
          gg.fillStyle = C.water;
          gg.fillRect(f ? 3 : 5, 46, 22, 2);
          gg.fillRect(f ? 7 : 3, 49, 22, 1);
        },
        mirror,
      );
    }
  }
  return out;
}
