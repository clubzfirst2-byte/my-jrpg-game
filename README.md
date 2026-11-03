# 星脈のワイルズ（仮）

ブラウザで遊べる 2D 見下ろし型オープンワールド・アクションアドベンチャー（iPhone 対応）。
設計書：[docs/DESIGN.md](docs/DESIGN.md)

現在の段階：**P0（環境構築と計測基盤）**。ゲームプレイはまだありません。

## 遊ぶ・確認する

- 公開版：https://clubzfirst2-byte.github.io/my-jrpg-game/
- 計測表示を最初から開く：`?debug=1`
- 負荷テストのスプライト数を指定：`?bench=1000`
- 計測レポートの時間（秒）を変更：`?reportSec=60`

画面右上の「計測」で、FPS・フレーム時間・描画回数・テクスチャ数などを表示します。
エラーが起きると、赤い「エラー n」ボタンが出ます。押すと内容を確認できます。

## 開発

```bash
npm install
npm run dev        # 開発サーバ（同じ Wi-Fi の iPhone から表示された URL で開ける）
npm run lint       # ESLint（src/game が描画層に依存していないかも検査）
npm run typecheck  # JSDoc の型チェック
npm test           # 単体テスト（Vitest）
npm run test:e2e   # ビルド＋E2E（Playwright、iPhone サイズ）
npm run check      # 上記すべて
```

## ブランチ運用

`main` は常に動く状態に保ちます。作業は `feature/...` ブランチで行い、プルリクエストで GitHub Actions のテストが通ってから `main` に統合します。`main` に統合されると GitHub Pages に自動で公開されます（DESIGN.md 7.6）。

## 実機テスト

`docs/device-tests/TEMPLATE.md` をコピーして記録します。
