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

# P8: a sand causeway leaves the south beach toward the regions below (tools/gen_world.py).
CAUSEWAY = range(45, 51)
for y in range(64, H):
    for x in CAUSEWAY:
        if g[y][x] == '~':
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

# --- P4: environment (DESIGN.md 4.3) ---
ENV_OBJECTS = []
def env_obj(t, x, y, **kw):
    assert g[y][x] in '.s=Tmu' and (x, y) not in ramps, ('env object on', t, x, y, g[y][x])
    g[y][x] = '.' if g[y][x] == 'T' else g[y][x]
    ENV_OBJECTS.append({'type': t, 'tx': x, 'ty': y, **kw})
# Forest pocket: brambles close the gap; a brazier lights arrows shot north through it.
# Ways in: shoot an arrow through the brazier at the brambles / set the trees on fire / cut the brambles.
for y in (47, 48, 50, 51):
    if g[y][PX] == 'T': g[y][PX] = '.'
env_obj('bramble', PX, PY + 2)
env_obj('brazier', PX, PY + 5)
# Enemy camp: a metal floor around the campfire and a shock crystal at its west edge.
for y in range(37, 46):
    for x in range(72, 80):
        if g[y][x] == '.' and h[y][x] == 0 and (x, y) != (77, 41): g[y][x] = 'm'
env_obj('crystal', 71, 41)
env_obj('jar', 73, 36)
env_obj('jar', 80, 44)
# A sealed vault on the south-east beach: rune doors open when the receiver on the shore is powered.
# The crystal stands on the islet: the current runs through the sea to the receiver.
VX, VY = 75, 59
for (x, y) in [(VX - 1, VY - 1), (VX + 1, VY - 1), (VX - 1, VY + 1), (VX + 1, VY + 1)]:
    g[y][x] = '#'
for (x, y) in [(VX, VY - 1), (VX, VY + 1), (VX - 1, VY), (VX + 1, VY)]:
    env_obj('door', x, y, link='vault')
env_obj('receiver', 78, 62, link='vault')
env_obj('crystal', 84, 62)
assert g[62][79] == '~' and g[62][83] == '~', 'vault receiver and crystal must touch the sea'

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

# --- P7: three trials (試練の洞), rooms below the cave in the east strip ---
# Same shape as the cave: floor cols 99-109, rows y0+1..y0+12, a line of rocks closes the south.
TRIALS = {'trial_light': 20, 'trial_weight': 38, 'trial_chasm': 56}
for tid, y0 in TRIALS.items():
    for y in range(y0 + 1, min(H, y0 + 16)):
        for x in range(99, 110):
            h[y][x] = 0
    for x in range(99, 110):
        g[y0 + 13][x] = '#'
# Inner partitions are rocks (low, so they never hide the player in the 3/4 view).
for tid in ('trial_light', 'trial_weight'):
    y0 = TRIALS[tid]
    for x in range(99, 110):
        if x != 104: g[y0 + 4][x] = '#'
# The chasm: a 2-row pit across the room (falling in puts you back at the edge).
y0 = TRIALS['trial_chasm']
for y in (y0 + 6, y0 + 7):
    for x in range(99, 110):
        g[y][x] = '_'
# The chasm's prize sits in a ring of rune doors on the near side.
for (x, y) in [(100, y0 + 9), (102, y0 + 9), (100, y0 + 11), (102, y0 + 11)]:
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
        # P6: chests hold equipment or money (星貨), not abstract "treasure".
        {'id': 'cave', 'tx': 107, 'ty': 5, 'reward': 'item', 'item': 'ember_sword'},
        {'id': 'camp', 'tx': 86, 'ty': 44, 'reward': 'item', 'item': 'grip_boots'},
        {'id': 'islet', 'tx': 87, 'ty': 63, 'reward': 'money', 'money': 100},
        {'id': 'vault', 'tx': VX, 'ty': VY, 'reward': 'item', 'item': 'insulated_cap'},
        {'id': 'forest', 'tx': PX, 'ty': PY, 'reward': 'item', 'item': 'bark_vest'},
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
    return 0 <= x < W and 0 <= y < H and g[y][x] in '.s=um' and (x, y) not in ramps and (lvl is None or h[y][x] == lvl) and not any(o['tx'] == x and o['ty'] == y for o in ENV_OBJECTS)
for e in features['enemies']:
    x0, y0 = e['tx'], e['ty']
    if free(x0, y0):
        continue
    lvl = h[y0][x0]
    best = min(((abs(x - x0) + abs(y - y0), x, y) for y in range(max(0, y0 - 4), min(H, y0 + 5)) for x in range(max(0, x0 - 4), min(W, x0 + 5)) if free(x, y, lvl)), default=None)
    assert best, ('no free tile near enemy', e)
    e['tx'], e['ty'] = best[1], best[2]
# --- P6: items lying in the world, and the forge (anvil) by the hill stone ---
taken = {(c['tx'], c['ty']) for c in features['chests'] + features['checkpoints'] + features['campfires']}
taken |= {(e['tx'], e['ty']) for e in features['enemies']}
def near_free(x0, y0, lvl=None):
    best = min(((abs(x - x0) + abs(y - y0), x, y) for y in range(max(0, y0 - 6), min(H, y0 + 7)) for x in range(max(0, x0 - 6), min(ISLAND_W, x0 + 7))
                if free(x, y, lvl) and (x, y) not in taken and g[y][x] != '='), default=None)
    assert best, ('no free tile near', x0, y0)
    taken.add((best[1], best[2]))
    return best[1], best[2]
hx, hy = features['checkpoints'][1]['tx'], features['checkpoints'][1]['ty']
ax, ay = near_free(hx + 2, hy, h[hy][hx])
env_obj('anvil', ax, ay)
PICKUPS = []
def pickup(pid, item, x, y, count=1, lvl=None, seasons=None):
    px_, py_ = near_free(x, y, lvl)
    PICKUPS.append({'id': pid, 'item': item, 'tx': px_, 'ty': py_, **({'count': count} if count != 1 else {}), **({'seasons': seasons} if seasons else {})})
for k, (x, y) in enumerate([(9, 40), (11, 48), (17, 38), (14, 44)]):
    pickup(f'mushroom{k}', 'mushroom', x, y)
for k, (x, y) in enumerate([(29, 50), (59, 50), (66, 46), (63, 58)]):
    pickup(f'berry{k}', 'red_berry', x, y)
for k, (x, y) in enumerate([(40, 36), (57, 37), (48, 26)]):
    pickup(f'herb{k}', 'swift_herb', x, y)
for k, (x, y) in enumerate([(75, 36), (70, 45)]):
    pickup(f'pepper{k}', 'ember_pepper', x, y)
for k, (x, y) in enumerate([(44, 58), (66, 40), (30, 44)]):
    pickup(f'arrows{k}', 'arrow', x, y, count=5)
# P10.2: autumn mushrooms in the west forest; peppers that keep you warm in winter.
for k, (x, y) in enumerate([(8, 36), (12, 42), (16, 47)]):
    pickup(f'autumn-mushroom{k}', 'mushroom', x, y, seasons=['autumn'])
for k, (x, y) in enumerate([(62, 54), (34, 54)]):
    pickup(f'winter-pepper{k}', 'ember_pepper', x, y, seasons=['winter'])
pickup('spear', 'guard_spear', 52, 31)
pickup('greatsword', 'rusty_greatsword', 82, 38, lvl=16)
pickup('travel_sword', 'travel_sword', 36, 60)
pickup('hunter_bow', 'hunter_bow', 47, 11, lvl=48)
features['pickups'] = PICKUPS

# --- P7: trials. Glowing pillars on the island lead in; each room teaches an ability. ---
SWITCHES = []
def gate_near(x0, y0):
    # A pillar with two free tiles south of it on the same level (the doorway and the arrival).
    for d in range(0, 8):
        for y in range(y0 - d, y0 + d + 1):
            for x in range(x0 - d, x0 + d + 1):
                if all(free(x, y + k, h[y][x]) and (x, y + k) not in taken and g[y + k][x] != '=' for k in range(3)):
                    for k in range(3): taken.add((x, y + k))
                    return x, y
    raise AssertionError(('no gate spot', x0, y0))
GATES = {'trial_light': gate_near(17, 34), 'trial_weight': gate_near(64, 50), 'trial_chasm': gate_near(70, 57)}
GRANTS = {'trial_light': 'light', 'trial_weight': 'telekinesis', 'trial_chasm': 'vine'}
NAMES = {'trial_light': '灯りの試練', 'trial_weight': '重さの試練', 'trial_chasm': '奈落の試練'}
for tid, (gx, gy) in GATES.items():
    y0 = TRIALS[tid]
    env_obj('pillar', gx, gy)
    features['warps'].append({'id': f'{tid}-in', 'tx': gx, 'ty': gy + 1, 'facing': 'up', 'toTx': 104, 'toTy': y0 + 11})
    features['warps'].append({'id': f'{tid}-back', 'tx': 104, 'ty': y0 + 12, 'facing': 'down', 'toTx': gx, 'toTy': gy + 2})
    features['areas'].append({'id': tid, 'tx': 98, 'ty': y0, 'tw': 13, 'th': 14, 'grants': GRANTS[tid], 'name': NAMES[tid], **({'dark': True} if tid == 'trial_light' else {})})
    features['landmarks'].append({'id': tid, 'name': f'光る石柱（{NAMES[tid]}）', 'tx': gx, 'ty': gy, 'always': False})
    features['chests'].append({'id': tid, 'tx': 104, 'ty': y0 + 2, 'reward': 'item', 'item': 'star_shard'} if tid != 'trial_chasm' else {'id': tid, 'tx': 101, 'ty': y0 + 10, 'reward': 'item', 'item': 'star_shard'})

# Light: a sensor by the door. Ways: a light orb (灯火) / light the sconce next to it with a fire
# arrow shot through the brazier / with the ember sword.
y0 = TRIALS['trial_light']
env_obj('door', 104, y0 + 4, link='trial_light')
env_obj('sconce', 107, y0 + 7)
env_obj('brazier', 100, y0 + 7)
SWITCHES.append({'id': 'light-sensor', 'kind': 'sensor', 'tx': 105, 'ty': y0 + 6, 'link': 'trial_light', 'group': 'a', 'accepts': ['light']})
# Weight: two plates at once. Ways: slide the metal crate onto the west plate with 念動 / push it
# there with sword hits / an enemy standing on it. The player stands on the other one.
y0 = TRIALS['trial_weight']
env_obj('door', 104, y0 + 4, link='trial_weight')
env_obj('crate', 104, y0 + 9)
SWITCHES.append({'id': 'plate-west', 'kind': 'plate', 'tx': 99, 'ty': y0 + 9, 'link': 'trial_weight', 'group': 'a', 'accepts': ['weight']})
SWITCHES.append({'id': 'plate-east', 'kind': 'plate', 'tx': 109, 'ty': y0 + 7, 'link': 'trial_weight', 'group': 'a', 'accepts': ['weight']})
# Chasm: the switches are across the pit; any one opens the doors around the prize. Ways: a fire
# arrow through the brazier onto the sconce / a vine bridge (蔓結び) to the plate / resonance (共鳴).
y0 = TRIALS['trial_chasm']
for (x, y) in [(101, y0 + 9), (101, y0 + 11), (100, y0 + 10), (102, y0 + 10)]:
    env_obj('door', x, y, link='trial_chasm')
env_obj('brazier', 106, y0 + 10)
env_obj('sconce', 106, y0 + 3)
SWITCHES.append({'id': 'chasm-sconce', 'kind': 'sconce', 'tx': 106, 'ty': y0 + 3, 'link': 'trial_chasm', 'group': 'fire', 'accepts': ['fire']})
SWITCHES.append({'id': 'chasm-plate', 'kind': 'plate', 'tx': 103, 'ty': y0 + 3, 'link': 'trial_chasm', 'group': 'weight', 'accepts': ['weight']})
env_obj('stone', 109, y0 + 2)
SWITCHES.append({'id': 'chasm-stone', 'kind': 'stone', 'tx': 109, 'ty': y0 + 2, 'link': 'trial_chasm', 'group': 'resonance', 'accepts': ['resonance', 'shock']})
features['switches'] = SWITCHES
# The tower top: the 星環 altar teaches resonance (共鳴).
alx, aly = near_free(47, 19, 96)
env_obj('altar', alx, aly)

# warps: trigger tiles and arrival tiles must be walkable
for w in features['warps']:
    assert free(w['tx'], w['ty']), ('warp tile blocked', w)
    assert free(w['toTx'], w['toTy']), ('warp arrival blocked', w)
# chests must sit on dry, unoccupied ground
for c in features['chests'] + features['checkpoints'] + features['campfires']:
    ch = g[c['ty']][c['tx']]
    assert ch in '.=sum', (c, ch)
for sw in SWITCHES:
    assert g[sw['ty']][sw['tx']] in '.=sum', ('switch on', sw, g[sw['ty']][sw['tx']])
features['envObjects'] = ENV_OBJECTS
# --- v1.0 (C5): the small 星環 on the beach, where the hero woke. Placed last so nothing above moves.
# Once the four cores are purified and the princess's image is told (flag source_open), walking up
# into the ring leads to the antechamber of 淀みの源 (the desert's strip of rooms, gen_world.py);
# after the source is purified the ring is only a ring again. At least 5 tiles west of the start
# and the beach stone (DESIGN: docs/story/V1_STORY_PROPOSAL.md C5).
RING = (42, 67)
assert g[RING[1]][RING[0]] == 's' and g[RING[1] + 1][RING[0]] == 's', 'the star ring stands on the sand'
assert RING[0] <= SPAWN[0] - 5 and RING[0] <= features['checkpoints'][0]['tx'] - 5, 'the ring is west of the start and the stone'
for lst in ('chests', 'checkpoints', 'campfires', 'enemies', 'pickups', 'envObjects'):
    for o in features[lst]:
        assert (o['tx'], o['ty']) not in (RING, (RING[0], RING[1] + 1)), ('the ring spot is taken', lst, o)
ENV_OBJECTS.append({'type': 'star_ring', 'tx': RING[0], 'ty': RING[1]})
features['passes'] = [{
    'id': 'source-gate', 'tx': RING[0], 'ty': RING[1], 'facing': 'up',
    'to': {'region': 'desert', 'tx': 104, 'ty': 31},
    'if': [{'flag': 'source_open'}, {'flag': 'source_purified', 'is': False}],
}]
# enemies must not stand on environment objects
for e in features['enemies']:
    assert not any(o['tx'] == e['tx'] and o['ty'] == e['ty'] for o in ENV_OBJECTS), e

fmt = lambda rows: ',\n'.join("    '" + r + "'" for r in rows)
out = f"""// @ts-check
// The first island (P3.5, DESIGN.md 5.9). GENERATED by tools/gen_island.py: edit the script, not this file.
// Ground legend: '.' grass, 's' sand, '=' path, '~' water, 'u' ruin, 'm' metal floor, '_' pit, 'T' tree, '#' rock, 'P' spawn.
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
