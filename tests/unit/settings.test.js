import { describe, it, expect } from 'vitest';
import { createGameState } from '../../src/game/state.js';
import { WORLD } from '../../src/game/world/world.js';
import { hitPlayer, DIFFICULTY } from '../../src/game/combat/damage.js';
import { SETTING_ROWS } from '../../src/ui/settingsMenu.js';

// P11.3: settings — difficulty changes how hard hits land; every setting has its row.

describe('difficulty', () => {
  const hurt = (difficulty, damage) => {
    const s = createGameState(WORLD);
    s.difficulty = difficulty;
    const before = s.player.hp;
    hitPlayer(s, { owner: 'enemy', id: 'x', damage, from: { x: s.player.x, y: s.player.y - 20 }, kind: 'melee' });
    return before - s.player.hp;
  };
  it('easy halves, hard adds half again (rounded, never below one quarter heart)', () => {
    expect(hurt('normal', 2)).toBe(2);
    expect(hurt('easy', 2)).toBe(1);
    expect(hurt('easy', 1)).toBe(1);
    expect(hurt('hard', 2)).toBe(3);
    expect(hurt('hard', 3)).toBe(5);
    expect(Object.keys(DIFFICULTY)).toEqual(['easy', 'normal', 'hard']);
  });
  it('a new game is normal', () => {
    expect(createGameState(WORLD).difficulty).toBe('normal');
  });
});

describe('the settings screen', () => {
  it('has a row for each setting, each with its choices', () => {
    expect(SETTING_ROWS.map((r) => r.key)).toEqual(['difficulty', 'textSize', 'buttonSize', 'hand', 'bgmVolume', 'sfxVolume']);
    for (const r of SETTING_ROWS) expect(r.options.length).toBeGreaterThanOrEqual(2);
  });
});
