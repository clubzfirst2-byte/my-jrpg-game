import { test, expect } from "@playwright/test";

// Uses the height verification map (default map). Tile coordinates refer to
// src/game/world/maps/heightTest.js.

async function open(page) {
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/?map=height");
  await expect(page.locator("body")).toHaveAttribute("data-ready", "true", {
    timeout: 20_000,
  });
  // Not a combat test: keep enemies from interfering (P3 added enemies to this map).
  await page.evaluate(() => window.__debugApi.clearEnemies());
  return errors;
}

const player = (page) => page.evaluate(() => window.__debugApi.player());
const teleport = (page, tx, ty) =>
  page.evaluate(([x, y]) => window.__debugApi.teleport(x, y), [tx, ty]);

/** Hold keys for a while (game time advances in real time). */
async function hold(page, keys, ms) {
  for (const k of keys) await page.keyboard.down(k);
  await page.waitForTimeout(ms);
  for (const k of keys) await page.keyboard.up(k);
}

test("Space jumps and the player lands back on the ground", async ({
  page,
}) => {
  const errors = await open(page);
  let maxZ = 0;
  await page.keyboard.down("Space");
  for (let i = 0; i < 12; i++) {
    maxZ = Math.max(maxZ, (await player(page)).z);
    await page.waitForTimeout(25);
  }
  await page.keyboard.up("Space");
  await page.waitForTimeout(600);
  expect(maxZ).toBeGreaterThan(8);
  const p = await player(page);
  expect(p.grounded).toBe(true);
  expect(p.z).toBe(0);
  expect(errors).toEqual([]);
});

test("a ruin wall blocks walking (and cannot be climbed)", async ({ page }) => {
  await open(page);
  await teleport(page, 33, 23); // just south of the ruin block (2 levels, ruin)
  await hold(page, ["ArrowUp"], 1000);
  const p = await player(page);
  expect(p.z).toBe(0);
  expect(p.climbing).toBe(false);
  expect(p.y).toBeCloseTo(23 * 16 + 6, 0); // stopped at the wall
});

test("a 1-level ledge can be jumped onto", async ({ page }) => {
  await open(page);
  await teleport(page, 14, 22); // just south of the floating plateau B (1 level = 16px)
  await page.keyboard.down("ArrowUp");
  await page.keyboard.down("Space");
  await page.waitForTimeout(700);
  await page.keyboard.up("Space");
  await page.keyboard.up("ArrowUp");
  await page.waitForTimeout(300);
  const p = await player(page);
  expect(p.grounded).toBe(true);
  expect(p.z).toBe(16);
  expect(p.y).toBeLessThan(22 * 16);
});

test("walking up a ramp reaches the plateau", async ({ page }) => {
  await open(page);
  await teleport(page, 7, 24); // on the path south of plateau A's ramp
  // Walk until on top (real time is not game time when a slow CI runner drops frames).
  await page.keyboard.down("ArrowUp");
  await expect
    .poll(async () => (await player(page)).z, { timeout: 10_000 })
    .toBe(16);
  await page.keyboard.up("ArrowUp");
  const p = await player(page);
  expect(p.z).toBe(16);
  expect(p.grounded).toBe(true);
});

test("jumping off the 4-level tower costs half a heart", async ({
  page,
}, testInfo) => {
  await open(page);
  await teleport(page, 27, 5); // east edge of the tower top (4 levels = 64px)
  expect((await player(page)).z).toBe(64);
  await expect(page.locator("#hud-hearts")).toHaveAttribute("data-hp", "12");
  await page.keyboard.down("ArrowRight");
  await expect
    .poll(
      async () => {
        const q = await player(page);
        return q.grounded && q.z === 0;
      },
      { timeout: 10_000 },
    )
    .toBe(true);
  await page.keyboard.up("ArrowRight");
  const p = await player(page);
  expect(p.z).toBe(0);
  expect(p.hp).toBe(10);
  await expect(page.locator("#hud-hearts")).toHaveAttribute("data-hp", "10");
  await page.screenshot({ path: testInfo.outputPath("after-fall.png") });
});

test("a silhouette shows the player hidden behind the tower", async ({
  page,
}, testInfo) => {
  await open(page);
  await teleport(page, 24, 3); // ground just north of the tower
  await page.waitForTimeout(200);
  expect(await page.evaluate(() => window.__debugApi.occluded())).toBe(true);
  await page.screenshot({ path: testInfo.outputPath("behind-tower.png") });

  await teleport(page, 24, 5); // on top of the tower: fully visible
  await page.waitForTimeout(200);
  expect(await page.evaluate(() => window.__debugApi.occluded())).toBe(false);

  await teleport(page, 24, 22); // in front (south) of the tower
  await page.waitForTimeout(200);
  expect(await page.evaluate(() => window.__debugApi.occluded())).toBe(false);
});

test("the touch jump button jumps", async ({ page }) => {
  await open(page);
  const btn = page.locator("#jump-button");
  await expect(btn).toBeVisible();
  await btn.dispatchEvent("pointerdown", { pointerId: 7 });
  let maxZ = 0;
  for (let i = 0; i < 10; i++) {
    maxZ = Math.max(maxZ, (await player(page)).z);
    await page.waitForTimeout(25);
  }
  await btn.dispatchEvent("pointerup", { pointerId: 7 });
  expect(maxZ).toBeGreaterThan(4);
});

test("the flat test field is still available with ?map=field", async ({
  page,
}) => {
  await page.goto("/?map=field");
  await expect(page.locator("body")).toHaveAttribute("data-ready", "true", {
    timeout: 20_000,
  });
  const p = await player(page);
  expect(p.z).toBe(0);
  expect(p.x).toBe(5 * 16 + 8);
});
