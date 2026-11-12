// @ts-check
// Graphics v3 (?v3=1): the normal enemies at density 4 (src/art-release-v3/enemy, docs/art-release-v3/
// ENEMY.md; same keys, frame counts, fps and feet as v2, twice the pixels). Memory (STYLE.md 10.2, the
// coordinator: about 2.9 MB a region): each kind is a bundle of its own, "v3:enemy:<kind>", packed
// without the frames' transparent margins (placeholderPack opaqueBox), and a chunk loads the kinds that
// spawn in its regions — a region holds only its own kinds, and two regions side by side share theirs
// (a bundle per region would hold a kind twice at the border). An enemy of another kind (a debug spawn)
// has its kind loaded while it lives (gameView.updateEnemyBundles); until then it is drawn with the
// base bundle's frames. The bosses keep their v2 frames, blown up 2×2. The shots are not drawn by the
// game yet (as in v2), so they are not packed; neither are the minimal frames (enemy.<kind>.0 / .1:
// the same pictures as idle.0 / move.0), which stay v2 in the base bundle.
// Pure (no PixiJS).

/** The kinds with v3 frames. */
export const V3_ENEMY_KINDS = Object.freeze(['slime', 'beast', 'archer', 'sentinel']);

/** A v3 normal enemy's per-action frame key → its kind, else null. @param {string} key */
export function v3EnemyKindOf(key) {
  const m = /^enemy\.(slime|beast|archer|sentinel)\.(?:idle|move|windup|attack|hurt|defeat)\.\d+$/.exec(key);
  return m ? m[1] : null;
}

/** Whether a v3 enemy key is one this does not use (the shots, the minimal frames). @param {string} key */
export const v3EnemyUnused = (key) => /^enemy\.shot\./.test(key) || /^enemy\.(?:slime|beast|archer|sentinel)\.\d+$/.test(key);

/** The bundle of a kind. @param {string} kind */
export const v3EnemyBundle = (kind) => `v3:enemy:${kind}`;

/**
 * The kinds that spawn in each region (from the map's spawns; '' = outside every region). @param {{ kind: string, tx: number, ty: number }[]} spawns
 * @param {(tx: number, ty: number) => string | null | undefined} regionAt @returns {Map<string, Set<string>>}
 */
export function kindsByRegion(spawns, regionAt) {
  /** @type {Map<string, Set<string>>} */
  const out = new Map();
  for (const s of spawns) {
    const r = regionAt(s.tx, s.ty) ?? ''; // ('' = outside every region)
    if (!V3_ENEMY_KINDS.includes(s.kind)) continue;
    if (!out.has(r)) out.set(r, new Set());
    /** @type {Set<string>} */ (out.get(r)).add(s.kind);
  }
  return out;
}
