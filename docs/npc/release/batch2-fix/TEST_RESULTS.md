# NPC 製品版 第 2 回 最終調整 テスト結果

> 2026-11-09。ブランチ `feature/npc-release-batch2-fix` で、ローカルで実行した。

| 確認 | 結果 |
|---|---|
| lint（eslint） | 成功 |
| 型チェック（tsc） | 成功 |
| データ検証 | 成功（28 items, 6 recipes, 6 dialogues, 3 quests, 1 shops） |
| 単体テスト（Vitest） | **494 件成功・失敗 0**（2 件追加） |
| E2E（Playwright、iPhone 15 横画面・Chromium） | **115 件成功・失敗 0**（1 件追加） |
| GIF の再生確認 | 8 本すべてで、コマ数（待機 4・歩行 6）と 1 周の長さが正しい（`GIF_CHECK.md`） |

## 追加したテスト

### 単体テスト
- **第 2 回の提出版が変わっていない**：160 枚すべてが、提出時と 1 バイト単位で同じ
- **第 2 回の修正案**
  - 村の女性・村の子・鍛冶職人の 3 人だけで、各 40 枚ある（料理人のファイルはない）
  - すべて 32×56・8 ビット RGBA・四隅が透明
  - 足元（下の 2 行）が、全コマで提出版と同じ
  - 直すよう指示された向き（女性の正面・横向き、子どもの正面・背面・横向き、鍛冶職人の正面・横向き）は、提出版と違う絵になっている
  - 女性の背面は変わっていない
  - 3 人とも、待機・歩行の全コマが違う絵

### E2E
- `?npc=revision-b2` のとき、女性・子ども・鍛冶職人だけが修正案の絵になる。料理人と第 1 回の絵は変わらない
- `?npc=revision,revision-b2` のとき、両方の修正案が使われる

## 既存素材を変更していないことの証明

```
$ git diff --name-only feature/npc-release-batch2 -- src/art src/art-proto public src/art-release/hero src/art-release/npc src/art-release/npc-revision | wc -l
0
```
- `src/art-release/npc/`（第 1 回の承認済み 120 枚・第 2 回の提出版 160 枚）：変更なし。単体テストのハッシュ比較でも確認した
- `src/art-release/npc-revision/`（第 1 回の修正案）：変更なし
- 費用はかかっていない
