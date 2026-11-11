"""Ground v2 file names: the generator works with short internal names (g2.<ground>.<x>); the files use
the GAME's keys, because a v2 group replaces the v1 terrain group entirely (every v1 key must exist in
src/art-release-v2/terrain, redrawn or copied):

  ground tile     <prefix>.<n>            n = 0-15, the edge-type index N + 2E + 4S + 8W (wang.py; 0 = the calm
                                           base); grounds whose v1 key has no number (tile.sand, tile.path,
                                           tile.ruin): <prefix> = n 0, <prefix>.<n> n = 1-15
  macro pieces    <prefix>.macro.<q>, <prefix>.macro2.<q>  (2x2, q = 0 NW, 1 NE, 2 SW, 3 SE)
                  <prefix>.macro3.<q>                      (3x3, q = 0-8 in reading order)
  overlay         <prefix>.edge.<mask>.<v> mask 1-14 (NW 1, NE 2, SW 4, SE 8), v = 0 / 1
  seasons         autumn.<...> / winter.<...> in front of any of the above
  water           tile.water.<f>, tile.water.v1.<f>             shallow, frames 0-3
                  tile.water.deep.<f>, tile.water.deep.v1.<f>   deep
                  tile.water.deep.edge.<mask>.<f>               deep over shallow
                  tile.water.foam.<mask>.<f>                    foam (mask = land corners)
"""

PREFIX = {"grass": "tile.grass", "plains": "plains.grass", "lake": "lake.grass", "moss": "forest.grass",
          "snow": "mountains.snow", "sand": "tile.sand", "dsand": "desert.sand", "path": "tile.path", "ruin": "tile.ruin"}
SINGLE = {"sand", "path", "ruin"}  # v1 key without a number


def final_name(internal):
    season = ""
    k = internal
    if k.startswith(("autumn.", "winter.")):
        season, k = k.split(".", 1)
        season += "."
    parts = k.split(".")  # g2, ground, ...
    if parts[1] == "water":
        depth, rest = parts[2], parts[3:]
        if depth in ("shallow", "deep"):
            if rest[0].startswith("e"):  # g2.water.deep.e<m>.<f>
                return f"tile.water.deep.edge.{rest[0][1:]}.{rest[1]}"
            v, f = rest
            base = "tile.water" if depth == "shallow" else "tile.water.deep"
            return f"{base}.{f}" if v == "0" else f"{base}.v{v}.{f}"
        if depth == "foam":  # g2.water.foam.e<m>.<f>
            return f"tile.water.foam.{rest[0][1:]}.{rest[1]}"
    g, rest = parts[1], parts[2:]
    p = PREFIX[g]
    if rest[0].startswith("e"):
        return f"{season}{p}.edge.{rest[0][1:]}.{rest[1]}"
    if rest[0].startswith("steptwoinner"):  # round 10: step2.inner.<ne|nw>.<s>
        return f"{season}{p}.step2.inner.{rest[0][12:]}.{rest[1]}"
    if rest[0].startswith("steptwo"):  # round 10: step2.<mask>.<code>
        return f"{season}{p}.step2.{rest[0][7:]}.{rest[1]}"
    if rest[0].startswith("stepshade"):  # round 7
        return f"{season}{p}.step.shade.{rest[1]}"
    if rest[0].startswith("stepinner"):  # round 8
        return f"{season}{p}.step.inner.{rest[1]}"
    if rest[0].startswith("step"):
        return f"{season}{p}.step.{rest[0][4:]}.{rest[1]}"
    if rest[0].startswith(("macro", "dune")):
        return f"{season}{p}.{rest[0]}.{rest[1]}"
    n = rest[0]
    if g in SINGLE and n == "0":
        return f"{season}{p}"
    return f"{season}{p}.{n}"
