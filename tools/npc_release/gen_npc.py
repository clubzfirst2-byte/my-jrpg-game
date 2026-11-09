"""The villagers — RELEASE art, batch 1 (elder, merchant, guard). QUALITY_POLICY.md: made at release
quality, adopted after approval. Plan: docs/npc/NPC_RELEASE_PLAN.md.

Writes src/art-release/npc/npc.<id>.<idle|walk>.<down|up|right|left>.<n>.png (32x56, feet at the
bottom centre), 40 per villager.
Run: python3 tools/npc_release/gen_npc.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "art_proto"))
from pixel import png  # noqa: E402
import elder  # noqa: E402
import merchant  # noqa: E402
import guard  # noqa: E402

NPCS = [elder.NPC, merchant.NPC, guard.NPC]
BY_ID = {n.id: n for n in NPCS}
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "src", "art-release", "npc")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    count = 0
    for npc in NPCS:
        for name, img in npc.frames().items():
            with open(os.path.join(OUT, f"{name}.png"), "wb") as fh:
                fh.write(png(img))
            count += 1
    print(f"{count} release frames -> src/art-release/npc/")
