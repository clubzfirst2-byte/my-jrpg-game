// @ts-check
// Boot: wires platform (input, lifecycle, settings), logic (fixed-step game state),
// view (PixiJS) and the measurement overlay. main.js only connects layers.
import './styles.css';
import { UPDATE_PRIORITY } from 'pixi.js';
import { ErrorLog, installGlobalHandlers } from './debug/errorLog.js';
import { FrameStats } from './debug/frameStats.js';
import { installDrawCounter } from './debug/drawCounter.js';
import { collectDeviceInfo } from './debug/deviceInfo.js';
import { buildReport } from './debug/report.js';
import { createOverlay } from './debug/overlay.js';
import { createRenderer, resizeRenderer } from './view/renderer.js';
import { RESOLUTION_CANDIDATES, DEFAULT_TARGET_HEIGHT, nextCandidate } from './view/resolution.js';
import { AssetManager } from './view/assets/assetManager.js';
import { tableForArt, useEnemyFrameTable } from './view/enemyFrames.js';
import { buildPlaceholderPack, buildRegionPack, REGION_ENTRIES, placeholderEntries, releaseHeroEntries, releaseNpcEntries, releaseEnemyEntries, SOURCE_BUNDLE, sourceEntries } from './view/assets/placeholderPack.js';
import { finalBossDebugApi, finalBossToast } from './debug/finalBossDebug.js';
import { storyDebugApi } from './debug/storyDebug.js';
import { startOpening, skipOpening, finishEnding, endingLine, ENDING } from './game/story/story.js';
import { EndingScreen } from './ui/ending.js';
import { ART_OVERRIDES } from './view/assets/artOverrides.js';
import { ART_SCALE } from './view/assets/placeholderPack.js';
import { testHeroFrames } from './debug/testHero.js';
import { createNpcs, NPC_BODY, npcSolid } from './game/npc/npcs.js';
import { availableV1Groups, availableV2Groups, prototypeFrames, releaseFrames, requestedProtoGroups } from './view/assets/heroPrototype.js';
import { resolveArtGroups, v2Name } from './view/assets/artV2.js';
import { hurryUiArt, installUiSkin, loadOtherUiArt, loadTitleArt, showButtonLabels } from './ui/uiSkin.js';
import { GROUND_RUIN_BUNDLE, ISLAND_EDGES_BUNDLE, ISLAND_STEPS_BUNDLE, TERRAIN_GROUP, releaseTerrainEntries, v2BundleParts, terrainDebugApi, wantsTerrainArt } from './view/assets/terrainArt.js';
import { objectsReleaseGroups, installItemIcons, objectsDebugApi } from './view/assets/objectsArt.js';
import { GameView } from './view/gameView.js';
import { fxVersion } from './view/fxSwitch.js';
import { atlasStats } from './view/pixelAtlas.js';
import { Bench } from './view/bench.js';
import { InputManager } from './platform/inputManager.js';
import { installLifecycle } from './platform/lifecycle.js';
import { countSession, loadSettings, peekSessions, saveSettings } from './platform/settings.js';
import { PauseOverlay } from './ui/pauseOverlay.js';
import { BUTTON_LABELS_ROW, SETTING_ROWS, SettingsMenu } from './ui/settingsMenu.js';
import { HeartsHud } from './ui/hud.js';
import { RotateHint } from './ui/rotateHint.js';
import { TitleScreen } from './ui/title.js';
import { StartLoading } from './ui/startLoading.js';
import { InventoryMenu } from './ui/inventoryMenu.js';
import { DialogueBox } from './ui/dialogueBox.js';
import { ShopMenu } from './ui/shopMenu.js';
import { startDialogue, dialogueView, advance, questDef } from './game/npc/talk.js';
import { itemName } from './game/items/itemSystem.js';
import { equippedWeapon, itemDef, addItem } from './game/items/inventory.js';
import { ABILITY_NAMES, cycleAbility, grantAbility } from './game/puzzles/abilities.js';
import { Toast } from './ui/toast.js';
import { SaveStore } from './save/saveStore.js';
import { Autosave } from './save/autosave.js';
import { failureMessage } from './save/saveFormat.js';
import { FixedStepLoop } from './game/core/fixedStep.js';
import { createGameState, stepGame, spawnEnemies, respawnPlayer, MAPS } from './game/state.js';
import { applyProgress, areaAt } from './game/world/features.js';
import { markNewGame, noticeOnLoad, noticeOnCore } from './game/npc/storyNotices.js';
import { activeBoss } from './game/entities/bosses.js';
import { registerServiceWorker, loadTiming } from './platform/pwa.js';
import { AudioEngine } from './audio/audioEngine.js';
import { sfxFor, chooseTrack } from './audio/cues.js';
import { hitEnemy } from './game/combat/damage.js';
import { envSummary, ignite, material, setWorldTime } from './game/env/envSim.js';
import { playerWeather } from './game/env/weatherActions.js';
import { regionAt } from './game/world/world.js';
import { computeWorldDiff } from './game/world/worldDiff.js';
import { TOUR, TOUR_STOPS, tourReport } from './debug/tour.js';
import { clockText, CLOCK, SEASON, seasonAt, inSeason, hourOf } from './game/env/weather.js';
import { groundHeightUnder } from './game/physics/collision.js';
import { GAME_TITLE, PHASE } from './game/version.js';

const errorLog = new ErrorLog();
installGlobalHandlers(errorLog, window);

const params = new URLSearchParams(window.location.search);
/** @param {string} key @param {number} fallback */
const intParam = (key, fallback) => {
  const v = Number.parseInt(params.get(key) ?? '', 10);
  return Number.isFinite(v) && v >= 0 ? v : fallback;
};

/** @param {string} message */
function showFatal(message) {
  const box = document.getElementById('fatal');
  if (!box) return;
  box.hidden = false;
  box.textContent = message;
}

/** @param {import('pixi.js').Container} node */
function countDisplayObjects(node) {
  let n = 1;
  for (const child of node.children) n += countDisplayObjects(child);
  return n;
}

/**
 * gfx v2 integration (start-up): the deep-water map of a map definition, from a worker (deepWorker.js);
 * null when no worker can do it (the view then works it out itself).
 * @param {any} def @returns {Promise<Uint8Array | null>}
 */
function deepMapInWorker(def) {
  return new Promise((resolve) => {
    try {
      const w = new Worker(new URL('./view/deepWorker.js', import.meta.url), { type: 'module' });
      const done = (/** @type {Uint8Array | null} */ v) => {
        w.terminate();
        resolve(v);
      };
      w.onmessage = (e) => done(e.data instanceof Uint8Array ? e.data : null);
      w.onerror = () => done(null);
      w.postMessage(Array.isArray(def) ? { ground: def } : { ground: def.ground, height: def.height });
    } catch {
      resolve(null);
    }
  });
}

/** Resolves once the page has painted (a frame, then a task), or after 100 ms when no frame comes (a hidden page). */
const afterPaint = () =>
  new Promise((resolve) => {
    const done = () => resolve(undefined);
    const t = setTimeout(done, 100);
    requestAnimationFrame(() =>
      setTimeout(() => {
        clearTimeout(t);
        done();
      }, 0),
    );
  });

async function boot() {
  performance.mark('boot');
  const host = /** @type {HTMLElement} */ (document.getElementById('app'));
  const uiRoot = /** @type {HTMLElement} */ (document.getElementById('ui'));
  document.title = GAME_TITLE;
  // v1.0: the measurement button and the build label are for development: shown with ?debug=
  // (1 opens the panel, 0 only shows the button) or in the dev server, not in normal play.
  const debugUi = params.has('debug') || import.meta.env.DEV;
  const label = document.getElementById('phase-label');
  if (label) {
    label.textContent = `${GAME_TITLE} ${PHASE} v${__APP_VERSION__} (${__COMMIT__})`;
    label.hidden = !debugUi;
  }

  const settings = loadSettings();
  const resParam = intParam('res', 0);
  let targetHeight = /** @type {readonly number[]} */ (RESOLUTION_CANDIDATES).includes(resParam)
    ? resParam
    : /** @type {readonly number[]} */ (RESOLUTION_CANDIDATES).includes(settings.resolution)
      ? settings.resolution
      : DEFAULT_TARGET_HEIGHT;

  // P11.5: which art, and how fine. The real art (src/art) has 2 pixels per game pixel, so with any
  // of it the canvas gets 2 pixels per game pixel too (the world keeps its size on screen).
  //   ?hd=0        the placeholder art only, as before the real art (for before/after comparison)
  //   ?hd=1        the fine canvas even without real art
  //   ?hero=test   a size-test hero (仮, 32×56) in place of the hero, to check the new standard
  const hdParam = params.get('hd');
  /** @type {Map<string, import('./view/assets/placeholderPack.js').ArtSource>} */
  const artOverrides = hdParam === '0' ? new Map() : new Map(ART_OVERRIDES);
  if (params.get('hero') === 'test' && hdParam !== '0') for (const [k, v] of testHeroFrames()) artOverrides.set(k, v);
  //   ?hero=proto / ?npc=proto / ?enemy=proto / ?proto=all   the P12 prototypes (仮素材) — shown
  //   only when asked, until approved
  const protoGroups = requestedProtoGroups(params);
  if (protoGroups.length && hdParam !== '0') for (const [k, v] of await prototypeFrames(protoGroups)) artOverrides.set(k, v);
  // The hero's release art (src/art-release/hero, adopted 2026-11-08) is the hero of normal play.
  //   ?hero=placeholder   the old 16×16 placeholder hero instead (comparison)
  //   ?hero=test / ?hero=proto / ?proto=all   the size-test hero / the P12 prototype instead (they replace the
  //                       placeholder frames, so the release art stays out of their way)
  //   ?hero=release       still accepted (the same as no ?hero)
  const heroParam = params.get('hero');
  const releaseHero = hdParam !== '0' && (heroParam === null || heroParam === 'release') && !protoGroups.includes('hero');
  /** Release art folders to load (all at once, below), in the order they override each other. @type {string[]} */
  const releaseGroups = releaseHero ? ['hero'] : [];
  //   the villagers' release art (NPC batch 1: elder, merchant, guard; the others keep the
  //   placeholder) goes with the hero's release art, which it is drawn to match (2 pixels per game
  //   pixel): in normal play like the hero, or alone with ?npc=release / ?hd=1. ?npc=placeholder leaves
  //   it out (before/after comparison), and so do ?hero=placeholder / ?hero=test and the prototype
  //   views (?…=proto)
  const npcParam = params.get('npc');
  //   ?npc=revision      batch 1 with the review's fixes (src/art-release/npc-revision/)
  //   ?npc=revision-b2   batch 2 with the review's fixes (src/art-release/npc-revision-b2/)
  //   (both: ?npc=revision,revision-b2) — each kept apart from the frames under review until approved
  const npcModes = new Set((npcParam ?? '').split(','));
  const revisions = ['revision', 'revision-b2'].filter((m) => npcModes.has(m));
  const releaseNpcs = releaseHero || npcModes.has('release') || revisions.length > 0 || hdParam === '1';
  if (releaseNpcs && hdParam !== '0' && !npcModes.has('placeholder') && !protoGroups.length) {
    releaseGroups.push('npc', ...revisions.map((m) => `npc-${m}`));
  }
  //   v1.0: the enemies' release art (src/art-release/enemy, when it is there) goes with the hero's
  //   release art in normal play, or alone with ?enemy=release; ?enemy=placeholder leaves it out, and
  //   so does ?enemy=proto / ?proto=all
  const enemyParam = params.get('enemy');
  if (hdParam !== '0' && enemyParam !== 'placeholder' && !protoGroups.includes('enemy') && (releaseHero || enemyParam === 'release')) releaseGroups.push('enemy');
  if (wantsTerrainArt(params, releaseHero)) releaseGroups.push(TERRAIN_GROUP); // v1.0: the terrain release art (?terrain=placeholder|release, terrainArt.js)
  //   v1.0: the objects' release art (buildings, chests, switches, icons, effects; objectsArt.js)
  releaseGroups.push(...objectsReleaseGroups(params, { releaseHero, protoGroups }));
  // Graphics v2: a group's v2 art (src/art-release-v2) in place of its v1 art when enabled (?v2=0, ?<group>=v1|v2; artV2.js)
  const artGroups = resolveArtGroups(releaseGroups, params, { available: availableV2Groups(), v1Groups: availableV1Groups() });
  // W4: the v2 UI art (v2/ui) is not world art: it goes to the DOM UI (uiSkin.js), not the sprite packs.
  const uiArtGroup = artGroups.find((g) => g === v2Name('ui'));
  // (one file per frame: put on at once, nothing cut out. The title's frames, preloaded by the page,
  // decode meanwhile and the title waits for them just before it is built; the other frames load once
  // the title is up. If anything fails, the v1 UI.)
  /** @type {Map<string, import('./view/assets/placeholderPack.js').ArtSource> | null} */
  let uiFrames = null;
  /** @type {Promise<void>} */
  let uiTitleArt = Promise.resolve();
  const uiSkinLoad = uiArtGroup
    ? releaseFrames(uiArtGroup)
        .then((f) => {
          if (!f.size) return false;
          installUiSkin(uiRoot, f);
          uiFrames = f;
          if (params.get('map') === null) uiTitleArt = loadTitleArt(f);
          return true;
        })
        .catch((err) => (console.warn(`art: v2 ui: ${String(err)}; using the v1 UI`), false))
    : Promise.resolve(false);
  // gfx v2 integration (start-up): the v2 ground's deep-water map is worked out in a worker from now on
  // (another thread: it does not hold the title back), ready by the time the view draws (deepWorker.js)
  const deepEarly = artGroups.includes(v2Name('terrain')) ? deepMapInWorker(MAPS[/** @type {keyof typeof MAPS} */ (params.get('map') ?? 'world')] ?? MAPS.world) : Promise.resolve(null);
  // gfx v2 integration (start-up): the title first. Without ?map= the page shows the title as soon as
  // its own art and the save are read, and only then prepares the world (the art sheets, the atlases,
  // the view, the HUD), which the title does not need (with the v2 art that work held the title back by
  // 1.5 s or more on a cold start). A start pressed before the world is ready, or before the start area
  // is drawn with all its art, waits behind a short loading note (StartLoading; beginPlay below).
  // ?map=... (tests, height/field test maps) skips the title and never touches the save.
  const mapParam = params.get('map');
  const withTitle = mapParam === null;
  const store = new SaveStore(__APP_VERSION__);
  /** @type {any} */
  let loaded = { status: 'empty' };
  let inTitle = withTitle;
  /** The game has started but its start area is not drawn yet: the world waits (beginPlay). */
  let holding = false;
  /** @type {TitleScreen | null} */
  let title = null;
  const startLoading = new StartLoading(uiRoot);
  /** Starts the game once the world is ready (set at the end of boot). @type {((fromSave: boolean) => void) | null} */
  let startWhenReady = null;
  /** A start pressed before that. @type {boolean | null} */
  let startAsked = null;
  const requestStart = (/** @type {boolean} */ fromSave) => {
    startLoading.show();
    if (startWhenReady) startWhenReady(fromSave);
    else startAsked = fromSave;
  };
  if (withTitle) {
    loaded = await store.load();
    performance.mark('save');
    const notes = {
      empty: '',
      ok: loaded.recovered ? '最新の保存データが壊れていたため、ひとつ前の保存から再開します。' : '',
      corrupt: '保存データが壊れていて読み込めませんでした。はじめから遊べます。',
      newer: 'この保存データは新しいバージョンで作られています。ページを再読み込みしてください（データは消しません）。',
      error: loaded.status === 'error' ? failureMessage(loaded.reason) : '',
    };
    await uiSkinLoad; // (the v2 UI's skin on, and its title frames asked for: uiTitleArt)
    await uiTitleArt; // W4: the v2 title's frames decoded (they load alongside everything above)
    performance.mark('titleArt');
    title = new TitleScreen(uiRoot, {
      title: GAME_TITLE,
      hasSave: loaded.status === 'ok',
      saveNote: notes[/** @type {keyof typeof notes} */ (loaded.status)] ?? '',
      onNew: () => requestStart(false),
      onContinue: () => requestStart(true),
    });
    performance.mark('title');
    await afterPaint(); // the title on screen before the world's work starts
  }
  // W4: the HUD's and menus' frames, now that the title is up — at once (gfx v2 integration: a start
  // pressed now waits for them, beginPlay; they are small and decode off the main thread)
  await uiSkinLoad; // (with ?map=, no title: the v2 UI's frames are listed by now)
  const uiOtherArt = uiFrames ? loadOtherUiArt(uiFrames) : Promise.resolve();
  hurryUiArt();
  // gfx v2 integration (start-up): the world's art sheets are fetched (and decoded, off the main thread)
  // from now on, while the title shows
  const worldArtLoad = Promise.all(artGroups.filter((g) => g !== uiArtGroup).map((g) => releaseFrames(g)));
  /** With the title up, a break between the world's steps, so a tap on the title is answered meanwhile (a task, not a frame: frames are slow while the world is prepared). */
  const breathe = () => (withTitle ? new Promise((resolve) => setTimeout(resolve, 0)) : Promise.resolve());
  for (const frames of await worldArtLoad) for (const [k, v] of frames) artOverrides.set(k, v);
  //   gfx W3: the enemies' frame counts and speeds come from their art's frames.json — the table of
  //   the enemy art that was just loaded (v1, or v2 from src/art-release-v2/enemy; enemyFrames.js)
  useEnemyFrameTable(tableForArt((k) => artOverrides.has(k)));
  await breathe();
  const uiV2 = await uiSkinLoad;
  // W4: plays so far, this one included. A play is counted when it starts (startGame: はじめから /
  // つづきから), not on each page load; the title shows what the next play will be. Without the title
  // (?map=…) the page load is the start. (The v1 UI stores nothing new.)
  let sessions = !uiV2 ? 1 : params.get('map') === null ? peekSessions() + 1 : countSession();
  installItemIcons(artOverrides); // the menus' item icons, from the same art
  const artDensity = hdParam === '0' ? 1 : hdParam === '1' || artOverrides.size > 0 ? ART_SCALE : 1;

  /** @type {import('pixi.js').Application} */
  let app;
  try {
    app = await createRenderer(host, targetHeight, artDensity);
    performance.mark('renderer');
    await breathe();
  } catch (err) {
    errorLog.add('error', err, performance.now());
    showFatal(
      'WebGL を初期化できませんでした。Safari を最新版に更新するか、ほかのアプリを閉じて再読み込みしてください。\n\n' +
        String(err instanceof Error ? err.message : err),
    );
    return;
  }
  const fpsCap = intParam('fps', 0);
  if (fpsCap > 0) app.ticker.maxFPS = fpsCap; // e.g. ?fps=30 to verify 30fps behaviour

  // --- assets / logic / view ---
  const assets = new AssetManager();
  // gfx W1: the v2 ground's island grounds and water (terrainArt.js "common:ground") go in the base atlas,
  // packed tallest first so that it stays 2048×1024 (no second atlas). Without the v2 ground: as before.
  const groundV2Entries = releaseTerrainEntries('common:ground', artOverrides);
  assets.register('placeholder', () =>
    buildPlaceholderPack([...placeholderEntries(), ...releaseHeroEntries(artOverrides), ...releaseNpcEntries(artOverrides), ...releaseEnemyEntries(artOverrides), ...releaseTerrainEntries('placeholder', artOverrides), ...groundV2Entries], artOverrides, {
      tallestFirst: groundV2Entries.length > 0,
    }),
  );
  // P8: each region's art is its own bundle, loaded by the view near the region.
  // gfx W1: with the v2 ground, a region's own ground is apart ("ground:<region>"), and so is each
  // seasonal ground's autumn /
  // winter art ("season:<season>:<ground>"): terrainArt.v2BundleParts. (REGION_ENTRIES holds the seasons too.)
  for (const name of Object.keys(REGION_ENTRIES)) {
    const parts = groundV2Entries.length > 0 ? v2BundleParts(name) : null;
    if (!parts) assets.register(name, () => buildRegionPack(name, artOverrides));
    else for (const [part, keep] of parts) assets.register(part, () => buildRegionPack(name, artOverrides, (e) => keep(e.key)));
  }
  // v1.0: the final boss's art (loaded by the view only near its arena).
  // gfx W1 round 3: the ruin floor's edges over water, loaded with the chunks where the ruin floor meets water
  // (rounds 7-8: and the island grounds' edge variants 2 / 3 and step pieces, loaded with the chunks that draw them)
  for (const name of [GROUND_RUIN_BUNDLE, ISLAND_EDGES_BUNDLE, ISLAND_STEPS_BUNDLE]) {
    const entries = releaseTerrainEntries(name, artOverrides);
    if (entries.length) assets.register(name, () => buildPlaceholderPack(entries, artOverrides));
  }
  assets.register(SOURCE_BUNDLE, () => buildPlaceholderPack(sourceEntries(), artOverrides));
  await assets.load('placeholder');
  performance.mark('art');
  await breathe();
  // Without ?map= the game starts at the title on the first island and saves its progress (above).
  // P8: a new game is the whole world (the island and the regions south of it).
  const mapName = /** @type {keyof typeof MAPS} */ (mapParam ?? 'world');
  const state = createGameState(MAPS[mapName] ?? MAPS.world);
  performance.mark('world');
  // gfx W5: light, shadow and effects — on, or the look before them with ?fx=v1 / ?v2=0 (fxSwitch.js)
  const view = new GameView(app, assets, state, { fx: fxVersion(params) });
  view.presetDeepWater(await deepEarly);
  // gfx v2 integration (start-up): behind the title, one chunk a frame (a tap on the title is answered
  // meanwhile); all at once from the start press on (beginPlay)
  if (withTitle) view.chunkBudget = 1;
  performance.mark('view');
  await breathe();
  // Test / check helpers: ?time=20 (hour) and ?weather=rain|storm|cloudy|clear.
  const timeParam = Number.parseFloat(params.get('time') ?? '');
  if (Number.isFinite(timeParam)) setWorldTime(state.env, timeParam * CLOCK.hourMs);
  // P10.2: ?season=spring|summer|autumn|winter (the first day of it, same hour).
  const seasonParam = params.get('season');
  if (seasonParam && SEASON.order.includes(/** @type {any} */ (seasonParam))) setWorldTime(state.env, inSeason(state.env.now, /** @type {any} */ (seasonParam)));
  const weatherParam = params.get('weather');
  if (weatherParam && ['clear', 'cloudy', 'rain', 'storm', 'snow'].includes(weatherParam)) state.env.weatherOverride = /** @type {any} */ (weatherParam);
  if (params.get('light') === '0') view.weather.enabled = false;
  if (params.get('chunks') === 'all') view.loadAll = true; // P8: draw the whole map at once (comparison)
  // The camera zooms by the art density, so a game pixel covers the same screen area either way.
  view.camera.setZoom(artDensity);
  const zoomParam = Number.parseFloat(params.get('zoom') ?? '');
  if (Number.isFinite(zoomParam)) view.camera.setZoom(zoomParam * artDensity); // e.g. ?zoom=2 (zoom is adjustable later)
  const loop = new FixedStepLoop();
  const input = new InputManager(uiRoot);
  const hud = new HeartsHud(uiRoot);
  const rotateHint = new RotateHint(uiRoot);
  const deathOverlay = document.createElement('div');
  deathOverlay.id = 'death-overlay';
  deathOverlay.textContent = '力尽きた…';
  deathOverlay.hidden = true;
  uiRoot.append(deathOverlay);
  const toast = new Toast(uiRoot);
  // P11.2: sound. iOS allows sound only after a touch: start it on the first one.
  const audio = new AudioEngine();
  audio.setVolumes({ bgm: settings.bgmVolume, sfx: settings.sfxVolume });
  const unlockAudio = () => audio.unlock();
  for (const type of ['pointerdown', 'touchend', 'keydown']) window.addEventListener(type, unlockAudio, { capture: true });
  const treasureHud = document.createElement('div');
  treasureHud.id = 'hud-treasure';
  treasureHud.hidden = true;
  uiRoot.append(treasureHud);
  let shownTreasures = '';
  const abilityButton = /** @type {HTMLButtonElement} */ (document.getElementById('ability-button'));
  abilityButton.hidden = true;
  const abilityNext = document.createElement('button');
  abilityNext.type = 'button';
  abilityNext.id = 'ability-next';
  abilityNext.textContent = '⇄';
  abilityNext.setAttribute('aria-label', '能力を切り替える');
  abilityNext.hidden = true;
  abilityNext.addEventListener('click', () => cycleAbility(state));
  uiRoot.append(abilityNext);
  treasureHud.hidden = false;
  const clockHud = document.createElement('div');
  clockHud.id = 'hud-clock';
  uiRoot.append(clockHud);
  let shownClock = '';
  // P10.4: the boss's name and health while a core of the murk is fighting.
  const bossBar = document.createElement('div');
  bossBar.id = 'boss-bar';
  bossBar.hidden = true;
  const bossName = document.createElement('div');
  bossName.className = 'boss-name';
  const bossTrack = document.createElement('div');
  bossTrack.className = 'boss-track';
  const bossFill = document.createElement('div');
  bossFill.className = 'boss-fill';
  bossTrack.append(bossFill);
  bossBar.append(bossName, bossTrack);
  uiRoot.append(bossBar);
  let shownBoss = '';
  const WEATHER_NAMES = { clear: '晴れ', cloudy: 'くもり', rain: '雨', storm: '雷雨', snow: '雪' };

  // --- save (DESIGN.md 2.6) ---
  const autosave = new Autosave(
    store,
    () => ({ ...state.progress, worldMs: Math.round(state.env.now), worldDiff: computeWorldDiff(state) }),
    (msg) => toast.show(msg, { kind: 'error', ms: 6000 }),
  );
  let inMenu = false;
  const menu = new InventoryMenu(uiRoot, {
    getState: () => state,
    onOpen: () => {
      inMenu = true;
      input.clear();
    },
    onClose: () => {
      inMenu = false;
      input.clear();
      loop.reset();
    },
    toast: (msg) => toast.show(msg),
    talk: () => {
      const n = state.nearbyNpc;
      if (n) startDialogue(state, n.dialogue, n.id);
      else if (state.nearby === 'sleep') startDialogue(state, 'bed'); // P10.1
    },
  });
  // P9: conversations and the shop (the game waits while either is open).
  /**
   * Moves the conversation on. When it ends, input is cleared right here, so the press that closed
   * it does not carry into the world, while keys pressed after it are kept.
   * @param {number} [choice]
   */
  const advanceTalk = (choice) => {
    advance(state, choice);
    if (!inTalk()) {
      input.clear();
      loop.reset();
      wasTalking = false;
    }
  };
  const dialogueBox = new DialogueBox(uiRoot, {
    next: () => advanceTalk(),
    choose: (i) => advanceTalk(i),
  });
  const shopMenu = new ShopMenu(uiRoot, {
    getState: () => state,
    onClose: () => {
      state.shop = null;
      input.clear();
      loop.reset();
    },
    toast: (msg) => toast.show(msg),
  });
  /** Talking or shopping: the world waits. */
  const inTalk = () => !!state.dialogue || !!state.shop;
  window.addEventListener('keydown', (e) => {
    if (state.dialogue && (e.code === 'KeyJ' || e.code === 'Enter' || e.code === 'Space')) {
      e.preventDefault();
      if (!dialogueView(state)?.choices) advanceTalk();
      return;
    }
    if ((e.code === 'KeyE' || e.code === 'Tab') && !inTitle && !paused && state.ending !== 'screen' && !state.opening) {
      e.preventDefault();
      if (menu.isOpen) menu.close();
      else menu.open(state.nearby === 'cook' || state.nearby === 'forge' ? state.nearby : undefined);
    } else if (e.code === 'Escape' && menu.isOpen) menu.close();
    else if (e.code === 'KeyR' && !inTitle && !menu.isOpen) cycleAbility(state);
  });
  // (the title is up already, and the HUD's frames are loading: above)
  /** @param {boolean} fromSave */
  function startGame(fromSave) {
    if (fromSave && loaded.status === 'ok') {
      applyProgress(state, loaded.data);
      respawnPlayer(state);
      if (loaded.recovered) toast.show('ひとつ前の保存から再開しました。', { ms: 4000 });
      // v1.0 (C8): a save from before the story whose player never met the princess.
      const notice = noticeOnLoad(state);
      if (notice) setTimeout(() => toast.show(notice, { ms: 5000 }), loaded.recovered ? 4000 : 600);
    } else {
      markNewGame(state);
      startOpening(state); // v1.0 (C9): a new game only
    }
    // Never overwrite a save written by a newer version of the game.
    autosave.enabled = loaded.status !== 'newer';
    void store.requestPersistence();
    inTitle = false;
    input.clear();
    loop.reset();
    view.snapCamera(state);
    if (uiV2) {
      sessions = countSession(); // W4: one more play (the labels of the first plays)
      applySettings();
    }
  }
  /**
   * gfx v2 integration: resolves once the start area is drawn with all its art — a frame drawn with no
   * chunk waiting for its art bundles (the chunks are built and drawn in the same frame) — and the HUD's
   * frames are in.
   * @returns {Promise<void>}
   */
  const worldDrawn = () =>
    Promise.all([
      uiOtherArt,
      new Promise((resolve) => {
        let frames = 0;
        const check = () => {
          const s = view.streamStats();
          frames = s.pending === 0 && s.chunks > 0 ? frames + 1 : 0;
          if (frames >= 1) resolve(undefined);
          else requestAnimationFrame(check);
        };
        requestAnimationFrame(check);
      }),
    ]).then(() => {});
  /**
   * gfx v2 integration: starts the game from the title; the loading note (shown on the press) stays,
   * and the world waits, until the start area is drawn with its art. @param {boolean} fromSave
   */
  const beginPlay = (fromSave) => {
    holding = true;
    performance.mark('beginPlay');
    view.chunkBudget = Infinity; // (the start was pressed: what is left is built at once)
    hurryUiArt(); // (and the HUD's frames are asked for at once, not when the page is idle)
    startGame(fromSave);
    void worldDrawn().then(() => {
      performance.mark('drawn');
      holding = false; // (keys held meanwhile are kept: startGame cleared the press that started it)
      loop.reset();
      startLoading.hide();
    });
  };
  // v1.0 (C9): a tap or a key skips the opening.
  // The tap that skips it goes no further (not to the attack button or the stick).
  const skipOpeningNow = (/** @type {Event} */ e) => {
    if (!state.opening || inTitle) return; // (also behind the loading note: the first tap skips it, as before the note)
    skipOpening(state);
    e.preventDefault();
    e.stopPropagation();
    input.clear();
  };
  window.addEventListener('pointerdown', skipOpeningNow, true);
  window.addEventListener('keydown', skipOpeningNow, true);
  // v1.0 (C10): the ending screen, then the village in the morning (story.js), saved.
  /** @type {EndingScreen | null} */
  let endingScreen = null;
  const showEnding = () => {
    endingScreen = new EndingScreen(uiRoot, {
      title: GAME_TITLE,
      line: endingLine(state),
      ms: ENDING.screenMs,
      onDone: () => {
        endingScreen = null;
        finishEnding(state);
        input.clear();
        loop.reset();
        view.snapCamera(state);
        void autosave.saveNow();
      },
    });
  };
  // Save when the app goes to the background (iOS may close it without further notice).
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') void autosave.saveNow();
  });
  window.addEventListener('pagehide', () => void autosave.saveNow());

  // Messages for things that happened in the game.
  // Each event is announced once. (Events can happen while the clock stands still — in a
  // conversation, P9 — so the tick alone cannot tell old from new.)
  /** @type {WeakSet<object>} */
  const announced = new WeakSet();
  for (const e of state.events) announced.add(e);
  function announceEvents() {
    for (const e of state.events) {
      if (announced.has(e)) continue;
      // v1.0 (C10): 「淀みの源」 is reported as her words end; its toast waits until the ending screen is over.
      if (e.type === 'questDone' && state.ending === 'screen') continue;
      announced.add(e);
      const ev = /** @type {any} */ (e);
      audio.play(sfxFor(ev)); // P11.2
      const sourceMsg = finalBossToast(ev); // v1.0: the final boss
      if (sourceMsg) toast.show(sourceMsg.text, { ms: sourceMsg.ms });
      if (ev.type === 'chest') {
        toast.show(
          ev.reward === 'heart'
            ? 'ハートの器を手に入れた！ 体力が増えた'
            : ev.reward === 'money'
              ? `${ev.money} 星貨を手に入れた！`
              : `${itemName(ev.item)}を手に入れた！`,
        );
      } else if (ev.type === 'pickup') {
        toast.show(`${itemName(ev.item)}${ev.count > 1 ? ` ×${ev.count}` : ''}を手に入れた`, { ms: 1500 });
      } else if (ev.type === 'full') {
        toast.show(`${itemName(ev.item)}：これ以上持てない`);
      } else if (ev.type === 'broke') {
        toast.show(`${ev.name}が壊れた！`);
      } else if (ev.type === 'noArrows') {
        toast.show('矢がない', { ms: 1200 });
      } else if (ev.type === 'noBow') {
        toast.show('弓を持っていない', { ms: 1200 });
      } else if (ev.type === 'ability') {
        toast.show(`星環の力「${ABILITY_NAMES[ev.id]}」を手に入れた！ ${settings.hand === 'left' ? '左' : '右'}の「能力」ボタンで使える`, { ms: 4000 }); // (W4: the hand the buttons are under)
      } else if (ev.type === 'noAbility') {
        toast.show('星環の力をまだ持っていない', { ms: 1200 });
      } else if (ev.type === 'noTarget') {
        toast.show(ev.id === 'vine' ? '前に水か穴がない' : '前に動かせる箱がない', { ms: 1200 });
      } else if (ev.type === 'questStart') {
        toast.show(`クエスト「${questDef(ev.id).name}」を受けた（持ち物の「クエスト」で確認）`, { ms: 3500 });
      } else if (ev.type === 'questDone') {
        toast.show(`クエスト「${questDef(ev.id).name}」達成！`, { ms: 3500 });
      } else if (ev.type === 'season') {
        toast.show(`${SEASON.names[/** @type {string} */ (ev.id)]}になった`, { ms: 3000 });
      } else if (ev.type === 'bossAwake') {
        toast.show('澱の核が目を覚ました！', { ms: 2000 });
      } else if (ev.type === 'bossPhase') {
        toast.show('澱の核が怒り狂っている…！', { ms: 2000 });
      } else if (ev.type === 'bossDown') {
        toast.show(`${ev.name}を浄化した！（澱の核 ${ev.count}/4） 星のかけらを手に入れた`, { ms: 4500 });
        const notice = noticeOnCore(state); // v1.0 (C8): the fourth core, the princess not told yet
        if (notice) setTimeout(() => toast.show(notice, { ms: 5000 }), 4500);
      } else if (ev.type === 'warp') {
        // P10.1: stepping into a house shows its name.
        const room = areaAt(state, state.player.x, state.player.y);
        if (room?.home && room.name) toast.show(room.name, { ms: 1500 });
      } else if (ev.type === 'fell') {
        toast.show('穴に落ちた…', { ms: 1200 });
      } else if (ev.type === 'checkpoint') {
        toast.show('記録石に触れた — 倒れてもここから再開できる');
      } else if (ev.type === 'gateOpen') {
        toast.show('どこかで扉が開いた音がする…');
      } else if (ev.type === 'landmark') {
        const l = state.landmarks.find((x) => x.id === ev.id);
        if (l && !l.always) toast.show(`発見：${l.name}`);
      }
    }
  }

  const bench = new Bench(app);
  bench.setCount(intParam('bench', 0));

  // v1.0: back to the title from the pause screen: save, then start the page afresh (the title shows,
  // つづきから reads that save). A save that fails keeps the player here, with the message.
  async function backToTitle() {
    if (autosave.enabled && !(await autosave.saveNow())) {
      toast.show('保存できなかったため、タイトルへ戻るのをやめました。', { kind: 'error', ms: 4000 });
      return;
    }
    location.assign(location.pathname);
  }

  // --- pause / resume ---
  let paused = false;
  const pauseOverlay = new PauseOverlay(uiRoot, {
    onPauseRequest: () => pause(''),
    onResume: () => resume(),
    // P11.2: volumes step 0 -> 25 -> 50 -> 75 -> 100 % and round again; remembered.
    onVolume: (kind) => setVolume(kind, nextVolume(kind === 'bgm' ? settings.bgmVolume : settings.sfxVolume)),
    volumes: () => ({ bgm: settings.bgmVolume, sfx: settings.sfxVolume }),
    onSettings: () => settingsMenu.open(),
    // v1.0: 「タイトルへ」 — saved first; with no title (?map= test maps) there is none.
    onTitle: withTitle ? () => void backToTitle() : undefined,
    version: `v${__APP_VERSION__}`,
  });
  // P11.3: the settings screen; every choice applies at once and is remembered.
  const settingsMenu = new SettingsMenu(uiRoot, {
    get: () => settings,
    set: (key, value) => {
      /** @type {any} */ (settings)[key] = value;
      saveSettings(settings);
      applySettings();
    },
    onClose: () => pauseOverlay.refresh(),
  }, uiV2 ? [...SETTING_ROWS, BUTTON_LABELS_ROW] : SETTING_ROWS);
  function applySettings() {
    // W4: the round buttons' text labels (v2 UI): the first few sessions, always, or never.
    uiRoot.classList.toggle('ui-labels', uiV2 && showButtonLabels(settings.buttonLabels, sessions));
    uiRoot.classList.toggle('text-large', settings.textSize === 'large');
    uiRoot.classList.toggle('btn-small', settings.buttonSize === 'small');
    uiRoot.classList.toggle('btn-large', settings.buttonSize === 'large');
    uiRoot.classList.toggle('left-handed', settings.hand === 'left');
    input.touch.leftHanded = settings.hand === 'left';
    audio.setVolumes({ bgm: settings.bgmVolume, sfx: settings.sfxVolume });
    pauseOverlay.refresh();
  }
  applySettings();
  /** @param {number} v */
  const nextVolume = (v) => (Math.round(v * 4) + 1) % 5 / 4;
  /** @param {'bgm' | 'sfx'} kind @param {number} v */
  function setVolume(kind, v) {
    if (kind === 'bgm') settings.bgmVolume = v;
    else settings.sfxVolume = v;
    saveSettings(settings);
    audio.setVolumes({ bgm: settings.bgmVolume, sfx: settings.sfxVolume });
    pauseOverlay.refresh();
  }
  /** @param {string} message */
  function pause(message) {
    paused = true;
    audio.suspend();
    input.clear();
    pauseOverlay.show(message);
  }
  function resume() {
    paused = false;
    audio.resume();
    loop.reset(); // never "catch up" on time spent paused
    stats.reset();
    skipNextFrame = true;
    pauseOverlay.hide();
  }

  // Non-integer canvas scale (HD art, odd device scale): scroll in whole game px so every step is
  // the same number of device pixels (docs/perf/hd-view-size.md).
  const applyResolution = () => {
    const res = resizeRenderer(app, targetHeight, artDensity);
    view.camera.snapStep = Number.isInteger(res.canvasScale) ? 0 : 1;
    return res;
  };
  let resolution = applyResolution();
  installLifecycle(app.canvas, {
    onPause: () => {
      // (under the ending screen nothing is paused: it is only a screen with a timer; v1.0)
      if (!paused && state.ending !== 'screen') pause('');
      void autosave.saveNow();
    },
    onContextLost: () => pause('描画が一時的に中断されました。戻らない場合は再読み込みしてください。'),
    onContextRestored: () => pauseOverlay.show('描画が復帰しました。'),
    onViewportChange: () => {
      resolution = applyResolution();
    },
  });

  // --- measurement ---
  const renderer = /** @type {any} */ (app.renderer);
  const gl = renderer.gl ?? null;
  const drawCounter = installDrawCounter(gl);
  const stats = new FrameStats(240);
  const reportSec = intParam('reportSec', 30) || 30;
  let frameStart = performance.now();
  let lastCpu = 0;
  let lastDraws = 0;
  const originalRender = renderer.render.bind(renderer);
  renderer.render = (/** @type {any[]} */ ...args) => {
    const result = originalRender(...args);
    lastCpu = performance.now() - frameStart;
    return result;
  };

  /** @type {null | { endAt: number, intervals: number[], cpu: number[], draws: number[], errorsAtStart: number }} */
  let recording = null;
  let lastReport = '';
  // Pixi leaves empty (null) slots for freed textures: count only the live ones.
  const textureCount = () => (renderer.texture?.managedTextures ?? []).filter(Boolean).length;
  let skipNextFrame = true;

  const overlay = createOverlay(
    uiRoot,
    errorLog,
    {
      onScaleSprites(factor) {
        const next = factor === 0 ? 0 : bench.count === 0 ? 100 : bench.count * factor;
        bench.setCount(next);
      },
      onStartReport() {
        if (recording) return;
        stats.reset();
        recording = { endAt: performance.now() + reportSec * 1000, intervals: [], cpu: [], draws: [], errorsAtStart: errorLog.total };
      },
      onToggleTour() {
        if (tour) {
          finishTour();
          return false;
        }
        startTour(intParam('tour', 60) || 60);
        return true;
      },
      onCycleResolution() {
        targetHeight = nextCandidate(targetHeight);
        settings.resolution = targetHeight;
        saveSettings(settings);
        resolution = applyResolution();
        stats.reset();
        return targetHeight;
      },
    },
    { open: params.get('debug') === '1', reportSec, resolution: targetHeight, showToggle: debugUi },
  );

  // --- P8: 自動巡回 (long-play measurement) ---
  /** @type {null | { minutes: number, startMs: number, nextStopMs: number, nextSampleMs: number, stop: number, samples: import('./debug/tour.js').TourSample[] }} */
  let tour = null;
  /** @param {number} minutes */
  function startTour(minutes) {
    const now = performance.now();
    stats.reset();
    tour = { minutes, startMs: now, nextStopMs: now, nextSampleMs: now + TOUR.sampleSec * 1000, stop: 0, samples: [] };
    state.enemySpawns = []; // nothing attacks the tourist
    state.enemies = [];
  }
  function sampleTour(/** @type {number} */ now) {
    if (!tour) return;
    const s = stats.summary();
    const mem = /** @type {any} */ (performance).memory;
    tour.samples.push({
      tSec: (now - tour.startMs) / 1000,
      fps: s.fps,
      p95Ms: s.p95Ms,
      textures: textureCount(),
      displayObjects: countDisplayObjects(app.stage),
      chunks: view.chunks.size,
      bundles: assets.stats().bundles,
      heapMb: mem ? mem.usedJSHeapSize / 1048576 : null,
    });
  }
  function finishTour() {
    if (!tour) return;
    sampleTour(performance.now());
    lastReport = tourReport(tour.samples, {
      minutes: Math.round((performance.now() - tour.startMs) / 60000),
      version: `${__APP_VERSION__} (${__COMMIT__})`,
      device: collectDeviceInfo(gl, app.renderer.name),
    });
    tourResult = tour.samples;
    tour = null;
    overlay.showReport(lastReport);
  }
  /** @type {import('./debug/tour.js').TourSample[] | null} */
  let tourResult = null;
  function stepTour(/** @type {number} */ now) {
    if (!tour || paused || inMenu || inTitle) return;
    if (now >= tour.nextStopMs) {
      const [tx, ty] = TOUR_STOPS[tour.stop % TOUR_STOPS.length];
      tour.stop++;
      api.teleport(tx, ty);
      tour.nextStopMs = now + TOUR.stopSec * 1000;
    }
    if (now >= tour.nextSampleMs) {
      sampleTour(now);
      tour.nextSampleMs = now + TOUR.sampleSec * 1000;
    }
    if (now - tour.startMs >= tour.minutes * 60_000) finishTour();
  }

  function finishRecording() {
    if (!recording) return;
    const r = recording;
    recording = null;
    overlay.setRecording(null);
    lastReport = buildReport({
      version: __APP_VERSION__,
      commit: __COMMIT__,
      dateIso: new Date().toISOString(),
      durationSec: reportSec,
      intervals: r.intervals,
      cpu: r.cpu,
      drawCalls: r.draws,
      sprites: bench.count,
      textures: textureCount(),
      errors: errorLog.total - r.errorsAtStart,
      load: timing,
      device: {
        内部解像度: `${resolution.width}×${resolution.height}（目標 ${targetHeight}、×${resolution.canvasScale}、見える高さ ${resolution.gameHeight}）`,
        ...collectDeviceInfo(gl, app.renderer.name),
      },
    });
    overlay.showReport(lastReport);
  }

  /** Test helper: a fixed clock for purely visual animation (water, flames, bobbing items). @type {number | null} */
  let visualTime = null;
  let objectCount = 0;
  let lastObjectCount = 0;
  let lastOverlay = 0;

  // HIGH priority: runs first each frame and records the previous frame's numbers.
  app.ticker.add(
    (ticker) => {
      const now = performance.now();
      lastDraws = drawCounter.take();
      if (skipNextFrame || paused) {
        skipNextFrame = false;
      } else {
        stats.push(ticker.elapsedMS, lastCpu);
        if (recording) {
          recording.intervals.push(ticker.elapsedMS);
          recording.cpu.push(lastCpu);
          recording.draws.push(lastDraws);
          if (now >= recording.endAt) finishRecording();
          else overlay.setRecording(Math.ceil((recording.endAt - now) / 1000));
        }
      }
      frameStart = now;
      stepTour(now);

      if (now - lastObjectCount > 500) {
        objectCount = countDisplayObjects(app.stage);
        lastObjectCount = now;
      }
      if (now - lastOverlay > 250) {
        lastOverlay = now;
        const s = stats.summary();
        const p = state.player;
        overlay.setStats(
          [
            `FPS ${s.fps.toFixed(1)}   30fps未満 ${s.over33Pct.toFixed(1)}%`,
            `フレーム 平均${s.avgMs.toFixed(1)} / 遅い5% ${s.p95Ms.toFixed(1)} / 最大${s.maxMs.toFixed(1)} ms`,
            `JS ${s.avgCpuMs.toFixed(2)}ms   描画 ${lastDraws}回${drawCounter.supported ? '' : '(未対応)'}`,
            `表示物 ${objectCount}   テクスチャ ${textureCount()}   負荷 ${bench.count}`,
            `内部 ${resolution.width}×${resolution.height} ×${resolution.canvasScale} 見える高さ${resolution.gameHeight}  DPR ${window.devicePixelRatio}`,
            `位置 ${p.x.toFixed(0)},${p.y.toFixed(0)} 高さ ${p.z.toFixed(0)}（地面 ${p.groundZ.toFixed(0)}）${p.grounded ? '' : ' 空中'}`,
            `体力 ${p.hp}/${p.maxHp}  スタミナ ${p.stamina.toFixed(0)}${p.exhausted ? '（疲労）' : ''}${p.climbing ? ' 登攀中' : ''}${p.gliding ? ' 滑空中' : ''}${p.swimming ? ' 水泳中' : ''}`,
            `${p.facing}${p.dashing ? ' ダッシュ' : ''}  エラー ${errorLog.total}`,
            (() => {
              const e = envSummary(state.env);
              return `環境 燃焼${e.burning} 計算${e.lastTickCells}/最大${e.maxTickCells} 灰${e.ash} 凍結${state.env.rw * state.env.rh - e.awakeRegions}${e.jobs ? ` 早送り中${e.jobs}` : ''}\nチャンク ${view.chunks.size}（作成${view.chunkStats.built}/解放${view.chunkStats.freed}） 素材の束 ${assets.stats().bundles}\nライト ${view.weather.lightOn ? `${view.weather.lightMs.toFixed(2)}ms` : 'なし'}  ${shownClock}`;
            })(),
          ].join('\n'),
        );
      }
    },
    undefined,
    UPDATE_PRIORITY.HIGH,
  );

  // NORMAL priority: fixed-step logic, then draw the interpolated state.
  let alpha = 0;
  let wasTalking = false;
  const TAP_KEYS = /** @type {const} */ (['jump', 'attack', 'dodge', 'ability']);
  /** @type {Record<string, boolean>} */
  const heldTaps = {};
  app.ticker.add((ticker) => {
    if (!paused && !inTitle && !holding && !inMenu && !inTalk()) {
      const frameInput = input.sample();
      // A tap read on a frame where the logic runs no step must not be lost: keep it for the next
      // frame (the display can run slightly faster than the 60 Hz logic).
      for (const k of TAP_KEYS) if (heldTaps[k]) frameInput[k] = true;
      // Real elapsed time (PixiJS caps ticker.deltaMS at 100ms); the loop applies its own clamp
      // and accounts for any time it drops (DESIGN.md 1.3).
      state.difficulty = settings.difficulty; // P11.3
      const result = loop.advance(ticker.elapsedMS, () => stepGame(state, frameInput));
      alpha = result.alpha;
      for (const k of TAP_KEYS) heldTaps[k] = result.steps === 0 && !!frameInput[k];
    }
    if (state.ending === 'screen' && !endingScreen) showEnding();
    // P9: show the conversation / shop; when a talk ends, the world goes on with fresh input.
    dialogueBox.show(dialogueView(state));
    if (state.shop && !shopMenu.isOpen) shopMenu.open();
    if (wasTalking && !inTalk()) {
      input.clear();
      loop.reset();
    }
    wasTalking = inTalk();
    if (!paused && !inTitle && !holding && !inMenu && !inTalk()) {
      announceEvents();
      autosave.update(state, ticker.elapsedMS);
    }
    view.render(state, alpha, visualTime ?? performance.now() / 1000, ticker.elapsedMS / 1000);
    hud.update(state.player.hp, state.player.maxHp);
    const season = seasonAt(state.env.now);
    const clock = `${season.name} ${season.day}日目 ${clockText(state.env.now)} ${WEATHER_NAMES[playerWeather(state).kind]}`;
    if (clock !== shownClock) {
      shownClock = clock;
      clockHud.textContent = clock;
    }
    const boss = activeBoss(state);
    // P11.2: the music for where the player is.
    {
      const p = state.player;
      const tx = Math.floor(p.x / 16);
      const ty = Math.floor(p.y / 16);
      audio.setTrack(chooseTrack({ inTitle, boss: !!boss, area: areaAt(state, p.x, p.y), region: regionAt(state.regions, tx, ty)?.id ?? null, hour: hourOf(state.env.now) }));
    }
    const bossKey = boss ? `${boss.name}:${boss.hp}:${boss.phase}` : '';
    if (bossKey !== shownBoss) {
      shownBoss = bossKey;
      bossBar.hidden = !boss;
      uiRoot.classList.toggle('boss-fight', !!boss); // toasts move to the bottom (styles.css)
      if (boss) {
        bossName.textContent = boss.name;
        bossFill.style.width = `${(100 * boss.hp) / boss.maxHp}%`;
        bossBar.classList.toggle('phase2', boss.phase === 2);
      }
    }
    const inv = state.progress.inv;
    const w = equippedWeapon(inv);
    const gearText = `★${inv.money}  ${w ? `${itemDef(w.id).name}${w.lvl ? `+${w.lvl}` : ''} ${w.dur}` : '素手'}  矢${inv.items.arrow ?? 0}`;
    if (gearText !== shownTreasures) {
      shownTreasures = gearText;
      treasureHud.textContent = shownTreasures;
    }
    menu.setNearby(inTitle || inTalk() ? null : state.nearby, state.nearbyNpc?.name ?? '');
    // The ability button shows the selected 星環 power (hidden until the first one is learned).
    const abilityLabel = state.progress.ability ? ABILITY_NAMES[state.progress.ability] : '';
    if (abilityButton.textContent !== abilityLabel) {
      // W4 (R-8): a 3-character name (蔓結び) may break into 蔓 / 結び on the smallest v2 ring (styles.css);
      // each part is kept whole, and the v1 UI keeps it on one line (white-space: nowrap there).
      if (abilityLabel.length === 3) {
        const part = (/** @type {string} */ t) => Object.assign(document.createElement('span'), { textContent: t });
        abilityButton.replaceChildren(part(abilityLabel.slice(0, 1)), document.createElement('wbr'), part(abilityLabel.slice(1)));
      } else abilityButton.textContent = abilityLabel;
      if (abilityLabel) abilityButton.setAttribute('aria-label', abilityLabel); // W4: the v2 UI shows an icon
    }
    // W4 (v2 UI): the round buttons are hidden while the dialogue box is open (styles.css).
    const talking = !!state.dialogue;
    if (uiRoot.classList.contains('talking') !== talking) uiRoot.classList.toggle('talking', talking);
    // W4 (v2 UI, inspection W-4): the HUD is hidden under the full-screen panels (inventory / cooking,
    // shop, settings), so nothing shows through them or peeks out at their edges (styles.css).
    const panelOpen = menu.isOpen || shopMenu.isOpen || settingsMenu.isOpen;
    if (uiRoot.classList.contains('panel-open') !== panelOpen) uiRoot.classList.toggle('panel-open', panelOpen);
    const showAbility = !!state.progress.ability && !inTitle;
    if (abilityButton.hidden === showAbility) abilityButton.hidden = !showAbility;
    const showNext = showAbility && state.progress.abilities.length > 1;
    if (abilityNext.hidden === showNext) abilityNext.hidden = !showNext;
    deathOverlay.hidden = state.deathMs < 0;
    bench.update(ticker.elapsedMS / 1000);
  });

  // Read-only hook for automated E2E tests.
  const api = {
    summary: () => stats.summary(),
    /** Starts the frame statistics afresh (measuring one setting after another). */
    resetStats: () => stats.reset(),
    sprites: () => bench.count,
    setSprites: (/** @type {number} */ n) => bench.setCount(n),
    drawCalls: () => lastDraws,
    errors: () => errorLog.total,
    rendererName: () => app.renderer.name,
    lastReport: () => lastReport,
    player: () => {
      const p = state.player;
      return {
        x: p.x,
        y: p.y,
        z: p.z,
        groundZ: p.groundZ,
        grounded: p.grounded,
        hp: p.hp,
        facing: p.facing,
        dashing: p.dashing,
        climbing: p.climbing,
        gliding: p.gliding,
        swimming: p.swimming,
        dead: !!p.dead,
        action: p.action,
        guarding: !!p.guarding,
        invulnMs: p.invulnMs,
        stamina: p.stamina,
        exhausted: p.exhausted,
      };
    },
    occluded: () => view.playerOccluded,
    /** Test helper: place the player on tile (tx, ty), standing on the terrain. */
    teleport: (/** @type {number} */ tx, /** @type {number} */ ty) => {
      const p = state.player;
      const ts = state.map.tileSize;
      p.x = p.prevX = tx * ts + ts / 2;
      p.y = p.prevY = ty * ts + ts - 2;
      p.z = p.prevZ = p.groundZ = groundHeightUnder(p, state.map);
      p.vx = p.vy = p.vz = 0;
      p.grounded = true;
      p.climbing = false;
      view.snapCamera(state);
    },
    camera: () => {
      const c = view.camera;
      return { x: c.x, y: c.y, zoom: c.zoom, origin: c.origin(), viewWidth: c.viewWidth, viewHeight: c.viewHeight, bounds: c.bounds };
    },
    setZoom: (/** @type {number} */ z) => view.camera.setZoom(z),
    /** Test helper: remove all enemies (for tests that are not about combat). */
    clearEnemies: () => {
      state.enemySpawns = [];
      state.enemies = [];
      state.projectiles = [];
    },
    enemies: () => state.enemies.map((e) => ({ id: e.id, kind: e.kind, x: e.x, y: e.y, z: e.z, hp: e.hp, state: e.state })),
    projectiles: () => state.projectiles.map((pr) => ({ kind: pr.kind, owner: pr.owner, x: pr.x, y: pr.y })),
    flurry: () => state.flurryMs,
    /** Test helper: place an enemy next to the player. */
    spawnEnemy: (/** @type {import('./game/entities/enemies.js').EnemyKind} */ kind, /** @type {number} */ tx, /** @type {number} */ ty) => {
      state.enemySpawns.push({ kind, tx, ty });
      spawnEnemies(state);
    },
    /** Test helper: set health (quarter hearts). */
    setHp: (/** @type {number} */ v) => {
      state.player.hp = v;
    },
    deathMs: () => state.deathMs,
    /** v1.0: each enemy on screen: frame drawn, size in game px, wind-up overlay strength and colour. */
    enemyView: () => view.enemyDebug(state),
    /** gfx W5: switch an effect group off / on (measuring its cost): shadows, particles, hitfx, windows, rain. */
    fx: (/** @type {string} */ name, /** @type {boolean} */ on) => view.setFx(name, on),
    /** gfx W5: what the effects draw now (version, groups on, sprites showing). */
    fxInfo: () => view.fxDebug(),
    /** gfx v2 integ: the effects' shared mask sheet (pixelAtlas.js): frames, rows used, sheet size. */
    pixelAtlas: () => atlasStats(),
    /** gfx W5 (capturing a still): hold the hit effects where they are / let them go on. */
    fxHold: (/** @type {boolean} */ on) => {
      view.fxHold = on;
    },
    /** Recent game events (last 64): lets tests observe short actions without racing them. */
    events: () => state.events.map((e) => e.type),
    /** Test helper: set stamina (e.g. to check drowning without waiting). */
    setStamina: (/** @type {number} */ v) => {
      state.player.stamina = v;
    },
    rotateHintVisible: () => rotateHint.visible,
    titleVisible: () => !!title && title.visible,
    /** P11.2: sound (state, track, effects played) and volume. */
    audio: () => audio.stats(),
    settings: () => ({ ...settings }),
    setVolume: (/** @type {'bgm' | 'sfx'} */ kind, /** @type {number} */ v) => setVolume(kind, v),
    /** P10.6 test helper: where things are (checkpoints, chests, doorways). */
    places: () => ({
      checkpoints: state.checkpointDefs.map((/** @type {any} */ c) => ({ id: c.id, tx: c.tx, ty: c.ty })),
      chests: state.chests.map((/** @type {any} */ c) => ({ id: c.id, tx: c.tx, ty: c.ty })),
      warps: state.warps.map((/** @type {any} */ w) => ({ id: w.id, tx: w.tx, ty: w.ty, facing: w.facing })),
    }),
    /** P10.4 test helpers: the bosses, and a heavy blow to one. */
    bosses: () => state.enemies.filter((/** @type {any} */ e) => e.boss).map((/** @type {any} */ e) => ({ id: e.bossId, name: e.name, hp: e.hp, maxHp: e.maxHp, phase: e.phase, awake: e.awake, state: e.state, pattern: e.pattern, x: e.x, y: e.y, arena: e.arena })),
    hurtBoss: (/** @type {string} */ id, /** @type {number} */ damage) => {
      const e = state.enemies.find((/** @type {any} */ x) => x.boss && x.bossId === id);
      if (e) hitEnemy(state, e, { owner: 'player', id: `debug${state.tick}-${Math.random()}`, damage, from: { x: e.x, y: e.y + 20 }, kind: 'melee' });
    },
    progress: () => JSON.parse(JSON.stringify(state.progress)),
    /** P6: inventory, pickups and the menu. */
    inventory: () => JSON.parse(JSON.stringify(state.progress.inv)),
    pickups: () => state.pickups.map((p) => ({ key: p.key, item: p.item, count: p.count, tx: Math.floor(p.x / 16), ty: Math.floor(p.y / 16) })),
    nearby: () => state.nearby,
    /** P9: villagers and conversations. */
    npcs: () => state.npcs.map((n) => ({ id: n.id, name: n.name, tx: Math.floor(n.x / 16), ty: Math.floor(n.y / 16) })),
    /** NPC batch 1: the villagers' sprites (frame key, size, draw order) and their state. */
    npcSprites: () => view.npcs.debug(),
    npcState: () => state.npcs.map((n) => ({ id: n.id, facing: n.facing, moving: n.moving, x: n.x, y: n.y })),
    /** Test helper: an extra villager, for a look on screen only; it is not saved and the village
     *  data is unchanged (the woman and the smith are in the village since v1.0). */
    addNpc: (/** @type {string} */ id, /** @type {number} */ tx, /** @type {number} */ ty) => {
      state.npcs.push(...createNpcs(state.map, [{ id, name: id, dialogue: 'elder', look: 1, tx, ty }]));
    },
    dialogue: () => dialogueView(state),
    talkTo: (/** @type {string} */ id) => {
      const n = state.npcs.find((x) => x.id === id);
      if (n) startDialogue(state, n.dialogue, n.id);
    },
    shopOpen: () => state.shop,
    /** Test helper: stand just south of a villager, facing them. */
    standBy: (/** @type {string} */ id) => {
      const n = state.npcs.find((x) => x.id === id);
      if (!n) return;
      const p = state.player;
      p.x = p.prevX = n.x;
      // Right against its body, below; a ghost has no body (and some have a short reach, 18): the
      // old 14 px, always inside the talk reach.
      const gap = npcSolid(n) ? NPC_BODY.depth + NPC_BODY.front : 14;
      p.y = p.prevY = n.y + Math.min(gap, n.reach - 4);
      p.z = p.prevZ = p.groundZ = n.z;
      p.facing = 'up';
      p.aimX = 0;
      p.aimY = -1;
      view.snapCamera(state);
    },
    /** P8: streaming numbers (chunks, bundles, textures, display objects). */
    /** GPU textures by size (find leaks). */
    textureList: () => (renderer.texture?.managedTextures ?? []).filter(Boolean).map((/** @type {any} */ t) => `${t.label ?? ''}:${t.pixelWidth ?? t.width}x${t.pixelHeight ?? t.height}`),
    stream: () => ({ ...view.streamStats(), bundleNames: [...assets.loaded.keys()], textures: textureCount(), displayObjects: countDisplayObjects(app.stage), region: regionAt(state.regions, Math.floor(state.player.x / 16), Math.floor(state.player.y / 16))?.id ?? null }),
    /** P7: abilities and switches. */
    abilities: () => ({ owned: [...state.progress.abilities], selected: state.progress.ability, ready: (state.abilityReadyAt ?? 0) <= state.env.now }),
    grantAbility: (/** @type {string} */ id) => grantAbility(state, id),
    selectAbility: (/** @type {string} */ id) => {
      state.progress.ability = id;
    },
    switches: () => ({ ...state.switchActive }),
    gates: () => [...state.progress.gates],
    menuOpen: () => menu.isOpen,
    /** Test helper: put items into the bag. */
    give: (/** @type {string} */ id, /** @type {number} */ n = 1) => addItem(state.progress.inv, id, n),
    addMoney: (/** @type {number} */ n) => {
      state.progress.inv.money += n;
    },
    area: () => areaAt(state, state.player.x, state.player.y)?.id ?? null,
    /** Test helper: save immediately; resolves to whether it worked. */
    saveNow: () => autosave.saveNow(),
    saveInfo: () => ({ enabled: autosave.enabled, saves: autosave.saves, failures: autosave.failures, loaded: loaded.status }),
    toasts: () => [...toast.history],
    markers: () => view.features.visibleMarkers(),
    /** P4 environment: summary, and test helpers to set a tile alight / read a tile. */
    env: () => envSummary(state.env),
    envIgnite: (/** @type {number} */ tx, /** @type {number} */ ty) => ignite(state.env, state.map, ty * state.map.width + tx),
    envTile: (/** @type {number} */ tx, /** @type {number} */ ty) => {
      const i = ty * state.map.width + tx;
      return { material: material(state.env, state.map, i), burning: state.env.burning.has(i), solid: state.map.solid[i] === 1 };
    },
    /** P5: time of day and weather. */
    weather: () => ({ ...playerWeather(state), clock: clockText(state.env.now), lightOn: view.weather.lightOn, lightMs: view.weather.lightMs, rainVisible: view.weather.rain.visible, snowVisible: view.weather.snow.visible }),
    /** P10.2: jump to the first day of a season (same hour). */
    setSeason: (/** @type {any} */ id) => setWorldTime(state.env, inSeason(state.env.now, id)),
    season: () => ({ ...seasonAt(state.env.now), view: view.season }),
    setHour: (/** @type {number} */ h) => setWorldTime(state.env, Math.floor(state.env.now / CLOCK.dayMs) * CLOCK.dayMs + h * CLOCK.hourMs),
    setWeather: (/** @type {any} */ kind) => {
      state.env.weatherOverride = kind;
    },
    /** Test helper: a lightning strike on tile (tx, ty) after the usual warning. */
    forceStrike: (/** @type {number} */ tx, /** @type {number} */ ty) => {
      state.env.strike = { i: ty * state.map.width + tx, atMs: state.env.now + 900 };
    },
    strikePending: () => !!state.env.strike,
    envEvents: () => state.events.filter((e) => ['ignite', 'fireArrow', 'discharge', 'douse', 'gateOpen', 'burn', 'cut'].includes(e.type)).map((e) => e.type),
    /** Test helper: point the player in a direction without moving (for opening chests). */
    face: (/** @type {'up' | 'down' | 'left' | 'right'} */ dir) => {
      const v = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }[dir];
      state.player.facing = dir;
      state.player.aimX = v[0];
      state.player.aimY = v[1];
    },
    tick: () => state.tick,
    loop: () => ({ totalSteps: loop.totalSteps, droppedMs: loop.droppedMs, elapsedMs: loop.elapsedMs, pendingMs: loop.accumulator }),
    paused: () => paused,
    /** Test helpers: freeze / unfreeze the game deterministically (same as the pause button). */
    pause: () => pause(''),
    resume: () => resume(),
    /** Test helper: while paused, advance exactly `n` logic steps with the current input. */
    step: (/** @type {number} */ n = 1) => {
      for (let i = 0; i < n; i++) stepGame(state, input.sample());
    },
    resolution: () => ({ ...resolution, target: targetHeight }),
    /** The hero's current animation (action and frame) and the texture drawn. */
    heroPose: () => ({ ...view.heroPose, texture: view.heroKey }),
    /**
     * A sprite's art (tests: release / revision / prototype): its PNG URL, or for a frame on a
     * packed sheet (the build) the frame's pixels as a data URL, so two sets compare by content.
     */
    artUrl: (/** @type {string} */ key) => {
      const src = artOverrides.get(key);
      if (src === undefined || typeof src === 'string') return src ?? null;
      const c = document.createElement('canvas');
      c.width = src.w;
      c.height = src.h;
      /** @type {CanvasRenderingContext2D} */ (c.getContext('2d')).drawImage(src.sheet, src.x, src.y, src.w, src.h, 0, 0, src.w, src.h);
      return c.toDataURL();
    },
    /** P11.5: the art in use (density, how many real-art sprites) and the drawn hero's size in game px. */
    art: () => ({ density: artDensity, overrides: artOverrides.size, groups: artGroups, zoom: view.camera.zoom, hero: { w: view.player.texture.width, h: view.player.texture.height, k: view.heroK } }),
    /** P8: the auto tour (minutes may be fractional in tests). */
    startTour: (/** @type {number} */ minutes) => startTour(minutes),
    stopTour: () => finishTour(),
    tourRunning: () => !!tour,
    tourResult: () => tourResult,
    /** Test helper: freeze visual animation at a time (seconds), or null to follow the clock. */
    setVisualTime: (/** @type {number | null} */ t) => {
      visualTime = t;
    },
    assets: () => assets.stats(),
  };
  Object.assign(api, finalBossDebugApi(state, api.teleport)); // v1.0: the source (flags, arena, seats)
  Object.assign(api, storyDebugApi(state)); // v1.0: the opening and the ending
  Object.assign(api, terrainDebugApi(assets, view)); // v1.0: which terrain is drawn from the release art (v1.1: water edges)
  Object.assign(api, objectsDebugApi(state, view, assets)); // v1.0: the objects' art
  /** @type {any} */ (window).__debugApi = api;
  // ?tour=60 starts the auto tour right away (with ?map=..., which skips the title).
  if (params.get('tour') && !withTitle) startTour(Number.parseFloat(params.get('tour') ?? '') || 60);
  // P11.1: how long the start took, and offline play (the service worker).
  const timing = loadTiming(performance.now());
  api.loadTiming = () => timing;
  registerServiceWorker({ onUpdate: () => toast.show('新しい版を受け取りました。次に開いたときから新しくなります', { ms: 4000 }) });
  // gfx v2 integration: the world is ready; a start pressed on the title meanwhile goes on now
  startWhenReady = beginPlay;
  if (startAsked !== null) beginPlay(startAsked);
  performance.mark('ready');
  document.body.dataset.ready = 'true';
}

boot().catch((err) => {
  errorLog.add('error', err, performance.now());
  showFatal(`起動に失敗しました: ${String(err instanceof Error ? err.message : err)}`);
});
