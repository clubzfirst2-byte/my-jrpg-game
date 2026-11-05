// Checks data/items.json and the island's references to it (P6: data integrity, DESIGN.md roadmap).
// Usage: npm run check:data   (exit code 1 and a list of problems when something is wrong)
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { validateItems } from '../src/game/items/validateItems.js';
import { WORLD } from '../src/game/world/world.js';
import { validateTalk } from '../src/game/npc/validateTalk.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
let data;
try {
  data = JSON.parse(readFileSync(join(root, 'data', 'items.json'), 'utf8'));
} catch (err) {
  console.error(`data/items.json: cannot read or parse (${err.message})`);
  process.exit(1);
}
const read = (/** @type {string} */ name) => JSON.parse(readFileSync(join(root, 'data', name), 'utf8'));
let talk;
try {
  talk = { dialogue: read('dialogue.json'), quests: read('quests.json'), shops: read('shops.json'), items: data };
} catch (err) {
  console.error(`data: cannot read or parse dialogue / quests / shops (${err.message})`);
  process.exit(1);
}
const errors = [...validateItems(data, WORLD), ...validateTalk(talk, WORLD)];
if (errors.length > 0) {
  console.error(`data: ${errors.length} problem(s)`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}
console.log(`data OK: ${data.items.length} items, ${data.recipes.length} recipes, ${Object.keys(talk.dialogue.dialogues).length} dialogues, ${talk.quests.quests.length} quests, ${talk.shops.shops.length} shops; world references checked`);
