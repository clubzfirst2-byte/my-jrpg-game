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

import revisions  # noqa: E402
import revisions_b2  # noqa: E402
import woman  # noqa: E402
import cook  # noqa: E402
import child  # noqa: E402
import smith  # noqa: E402

NPCS = [elder.NPC, merchant.NPC, guard.NPC]  # batch 1 (approved; not regenerated differently)
BATCH2 = [woman.NPC, cook.NPC, child.NPC, smith.NPC]
NPCS = NPCS + BATCH2
BY_ID = {n.id: n for n in NPCS}
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "src", "art-release", "npc")
# batch 1, revision 1: the same names in their own folder (the approved frames stay as they are)
REVISION_OUT = os.path.join(os.path.dirname(__file__), "..", "..", "src", "art-release", "npc-revision")
# batch 2, revision 1 (woman, child, smith; the cook is unchanged)
REVISION_B2_OUT = os.path.join(os.path.dirname(__file__), "..", "..", "src", "art-release", "npc-revision-b2")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    count = 0
    for npc in NPCS:
        for name, img in npc.frames().items():
            with open(os.path.join(OUT, f"{name}.png"), "wb") as fh:
                fh.write(png(img))
            count += 1
    print(f"{count} release frames -> src/art-release/npc/")
    os.makedirs(REVISION_OUT, exist_ok=True)
    count = 0
    for npc in revisions.REVISED:
        for name, img in npc.frames().items():
            with open(os.path.join(REVISION_OUT, f"{name}.png"), "wb") as fh:
                fh.write(png(img))
            count += 1
    print(f"{count} revised frames -> src/art-release/npc-revision/")
    os.makedirs(REVISION_B2_OUT, exist_ok=True)
    count = 0
    for npc in revisions_b2.REVISED_B2:
        for name, img in npc.frames().items():
            with open(os.path.join(REVISION_B2_OUT, f"{name}.png"), "wb") as fh:
                fh.write(png(img))
            count += 1
    print(f"{count} revised frames -> src/art-release/npc-revision-b2/")
