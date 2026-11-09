import { defineConfig } from 'vite';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';
import { packGroup, releaseGroups } from './tools/release-art-pack.mjs';

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
      const files = ['./', 'index.html', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png', 'icons/icon-maskable-512.png', 'icons/apple-touch-icon.png', ...Object.keys(bundle).filter((f) => !f.endsWith('.map'))];
      const source = readFileSync(new URL('./src/sw/sw-template.js', import.meta.url), 'utf8')
        .replace('__SW_VERSION__', JSON.stringify(version))
        .replace('__SW_FILES__', JSON.stringify([...new Set(files)]));
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
      const groups = releaseGroups(root).map((group) => {
        const { png, table, files } = packGroup(join(root, group));
        for (const f of files) this.addWatchFile(f);
        const sheet = this.emitFile({ type: 'asset', name: `release-${group}.png`, source: png });
        const frames = this.emitFile({ type: 'asset', name: `release-${group}.json`, source: JSON.stringify(table) });
        return `  ${JSON.stringify(group)}: { sheet: import.meta.ROLLUP_FILE_URL_${sheet}, table: import.meta.ROLLUP_FILE_URL_${frames} },`;
      });
      return `export default {\n${groups.join('\n')}\n};\n`;
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
  },
});
