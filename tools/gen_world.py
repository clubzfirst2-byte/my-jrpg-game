#!/usr/bin/env python3
"""Generates the region templates south of the first island (P8) as src/game/world/maps/regions.js.

Deterministic. Each region is 96 x 96 tiles (the world's outdoor width). They are stacked below
the island (rows 0-71) by src/game/world/world.js:

  風の草原 (plains, rows 72-167)  rolling hills, a lake, a windmill ruin, beasts
  赤砂の荒野 (desert, rows 168-263) dunes, mesas, cacti, an oasis; it never rains there

The island's sand causeway (cols 45-50) continues into the plains' north edge.
East of each region (cols 96-111, hidden from the outdoor camera) is a strip of rooms: P10.1 puts
the insides of the village houses there; their doors are warps.
Coordinates in the features below are LOCAL to each region; world.js offsets them.
"""
import math, json, os

RW, RH = 96, 96
EW = 16  # the room strip (world cols 96-111)
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
        self.features = {'enemies': [], 'chests': [], 'checkpoints': [], 'landmarks': [], 'pickups': [], 'envObjects': [], 'campfires': [], 'npcs': [], 'warps': [], 'areas': [], 'bosses': [], 'switches': []}
        # The room strip east of the region (P10.1): nothing there until a room is carved out.
        self.eg = [['%'] * EW for _ in range(RH)]
        self.eh = [[0] * EW for _ in range(RH)]

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
        # Houses (P9) cover 3 x 2 tiles: their anchor and the tiles beside / behind it.
        for o in self.features['envObjects']:
            if o['type'] == 'house' and abs(x - o['tx']) <= 1 and 0 <= o['ty'] - y <= 1: return False
        return (x, y) not in taken

    def near_free(self, x0, y0, lvl=0):
        for d in range(0, 12):
            for y in range(y0 - d, y0 + d + 1):
                for x in range(x0 - d, x0 + d + 1):
                    if self.free(x, y, lvl): return x, y
        raise AssertionError(('no free tile', self.id, x0, y0))

    def arena(self, bid, kind, x0, y0, w, h, level=0):
        """P10.4: a flat open ground where a core of the murk waits (its boss stays inside)."""
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + w):
                self.g[y][x] = '.'; self.h[y][x] = level
        for key in ('enemies', 'pickups', 'chests', 'checkpoints', 'campfires'):
            for o in self.features[key]:
                assert not (x0 <= o['tx'] < x0 + w and y0 <= o['ty'] < y0 + h), ('arena over', self.id, key, o)
        self.features['envObjects'] = [o for o in self.features['envObjects'] if not (x0 <= o['tx'] < x0 + w and y0 <= o['ty'] < y0 + h)]
        self.features['bosses'].append({'id': bid, 'kind': kind, 'tx': x0 + w // 2, 'ty': y0 + h // 2, 'arena': {'tx': x0, 'ty': y0, 'tw': w, 'th': h}})

    # --- P10.5: trials and the dungeon, in the strip (columns 99-109 inside, like the island's) ---
    def sg(self, X, y, ch, h=None):
        """Sets a strip tile by its region column (96-111)."""
        self.eg[y][X - 96] = ch
        if h is not None: self.eh[y][X - 96] = h

    def obj(self, t, X, y, **kw):
        self.features['envObjects'].append({'type': t, 'tx': X, 'ty': y, **kw})

    def switch(self, sid, kind, X, y, link, group, accepts):
        self.features['switches'].append({'id': sid, 'kind': kind, 'tx': X, 'ty': y, 'link': link, 'group': group, 'accepts': accepts})

    def puzzle_box(self, rid, name, y0, dark=False):
        """A ruin room like the island's trials: tall walls, floor cols 99-109, rows y0+1..y0+12, a line of
        rocks closing the south (y0+13; in the 3/4 view a tall south wall would hide the player).
        The way out is walking down from (104, y0+12)."""
        for y in range(y0, y0 + 16):
            for X in range(98, 111):
                self.sg(X, y, 'u', 48)
        for y in range(y0 + 1, y0 + 16):
            for X in range(99, 110):
                self.sg(X, y, 'u', 0)
        for X in range(99, 110):
            self.sg(X, y0 + 13, '#')
        self.features['areas'].append({'id': rid, 'name': name, 'tx': 98, 'ty': y0, 'tw': 13, 'th': 14, **({'dark': True} if dark else {})})

    def partition(self, y, door_link):
        """Rocks across the room with a rune door in the middle (opened by the room's switches)."""
        for X in range(99, 110):
            if X != 104: self.sg(X, y, '#')
        self.obj('door', 104, y, link=door_link)

    def pillar_gate(self, tid, name, near, y0):
        """A glowing pillar outdoors; walk up into it to enter (like the island's trials)."""
        x0, yy = near
        for d in range(0, 14):
            for y in range(yy - d, yy + d + 1):
                for x in range(x0 - d, x0 + d + 1):
                    if all(self.free(x, y + k, self.h[y][x] if 0 <= y < RH and 0 <= x < RW else None) and self.g[y + k][x] != '=' for k in range(3)):
                        self.obj('pillar', x, y)
                        self.features['warps'].append({'id': f'{tid}-in', 'tx': x, 'ty': y + 1, 'facing': 'up', 'toTx': 104, 'toTy': y0 + 11})
                        self.features['warps'].append({'id': f'{tid}-back', 'tx': 104, 'ty': y0 + 12, 'facing': 'down', 'toTx': x, 'toTy': y + 2})
                        self.features['landmarks'].append({'id': tid, 'name': f'光る石柱（{name}）', 'tx': x, 'ty': y, 'always': False})
                        return x, y
        raise AssertionError(('no gate spot', self.id, near))

    def room(self, rid, name, y0, door, furniture=(), home=True):
        """A room in the east strip (world cols 98-110, rows y0..y0+9) behind the door of a house.

        Walls: two raised rows on the north (their plaster face shows), flat wall tops west and east
        (a raised side wall would show its end at the bottom corners), and a low front wall on the
        south (in the 3/4 view a tall south wall would hide the player).
        Inside: floor rows y0+2..y0+8. The mat at (104, y0+8) leads back out (walk down onto it).
        """
        X0, X1 = 2, 14  # strip-local columns of the west and east walls (world 98, 110)
        for y in range(y0, y0 + 10):
            for x in range(X0, X1 + 1):
                wall = y < y0 + 2 or x in (X0, X1)
                self.eg[y][x] = 'H' if y == y0 + 9 else 'W' if wall else 'w'
                self.eh[y][x] = 32 if y < y0 + 2 else 0
        hx, hy = door
        wx = 96 + 8  # world column of the mat / arrival
        self.features['warps'].append({'id': f'{rid}-in', 'tx': hx, 'ty': hy + 1, 'facing': 'up', 'toTx': wx, 'toTy': y0 + 7})
        self.features['warps'].append({'id': f'{rid}-out', 'tx': wx, 'ty': y0 + 8, 'facing': 'down', 'toTx': hx, 'toTy': hy + 2})
        self.features['areas'].append({'id': rid, 'name': name, 'tx': 96 + X0, 'ty': y0, 'tw': X1 - X0 + 1, 'th': 10, **({'home': True} if home else {})})
        self.features['envObjects'].append({'type': 'mat', 'tx': wx, 'ty': y0 + 8})
        for (t, x, y) in furniture:
            assert self.eg[y0 + y][x - 96] == 'w', ('furniture on', t, x, y)
            assert (x, y) not in ((8 + 96, 7), (8 + 96, 8)), ('furniture blocks the door', t)
            self.features['envObjects'].append({'type': t, 'tx': x, 'ty': y0 + y})

    def out(self):
        def hc(v):
            assert v % 4 == 0 and v // 4 < 32
            return D[v // 4]
        return {
            'id': self.id, 'name': self.name,
            'ground': [''.join(self.g[y]) + ''.join(self.eg[y]) for y in range(RH)],
            'height': [''.join(hc(self.h[y][x]) for x in range(RW)) + ''.join(hc(self.eh[y][x]) for x in range(EW)) for y in range(RH)],
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
# --- P9: 風見の村 (a village by the causeway): houses, villagers, a well-trodden square ---
for y in range(9, 24):
    for x in range(11, 38):
        if P.g[y][x] != '~':
            P.g[y][x] = '.'; P.h[y][x] = 0
for x in range(11, 47):
    P.g[16][x] = '='
HOUSES = [(16, 13), (24, 13), (32, 13), (18, 21)]
for (x, y) in HOUSES:
    P.features['envObjects'].append({'type': 'house', 'tx': x, 'ty': y})
    for yy in (y - 1, y):
        for xx in (x - 1, x, x + 1):
            assert P.g[yy][xx] in '.=', ('house on', xx, yy)
# --- P10.1: inside the houses (rooms in the east strip; local x is the world column 96..111) ---
# 雑貨屋: the shopkeeper stands behind the counter and sells across it.
P.room('shop', '風見の雑貨屋', 3, HOUSES[0], [
    *[('counter', x, 4) for x in range(99, 110) if x != 104], ('counter', 104, 4),
    ('shelf', 100, 2), ('shelf', 102, 2), ('shelf', 106, 2), ('shelf', 108, 2), ('barrel', 99, 7), ('barrel', 109, 7),
])
# 料理番の家: a stove to cook at.
P.room('kitchen', '料理番の家', 15, HOUSES[1], [('stove', 100, 2), ('stove', 101, 2), ('table', 106, 5), ('table', 107, 5), ('barrel', 109, 2), ('shelf', 103, 2)])
# 長老の家: the charm goes on the shelf once it is brought back.
P.room('elder_house', '長老の家', 27, HOUSES[2], [('charm_shelf', 104, 2), ('shelf', 100, 2), ('bed', 108, 3), ('table', 101, 6)])
# 風見の宿: beds to sleep in until morning or evening.
P.room('inn', '風見の宿', 39, HOUSES[3], [('bed', 100, 3), ('bed', 102, 3), ('bed', 106, 3), ('bed', 108, 3), ('table', 104, 3), ('barrel', 109, 7)])
P.features['npcs'] = [
    {'id': 'elder', 'name': '長老', 'dialogue': 'elder', 'look': 1, 'tx': 20, 'ty': 17},
    {'id': 'cook', 'name': '宿の料理人', 'dialogue': 'cook', 'look': 2, 'tx': 26, 'ty': 15},
    {'id': 'guard', 'name': '見張り', 'dialogue': 'guard', 'look': 3, 'tx': 37, 'ty': 17},
    # Behind the counter: stays put, and is talked to across it.
    {'id': 'merchant', 'name': '雑貨屋', 'dialogue': 'merchant', 'look': 4, 'tx': 104, 'ty': 3 + 3, 'stay': True, 'reach': 40},
    {'id': 'child', 'name': '村の子', 'dialogue': 'child', 'look': 5, 'tx': 23, 'ty': 22},
]
P.features['landmarks'].append({'id': 'village', 'name': '風見の村', 'tx': 24, 'ty': 15, 'always': False})
P.features['checkpoints'].append({'id': 'plains', **dict(zip(('tx', 'ty'), P.near_free(42, 14)))})
for k, (x, y) in enumerate([(40, 40), (60, 58), (30, 75), (66, 80)]):
    tx, ty = P.near_free(x, y)
    P.features['enemies'].append({'kind': 'beast', 'tx': tx, 'ty': ty})
for k, (x, y, item) in enumerate([(35, 26, 'red_berry'), (22, 40, 'mushroom'), (55, 70, 'swift_herb'), (75, 66, 'red_berry'), (44, 86, 'arrow')]):
    tx, ty = P.near_free(x, y)
    P.features['pickups'].append({'id': f'plains{k}', 'item': item, 'tx': tx, 'ty': ty, **({'count': 5} if item == 'arrow' else {})})
# P10.2: what each season brings to the plains (items lying around, and who roams).
SEASONAL = [
    ('spring', 'swift_herb', [(18, 34), (40, 50), (62, 72)]),
    ('summer', 'red_berry', [(26, 46), (58, 36), (36, 66)]),
    ('autumn', 'mushroom', [(14, 50), (32, 82), (78, 74), (54, 30)]),
    ('winter', 'ember_pepper', [(20, 30), (66, 64)]),
]
for season, item, spots in SEASONAL:
    for k, (x, y) in enumerate(spots):
        tx, ty = P.near_free(x, y)
        P.features['pickups'].append({'id': f'plains-{season}{k}', 'item': item, 'tx': tx, 'ty': ty, 'seasons': [season]})
# Autumn: beasts fatten up and come out in packs; in winter one of the usual ones keeps to its den.
for (x, y) in [(36, 56), (64, 44), (24, 84)]:
    tx, ty = P.near_free(x, y)
    P.features['enemies'].append({'kind': 'beast', 'tx': tx, 'ty': ty, 'seasons': ['autumn']})
P.features['enemies'][0]['seasons'] = ['spring', 'summer', 'autumn']
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
# P9: the elder's lost charm, by the oasis.
cx_, cy_ = S.near_free(43, 66)
S.features['pickups'].append({'id': 'charm', 'item': 'lost_charm', 'tx': cx_, 'ty': cy_})
for k, (x, y, item) in enumerate([(38, 64, 'red_berry'), (64, 40, 'ember_pepper'), (25, 26, 'arrow'), (80, 60, 'ember_pepper')]):
    tx, ty = S.near_free(x, y, S.h[y][x] if S.g[y][x] == 's' else 0)
    S.features['pickups'].append({'id': f'desert{k}', 'item': item, 'tx': tx, 'ty': ty, **({'count': 5} if item == 'arrow' else {})})
tx, ty = S.near_free(70, 15, 48)
S.features['chests'].append({'id': 'mesa', 'tx': tx, 'ty': ty, 'reward': 'item', 'item': 'hunter_bow'})
S.features['landmarks'].append({'id': 'mesa', 'name': '大岩', 'tx': 70, 'ty': 18, 'always': False})
taken = {(o['tx'], o['ty']) for lst in S.features.values() for o in lst if isinstance(o, dict) and 'tx' in o}
S.features['envObjects'] = [{'type': 'cactus', 'tx': x, 'ty': y} for (x, y) in cacti if (x, y) not in taken and x not in CAUSEWAY]
S.extra = {'climate': 'dry', 'bundle': 'region:desert'}

# ---------------- P10.3: the east column (white peaks, whispering forest, mirror lake) ----------------
# Passes join the columns: walk off the east edge of the plains / desert (facing east) and you come
# out at the west edge of the forest / lake, and back. Within the east column the regions touch:
# a road runs from the mountains' south edge through the forest to the lake.

def carve_pass(R, rows, side):
    """A flat path from the region's west / east edge inland until it meets open ground."""
    xs = range(RW - 1, -1, -1) if side == 'east' else range(0, RW)
    for y in rows:
        for x in xs:
            if R.g[y][x] in '.s' and R.h[y][x] == 0 and abs(x - (RW - 1 if side == 'east' else 0)) > 6:
                break
            R.g[y][x] = '='; R.h[y][x] = 0
    for lst in R.features.values():
        for o in lst:
            if isinstance(o, dict) and 'tx' in o and o.get('type') not in ('cactus',) and 'ty' in o:
                assert not (o['ty'] in rows and R.g[o['ty']][o['tx']] == '=' and o['tx'] in range(RW)) or o in R.features['envObjects'], ('pass over', R.id, o)
    R.features['envObjects'] = [o for o in R.features['envObjects'] if not (o['ty'] in rows and R.g[o['ty']][o['tx']] == '=')]

def road_south(R, top=False, bottom=False):
    """The road through the east column: open the north and / or south edge at cols 45-50."""
    if top:
        for y in range(0, 8):
            for x in CAUSEWAY:
                R.g[y][x] = '='; R.h[y][x] = 0
    if bottom:
        for y in range(RH - 8, RH):
            for x in CAUSEWAY:
                R.g[y][x] = '='; R.h[y][x] = 0
    for y in range(RH):
        x = int(47 + 4 * math.sin(y / 9))
        for dx in (0, 1, 2):
            if R.g[y][x + dx] in '.T#' and R.h[y][x + dx] == 0: R.g[y][x + dx] = '='

def rocks_and_trees(R, rock, tree, seed, tree_lvls=(0,)):
    for y in range(RH):
        for x in range(RW):
            if R.g[y][x] != '.': continue
            if R.h[y][x] in tree_lvls and hsh(x, y, seed) < tree: R.g[y][x] = 'T'
            elif hsh(x, y, seed + 1) < rock: R.g[y][x] = '#'

# 白嶺山脈: snowfields rising in steps to a summit; cold all year (it snows instead of raining).
M = Region('mountains', '白嶺山脈', 71)
M.base = '.'
M.land(3)
M.plateau(48, 40, 34, 26, 16, 72)
M.plateau(50, 36, 24, 18, 32, 73)
M.plateau(52, 32, 15, 11, 48, 74)
M.plateau(53, 30, 7, 5, 64, 75)
M.plateau(18, 72, 10, 8, 16, 76)
M.water(78, 70, 7, 5, 77)  # a cold tarn
road_south(M, bottom=True)
for y in range(RH - 30, RH):  # the road climbs nowhere: keep it in the valley
    for x in range(44, 52):
        if M.g[y][x] == '=': M.h[y][x] = 0
rocks_and_trees(M, 0.03, 0.04, 78, (0, 16))
M.features['checkpoints'].append({'id': 'mountains', **dict(zip(('tx', 'ty'), M.near_free(47, 86)))})
tx, ty = M.near_free(53, 30, 64)
M.features['chests'].append({'id': 'summit', 'tx': tx, 'ty': ty, 'reward': 'money', 'money': 150})
M.features['landmarks'].append({'id': 'summit', 'name': '白嶺の頂', 'tx': 53, 'ty': 30, 'always': False})
for (x, y, lvl) in [(30, 50, 16), (40, 62, 16), (50, 26, 48)]:
    tx, ty = M.near_free(x, y, lvl)
    M.features['enemies'].append({'kind': 'archer', 'tx': tx, 'ty': ty})
tx, ty = M.near_free(20, 78, 16)
M.features['enemies'].append({'kind': 'beast', 'tx': tx, 'ty': ty})
for k, (x, y, item, lvl) in enumerate([(40, 70, 'ember_pepper', 0), (60, 56, 'ember_pepper', 16), (26, 60, 'arrow', 16), (70, 24, 'swift_herb', 0)]):
    tx, ty = M.near_free(x, y, lvl)
    M.features['pickups'].append({'id': f'mountains{k}', 'item': item, 'tx': tx, 'ty': ty, **({'count': 5} if item == 'arrow' else {})})
M.extra = {'climate': 'cold', 'bundle': 'region:mountains', 'col': 1}

# 囁きの森: a deep forest with bog pools; narrow paths, a thicket hiding a chest. It burns well.
F = Region('forest', '囁きの森', 81)
F.base = '.'
F.land(3)
for (cx, cy, rx, ry, sd) in [(24, 30, 6, 4, 82), (66, 62, 7, 5, 83), (38, 78, 5, 3, 84), (74, 22, 4, 3, 85)]:
    F.water(cx, cy, rx, ry, sd)
F.plateau(20, 64, 9, 7, 16, 86)
road_south(F, top=True, bottom=True)
rocks_and_trees(F, 0.01, 0.42, 87, (0, 16))
# A winding side path east from the road, and a clearing with the forest's great tree.
for x in range(10, 47):
    y = int(52 + 3 * math.sin(x / 5))
    for dy in (0, 1):
        if F.g[y + dy][x] in '.T': F.g[y + dy][x] = '='
for y in range(40, 49):
    for x in range(68, 80):
        if F.g[y][x] in '.T#': F.g[y][x] = '.'
F.features['landmarks'].append({'id': 'great_tree', 'name': '囁きの大樹', 'tx': 74, 'ty': 44, 'always': False})
F.features['checkpoints'].append({'id': 'forest', **dict(zip(('tx', 'ty'), F.near_free(12, 53)))})
tx, ty = F.near_free(82, 76)
F.features['chests'].append({'id': 'thicket', 'tx': tx, 'ty': ty, 'reward': 'money', 'money': 120})
for (x, y, kind) in [(30, 40, 'beast'), (58, 70, 'beast'), (84, 30, 'beast'), (40, 20, 'archer'), (20, 64, 'archer')]:
    tx, ty = F.near_free(x, y, 16 if (x, y) == (20, 64) else 0)
    F.features['enemies'].append({'kind': kind, 'tx': tx, 'ty': ty})
for k, (x, y, item) in enumerate([(16, 44, 'mushroom'), (34, 60, 'mushroom'), (60, 30, 'mushroom'), (80, 58, 'red_berry'), (52, 86, 'arrow')]):
    tx, ty = F.near_free(x, y)
    F.features['pickups'].append({'id': f'forest{k}', 'item': item, 'tx': tx, 'ty': ty, **({'count': 5} if item == 'arrow' else {})})
F.extra = {'climate': 'temperate', 'bundle': 'region:forest', 'col': 1}

# 鏡湖と群島: a great lake dotted with islets; swim between them. A star shard waits on the far one.
L = Region('lake', '鏡湖と群島', 91)
L.base = '.'
L.land(3)
L.water(50, 50, 34, 30, 92)
ISLETS = [(34, 40, 5, 4), (58, 34, 4, 3), (66, 56, 6, 4), (44, 62, 4, 3), (74, 40, 3, 3)]
for (cx, cy, rx, ry) in ISLETS:
    for y in range(RH):
        for x in range(RW):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d < 1: L.g[y][x] = '.' if d < 0.55 else 's'; L.h[y][x] = 0
for y in range(RH):  # sandy shores around the lake
    for x in range(RW):
        if L.g[y][x] == '.' and any(0 <= y + dy < RH and 0 <= x + dx < RW and L.g[y + dy][x + dx] == '~' for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
            L.g[y][x] = 's'
road_south(L, top=True)
for y in range(8, 22):  # the road from the forest reaches the north shore
    for x in range(45, 51):
        if L.g[y][x] == '~': L.g[y][x] = '='
rocks_and_trees(L, 0.01, 0.06, 93)
L.features['landmarks'].append({'id': 'mirror_lake', 'name': '鏡湖', 'tx': 50, 'ty': 50, 'always': False})
L.features['checkpoints'].append({'id': 'lake', **dict(zip(('tx', 'ty'), L.near_free(10, 47)))})
tx, ty = L.near_free(74, 40)
L.features['chests'].append({'id': 'far_islet', 'tx': tx, 'ty': ty, 'reward': 'item', 'item': 'star_shard'})
for (x, y) in [(34, 40), (66, 56)]:
    tx, ty = L.near_free(x, y)
    L.features['enemies'].append({'kind': 'archer', 'tx': tx, 'ty': ty})
for (x, y) in [(14, 70), (80, 80)]:
    tx, ty = L.near_free(x, y)
    L.features['enemies'].append({'kind': 'beast', 'tx': tx, 'ty': ty})
for k, (x, y, item) in enumerate([(58, 34, 'red_berry'), (44, 62, 'swift_herb'), (12, 30, 'red_berry'), (84, 66, 'arrow')]):
    tx, ty = L.near_free(x, y)
    L.features['pickups'].append({'id': f'lake{k}', 'item': item, 'tx': tx, 'ty': ty, **({'count': 5} if item == 'arrow' else {})})
L.extra = {'climate': 'temperate', 'bundle': 'region:lake', 'col': 1}

# P10.4: the four cores of the murk, each in an open arena of its region.
F.arena('core_forest', 'root', 66, 38, 16, 12)          # the clearing of the great tree
M.arena('core_mountains', 'frost', 60, 44, 16, 11, 16)  # a snowfield shelf below the summit
S.arena('core_desert', 'sand', 72, 76, 16, 12)          # the dunes south-east
L.arena('core_lake', 'storm', 60, 78, 18, 10)           # the south shore
for R in (F, M, S, L):
    for b in R.features['bosses']:
        R.features['landmarks'].append({'id': b['id'], 'name': '澱の核', 'tx': b['tx'], 'ty': b['ty'], 'always': False})

# ---------------- P10.5: three more trials, and a dungeon under the mountains ----------------
# Each puzzle room can be solved in at least two ways (tests/unit/trials2.test.js).

# 双火の試練 (forest): two sconces must both burn. Fire arrows through the braziers, or the fire blade.
F.puzzle_box('trial_twin', '双火の試練', 4)
F.partition(8, 'trial_twin')
F.features['chests'].append({'id': 'trial_twin', 'tx': 104, 'ty': 6, 'reward': 'money', 'money': 120})
F.obj('brazier', 100, 11); F.obj('sconce', 102, 11)
F.obj('brazier', 108, 13); F.obj('sconce', 106, 13)
F.switch('twin-a', 'sconce', 102, 11, 'trial_twin', 'fire', ['fire'])
F.switch('twin-b', 'sconce', 106, 13, 'trial_twin', 'fire', ['fire'])
F.pillar_gate('trial_twin', '双火の試練', (40, 46), 4)

# 暗がりの試練 (desert, a dark room): light on the sensor AND weight on the plate at once.
S.puzzle_box('trial_dark', '暗がりの試練', 4, dark=True)
S.partition(8, 'trial_dark')
S.features['chests'].append({'id': 'trial_dark', 'tx': 104, 'ty': 6, 'reward': 'money', 'money': 120})
S.switch('dark-sensor', 'sensor', 105, 10, 'trial_dark', 'a', ['light'])
S.obj('brazier', 100, 11); S.obj('sconce', 107, 11)
S.switch('dark-plate', 'plate', 99, 13, 'trial_dark', 'a', ['weight'])
S.obj('crate', 104, 13)
S.pillar_gate('trial_dark', '暗がりの試練', (30, 60), 4)

# 水鏡の試練 (lake): the switches are across a water channel; any one opens the ring of doors
# around the prize. A fire arrow over the water / swim across to the plate / 共鳴 on the stone.
L.puzzle_box('trial_water', '水鏡の試練', 4)
for y in (10, 11):
    for X in range(99, 110):
        L.sg(X, y, '~')
L.features['chests'].append({'id': 'trial_water', 'tx': 101, 'ty': 14, 'reward': 'money', 'money': 120})
for (X, y) in [(101, 13), (101, 15), (100, 14), (102, 14)]:
    L.obj('door', X, y, link='trial_water')
for (X, y) in [(100, 13), (102, 13), (100, 15), (102, 15)]:
    L.sg(X, y, '#')
L.obj('brazier', 106, 14)
L.obj('sconce', 106, 7)
L.switch('water-sconce', 'sconce', 106, 7, 'trial_water', 'fire', ['fire'])
L.switch('water-plate', 'plate', 103, 7, 'trial_water', 'weight', ['weight'])
L.obj('stone', 109, 6)
L.switch('water-stone', 'stone', 109, 6, 'trial_water', 'resonance', ['resonance', 'shock'])
L.pillar_gate('trial_water', '水鏡の試練', (14, 58), 4)

# 白嶺の坑道 (the dungeon): three floors under the mountains, stairs between them.
MINE = [4, 22, 40]
M.puzzle_box('mine_1', '白嶺の坑道 地下1階', MINE[0], dark=True)
M.puzzle_box('mine_2', '白嶺の坑道 地下2階', MINE[1])
M.puzzle_box('mine_3', '白嶺の坑道 地下3階', MINE[2])
# 1F (dark): light the sensor — a light orb, or a fire arrow through the brazier onto the sconce.
y0 = MINE[0]
M.partition(y0 + 4, 'mine_1')
M.switch('mine1-sensor', 'sensor', 105, y0 + 6, 'mine_1', 'a', ['light'])
M.obj('brazier', 100, y0 + 7); M.obj('sconce', 107, y0 + 7)
# 2F: electricity — strike the crystal (sparks run along the metal floor to the stone), or 共鳴.
y0 = MINE[1]
M.partition(y0 + 4, 'mine_2')
for X in range(101, 110):
    M.sg(X, y0 + 8, 'm')
M.obj('crystal', 100, y0 + 8)
M.obj('stone', 109, y0 + 7)
M.switch('mine2-stone', 'stone', 109, y0 + 7, 'mine_2', 'a', ['resonance', 'shock'])
# 3F: two plates at once — a crate (念動 or sword pushes) on one, the player on the other.
y0 = MINE[2]
M.partition(y0 + 4, 'mine_3')
M.obj('crate', 104, y0 + 9)
M.switch('mine3-west', 'plate', 99, y0 + 9, 'mine_3', 'a', ['weight'])
M.switch('mine3-east', 'plate', 109, y0 + 7, 'mine_3', 'a', ['weight'])
M.features['chests'].append({'id': 'mine', 'tx': 104, 'ty': y0 + 2, 'reward': 'item', 'item': 'star_shard'})
# Stairs: up from the far side of 1F / 2F to the next floor; down from its south end back up.
for k in (0, 1):
    a, b = MINE[k], MINE[k + 1]
    M.obj('stairs', 104, a + 2)
    M.features['warps'].append({'id': f'mine{k + 1}-down', 'tx': 104, 'ty': a + 2, 'facing': 'up', 'toTx': 104, 'toTy': b + 11})
    M.features['warps'].append({'id': f'mine{k + 2}-up', 'tx': 104, 'ty': b + 12, 'facing': 'down', 'toTx': 104, 'toTy': a + 3})
# The way in: a dark opening in a cliff of the mountains (walk up into it).
def cliff_door(R, near):
    x0, y0_ = near
    for d in range(0, 20):
        for y in range(y0_ - d, y0_ + d + 1):
            for x in range(x0 - d, x0 + d + 1):
                if 2 < y < RH - 2 and 2 < x < RW - 2 and R.free(x, y) and R.free(x, y + 1, R.h[y][x]) and R.h[y - 1][x] >= R.h[y][x] + 16 and R.g[y][x] != '=':
                    return x, y
    raise AssertionError(('no cliff', R.id, near))
mx, my = cliff_door(M, (30, 66))
M.features['warps'].append({'id': 'mine-in', 'tx': mx, 'ty': my, 'facing': 'up', 'toTx': 104, 'toTy': MINE[0] + 11, 'reveal': True})
M.features['warps'].append({'id': 'mine-out', 'tx': 104, 'ty': MINE[0] + 12, 'facing': 'down', 'toTx': mx, 'toTy': my + 1})
M.features['landmarks'].append({'id': 'mine', 'name': '白嶺の坑道', 'tx': mx, 'ty': my, 'always': False})

# ---------------- v1.0 (C6): 淀みの源, in the desert's strip of rooms (rows below the dark trial) ----------------
# The island's strip is full (rows 2-69) and making the island taller would shift every region below
# it (and break saves), so the source lives in the desert's strip, in the same west column as the
# island's beach. The small 星環 on the beach (gen_island.py) leads into the antechamber; the
# antechamber's way out leads back to the sand in front of that ring.
#
#   antechamber (rows 20-33): a record stone; walk north into the opening to enter the arena
#   arena       (rows 36-57): the inverted ring floats in the middle; four seats (座) around it
#
# Seats (each takes at least two ways, at least one without any 星環 ability; tests/unit/finalBoss.test.js):
#   fire      sconce (100,40): a fire arrow shot north through the brazier at (100,44) / the fire blade
#   light     sensor (108,39): a light orb (灯火) / a fire arrow shot north through the brazier at (108,43)
#             sets the grass under the north wall (107-109,37) alight. 3+ tiles from every brazier and
#             sconce, so it is never lit from the start and the fire seat never lights it too.
#   weight    plate  (99,54) with a crate at (101,54): push it there with the sword / 念動 / stand on it.
#             The ring floats in rows 40-45 only: it never reaches the plate (and never counts as weight).
#   resonance stone  (109,53): strike the crystal at (106,54) (the current runs along the metal floor
#             under the stone) / 共鳴
ANTE = 20
S.puzzle_box('source_gate', '星環の前室', ANTE)
S.features['checkpoints'].append({'id': 'source', 'tx': 104, 'ty': ANTE + 7})  # on the way through: touched in passing
# A quiver of arrows that comes back a minute after it is taken: the fire and light seats' ways
# without abilities use fire arrows (2+ a round), so nobody runs out at the source.
S.features['pickups'].append({'id': 'source_arrows', 'item': 'arrow', 'tx': 101, 'ty': ANTE + 9, 'count': 10, 'regrowMs': 60_000})
# Back out: walk down from the south end; you come out on the sand in front of the beach ring.
S.extra['passes'] = [{'id': 'source-out', 'tx': 104, 'ty': ANTE + 12, 'facing': 'down', 'to': {'region': 'island', 'tx': 42, 'ty': 68}}]
AR0, AR1 = 36, 57  # the arena's walls (top) and its line of rocks (bottom)
for y in range(AR0, AR1 + 3):
    for X in range(98, 111):
        S.sg(X, y, 'u', 48)
for y in range(AR0 + 1, AR1 + 3):
    for X in range(99, 110):
        S.sg(X, y, 'u', 0)
for X in range(99, 110):
    S.sg(X, AR1, '#')
S.features['areas'].append({'id': 'source_arena', 'name': '淀みの源', 'tx': 98, 'ty': AR0, 'tw': 13, 'th': AR1 - AR0 + 1})
# Into the arena from the north end of the antechamber (a dark opening in its wall), and back.
S.features['warps'].append({'id': 'source-arena-in', 'tx': 104, 'ty': ANTE + 1, 'facing': 'up', 'toTx': 104, 'toTy': AR1 - 2})
S.features['warps'].append({'id': 'source-arena-out', 'tx': 104, 'ty': AR1 - 1, 'facing': 'down', 'toTx': 104, 'toTy': ANTE + 2})
# Fire.
S.obj('sconce', 100, 40); S.obj('brazier', 100, 44)
S.switch('source-fire', 'sconce', 100, 40, 'source', 'fire', ['fire'])
# Light: the grass under the north wall catches the fire arrows.
for X in (107, 108, 109):
    S.sg(X, AR0 + 1, '.')
S.obj('brazier', 108, 43)
S.switch('source-light', 'sensor', 108, 39, 'source', 'light', ['light'])
# Weight.
S.obj('crate', 101, 54)
S.switch('source-weight', 'plate', 99, 54, 'source', 'weight', ['weight'])
# Resonance.
for X in (107, 108, 109):
    S.sg(X, 54, 'm')
S.obj('crystal', 106, 54)
S.obj('stone', 109, 53)
S.switch('source-echo', 'stone', 109, 53, 'source', 'resonance', ['resonance', 'shock'])
for sw in S.features['switches']:
    if sw['link'] == 'source': sw['seat'] = True
S.extra['finalBoss'] = {
    'id': 'source', 'tx': 104, 'ty': 43,
    'arena': {'tx': 99, 'ty': AR0 + 1, 'tw': 11, 'th': AR1 - AR0 - 1},  # wakes when the player is in here
    'roam': {'tx': 102, 'ty': 40, 'tw': 5, 'th': 6},                    # and floats only in here
    'seats': ['source-fire', 'source-light', 'source-weight', 'source-echo'],
    'crate': {'tx': 101, 'ty': 54},
    'grass': [{'tx': X, 'ty': AR0 + 1} for X in (107, 108, 109)],  # the wave makes it whole again
}
# The rules the spec sets for the seats (C6).
def tiles(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
_fires = [(o['tx'], o['ty']) for o in S.features['envObjects'] if o['type'] in ('brazier', 'sconce') and 98 <= o['tx'] <= 110 and AR0 <= o['ty'] <= AR1]
assert all(tiles((108, 39), f) >= 3 for f in _fires), 'the light seat must be 3+ tiles from braziers and sconces'
_roam = S.extra['finalBoss']['roam']
assert not (_roam['tx'] - 3 <= 99 <= _roam['tx'] + _roam['tw'] + 2 and _roam['ty'] - 3 <= 54 <= _roam['ty'] + _roam['th'] + 2), 'the plate is out of the ring\'s reach'

# The passes between the columns.
PASS_PF = range(52, 55)
PASS_SL = range(46, 49)
carve_pass(P, PASS_PF, 'east'); carve_pass(F, PASS_PF, 'west')
carve_pass(S, PASS_SL, 'east'); carve_pass(L, PASS_SL, 'west')
P.extra['passes'] = [{'id': 'pass-forest', 'tx': RW - 1, 'ty': 53, 'facing': 'right', 'to': {'region': 'forest', 'tx': 1, 'ty': 53}}]
F.extra['passes'] = [{'id': 'pass-plains', 'tx': 0, 'ty': 53, 'facing': 'left', 'to': {'region': 'plains', 'tx': RW - 2, 'ty': 53}}]
S.extra['passes'] = [{'id': 'pass-lake', 'tx': RW - 1, 'ty': 47, 'facing': 'right', 'to': {'region': 'lake', 'tx': 1, 'ty': 47}}] + S.extra.get('passes', [])
L.extra['passes'] = [{'id': 'pass-desert', 'tx': 0, 'ty': 47, 'facing': 'left', 'to': {'region': 'desert', 'tx': RW - 2, 'ty': 47}}]

# ---------------- v1.0: the new enemies (docs/enemy/ENEMY_BOSS_DESIGN.md 2.3, 2.4) ----------------
# Added after everything else and at the end of each region's list, so nothing placed before moves.
# 澱だまり (slime): by the forest's bog pools, and in the dark first floor of 白嶺の坑道.
for (x, y) in [(24, 36), (60, 69), (38, 83), (74, 28)]:
    tx, ty = F.near_free(x, y)
    F.features['enemies'].append({'kind': 'slime', 'tx': tx, 'ty': ty})
for (X, y) in [(101, MINE[0] + 10), (108, MINE[0] + 9)]:
    assert M.eg[y][X - 96] == 'u' and not any(o.get('tx') == X and o.get('ty') == y for lst in M.features.values() for o in lst if isinstance(o, dict)), ('mine slime', X, y)
    M.features['enemies'].append({'kind': 'slime', 'tx': X, 'ty': y})
# 遺跡の番兵 (sentinel): by the ruin pillar of 暗がりの試練 and under the 大岩 in the desert, and on the
# second floor of the mine (where the crystal's sparks can reach it on the metal floor).
for (x, y) in [(34, 62), (62, 36)]:
    tx, ty = S.near_free(x, y)
    S.features['enemies'].append({'kind': 'sentinel', 'tx': tx, 'ty': ty})
X, y = 103, MINE[1] + 6
assert M.eg[y][X - 96] == 'u', ('mine sentinel', X, y)
M.features['enemies'].append({'kind': 'sentinel', 'tx': X, 'ty': y})
# --- v1.0 (docs/story/V1_STORY_PROPOSAL.md C4): the new people. Placed last, on free tiles, so nothing
# placed before them moves (saves name things by place; tests/unit/compat.test.js). ---
# The princess's 写し身 (see-through) by the record stone of each region: there once she has been met
# on the beach, until the source is purified / the ending is seen. Every princess is drawn from
# npc.princess.* (art). Her talk range is short (18 px): the player comes back to life just south of
# the stone, diagonally from her (about 23 px), and an attack there should swing, not talk.
PRINCESS_REACH = 18
PRINCESS_IF = [{'flag': 'princess_met'}, {'flag': 'source_purified', 'is': False}, {'flag': 'ending_seen', 'is': False}]
def beside_stone(R):
    """A free tile right beside the region's record stone, on its level (off the road when it can be)."""
    cp = R.features['checkpoints'][0]
    lvl = R.h[cp['ty']][cp['tx']]
    spots = [(cp['tx'] + dx, cp['ty'] + dy) for (dx, dy) in ((1, 0), (-1, 0), (1, 1), (-1, 1), (0, 1), (1, -1), (-1, -1))]
    for road_ok in (False, True):
        for (x, y) in spots:
            if R.free(x, y, lvl) and (road_ok or R.g[y][x] != '='): return x, y
    raise AssertionError(('no tile beside the stone', R.id))
for R in (P, S, M, F, L):
    x, y = beside_stone(R)
    R.features['npcs'].append({'id': f'princess_{R.id}', 'name': '星環の姫', 'dialogue': 'princess', 'look': 9, 'art': 'princess', 'tx': x, 'ty': y, 'stay': True, 'reach': PRINCESS_REACH, 'if': PRINCESS_IF, 'ghost': True})
def village_spot(x, y):
    assert P.free(x, y, 0) and P.g[y][x] == '.', ('village spot taken', x, y)
    return {'tx': x, 'ty': y}
# In 風見の村: the woman east of the cook's house, the smith west of the guard (a village anvil is for later,
# C13), and after the ending the princess in front of the inn (beside its door; she stays there, off the doorstep).
P.features['npcs'] += [
    {'id': 'woman', 'name': '村の女性', 'dialogue': 'woman', 'look': 6, **village_spot(29, 14)},
    {'id': 'smith', 'name': '鍛冶職人', 'dialogue': 'smith', 'look': 7, **village_spot(34, 18)},
    {'id': 'princess_home', 'name': '星環の姫', 'dialogue': 'princess', 'look': 9, 'art': 'princess', **village_spot(20, 22), 'stay': True, 'if': [{'flag': 'ending_seen'}]},
]
# v1.0 (C10): once the source is purified the princess stands before the ring in its arena, herself (not a
# 写し身), and speaks the ending; gone once the ending has been seen.
_end = (104, 46)  # south of where the ring floats (rows 40-45), on the arena floor
assert S.eg[_end[1]][_end[0] - 96] == 'u' and S.eh[_end[1]][_end[0] - 96] == 0, 'princess_end floor'
assert not any(o.get('tx') == _end[0] and o.get('ty') == _end[1] for lst in S.features.values() for o in lst if isinstance(o, dict)), 'princess_end spot taken'
S.features['npcs'].append({'id': 'princess_end', 'name': '星環の姫', 'dialogue': 'ending', 'look': 9, 'art': 'princess', 'tx': _end[0], 'ty': _end[1], 'stay': True,
                           'if': [{'flag': 'source_purified'}, {'flag': 'ending_seen', 'is': False}]})
# The traveller rests on the plains side of the pass to the forest.
assert P.free(88, 51, 0) and P.g[51][88] == '.', 'traveller spot'
P.features['npcs'].append({'id': 'traveller', 'name': '旅人', 'dialogue': 'traveller', 'look': 8, 'tx': 88, 'ty': 51})

# v1.0 (terrain inspection, final QA): a rock right north of a tree stood under the tree's crown (the
# pine is 30 px tall and covers most of the tile behind it). Done last, so nothing placed before
# moves. Trees stay where they are (saves name a burnt tree by its place); rocks never change, so
# they never enter a save (src/game/world/worldDiff.js) and can move. Each goes to the nearest grass
# tile where it closes no path (the open tiles beside it still reach each other round it) and stands
# under no crown, away from everything the regions place, the boss arenas and the road.
def move_rocks_under_crowns(R):
    def feature_near(x, y):
        for lst in R.features.values():
            for o in lst:
                if not isinstance(o, dict): continue
                if 'tx' in o and 'tw' not in o and max(abs(o['tx'] - x), abs(o['ty'] - y)) <= 2: return True
                a = o.get('arena') or (o if 'tw' in o else None)
                if a and a['tx'] - 1 <= x < a['tx'] + a['tw'] + 1 and a['ty'] - 1 <= y < a['ty'] + a['th'] + 1: return True
                if o.get('type') == 'house' and abs(x - o['tx']) <= 2 and -1 <= o['ty'] - y <= 3: return True
        return False
    WALK = '.s='
    def joined_without(x, y, sides):
        """Whether the open sides of (x, y) still reach each other (on land, level by level) with a rock
        there: then no path that crossed the tile is cut (it can go round). Searched within 12 tiles."""
        start, goals = sides[0], set(sides[1:])
        seen, todo = {start}, [start]
        while todo and goals:
            cx, cy = todo.pop()
            goals.discard((cx, cy))
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in seen or (nx, ny) == (x, y) or max(abs(nx - x), abs(ny - y)) > 12: continue
                if not (0 <= nx < RW and 0 <= ny < RH) or R.g[ny][nx] not in WALK or R.h[ny][nx] != R.h[cy][cx]: continue
                seen.add((nx, ny)); todo.append((nx, ny))
        return not goals
    def open_spot(x, y):
        if not (1 <= x < RW - 1 and 1 <= y < RH - 1) or R.g[y][x] != '.': return False
        if R.g[y + 1][x] == 'T': return False  # (under another crown)
        if feature_near(x, y): return False
        lvl = R.h[y][x]
        sides = [(x + dx, y + dy) for (dx, dy) in ((0, -1), (1, 0), (0, 1), (-1, 0)) if R.g[y + dy][x + dx] in WALK and R.h[y + dy][x + dx] == lvl]
        if len(sides) < 2: return True  # a dead end (or closed in): nothing passes through
        return joined_without(x, y, sides)
    moved = []
    for y in range(RH - 1):
        for x in range(RW):
            if R.g[y][x] != '#' or R.g[y + 1][x] != 'T': continue
            spot = None
            for d in range(1, 9):
                ring = [(x + dx, y + dy) for dy in range(-d, d + 1) for dx in range(-d, d + 1) if max(abs(dx), abs(dy)) == d]
                ring.sort(key=lambda p: (abs(p[0] - x) + abs(p[1] - y), p[1], p[0]))
                spot = next((p for p in ring if open_spot(*p)), None)
                if spot: break
            assert spot, ('no place for the rock', R.id, x, y)
            R.g[y][x] = '.'
            R.g[spot[1]][spot[0]] = '#'
            moved.append(((x, y), spot))
    return moved
for R in (P, S, M, F, L):
    _moved = move_rocks_under_crowns(R)
    if _moved: print('rocks moved from under crowns:', R.id, len(_moved))
    assert not any(R.g[y][x] == '#' and R.g[y + 1][x] == 'T' for y in range(RH - 1) for x in range(RW)), ('rock under a crown', R.id)

regions = [P.out(), S.out(), M.out(), F.out(), L.out()]
for r in regions:
    assert len(r['ground']) == RH and all(len(row) == RW + EW for row in r['ground'])
    walk = lambda x, y: r['ground'][y][x] in '.s=wum' and not any(o['tx'] == x and o['ty'] == y for o in r['envObjects'] if o['type'] not in ('mat', 'stairs'))
    for w in r.get('passes', []):
        if w['facing'] in ('left', 'right'):
            assert r['ground'][w['ty']][w['tx']] in '=.s', ('pass blocked', r['id'], w)
            assert r['ground'][w['ty']][w['tx'] + (-1 if w['facing'] == 'right' else 1)] in '=.s', ('pass approach blocked', r['id'], w)
        else:  # v1.0: a doorway to another region (the source's antechamber back to the island)
            assert walk(w['tx'], w['ty']), ('doorway blocked', r['id'], w)
    for w in r['warps']:
        assert walk(w['tx'], w['ty']), ('warp tile blocked', r['id'], w)
        assert walk(w['toTx'], w['toTy']), ('warp arrival blocked', r['id'], w)
    for c in r['chests'] + r['checkpoints']:
        assert r['ground'][c['ty']][c['tx']] in '.s=u', (r['id'], c)

out = """// @ts-check
// Region templates south of the first island (P8). GENERATED by tools/gen_world.py: edit the script.
// Each region is 96 x 96 tiles plus a 16-column strip of rooms to the east (P10.1); coordinates are local to the region (src/game/world/world.js
// stacks the regions under the island and offsets them).

/** @typedef {{ id: string, tx: number, ty: number, facing: 'up' | 'down' | 'left' | 'right', to: { region: string, tx: number, ty: number }, if?: import('../features.js').FlagCondition[] }} PassDef */
/** @typedef {import('../tilemap.js').IslandDef & { id: string, name: string, climate: 'temperate' | 'dry' | 'cold', bundle: string, col?: number, passes?: PassDef[], finalBoss?: import('../../entities/finalBoss.js').FinalBossDef }} RegionDef */

/** @type {RegionDef[]} */
export const REGIONS = %s;
""" % json.dumps(regions, ensure_ascii=False, separators=(",", ":"))
path = os.path.join(os.path.dirname(__file__), '..', 'src', 'game', 'world', 'maps', 'regions.js')
with open(path, 'w') as f:
    f.write(out)
print('wrote', path, [(r['id'], len(r['enemies']), len(r['envObjects'])) for r in regions])
