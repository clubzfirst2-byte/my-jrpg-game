#!/usr/bin/env python3
"""Generates the region templates south of the first island (P8) as src/game/world/maps/regions.js.

Deterministic. Each region is 96 x 96 tiles (the world's outdoor width). They are stacked below
the island (rows 0-71) by src/game/world/world.js:

  風の草原 (plains, rows 72-167)  rolling hills, a lake, a windmill ruin, beasts
  赤砂の荒野 (desert, rows 168-263) dunes, mesas, cacti, an oasis; it never rains there

The island's sand causeway (cols 45-50) continues into the plains' north edge.
Coordinates in the features below are LOCAL to each region; world.js offsets them.
"""
import math, json, os

RW, RH = 96, 96
D = '0123456789abcdefghijklmnopqrstuv'
CAUSEWAY = range(45, 51)

def hsh(x, y, s=0):
    v = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xffffffff
    v = ((v ^ (v >> 13)) * 1274126177) & 0xffffffff
    return ((v ^ (v >> 16)) & 0xffff) / 65535.0

def noise(x, y, s, scale):
    fx, fy = x / scale, y / scale
    x0, y0 = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - x0, fy - y0
    a = hsh(x0, y0, s); b = hsh(x0 + 1, y0, s); c = hsh(x0, y0 + 1, s); d = hsh(x0 + 1, y0 + 1, s)
    sx, sy = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy

class Region:
    def __init__(self, rid, name, seed):
        self.id, self.name, self.seed = rid, name, seed
        self.g = [['~'] * RW for _ in range(RH)]
        self.h = [[0] * RW for _ in range(RH)]
        self.features = {'enemies': [], 'chests': [], 'checkpoints': [], 'landmarks': [], 'pickups': [], 'envObjects': [], 'campfires': []}

    def land(self, edge):
        # Land everywhere except a sea border (`edge` tiles) on the west, east and south.
        for y in range(RH):
            for x in range(RW):
                wob = int(noise(x, y, self.seed, 7) * 3)
                if x >= edge + wob and x < RW - edge - wob and y < RH - edge - wob:
                    self.g[y][x] = self.base

    def plateau(self, cx, cy, rx, ry, height, s):
        for y in range(RH):
            for x in range(RW):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + (noise(x, y, s, 5) - 0.5) * 0.3
                if d < 1 and self.g[y][x] not in '~':
                    self.h[y][x] = max(self.h[y][x], height)

    def water(self, cx, cy, rx, ry, s):
        for y in range(RH):
            for x in range(RW):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + (noise(x, y, s, 4) - 0.5) * 0.3
                if d < 1:
                    self.g[y][x] = '~'; self.h[y][x] = 0

    def free(self, x, y, lvl=None):
        if not (0 <= x < RW and 0 <= y < RH): return False
        if self.g[y][x] not in '.s=': return False
        if lvl is not None and self.h[y][x] != lvl: return False
        taken = [(o['tx'], o['ty']) for lst in self.features.values() for o in lst if isinstance(o, dict) and 'tx' in o]
        return (x, y) not in taken

    def near_free(self, x0, y0, lvl=0):
        for d in range(0, 12):
            for y in range(y0 - d, y0 + d + 1):
                for x in range(x0 - d, x0 + d + 1):
                    if self.free(x, y, lvl): return x, y
        raise AssertionError(('no free tile', self.id, x0, y0))

    def out(self):
        def hc(x, y):
            v = self.h[y][x]; assert v % 4 == 0 and v // 4 < 32
            return D[v // 4]
        return {
            'id': self.id, 'name': self.name,
            'ground': [''.join(r) for r in self.g],
            'height': [''.join(hc(x, y) for x in range(RW)) for y in range(RH)],
            **self.features, **self.extra,
        }

# ---------------- 風の草原 (plains) ----------------
P = Region('plains', '風の草原', 31)
P.base = '.'
P.land(3)
# The causeway arrives at the north edge.
for y in range(0, 6):
    for x in range(RW):
        if x not in CAUSEWAY: P.g[y][x] = '~'
        else: P.g[y][x] = 's'
for y in range(6, 9):
    for x in range(40, 56): P.g[y][x] = 's'
P.plateau(70, 30, 14, 10, 16, 41)
P.plateau(72, 30, 7, 5, 32, 42)
P.plateau(22, 64, 12, 9, 16, 43)
P.water(28, 32, 9, 6, 44)
# A path from the causeway south through the plains.
for y in range(6, RH - 6):
    x = int(48 + 6 * math.sin(y / 11))
    for dx in (0, 1):
        if P.g[y][x + dx] == '.' and P.h[y][x + dx] == 0: P.g[y][x + dx] = '='
# Windmill ruin on the high hill: a landmark seen from afar.
for y in range(28, 32):
    for x in range(70, 74):
        P.g[y][x] = 'u'; P.h[y][x] = 48
for y in range(RH):
    for x in range(RW):
        if P.g[y][x] == '.' and P.h[y][x] == 0 and hsh(x, y, 45) < 0.05: P.g[y][x] = 'T'
        elif P.g[y][x] == '.' and P.h[y][x] == 16 and hsh(x, y, 46) < 0.08: P.g[y][x] = 'T'
P.features['checkpoints'].append({'id': 'plains', **dict(zip(('tx', 'ty'), P.near_free(50, 12)))})
for k, (x, y) in enumerate([(40, 40), (60, 58), (30, 75), (66, 80)]):
    tx, ty = P.near_free(x, y)
    P.features['enemies'].append({'kind': 'beast', 'tx': tx, 'ty': ty})
for k, (x, y, item) in enumerate([(35, 26, 'red_berry'), (22, 40, 'mushroom'), (55, 70, 'swift_herb'), (75, 66, 'red_berry'), (44, 86, 'arrow')]):
    tx, ty = P.near_free(x, y)
    P.features['pickups'].append({'id': f'plains{k}', 'item': item, 'tx': tx, 'ty': ty, **({'count': 5} if item == 'arrow' else {})})
tx, ty = P.near_free(72, 33, 32)
P.features['chests'].append({'id': 'windmill', 'tx': tx, 'ty': ty, 'reward': 'money', 'money': 80})
P.features['landmarks'].append({'id': 'windmill', 'name': '風車跡', 'tx': 72, 'ty': 29, 'always': False})
# The road continues south into the desert.
for y in range(RH - 8, RH):
    for x in CAUSEWAY:
        P.g[y][x] = 's'; P.h[y][x] = 0
P.extra = {'climate': 'temperate', 'bundle': 'region:plains'}

# ---------------- 赤砂の荒野 (desert) ----------------
S = Region('desert', '赤砂の荒野', 51)
S.base = 's'
S.land(3)
for y in range(0, 4):
    for x in range(RW):
        S.g[y][x] = 's' if x in CAUSEWAY else '~'
S.plateau(24, 30, 9, 7, 32, 61)
S.plateau(70, 22, 8, 10, 48, 62)
S.plateau(60, 66, 12, 8, 16, 63)
S.water(36, 70, 5, 4, 64)
# Palms around the oasis, cacti in the dunes.
for y in range(RH):
    for x in range(RW):
        if S.g[y][x] != 's': continue
        near_oasis = ((x - 36) / 9) ** 2 + ((y - 70) / 7) ** 2 < 1
        if near_oasis and S.h[y][x] == 0 and hsh(x, y, 65) < 0.25: S.g[y][x] = 'T'
cacti = []
for y in range(8, RH - 6):
    for x in range(6, RW - 6):
        if S.g[y][x] == 's' and hsh(x, y, 66) < 0.025: cacti.append((x, y))
S.features['checkpoints'].append({'id': 'desert', **dict(zip(('tx', 'ty'), S.near_free(48, 10)))})
for (x, y) in [(30, 40), (60, 45), (40, 80)]:
    tx, ty = S.near_free(x, y)
    S.features['enemies'].append({'kind': 'archer', 'tx': tx, 'ty': ty})
for (x, y) in [(70, 80), (20, 55)]:
    tx, ty = S.near_free(x, y)
    S.features['enemies'].append({'kind': 'beast', 'tx': tx, 'ty': ty})
for k, (x, y, item) in enumerate([(38, 64, 'red_berry'), (64, 40, 'ember_pepper'), (25, 26, 'arrow'), (80, 60, 'ember_pepper')]):
    tx, ty = S.near_free(x, y, S.h[y][x] if S.g[y][x] == 's' else 0)
    S.features['pickups'].append({'id': f'desert{k}', 'item': item, 'tx': tx, 'ty': ty, **({'count': 5} if item == 'arrow' else {})})
tx, ty = S.near_free(70, 15, 48)
S.features['chests'].append({'id': 'mesa', 'tx': tx, 'ty': ty, 'reward': 'item', 'item': 'hunter_bow'})
S.features['landmarks'].append({'id': 'mesa', 'name': '大岩', 'tx': 70, 'ty': 18, 'always': False})
taken = {(o['tx'], o['ty']) for lst in S.features.values() for o in lst if isinstance(o, dict) and 'tx' in o}
S.features['envObjects'] = [{'type': 'cactus', 'tx': x, 'ty': y} for (x, y) in cacti if (x, y) not in taken and x not in CAUSEWAY]
S.extra = {'climate': 'dry', 'bundle': 'region:desert'}

regions = [P.out(), S.out()]
for r in regions:
    assert len(r['ground']) == RH and all(len(row) == RW for row in r['ground'])
    for c in r['chests'] + r['checkpoints']:
        assert r['ground'][c['ty']][c['tx']] in '.s=', (r['id'], c)

out = """// @ts-check
// Region templates south of the first island (P8). GENERATED by tools/gen_world.py: edit the script.
// Each region is 96 x 96 tiles; coordinates are local to the region (src/game/world/world.js
// stacks the regions under the island and offsets them).

/** @typedef {import('../tilemap.js').IslandDef & { id: string, name: string, climate: 'temperate' | 'dry', bundle: string }} RegionDef */

/** @type {RegionDef[]} */
export const REGIONS = %s;
""" % json.dumps(regions, ensure_ascii=False, indent=1)
path = os.path.join(os.path.dirname(__file__), '..', 'src', 'game', 'world', 'maps', 'regions.js')
with open(path, 'w') as f:
    f.write(out)
print('wrote', path, [(r['id'], len(r['enemies']), len(r['envObjects'])) for r in regions])
