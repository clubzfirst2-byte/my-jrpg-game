// Graphics v3: brings each villager's frames (src/art-release-v3/npc/npc.<who>.*.png) from the commit
// named in tools/art_v3/npc_v3_sources.json, and checks that the folder holds exactly those blobs.
//   node tools/art_v3/import_npc_v3.mjs           take the frames (git checkout <commit> -- <files>), then check
//   node tools/art_v3/import_npc_v3.mjs --check   only check (exit 1 on a difference)
// The pictures are never edited here: a person is replaced by changing its commit in the JSON.
import { execFileSync } from 'node:child_process';
import { readFileSync, readdirSync, rmSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const DIR = 'src/art-release-v3/npc';
const root = fileURLToPath(new URL('../../', import.meta.url));
const git = (/** @type {string[]} */ ...args) => execFileSync('git', args, { cwd: root, encoding: 'utf8', maxBuffer: 1 << 26 });
const { people } = JSON.parse(readFileSync(new URL('./npc_v3_sources.json', import.meta.url), 'utf8'));
const checkOnly = process.argv.includes('--check');

/** The frames of one person in a commit: file name → blob. @param {string} commit @param {string} who */
function framesIn(commit, who) {
  /** @type {Map<string, string>} */
  const out = new Map();
  for (const line of git('ls-tree', '-r', commit, '--', `${DIR}/`).split('\n')) {
    const m = /^\d+ blob ([0-9a-f]+)\t(.+)$/.exec(line);
    const name = m?.[2].slice(DIR.length + 1);
    if (m && name?.startsWith(`npc.${who}.`) && name.endsWith('.png')) out.set(name, m[1]);
  }
  return out;
}

let bad = 0;
const fail = (/** @type {string} */ msg) => {
  bad++;
  console.error(`NG  ${msg}`);
};
/** @type {Set<string>} */
const expected = new Set();
for (const [who, src] of Object.entries(people)) {
  const frames = framesIn(src.commit, who);
  if (frames.size !== src.files) fail(`${who}: ${frames.size} files in ${src.commit.slice(0, 7)}, the table says ${src.files}`);
  const lefts = [...frames.keys()].filter((n) => n.includes('.left.')).length;
  if ((src.left === 'mirror') !== (lefts === 0)) fail(`${who}: ${lefts} left files in ${src.commit.slice(0, 7)}, the table says left: ${src.left}`);
  if (!checkOnly) {
    for (const f of readdirSync(new URL(`../../${DIR}/`, import.meta.url))) if (f.startsWith(`npc.${who}.`) && !frames.has(f)) rmSync(new URL(`../../${DIR}/${f}`, import.meta.url));
    git('checkout', src.commit, '--', ...[...frames.keys()].map((n) => `${DIR}/${n}`));
  }
  let same = 0;
  for (const [name, blob] of frames) {
    expected.add(name);
    let here = '';
    try {
      here = git('hash-object', `${DIR}/${name}`).trim();
    } catch {
      /* missing */
    }
    if (here === blob) same++;
    else fail(`${name}: not the blob of ${src.commit.slice(0, 7)}`);
  }
  console.log(`${who.padEnd(10)} ${src.branch.padEnd(13)} ${src.commit.slice(0, 7)} ${src.state.padEnd(11)} left: ${src.left.padEnd(6)} ${same}/${frames.size} files are that commit's`);
}
const extra = readdirSync(new URL(`../../${DIR}/`, import.meta.url)).filter((f) => !expected.has(f));
if (extra.length) fail(`${extra.length} files of no listed person: ${extra.slice(0, 5).join(', ')}`);
console.log(`${expected.size} files expected, ${extra.length} others${bad ? `, ${bad} problems` : ''}`);
process.exit(bad ? 1 : 0);
