# 主人公の仮素材（P12・承認待ち）

**仮素材です。正式素材ではありません。** ゲームは URL に `?hero=proto` を付けたときだけこの絵を使います（`src/art` の外に置いているため、ふつうの起動では使われない）。

- 作り方：`python3 tools/hero_proto/gen_hero_prototype.py`（承認済みデザイン資料の色と、参考シート `docs/hero/reference/sprite_prototype/` の動きをもとに、32×56 で描き起こし）
- 20 枚：歩行 `player.walk.<向き>.0〜2`（0 が待機も兼ねる）、水泳 `player.swim.<向き>.0〜1`。向きは down / up / right / left（left は right の左右反転）
- 一覧と確認の手順：`docs/hero/P12_ASSET_LIST.md`
- **承認されたら**：この 20 枚を `src/art/characters/hero/sprites/` へ移すと、ふつうの起動の主人公になる
