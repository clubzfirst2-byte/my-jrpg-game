// Writes a Markdown test summary for the GitHub Actions job page (Job Summary).
// Usage: node tools/ci-summary.mjs [reports/unit.json] [reports/e2e.json]
import { readFileSync, appendFileSync, existsSync } from 'node:fs';

const [unitPath = 'reports/unit.json', e2ePath = 'reports/e2e.json'] = process.argv.slice(2);

function readJson(path) {
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch {
    return null;
  }
}

const lines = ['## テスト結果', '', '| 種類 | 成功 | 失敗 | スキップ | 判定 |', '|---|---|---|---|---|'];
const failures = [];

const unit = readJson(unitPath);
if (unit) {
  const ok = unit.numFailedTests === 0 && unit.numTotalTests > 0;
  lines.push(`| 単体テスト (Vitest) | ${unit.numPassedTests} | ${unit.numFailedTests} | ${unit.numPendingTests ?? 0} | ${ok ? '✅' : '❌'} |`);
  for (const file of unit.testResults ?? []) {
    for (const a of file.assertionResults ?? []) {
      if (a.status === 'failed') failures.push(`単体: ${a.fullName}`);
    }
  }
} else {
  lines.push('| 単体テスト (Vitest) | - | - | - | ⚠️ 結果なし |');
}

const e2e = readJson(e2ePath);
if (e2e) {
  const s = e2e.stats ?? {};
  const failed = (s.unexpected ?? 0);
  lines.push(`| E2E (Playwright) | ${(s.expected ?? 0) + (s.flaky ?? 0)} | ${failed} | ${s.skipped ?? 0} | ${failed === 0 ? '✅' : '❌'} |`);
  const walk = (suite, prefix) => {
    for (const spec of suite.specs ?? []) {
      for (const t of spec.tests ?? []) {
        if (t.status === 'unexpected') failures.push(`E2E [${t.projectName}]: ${prefix}${spec.title}`);
        if (t.status === 'flaky') failures.push(`E2E [${t.projectName}] (再試行で成功): ${prefix}${spec.title}`);
      }
    }
    for (const child of suite.suites ?? []) walk(child, prefix);
  };
  for (const suite of e2e.suites ?? []) walk(suite, '');
} else {
  lines.push('| E2E (Playwright) | - | - | - | ⚠️ 結果なし |');
}

if (failures.length) {
  lines.push('', '### 失敗・要確認', '', ...failures.map((f) => `- ${f}`));
}
lines.push('', 'スクリーンショットと詳細レポートは、このページ下部の Artifacts（`playwright-report`）からダウンロードできます。', '');

const md = lines.join('\n');
if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, md);
console.log(md);
