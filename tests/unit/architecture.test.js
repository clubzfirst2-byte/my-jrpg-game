// Guards the logic/render separation (DESIGN.md 1.1) independently of ESLint.
import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const GAME_DIR = new URL('../../src/game/', import.meta.url).pathname;

function listJs(dir) {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) return listJs(p);
    return p.endsWith('.js') ? [p] : [];
  });
}

const FORBIDDEN_IMPORT = /from\s+['"](pixi\.js|[^'"]*\/(view|debug|platform|ui|save)\/[^'"]*)['"]/;
const FORBIDDEN_GLOBAL = /\b(window|document|navigator|localStorage|indexedDB|requestAnimationFrame)\s*[.([]/;

describe('src/game stays pure (no renderer, no DOM)', () => {
  const files = listJs(GAME_DIR);

  it('has logic files to check', () => {
    expect(files.length).toBeGreaterThan(0);
  });

  for (const file of files) {
    it(`${file.slice(GAME_DIR.length)} has no forbidden imports or globals`, () => {
      const src = readFileSync(file, 'utf8').replace(/\/\/.*$/gm, '');
      expect(src).not.toMatch(FORBIDDEN_IMPORT);
      expect(src).not.toMatch(FORBIDDEN_GLOBAL);
    });
  }
});
