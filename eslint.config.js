import js from '@eslint/js';
import globals from 'globals';

export default [
  { ignores: ['dist/', 'node_modules/', 'test-results/', 'playwright-report/', 'reports/'] },
  js.configs.recommended,
  {
    files: ['**/*.js', '**/*.mjs'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: { ...globals.browser, __APP_VERSION__: 'readonly', __COMMIT__: 'readonly' },
    },
    rules: {
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  },
  {
    // P11.1: the service worker template (vite.config.js fills in the version and the file list).
    files: ['src/sw/**/*.js'],
    languageOptions: { sourceType: 'script', globals: { ...globals.serviceworker, __SW_VERSION__: 'readonly', __SW_FILES__: 'readonly' } },
  },
  {
    files: ['*.config.js', 'tools/**/*.mjs', 'tests/**/*.js'],
    languageOptions: { globals: { ...globals.node } },
  },
  {
    // Logic layer: must stay pure JavaScript (no PixiJS, no DOM, no browser APIs).
    // See docs/DESIGN.md section 1.1.
    files: ['src/game/**/*.js'],
    languageOptions: { globals: {} },
    rules: {
      'no-restricted-imports': [
        'error',
        {
          paths: [{ name: 'pixi.js', message: 'src/game must not depend on the renderer (DESIGN.md 1.1).' }],
          patterns: [
            {
              group: ['**/view/**', '**/debug/**', '**/platform/**', '**/ui/**', '**/save/**'],
              message: 'src/game must not import browser-side layers (DESIGN.md 1.1).',
            },
          ],
        },
      ],
      'no-restricted-globals': [
        'error',
        'window',
        'document',
        'navigator',
        'localStorage',
        'indexedDB',
        'requestAnimationFrame',
      ],
    },
  },
];
