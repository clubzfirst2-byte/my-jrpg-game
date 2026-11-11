import { defineConfig, devices } from '@playwright/test';

const isCI = !!process.env.CI;
// E2E_PORT: another port, so that several worktrees can run their own preview side by side.
const PORT = Number(process.env.E2E_PORT) || 4173;

// iPhone-sized landscape viewport (the game is played in landscape).
const iphoneLandscape = {
  ...devices['iPhone 15 landscape'],
};

const projects = [
  {
    name: 'iphone-chromium',
    use: {
      ...iphoneLandscape,
      browserName: 'chromium',
      // Headless Chromium needs SwiftShader for WebGL on machines without a GPU.
      launchOptions: { args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'] },
    },
  },
];

// WebKit (the engine behind iPhone Safari) runs in CI where it is installed.
if (isCI || process.env.PW_WEBKIT) {
  projects.push({ name: 'iphone-webkit', use: { ...iphoneLandscape, browserName: 'webkit' } });
}

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 60_000,
  retries: isCI ? 1 : 0,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'reports/e2e.json' }],
  ],
  use: {
    baseURL: `http://localhost:${PORT}`,
    screenshot: 'on',
    trace: 'retain-on-failure',
  },
  projects,
  webServer: {
    command: `npx vite preview --port ${PORT} --strictPort`,
    port: PORT,
    reuseExistingServer: !isCI,
  },
});
