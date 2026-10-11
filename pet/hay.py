# part of the Pet: the haystack at the bottom of a leap of faith: two lumps, a big one and a smaller one.
# it pops up below while the mascot dives, squashes and wobbles as it lands in it, and puffs away when the
# mascot hops out (with a couple of straws left stuck on its head). each lump has a lit side and a shady side,
# straw strokes all over, stray straws sticking out, and a soft shadow. its back half goes behind the mascot
# and its front half in front, so it sits in it. no dark edges.
import math
import random

from .art import BLOCK_H, BLOCK_W, HAY_C, SHADOW
from .sprites import Stage

PALE, DEEP = "#fbe9a8", "#94691f"   # (with HAY_C: base, light straw, dark straw)
STRAYS = ((-0.62, 0.55, -1.0), (-0.35, 0.92, -0.45), (-0.08, 1.0, 0.1), (0.2, 0.97, 0.5), (0.45, 0.82, 0.9),
          (0.7, 0.5, 1.25), (-0.9, 0.15, -1.45), (0.92, 0.18, 1.5))   # (across, up, lean) of straws poking out
LUMPS = ((0.3, 0.62), (0.36, 0.56))   # (how far out, how wide) the big lump and the small one are
cells_cache = {}


def smooth(k):
    k = min(1.0, max(0.0, k))
    return k * k * (3 - 2 * k)


def hay_top(x, half, height, flip, lumpy=True):
    # how tall the pile is at x (from its middle): two lumps, a taller one and a lower one, with a dip between,
    # like a haystack in an assassin's creed game. flip = which side the taller one is on.
    u = x / half * flip
    big = max(0.0, 1 - ((u + LUMPS[0][0]) / LUMPS[0][1]) ** 2) ** 0.42   # (plump: round tops, steep sides)
    small = 0.78 * max(0.0, 1 - ((u - LUMPS[1][0]) / LUMPS[1][1]) ** 2) ** 0.42
    low = 0.55 * max(0.0, 1 - u ** 6) ** 0.5   # (the dip between them, where it sits)
    if not lumpy:   # (for the lighting: the lumps blended smoothly, so the light turns gently across the dip)
        return height * math.log(sum(math.exp(10 * v) for v in (big, small, low))) / 10
    return height * max(big, small, low) * (1 + 0.04 * math.sin(u * 23))   # (a bit lumpy)


def hay_cells(half, height, b, back, flip):
    # the pile as blocks, relative to the middle of its bottom: (x, y, w, colour) with y up from the floor.
    # each lump is lit on its left slope (pale near the top) and in shade on its right; dark along the bottom.
    key = (round(half), round(height), b, back, flip)
    if key in cells_cache:
        return cells_cache[key]
    def look(x, y):
        h = hay_top(x, half, height, flip)
        if y >= h:
            return None
        if back:
            return HAY_C[2] if y < h - 2 * b else HAY_C[0]
        if y < b:
            return DEEP
        # light from the top left. how the outline slopes there says which way the hay faces: rising to the
        # right faces the light, falling away is in shade. that matters most near the top and fades lower down,
        # and higher up is brighter. a checker of small nudges blends one shade into the next.
        slope = (hay_top(x + b, half, height, flip, False) - hay_top(x - b, half, height, flip, False)) / (2 * b)
        rel = y / h
        light = max(-1.0, min(1.0, slope * 1.4)) * (0.1 + 0.9 * rel) + (rel - 0.45) * 0.9
        light += 0.07 if (round(x / b) + round(y / b)) % 2 else -0.07
        if light > 0.72:
            return PALE
        if light > 0.18:
            return HAY_C[1]
        if light > -0.38:
            return HAY_C[0]
        return HAY_C[2]

    out, n = [], math.ceil(half * 1.05 / b)
    for r in range(math.ceil(height * 1.1 / b)):   # each row in runs of one colour
        y, run = r * b, None
        for i in range(-n, n + 1):
            col = look(i * b + b / 2, y + b / 2)
            if run and run[3] == col:
                run[2] += b
                continue
            if run and run[3]:
                out.append(tuple(run))
            run = [i * b, y, b, col]
        if run and run[3]:
            out.append(tuple(run))
    rng = random.Random(7 if back else 3)
    for _ in range(14 if back else 50):   # straw strokes: short, mostly flat dashes
        x = rng.uniform(-half, half)
        h = hay_top(x, half, height, flip)
        if h < 3 * b:
            continue
        y0 = rng.uniform(b, h - 2 * b)
        slope, steps = rng.uniform(-0.5, 0.5), rng.randint(2, 5)
        base = look(x, y0)
        lit = base in (HAY_C[1], PALE)
        col = (PALE if rng.random() < 0.3 else HAY_C[1]) if lit else (DEEP if rng.random() < 0.3 else HAY_C[2])
        for k in range(steps):
            cx, cy = x + k * b * (1 if slope >= 0 else -1), y0 + k * abs(slope) * b
            if cy + b < hay_top(cx + b / 2, half, height, flip):
                out.append((cx, round(cy / b) * b, b, col))
    cells_cache[key] = out
    return out


class HayMixin:
    def hay_size(self, s):
        bw, bh = max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s))
        return 15 * bw, 6 * bh, max(1, round(2 * s))   # half width, height of the front's taller lump, block

    def draw_hay(self, c, cx, base, s, layer, squash=0.0, k=1.0, sway=0.0, flip=1):
        # the pile on canvas c, the middle of its bottom at (cx, base). squash > 0 = squashed flat and wide,
        # k = how big (popping in or puffing away), sway = how far the stray straws lean (wind)
        half, height, b = self.hay_size(s)
        sx, sy = (1 + squash) * k, (1 - squash) * k
        if layer == "back":   # (the back half is a bit taller, so the lumps look round)
            height *= 1.12
        else:   # a soft shadow on the floor (every other pixel see-through)
            w = half * sx * 1.1
            c.create_rectangle(round(cx - w), round(base - b * 0.5), round(cx + w), round(base + b), fill=SHADOW,
                               outline="", stipple="gray50")
        for x, y, w, col in hay_cells(half, height, b, layer == "back", flip):
            x0, y1 = cx + x * sx, base - y * sy
            c.create_rectangle(round(x0), round(y1 - b * sy), round(x0 + max(b, w * sx)), round(y1), fill=col,
                               outline="")
        if k < 0.3:
            return
        for i, (ax, up, lean) in enumerate(STRAYS):   # stray straws poking out, leaning in the breeze
            if (abs(ax) > 0.6) == (layer == "back"):
                continue   # (the ones on top stick out of the back, behind the mascot; the side ones in front)
            ax, lean = ax * flip, lean * flip
            x0, y0 = cx + ax * half * sx, base - hay_top(ax * half, half, height, flip) * sy * up ** 0.3 + b
            ang = lean + sway * (1 if i % 2 else 0.6)
            n = 3 + i % 3
            col = HAY_C[1] if i % 3 else PALE
            for j in range(n):
                x = round(x0 + math.sin(ang) * j * b)
                y = round(y0 - math.cos(ang) * j * b)
                c.create_rectangle(x, y - b, x + b, y, fill=col, outline="")

    # ---- the pile while it isn't round the mascot: popping up below a dive, puffing away after ----
    def hay_spot(self, x, floor):
        # the dive has just started: a pile pops up where it's going to land
        self.hay_flip = random.choice((-1, 1))   # (which side the taller lump is on, this time)
        self.hay_show = {"x": x, "base": floor, "t": 0.0, "phase": "wait", "bits": []}

    def hay_tick(self, dt):
        if 0 < self.straw_t <= dt:   # the straws stuck on its head fall off
            self.spawn("straw")
        self.straw_t -= dt
        h = self.hay_show
        if h is None:
            return
        h["t"] += dt
        if h["phase"] == "wait" and not self.diving and self.hay_t <= 0:
            h["phase"], h["t"] = "gone", 0.0   # (snatched mid-dive: the pile goes away again)
        if h["phase"] == "sit" or self.hidden:
            if self.hay_stage is not None:
                self.hay_stage.hide()
            if self.hidden:
                self.hay_show = None
            return
        s = self.s()
        if h["phase"] == "gone":
            if h["t"] < dt * 1.5:   # straw flies as it goes
                for _ in range(10):
                    ang = random.uniform(math.pi * 1.05, math.pi * 1.95)
                    v = random.uniform(60, 160) * s
                    h["bits"].append([h["x"] + random.uniform(-30, 30) * s, h["base"] - random.uniform(4, 16) * s,
                                      math.cos(ang) * v, math.sin(ang) * v, random.choice(HAY_C), 0.7])
            if h["t"] > 0.8:
                self.hay_stage.hide()
                self.hay_show = None
                return
        for bit in h["bits"]:
            bit[0] += bit[2] * dt
            bit[1] += bit[3] * dt
            bit[3] += 500 * s * dt
            bit[5] -= dt
        h["bits"] = [bit for bit in h["bits"] if bit[5] > 0]
        if self.hay_stage is None:
            self.hay_stage = Stage(self.root)
        st = self.hay_stage
        if st.place(h["x"] - 110 * s, h["base"] - 110 * s, h["x"] + 110 * s, h["base"] + 12 * s):
            self.root.lift()   # (the mascot in front of it)
        c = st.canvas
        c.delete("all")
        ox, oy = st.origin
        t = h["t"]
        if h["phase"] == "wait":   # pops up with a little boing
            k, squash = min(1.0, smooth(t / 0.3) * (1 + 0.12 * math.sin(min(t, 0.6) / 0.6 * math.pi))), 0.0
        else:   # squashes as the mascot springs out, then shrinks away
            k = 1 - smooth((t - 0.25) / 0.5)
            squash = 0.25 * math.exp(-6 * t) * math.cos(14 * t)
        if k > 0.02:
            sway = math.sin(t * 2.2) * 0.15
            self.draw_hay(c, h["x"] - ox, h["base"] - oy, s, "back", squash, k, sway, self.hay_flip)
            self.draw_hay(c, h["x"] - ox, h["base"] - oy, s, "front", squash, k, sway, self.hay_flip)
        b = max(1, round(2 * s))
        for x, y, _, _, col, _ in h["bits"]:
            c.create_rectangle(round(x - ox), round(y - oy), round(x - ox + 2 * b), round(y - oy + b), fill=col,
                               outline="")

    def hay_lift(self, e, s):
        # how far up it sits in the pile, e seconds after landing: it lands deep in it, then pops up until its
        # eyes peek out over the top (its middle stays buried in the hay)
        bh = max(2, round(BLOCK_H * s))
        return round((self.hay_size(s)[1] - 3 * bh + 2 * s) * smooth((e - 0.15) / 0.3))

    def hay_squash(self, e):
        # how squashed the pile is, e seconds after landing in it: a big squash, then it wobbles back
        return 0.3 * math.exp(-7 * e) * math.cos(16 * e)

    def hay_landed(self):
        # it's in the pile: the pile is drawn round it now
        if self.hay_show:
            self.hay_show["phase"] = "sit"

    def hay_popped(self, floor):
        # out it hops: the pile it leaves behind puffs away, and a couple of straws stay stuck on its head
        self.hay_show = {"x": self.x, "base": floor, "t": 0.0, "phase": "gone", "bits": []}
        self.straw_t = random.uniform(3, 6)
