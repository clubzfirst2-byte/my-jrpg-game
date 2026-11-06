# NPC の仮素材（P12・承認待ち）

**仮素材です。正式素材ではありません。** `?npc=proto`（または `?proto=all`）のときだけ使われます。

| 回 | look | 人物 | 作り方 |
|---|---|---|---|
| 第 1 回 | 1 | 老人（長老） | `python3 tools/art_proto/gen_round1.py` |
| 第 1 回 | 3 | 兵士（見張り） | 同上 |
| 第 2 回 | 6 | 村人（新規） | `python3 tools/art_proto/gen_round2.py` |
| 第 2 回 | 4 | 商人（雑貨屋） | 同上 |
| 第 2 回 | 7 | 鍛冶屋（新規） | 同上 |
| 第 2 回 | 5 | 子ども（村の子） | 同上 |
| 第 2 回 | 8 | 旅人（新規） | 同上 |
| 第 2 回 | 9 | 星環の姫（新規） | 同上 |

- 各 12 コマ（歩行 3 × 4 方向、`npc.<look>.walk.<down|up|right|left>.<0〜2>.png`）、32×56、足元基準
- 確認：`?gallery=1`（名前つき・歩行アニメーション）、`?npc=proto&npclook=elder:9`（村の人物の見た目を入れ替えて表示。見た目だけ）
- プレビュー画像：`python3 tools/art_proto/previews_round2.py` → `docs/characters/round2/`
- 計画：`docs/characters/P12_NPC_ENEMY_PLAN.md`
