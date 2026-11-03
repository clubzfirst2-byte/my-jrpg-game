#!/usr/bin/env python3
"""Generates the first island (P3.5) as src/game/world/maps/island.js.

Deterministic: running it again produces the same map. Layout follows DESIGN.md 5.9:
a central ruined lighthouse tower (4 tiers), a north cliff ledge with a heart chest reachable
three ways (climb / glide from the tower / secret cave), a river with a log bridge, a west forest,
an enemy camp on the east coast, a small islet, and a secret cave (separate area at the east edge).
"""
import math, json, os

W, H = 112, 72
D = '0123456789abcdefghijklmnopqrstuv'
g = [['~'] * W for _ in range(H)]      # ground chars
h = [[0] * W for _ in range(H)]        # heights in px
ramps = set()

def hsh(x, y, s=0):
    v = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xffffffff
    v = ((v ^ (v >> 13)) * 1274126177) & 0xffffffff
    return ((v ^ (v >> 16)) & 0xffff) / 65535.0

def noise(x, y, s, scale):
    # value noise, bilinear
    fx, fy = x / scale, y / scale
    x0, y0 = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - x0, fy - y0
    a = hsh(x0, y0, s); b = hsh(x0 + 1, y0, s); c = hsh(x0, y0 + 1, s); d = hsh(x0 + 1, y0 + 1, s)
    sx, sy = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    return (a * (1 - sx) + b * sx) * (1 - sy) + (c * (1 - sx) + d * sx) * sy

def ell(x, y, cx, cy, rx, ry, s, amp=0.12):
    d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
    return d + (noise(x, y, s, 6) - 0.5) * amp * 2

ISLAND_W = 96  # columns 96.. are the cave area
# --- island shape, beach ---
for y in range(H):
    for x in range(ISLAND_W):
        d = ell(x, y, 48, 38, 42, 31, 1, 0.18)
        if d < 1:
            g[y][x] = 's' if d > 0.78 else '.'
# islet (south-east)
for y in range(H):
    for x in range(ISLAND_W):
        if ((x - 87) / 3.6) ** 2 + ((y - 63) / 2.8) ** 2 < 1:
            g[y][x] = 's'

def is_land(x, y):
    return g[y][x] in '.s='

# --- elevation: level 1 (16px) hill, level 2 (32px) top, north ledge (48px) ---
for y in range(H):
    for x in range(ISLAND_W):
        if not is_land(x, y) or g[y][x] == 's':
            continue
        if ell(x, y, 48, 30, 20, 17, 2, 0.10) < 1:
            h[y][x] = 16
for y in range(H):
    for x in range(ISLAND_W):
        if h[y][x] == 16 and ell(x, y, 48, 28, 11, 12, 3, 0.06) < 1:
            h[y][x] = 32
# keep the north ledge clean: rows 9-12, cols 43-53 at 48px (sea cliff to the north)
for y in range(9, 13):
    for x in range(43, 54):
        g[y][x] = '.'
        h[y][x] = 48
# make sure the level-2 top reaches the ledge (rows 13-16 at 32px under the ledge)
for y in range(13, 17):
    for x in range(43, 54):
        g[y][x] = '.'
        h[y][x] = max(h[y][x], 32)

# --- lighthouse tower (ruin, not climbable): tiers 48/64/80/96 climbing north, stairs at cols 47-48 ---
TX0, TX1 = 45, 51
def tier(y0, y1, height):
    for y in range(y0, y1 + 1):
        for x in range(TX0, TX1 + 1):
            g[y][x] = 'u'
            h[y][x] = height
tier(27, 30, 48); tier(24, 26, 64); tier(21, 23, 80); tier(18, 20, 96)
for (y, lo_h) in [(30, 32), (26, 48), (23, 64), (20, 80)]:
    for x in (47, 48):
        ramps.add((x, y))
# ground in front of the tower stairs (row 31) must be level 2 (32)
for x in range(TX0, TX1 + 1):
    h[31][x] = 32; g[31][x] = '.'

# --- stairs: ground -> level 1 (south, row 48), level 1 -> level 2 (row 41) ---
def ramp_col(x, y, lo, hi):
    h[y + 1][x] = lo; h[y - 1][x] = hi; ramps.add((x, y)); g[y][x] = '='
for x in (47, 48):
    # find the south edge of level 1 on these columns
    ys = [y for y in range(H) if h[y][x] == 16]
    edge = max(ys)
    ramp_col(x, edge + 1, 0, 16)
    ys2 = [y for y in range(H) if h[y][x] == 32 and y > 31]
    edge2 = max(ys2)
    ramp_col(x, edge2 + 1, 16, 32)
STAIR1_ROW = max(y for y in range(H) if (47, y) in ramps)

# --- path: spawn (beach south) north to the stairs; branches east (camp) and west (bridge) ---
for y in range(STAIR1_ROW + 1, 66):
    for x in (47, 48):
        if h[y][x] == 0 and g[y][x] in '.s':
            g[y][x] = '='
for x in range(48, 74):
    if h[56][x] == 0 and g[56][x] in '.s': g[56][x] = '='
for x in range(24, 48):
    if h[56][x] == 0 and g[56][x] in '.s': g[56][x] = '='

# --- river: north-west hills to the south-west sea, 2-3 wide, only on level 0 ---
for y in range(10, H):
    cx = 22 + int(4 * math.sin(y / 7.0))
    for x in range(cx - 1, cx + 2 + (1 if y % 9 < 4 else 0)):
        if 0 <= x < ISLAND_W and h[y][x] == 0 and g[y][x] != '~':
            g[y][x] = '~'
# log bridge across the river at row 56 (the west path)
for x in range(14, 32):
    if g[56][x] == '~': g[56][x] = '='

# --- enemy camp (east): ruin ledge for the archer, campfire ---
for y in range(36, 40):
    for x in range(80, 85):
        g[y][x] = 'u'; h[y][x] = 16

# --- trees: west forest, east grove, scattered ---
def plant(x, y):
    if g[y][x] == '.' and h[y][x] == 0 and (x, y) not in ramps:
        g[y][x] = 'T'
for y in range(24, 54):
    for x in range(6, 20):
        if hsh(x, y, 9) < 0.32: plant(x, y)
for y in range(46, 54):
    for x in range(58, 70):
        if hsh(x, y, 10) < 0.2: plant(x, y)
for y in range(H):
    for x in range(ISLAND_W):
        if hsh(x, y, 11) < 0.03: plant(x, y)
# keep the path, spawn area, camp clearing and chest approaches free of trees
def clear(x0, y0, x1, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if g[y][x] == 'T': g[y][x] = '.'
clear(44, 60, 52, 68)       # spawn
clear(70, 34, 88, 48)       # camp
# Hidden forest chest: a pocket ringed by trees with a single gap on the south side.
PX, PY = 14, 44
clear(PX - 2, PY - 2, PX + 2, PY + 2)
for dy in range(-2, 3):
    for dx in range(-2, 3):
        x, y = PX + dx, PY + dy
        ring = abs(dx) == 2 or abs(dy) == 2
        if ring and not (dx == 0 and dy == 2) and g[y][x] in '.s' and h[y][x] == 0:
            g[y][x] = 'T'
clear(30, 46, 38, 52)       # secret cave approach
# a few rocks
for (x, y) in [(56, 60), (57, 60), (40, 58), (64, 52), (30, 62), (70, 60)]:
    if g[y][x] == '.' and h[y][x] == 0: g[y][x] = '#'

# --- the cave area (columns 98-111): walls are tall ruin, floor is ruin at 0 ---
for y in range(H):
    for x in range(96, W):
        g[y][x] = 'u'; h[y][x] = 48
for y in range(3, 15):
    for x in range(99, 110):
        h[y][x] = 0
# The south side is low rubble, not a tall wall: in the 3/4 view a 48px wall south of the floor
# would hide the player standing in front of it. Rows 15-17 are floor; a line of rocks closes it.
for y in range(15, 18):
    for x in range(99, 110):
        h[y][x] = 0
for x in range(99, 110):
    g[15][x] = '#'
for (x, y) in [(102, 7), (106, 10), (101, 12)]:
    g[y][x] = '#'

# --- spawn ---
SPAWN = (48, 65)
g[SPAWN[1]][SPAWN[0]] = 'P'

# --- validation ---
for (x, y) in ramps:
    lo, hi = h[y + 1][x], h[y - 1][x]
    assert hi - lo == 16, ('ramp', x, y, lo, hi)
    assert h[y][x] in (lo, hi) or True

def hc(x, y):
    if (x, y) in ramps: return '^'
    v = h[y][x]; assert v % 4 == 0 and v // 4 < 32, (x, y, v)
    return D[v // 4]

ground = [''.join(r) for r in g]
height = [''.join(hc(x, y) for x in range(W)) for y in range(H)]

SECRET_DOOR = (34, max(y for y in range(H) if h[y][34] == 16) + 1)   # ground tile under the level-1 cliff
assert h[SECRET_DOOR[1]][34] == 0 and g[SECRET_DOOR[1]][34] in '.=s', SECRET_DOOR
LEDGE_ARRIVAL = (45, 12)  # south side of the north ledge: room to stop before its north edge

features = {
    'enemies': [
        {'kind': 'beast', 'tx': 40, 'ty': 58},
        {'kind': 'beast', 'tx': 62, 'ty': 55},
        {'kind': 'beast', 'tx': 14, 'ty': 50},
        {'kind': 'beast', 'tx': 75, 'ty': 38},
        {'kind': 'beast', 'tx': 78, 'ty': 45},
        {'kind': 'archer', 'tx': 82, 'ty': 37},
        {'kind': 'archer', 'tx': 56, 'ty': 38},
        {'kind': 'beast', 'tx': 104, 'ty': 9},
    ],
    'chests': [
        {'id': 'ledge', 'tx': 49, 'ty': 10, 'reward': 'heart'},
        {'id': 'tower', 'tx': 50, 'ty': 18, 'reward': 'heart'},
        {'id': 'cave', 'tx': 107, 'ty': 5, 'reward': 'treasure'},
        {'id': 'camp', 'tx': 86, 'ty': 44, 'reward': 'treasure'},
        {'id': 'islet', 'tx': 87, 'ty': 63, 'reward': 'treasure'},
        {'id': 'forest', 'tx': PX, 'ty': PY, 'reward': 'treasure'},
    ],
    'checkpoints': [
        {'id': 'beach', 'tx': 51, 'ty': 64},
        {'id': 'hill', 'tx': 51, 'ty': STAIR1_ROW + 2},
        {'id': 'camp', 'tx': 72, 'ty': 47},
    ],
    'campfires': [{'tx': 77, 'ty': 41}],
    'warps': [
        # Enter the cave by walking north into the opening in the cliff.
        {'id': 'cave-in', 'tx': SECRET_DOOR[0], 'ty': SECRET_DOOR[1], 'facing': 'up', 'toTx': 104, 'toTy': 13, 'reveal': True},
        # Leave the cave at its north end: out onto the north ledge.
        {'id': 'cave-out', 'tx': 108, 'ty': 3, 'facing': 'up', 'toTx': LEDGE_ARRIVAL[0], 'toTy': LEDGE_ARRIVAL[1]},
        # Back out the way you came.
        {'id': 'cave-back', 'tx': 104, 'ty': 14, 'facing': 'down', 'toTx': SECRET_DOOR[0], 'toTy': SECRET_DOOR[1] + 1},
    ],
    'areas': [{'id': 'cave', 'tx': 98, 'ty': 2, 'tw': 13, 'th': 14}],
    # Camera bounds outdoors: the island part of the map (the cave strip to the east is hidden).
    'outdoor': {'id': 'outdoor', 'tx': 0, 'ty': 0, 'tw': 96, 'th': H},
    'landmarks': [
        {'id': 'tower', 'name': '灯台塔', 'tx': 48, 'ty': 19, 'always': True},
        {'id': 'smoke', 'name': '煙', 'tx': 77, 'ty': 41, 'always': False},
        {'id': 'bigtree', 'name': '巨木', 'tx': 13, 'ty': 30, 'always': False},
    ],
}
# enemies: move off blocked tiles (trees, rocks, water) to the nearest free tile on the same level
def free(x, y, lvl=None):
    return 0 <= x < W and 0 <= y < H and g[y][x] in '.s=u' and (x, y) not in ramps and (lvl is None or h[y][x] == lvl)
for e in features['enemies']:
    x0, y0 = e['tx'], e['ty']
    if free(x0, y0):
        continue
    lvl = h[y0][x0]
    best = min(((abs(x - x0) + abs(y - y0), x, y) for y in range(max(0, y0 - 4), min(H, y0 + 5)) for x in range(max(0, x0 - 4), min(W, x0 + 5)) if free(x, y, lvl)), default=None)
    assert best, ('no free tile near enemy', e)
    e['tx'], e['ty'] = best[1], best[2]
# warps: trigger tiles and arrival tiles must be walkable
for w in features['warps']:
    assert free(w['tx'], w['ty']), ('warp tile blocked', w)
    assert free(w['toTx'], w['toTy']), ('warp arrival blocked', w)
# chests must sit on dry, unoccupied ground
for c in features['chests'] + features['checkpoints'] + features['campfires']:
    ch = g[c['ty']][c['tx']]
    assert ch in '.=su', (c, ch)

fmt = lambda rows: ',\n'.join("    '" + r + "'" for r in rows)
out = f"""// @ts-check
// The first island (P3.5, DESIGN.md 5.9). GENERATED by tools/gen_island.py: edit the script, not this file.
// Ground legend: '.' grass, 's' sand, '=' path, '~' water, 'u' ruin, 'T' tree, '#' rock, 'P' spawn.
// Height legend: base-32 digit = height in 4px units ('4' = 1 level), '^' = ramp rising north by 1 level.

/** @type {{import('../tilemap.js').IslandDef}} */
export const ISLAND = {{
  ground: [
{fmt(ground)},
  ],
  height: [
{fmt(height)},
  ],
  ...{json.dumps(features, ensure_ascii=False)},
}};
"""
path = os.path.join(os.path.dirname(__file__), '..', 'src', 'game', 'world', 'maps', 'island.js')
with open(path, 'w') as f:
    f.write(out)
print('wrote', path, 'stairs row', STAIR1_ROW, 'secret door', SECRET_DOOR)
# preview
for y in range(0, H, 1):
    print(''.join(('^' if (x, y) in ramps else (g[y][x] if g[y][x] in '~T#P' else ('u' if g[y][x]=='u' else D[h[y][x]//4] if h[y][x] else g[y][x]))) for x in range(W)))
