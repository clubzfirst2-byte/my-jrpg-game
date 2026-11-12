import { defineConfig } from 'vite';
import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { SEASON_PARTS, packGroup, releaseGroups, seasonPartOf } from './tools/release-art-pack.mjs';
import { precacheFiles, hasV2Pair, preloadReleaseGroup, preloadSwitchScript, releaseGroupOf } from './tools/precache.mjs';

const pkg = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf8'));

const version = `${pkg.version}-${(process.env.GITHUB_SHA || 'local').slice(0, 7)}`;

/**
 * P11.1: writes sw.js (the service worker) after the build, with the exact list of files to keep
 * for offline play. Its cache is named after the version, so a new release replaces the old files.
 * @returns {import('vite').Plugin}
 */
function serviceWorker() {
  return {
    name: 'service-worker',
    apply: 'build',
    generateBundle(_options, bundle) {
      // perf v1: files normal play never loads (prototype art, review / unused release art) are
      // left out; they still load from the network on demand (tools/precache.mjs).
      const files = precacheFiles(/** @type {any} */ (bundle));
      const source = readFileSync(new URL('./src/sw/sw-template.js', import.meta.url), 'utf8')
        .replace('__SW_VERSION__', JSON.stringify(version))
        .replace('__SW_FILES__', JSON.stringify(files));
      this.emitFile({ type: 'asset', fileName: 'sw.js', source });
    },
  };
}

/**
 * Release art packing (docs/perf/release-art-packing.md): `virtual:release-art` tells the game where
 * each src/art-release/<group> lives once built — one sheet PNG + one frame table JSON per group,
 * emitted straight into dist/assets (nothing generated is written into src/). In the dev server it
 * is `null` and the game loads the frame files one by one, as before.
 * @returns {import('vite').Plugin}
 */
function releaseArt() {
  const ID = 'virtual:release-art';
  const root = fileURLToPath(new URL('./src/art-release/', import.meta.url));
  // Graphics v2 (src/view/assets/artV2.js): src/art-release-v2/<group>, packed the same way, emitted as
  // release-v2-<group>.png / .json and named "v2/<group>" in the table.
  const rootV2 = fileURLToPath(new URL('./src/art-release-v2/', import.meta.url));
  // Graphics v3 (src/view/assets/artV3.js): src/art-release-v3/<group>, emitted as release-v3-<group>.png /
  // .json and named "v3/<group>" (loaded only with ?v3=1; not kept for offline play until it is the default).
  const rootV3 = fileURLToPath(new URL('./src/art-release-v3/', import.meta.url));
  let build = false;
  return {
    name: 'release-art',
    configResolved(config) {
      build = config.command === 'build';
    },
    resolveId(id) {
      return id === ID ? `\0${ID}` : undefined;
    },
    load(id) {
      if (id !== `\0${ID}`) return undefined;
      if (!build) return 'export default null;';
      // (graphics v3: a group's autumn and winter frames on sheets of their own, "v3/<group>.<season>":
      // building one season's bundle decodes only its sheet; release-art-pack.seasonPartOf)
      const v3Parts = (/** @type {string} */ group) =>
        SEASON_PARTS.map((part) => ({ dir: join(rootV3, group), name: `v3/${group}${part && `.${part}`}`, file: `v3-${group}${part && `.${part}`}`, keep: (/** @type {string} */ n) => seasonPartOf(n) === part })).filter((g) => readdirSync(g.dir).some((f) => f.endsWith('.png') && g.keep(f.slice(0, -4))));
      const all = [...releaseGroups(root).map((group) => ({ dir: join(root, group), name: group, file: group })), ...releaseGroups(rootV2).map((group) => ({ dir: join(rootV2, group), name: `v2/${group}`, file: `v2-${group}` })), ...releaseGroups(rootV3).flatMap(v3Parts)];
      const groups = all.map(({ dir, name, file, keep }) => {
        const { png, table, files } = packGroup(dir, keep);
        for (const f of files) this.addWatchFile(f);
        const sheet = this.emitFile({ type: 'asset', name: `release-${file}.png`, source: png });
        const frames = this.emitFile({ type: 'asset', name: `release-${file}.json`, source: JSON.stringify(table) });
        return `  ${JSON.stringify(name)}: { sheet: import.meta.ROLLUP_FILE_URL_${sheet}, table: import.meta.ROLLUP_FILE_URL_${frames} },`;
      });
      return `export default {\n${groups.join('\n')}\n};\n`;
    },
    // perf v1: the page starts fetching the sheets and frame tables of normal play (hero, npc,
    // enemy) as soon as the HTML arrives, alongside the game's JS, instead of after it has run. The
    // requests match the game's own (an <img> without crossorigin; fetch() same-origin), so the
    // browser reuses them.
    transformIndexHtml: {
      order: 'post',
      handler(_html, ctx) {
        if (!ctx.bundle) return undefined;
        const assets = Object.values(ctx.bundle).flatMap((out) => {
          if (out.type !== 'asset') return [];
          const group = (out.names ?? []).map(releaseGroupOf).find((g) => g !== null);
          return group ? [{ group, href: `./${out.fileName}`, png: out.fileName.endsWith('.png') }] : [];
        });
        const groups = new Set(assets.map((a) => a.group));
        // gfx W1: a group with a v2 counterpart (terrain) is preloaded by a script that reads the URL
        // (only the one drawn: an unused preload is a console warning); the others as before
        /** @type {Record<string, any>} */
        const pairs = {};
        for (const a of assets) {
          if (!hasV2Pair(a.group, groups)) continue;
          const g = a.group.replace(/^v2-/, '');
          const side = a.group.startsWith('v2-') ? 'v2' : 'v1';
          ((pairs[g] ??= {})[side] ??= {})[a.png ? 'png' : 'json'] = a.href;
        }
        const tags = assets
          .filter((a) => preloadReleaseGroup(a.group, groups))
          .map((a) => ({ tag: 'link', attrs: a.png ? { rel: 'preload', as: 'image', href: a.href } : { rel: 'preload', as: 'fetch', type: 'application/json', crossorigin: 'anonymous', href: a.href }, injectTo: /** @type {const} */ ('head') }));
        if (Object.keys(pairs).length) tags.push({ tag: 'script', children: preloadSwitchScript(pairs), injectTo: /** @type {const} */ ('head') });
        return tags;
      },
    },
  };
}

export default defineConfig({
  plugins: [releaseArt(), serviceWorker()],
  // Relative base so the build works both on GitHub Pages (/my-jrpg-game/) and locally.
  base: './',
  define: {
    __APP_VERSION__: JSON.stringify(pkg.version),
    __COMMIT__: JSON.stringify((process.env.GITHUB_SHA || 'local').slice(0, 7)),
  },
  server: { host: true },
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 1500,
    rollupOptions: {
      output: {
        // P11.4: PixiJS in one file, loaded together with the game (the page preloads it): its
        // renderer parts are imported on demand, which on a phone made a chain of round trips.
        manualChunks: (id) => (id.includes('node_modules/pixi.js') || id.includes('node_modules/@pixi') ? 'pixi' : undefined),
      },
    },
  },
  test: {
    include: ['tests/unit/**/*.test.js'],
    environment: 'node',
    // Many unit tests step the whole world for seconds of game time (1-4 s each alone). With E2E
    // and other suites running on the same machine they took past the 5 s default now and then:
    // a flaky failure, not a wrong result. 15 s keeps a real hang visible.
    testTimeout: 15_000,
  },
});
