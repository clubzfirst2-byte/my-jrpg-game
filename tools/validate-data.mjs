// Checks data/items.json and the island's references to it (P6: data integrity, DESIGN.md roadmap).
// Usage: npm run check:data   (exit code 1 and a list of problems when something is wrong)
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { validateItems } from '../src/game/items/validateItems.js';
import { ISLAND } from '../src/game/world/maps/island.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
let data;
try {
  data = JSON.parse(readFileSync(join(root, 'data', 'items.json'), 'utf8'));
} catch (err) {
  console.error(`data/items.json: cannot read or parse (${err.message})`);
  process.exit(1);
}
const errors = validateItems(data, ISLAND);
if (errors.length > 0) {
  console.error(`data/items.json: ${errors.length} problem(s)`);
  for (const e of errors) console.error(`  - ${e}`);
  process.exit(1);
}
console.log(`data/items.json OK: ${data.items.length} items, ${data.recipes.length} recipes, island references checked`);
