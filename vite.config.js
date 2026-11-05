import { defineConfig } from 'vite';
import { readFileSync } from 'node:fs';

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

export default defineConfig({
  plugins: [serviceWorker()],
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
  },
  test: {
    include: ['tests/unit/**/*.test.js'],
    environment: 'node',
  },
});
