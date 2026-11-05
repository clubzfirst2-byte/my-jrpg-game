// Collects the ids every released version wrote into saves (P10.6, save compatibility): chests,
// checkpoints, landmarks, map items and the links of doors / gates. A save can name any of them, so
// the current world must still know them all (tests/unit/compat.test.js).
//
//   node tools/gen_legacy_ids.mjs   ->   tests/fixtures/legacy-ids.json
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
/** Every version since saving began (P3.5), by its merge commit. */
const VERSIONS = {
  'P3.5': 'a8f4e28',
  P4: '22498ac',
  P5: 'e0eae4b',
  P6: 'fba410d',
  P7: 'edede33',
  P8: '9d3be4d',
  P9: '3e0ef80',
  'P10.1': '7754586',
  'P10.2': '6218d99',
  'P10.3': '3f262c7',
};
const exists = (commit, f) => {
  try {
    execFileSync('git', ['cat-file', '-e', `${commit}:${f}`], { cwd: root, stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
};

/** @type {Record<string, Record<string, string[]>>} */
const out = {};
for (const [version, commit] of Object.entries(VERSIONS)) {
  const dir = mkdtempSync(join(tmpdir(), `ids-${version}-`));
  const files = ['src/game/world/maps/island.js', 'src/game/world/world.js', 'src/game/world/maps/regions.js'].filter((f) => exists(commit, f));
  for (const f of files) {
    mkdirSync(dirname(join(dir, f)), { recursive: true });
    writeFileSync(join(dir, f), execFileSync('git', ['show', `${commit}:${f}`], { cwd: root, encoding: 'utf8' }));
  }
  const def = files.includes('src/game/world/world.js')
    ? (await import(join(dir, 'src/game/world/world.js'))).WORLD
    : (await import(join(dir, 'src/game/world/maps/island.js'))).ISLAND;
  const ids = (/** @type {any[]} */ list) => [...new Set((list ?? []).map((o) => o.id))].sort();
  out[version] = {
    chests: ids(def.chests),
    checkpoints: ids(def.checkpoints),
    landmarks: ids(def.landmarks),
    pickups: ids(def.pickups),
    links: [...new Set([...(def.envObjects ?? []).filter((o) => o.link).map((o) => o.link), ...(def.switches ?? []).map((s) => s.link)])].sort(),
  };
  console.log(version, commit, Object.fromEntries(Object.entries(out[version]).map(([k, v]) => [k, v.length])));
}
writeFileSync(join(root, 'tests/fixtures/legacy-ids.json'), JSON.stringify(out, null, 1) + '\n');
console.log('wrote tests/fixtures/legacy-ids.json');
