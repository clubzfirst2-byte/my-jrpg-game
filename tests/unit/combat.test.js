import { describe, it, expect } from 'vitest';
import { createGameState, stepGame, DEATH_DELAY_MS } from '../../src/game/state.js';
import { FixedStepLoop } from '../../src/game/core/fixedStep.js';
import { SWORD, COMBAT } from '../../src/game/entities/playerCombat.js';
import { ENEMY_KINDS, PARRY_STUN_MS } from '../../src/game/entities/enemies.js';
import { PLAYER_MAX_HP } from '../../src/game/entities/player.js';

const none = { moveX: 0, moveY: 0, dash: false, jump: false, attack: false, dodge: false, guard: false, bow: false };
const STEP_MS = 1000 / 60;

/** Open 24x12 arena; player spawn at tile (5,6). */
function arena(enemies = []) {
  const rows = [];
  for (let y = 0; y < 12; y++) {
    let r = '';
    for (let x = 0; x < 24; x++) r += x === 0 || y === 0 || x === 23 || y === 11 ? '#' : x === 5 && y === 6 ? 'P' : '.';
    rows.push(r);
  }
  return { ground: rows, enemies };
}

function run(s, input, steps) {
  for (let i = 0; i < steps; i++) stepGame(s, typeof input === 'function' ? input(i) : { ...none, ...input });
}

/** Turn the player to face right without moving noticeably. */
function faceRight(s) {
  stepGame(s, { ...none, moveX: 1 });
  run(s, none, 10);
}

/** Pin an enemy in place as a training dummy (it still takes hits). */
function dummy(e) {
  e.state = 'stun';
  e.t = 0;
  e.stunMs = 1e9;
}

/** Re-pin after each step (hits put enemies into a short stagger). */
function runDummy(s, input, steps) {
  for (let i = 0; i < steps; i++) {
    stepGame(s, typeof input === 'function' ? input(i) : { ...none, ...input });
    for (const e of s.enemies) if (e.state !== 'dead') dummy(e);
  }
}

describe('sword', () => {
  it('a swing hits an enemy in front once, during its active window only', () => {
    const s = createGameState(arena([{ kind: 'beast', tx: 6, ty: 6 }]));
    const e = s.enemies[0];
    dummy(e);
    faceRight(s);
    let firstHitStep = -1;
    runDummy(s, (i) => {
      if (firstHitStep < 0 && e.hp < ENEMY_KINDS.beast.hp) firstHitStep = i;
      return { ...none, attack: i === 0 };
    }, 40);
    expect(e.hp).toBe(ENEMY_KINDS.beast.hp - SWORD[0].damage); // exactly one hit
    // The blade connects only after the startup time (ms-based).
    expect(firstHitStep * STEP_MS).toBeGreaterThanOrEqual(SWORD[0].startupMs - STEP_MS);
  });

  it('does not hit an enemy behind the player', () => {
    const s = createGameState(arena([{ kind: 'beast', tx: 4, ty: 6 }]));
    dummy(s.enemies[0]);
    faceRight(s);
    runDummy(s, (i) => ({ ...none, attack: i === 0 }), 40);
    expect(s.enemies[0].hp).toBe(ENEMY_KINDS.beast.hp);
  });

  it('pressing again during the buffer window chains a 3-hit combo (finisher hits harder)', () => {
    const s = createGameState(arena([{ kind: 'beast', tx: 6, ty: 6 }]));
    const e = s.enemies[0];
    e.hp = e.maxHp = 100;
    dummy(e);
    faceRight(s);
    const seen = new Set();
    runDummy(s, (i) => {
      seen.add(s.player.comboIndex);
      return { ...none, attack: i % 12 === 0 }; // tap every 200ms
    }, 80);
    expect([...seen]).toEqual(expect.arrayContaining([0, 1, 2]));
    expect(100 - e.hp).toBe(SWORD[0].damage + SWORD[1].damage + SWORD[2].damage);
  });

  it('a press after the swing has finished starts over at the first swing', () => {
    const s = createGameState(arena());
    faceRight(s);
    run(s, (i) => ({ ...none, attack: i === 0 }), 40); // first swing finishes
    run(s, (i) => ({ ...none, attack: i === 0 }), 2);
    expect(s.player.action).toBe('attack');
    expect(s.player.comboIndex).toBe(0);
  });

  it('the combo deals the same damage at 30fps and 60fps (timings are in ms)', () => {
    const sim = (fps) => {
      const s = createGameState(arena([{ kind: 'beast', tx: 6, ty: 6 }]));
      const e = s.enemies[0];
      e.hp = e.maxHp = 100;
      dummy(e);
      faceRight(s);
      const loop = new FixedStepLoop();
      for (let f = 0; f < fps * 1.5; f++) {
        const t = (f * 1000) / fps;
        const input = { ...none, attack: Math.floor(t / 200) !== Math.floor((t - 1000 / fps) / 200) };
        loop.advance(1000 / fps, () => {
          stepGame(s, input);
          dummy(e);
        });
      }
      return 100 - e.hp;
    };
    expect(sim(30)).toBe(sim(60));
    expect(sim(30)).toBeGreaterThan(SWORD[0].damage);
  });

  it('movement is slowed while swinging', () => {
    const s = createGameState(arena());
    const x0 = s.player.x;
    run(s, (i) => ({ ...none, moveX: 1, attack: i === 0 }), 12);
    const swingDist = s.player.x - x0;
    const s2 = createGameState(arena());
    run(s2, { moveX: 1 }, 12);
    expect(swingDist).toBeLessThan((s2.player.x - x0) * 0.5);
  });
});

/** Beast right next to the player, about to lunge. Returns the state at the start of its attack. */
function beastAboutToLunge(fps = 60) {
  const s = createGameState(arena([{ kind: 'beast', tx: 7, ty: 6 }]));
  const loop = new FixedStepLoop();
  const e = s.enemies[0];
  // Let it notice the player and start its wind-up.
  for (let f = 0; f < fps * 3 && e.state !== 'windup'; f++) loop.advance(1000 / fps, () => stepGame(s, none));
  return { s, e, loop };
}

describe('dodge', () => {
  it('moves quickly and is invulnerable: a lunge during the dodge does no damage', () => {
    const { s, e, loop } = beastAboutToLunge();
    expect(e.state).toBe('windup');
    // Dodge late in the wind-up (not a perfect dodge window), toward the beast so the lunge connects.
    while (e.t < ENEMY_KINDS.beast.windupMs - 40) loop.advance(STEP_MS, () => stepGame(s, none));
    const toward = Math.sign(e.x - s.player.x);
    let hurt = false;
    for (let i = 0; i < 40; i++) {
      stepGame(s, { ...none, moveX: toward, dodge: i < 2 });
      if (s.player.hp < PLAYER_MAX_HP) hurt = true;
    }
    expect(hurt).toBe(false);
  });

  it('a dodge pressed early in a swing is buffered and happens when the blade has passed', () => {
    const s = createGameState(arena());
    faceRight(s);
    run(s, (i) => ({ ...none, attack: i === 0, dodge: i === 3 }), 3 + 1); // press dodge ~50ms into the swing
    expect(s.player.action).toBe('attack');
    const sw = SWORD[0];
    run(s, none, Math.ceil((sw.startupMs + sw.activeMs) / STEP_MS));
    expect(s.player.action).toBe('dodge'); // cancelled the recovery
  });

  it('a dodge pressed during a swing recovery cancels it immediately', () => {
    const s = createGameState(arena());
    faceRight(s);
    const sw = SWORD[0];
    run(s, (i) => ({ ...none, attack: i === 0 }), Math.ceil((sw.startupMs + sw.activeMs + 30) / STEP_MS));
    expect(s.player.action).toBe('attack');
    run(s, { dodge: true }, 1);
    expect(s.player.action).toBe('dodge');
  });

  for (const fps of [60, 30]) {
    it(`a perfect dodge (hit within ${COMBAT.justDodgeMs}ms) slows the enemies, at ${fps}fps too`, () => {
      const { s, e, loop } = beastAboutToLunge(fps);
      // Press dodge 1-2 frames before the lunge starts so the hit lands early in the dodge.
      const frameMs = 1000 / fps;
      while (e.t < ENEMY_KINDS.beast.windupMs - frameMs * 1.5) loop.advance(frameMs, () => stepGame(s, none));
      const toward = Math.sign(e.x - s.player.x);
      let flurry = false;
      for (let f = 0; f < fps * 0.6; f++) {
        const input = { ...none, moveX: toward, dodge: f === 0 };
        loop.advance(frameMs, () => stepGame(s, input));
        if (s.flurryMs > 0) flurry = true;
      }
      expect(flurry).toBe(true);
      expect(s.player.hp).toBe(PLAYER_MAX_HP);
    });
  }

  it('during the slow motion enemies move at a fraction of their speed', () => {
    const s = createGameState(arena([{ kind: 'beast', tx: 10, ty: 6 }])); // within sight
    const e = s.enemies[0];
    e.state = 'chase';
    stepGame(s, none);
    const x0 = e.x;
    run(s, none, 10);
    const normal = Math.abs(e.x - x0);
    s.flurryMs = COMBAT.flurryMs;
    const x1 = e.x;
    run(s, none, 10);
    const slowed = Math.abs(e.x - x1);
    expect(slowed).toBeLessThan(normal * COMBAT.flurryScale * 1.5);
  });
});

describe('guard', () => {
  it('blocks a frontal hit (no damage), but not a hit from behind', () => {
    const front = beastAboutToLunge();
    faceTowardBeast(front);
    run(front.s, (i) => ({ ...none, guard: true, moveX: i === 0 ? Math.sign(front.e.x - front.s.player.x) * 0.1 : 0 }), 2);
    // Guard raised well before the hit (not a parry).
    run(front.s, { guard: true }, 60);
    expect(front.s.player.hp).toBe(PLAYER_MAX_HP);
    expect(front.e.state).not.toBe('stun');

    const back = beastAboutToLunge();
    // Face away from the beast.
    stepGame(back.s, { ...none, moveX: -Math.sign(back.e.x - back.s.player.x) * 0.3 });
    run(back.s, { guard: true }, 60);
    expect(back.s.player.hp).toBeLessThan(PLAYER_MAX_HP);
  });

  it(`a perfect guard (raised within ${COMBAT.justGuardMs}ms of the hit) stuns a melee enemy`, () => {
    const { s, e } = beastAboutToLunge();
    faceTowardBeast({ s, e });
    while (e.t < ENEMY_KINDS.beast.windupMs - 30) stepGame(s, none);
    let stunned = false;
    for (let i = 0; i < 40; i++) {
      stepGame(s, { ...none, guard: true });
      if (e.state === 'stun' && e.stunMs === PARRY_STUN_MS) stunned = true;
    }
    expect(stunned).toBe(true);
    expect(s.player.hp).toBe(PLAYER_MAX_HP);
  });

  it('a perfect guard sends an archer orb back at the archer', () => {
    const s = createGameState(arena([{ kind: 'archer', tx: 11, ty: 6 }]));
    const a = s.enemies[0];
    faceRight(s);
    // Wait for the orb, then raise the guard just before it arrives.
    let parried = false;
    for (let i = 0; i < 600 && !parried; i++) {
      const orb = s.projectiles.find((pr) => pr.owner === 'enemy');
      const close = orb && Math.abs(orb.x - s.player.x) < 16 && Math.abs(orb.x - s.player.x) > 8;
      stepGame(s, { ...none, guard: !!close || s.player.guarding });
      if (s.projectiles.some((pr) => pr.reflected)) parried = true;
    }
    expect(parried).toBe(true);
    run(s, none, 120);
    expect(a.hp).toBeLessThan(ENEMY_KINDS.archer.hp);
  });
});

/** @param {{ s: any, e: any }} c */
function faceTowardBeast(c) {
  stepGame(c.s, { ...none, moveX: Math.sign(c.e.x - c.s.player.x) * 0.3 });
}

describe('bow', () => {
  it('a full draw then release shoots an arrow in the aim direction; an early release does not', () => {
    const s = createGameState(arena());
    faceRight(s);
    run(s, (i) => ({ ...none, bow: i < 5 }), 8); // ~83ms: too early
    expect(s.projectiles).toHaveLength(0);
    run(s, (i) => ({ ...none, bow: i < Math.ceil(COMBAT.bowDrawMs / STEP_MS) + 1 }), Math.ceil(COMBAT.bowDrawMs / STEP_MS) + 2);
    const arrows = s.projectiles.filter((p) => p.kind === 'arrow');
    expect(arrows).toHaveLength(1);
    expect(arrows[0].vx).toBeGreaterThan(0); // flying right, the aim direction
    expect(arrows[0].vy).toBeCloseTo(0, 6);
  });

  it('an arrow damages an enemy at range', () => {
    const s = createGameState(arena([{ kind: 'beast', tx: 14, ty: 6 }]));
    const e = s.enemies[0];
    dummy(e);
    faceRight(s);
    runDummy(s, (i) => ({ ...none, bow: i < Math.ceil(COMBAT.bowDrawMs / STEP_MS) + 1 }), 90);
    expect(e.hp).toBe(ENEMY_KINDS.beast.hp - COMBAT.arrowDamage);
  });

  it('arrows stop at walls', () => {
    const s = createGameState(arena());
    faceRight(s);
    run(s, (i) => ({ ...none, bow: i < Math.ceil(COMBAT.bowDrawMs / STEP_MS) + 1 }), 120);
    expect(s.projectiles).toHaveLength(0);
  });

  it('aiming in mid-air slows time and costs stamina', () => {
    const s = createGameState(arena());
    s.player.z = 64; // high in the air above flat ground
    s.player.grounded = false;
    s.player.vz = 0;
    const st0 = s.player.stamina;
    stepGame(s, { ...none, bow: true });
    stepGame(s, { ...none, bow: true });
    expect(s.bulletTime).toBe(true);
    const z0 = s.player.z;
    run(s, { bow: true }, 10);
    const slowFall = z0 - s.player.z;
    expect(s.player.stamina).toBeLessThan(st0);
    // Compare with a normal fall over the same steps.
    const s2 = createGameState(arena());
    s2.player.z = 64;
    s2.player.grounded = false;
    s2.player.vz = s.player.vz / COMBAT.bulletTimeScale;
    run(s2, none, 12);
    expect(slowFall).toBeLessThan(64 - s2.player.z);
  });
});

describe('taking damage, enemies and death', () => {
  it('a hit costs health, knocks back and gives a short invulnerability', () => {
    const { s, e } = beastAboutToLunge();
    const x0 = s.player.x;
    let hurtAt = -1;
    for (let i = 0; i < 60 && hurtAt < 0; i++) {
      stepGame(s, none);
      if (s.player.hp < PLAYER_MAX_HP) hurtAt = i;
    }
    expect(s.player.hp).toBe(PLAYER_MAX_HP - ENEMY_KINDS.beast.damage);
    expect(s.player.invulnMs).toBeGreaterThan(COMBAT.hurtInvulnMs - 50);
    run(s, none, 10);
    expect(Math.abs(s.player.x - x0)).toBeGreaterThan(3); // knocked back
    expect(e).toBeTruthy();
  });

  it('the beast telegraphs: its wind-up lasts the configured time before the lunge', () => {
    const { s, e } = beastAboutToLunge();
    let steps = 0;
    while (e.state === 'windup' && steps < 200) {
      stepGame(s, none);
      steps++;
    }
    expect(e.state).toBe('attack');
    expect((steps + 1) * STEP_MS).toBeGreaterThanOrEqual(ENEMY_KINDS.beast.windupMs - STEP_MS);
  });

  it('the archer keeps its distance and shoots orbs', () => {
    const s = createGameState(arena([{ kind: 'archer', tx: 8, ty: 6 }]));
    run(s, none, 240);
    const a = s.enemies[0];
    expect(Math.abs(a.x - s.player.x)).toBeGreaterThan(ENEMY_KINDS.archer.keepMin - 8);
    expect(s.events.some((e) => e.type === 'enemyShoot')).toBe(true);
  });

  it('an enemy at 0 health goes down and is removed', () => {
    const s = createGameState(arena([{ kind: 'archer', tx: 6, ty: 6 }]));
    const a = s.enemies[0];
    a.hp = 4;
    dummy(a);
    faceRight(s);
    runDummy(s, (i) => ({ ...none, attack: i === 0 }), 20);
    expect(a.state).toBe('dead');
    run(s, none, 60);
    expect(s.enemies).toHaveLength(0);
  });

  it('at 0 health the player collapses, then gets up at the spawn point with enemies reset', () => {
    const { s } = beastAboutToLunge();
    s.player.hp = 1;
    let died = false;
    for (let i = 0; i < 120 && !died; i++) {
      stepGame(s, none);
      died = s.player.dead;
    }
    expect(died).toBe(true);
    s.enemies[0].hp = 1; // changed while dead...
    run(s, none, Math.ceil(DEATH_DELAY_MS / STEP_MS) + 2);
    expect(s.player.dead).toBe(false);
    expect(s.player.hp).toBe(PLAYER_MAX_HP);
    expect(s.player.x).toBe(s.player.spawnX);
    expect(s.enemies[0].hp).toBe(ENEMY_KINDS.beast.hp); // ...and reset on respawn
  });
});
