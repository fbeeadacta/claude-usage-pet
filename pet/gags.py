# part of the Pet: coding jokes it acts out on its own when it's idle (picked alongside sweeping, painting...
# in pet/idle.py): a phone call from the API, cookies, rubber duck debugging, coffee, a bug hunt, an infinite
# loop, a stack overflow of pancakes, counting sheep off by one, a fortune cookie, a merge conflict, a recursive
# mirror, a lost semicolon (found with a magnifying glass), digging up a 404 (a shovel, a hole and a chest), and a
# tiny keyboard. positions are relative to the body's top left, like particles. no dark edges.
import math
import random

from .art import (ARMS, BEETLE, BEETLE_C, BEETLE_WINGS, BULB, BULB_C, CHECK, CHECK_C, CHEST, CHEST_C, CHEST_OPEN,
    COOKIE, COOKIE_C, DIGITS, DIRT_C, DUCK, DUCK_C, EYE, FENCE, FENCE_C, FORTUNE, FORTUNE_C, GAG_C, LEFT_WAVE,
    LEGS_STAND, LEGS_STEP, MERGE_IN, MERGE_OUT, MUG, MUG_C, NET_C, ORANGE, PAGE_C, PHONE, PHONE_C, SEMI_BIG, SEMI_C,
    SEMI_SMALL, SHEEP, SHEEP_C, SHOVEL, SHOVEL_C, SPARK_C, UNDO, WAVE)
from .lines import (BUG_END, BUG_FREE, BUG_START, COFFEE_END, COFFEE_LINES, COOKIE_END, COOKIE_LINES, DIG_END,
    DIG_LINES, DUCK_END, DUCK_START, FORTUNE_END, FORTUNE_LINES, FORTUNE_START, KEY_END, KEY_LINES, KEY_UNDO,
    LOOP_END, LOOP_LINES, MERGE_END, MERGE_LINES, PANCAKE_END, PANCAKE_LINES, PANCAKE_MORE, PHONE_HELLO, PHONE_MORE,
    RECURSION_END, RECURSION_LINES, SEMI_END, SEMI_LINES, SEMI_MORE, SHEEP_DOUBT, SHEEP_END, SHEEP_MID, SHEEP_START)

GAGS = {"phone": 9.0, "cookie": 7.0, "duck": 9.0, "coffee": 8.0, "bughunt": 10.0, "loop": 7.5, "pancakes": 10.0,
        "sheep": 10.5, "fortune": 8.0, "merge": 9.0, "recursion": 8.0, "semicolon": 10.0, "dig": 10.0,
        "keyboard": 9.0}   # each one, and how long it lasts (seconds)
BITES = (1.5, 2.5, 3.5, 4.5)              # cookie bites
SIPS = ((1.5, 2.3), (4.0, 4.8))           # coffee sips (from, to)
PANCAKES, TOPPLE = 10, 6.5                 # pancakes on the stack, and when it falls over
JUMPS = (0.8, 2.2, 3.6, 5.0, 6.4)         # sheep jumping the fence (the 4th one jumps back)
FINDS = ("dig", "bughunt", "semicolon")   # the three with their own parts below (finding things)
STROKES = tuple(0.6 + 0.7 * i for i in range(6))   # shovel strokes: down, lever, up and toss
CLINK, RISE, OPEN, CLOSE = 5.0, 5.6, 6.6, 8.8      # dig: hits something, the chest comes up, opens, closes
SWINGS = (2.6, 4.6, 6.6)                            # bug net swings (the last one catches it)
SWING = 0.35                                        # how long a swing takes
LIFT, FREE = 7.4, 8.6                               # bug hunt: lifting the net up, letting the bug go
FOUND, PICKED = 5.7, 6.6                            # semicolon: under the glass, picked up


def smooth(k):
    k = min(1.0, max(0.0, k))
    return k * k * (3 - 2 * k)


def cookie_rows(bites):
    # the cookie with `bites` bites out of its left side (scalloped, like teeth marks)
    out = []
    for j, row in enumerate(COOKIE):
        edge = 2 * bites - 1 + round(abs(j - 3) * 0.5) if bites else -1
        out.append("".join("." if i < edge else ch for i, ch in enumerate(row)))
    return out


class GagsMixin:
    def gag_start(self, kind, a):
        s = self.s()
        a["dur"] = GAGS[kind]
        if kind in FINDS:
            self.finds_start(kind, a)
        elif kind == "loop":
            a["x0"] = self.x
        elif kind == "merge":
            a["pick"] = random.choice((-1, 1))
        self.tally("gags")

    # ---- helpers ----
    def beside(self, side, w, gap=4):
        # the left edge of something w wide on the floor next to it, on that side
        s, pw = self.s(), self.pet_px[0]
        return pw + gap * s if side > 0 else -gap * s - w

    def gag_bounds(self):
        # how far it may walk about during a joke (not off the end of its window)
        s = self.s()
        lo, hi = self.x_limits()
        if self.plat is not None:
            lo, hi = max(lo, self.plat_box[1] + 20 * s), min(hi, self.plat_box[3] - 20 * s)
        return lo, hi

    def gag_part(self, kind, x, y, vx, vy, life, c, g=0.0):
        self.parts.append({"kind": kind, "x": x, "y": y, "vx": vx, "vy": vy, "life": life, "c": c, "g": g})

    def gag_puff(self, x, y, n=6):
        s = self.s()
        for _ in range(n):
            self.gag_part("puff", x + random.uniform(-6, 6) * s, y + random.uniform(-4, 4) * s,
                          random.uniform(-25, 25) * s, -random.uniform(10, 30) * s, random.uniform(0.3, 0.6), 0)

    def gag_crumbs(self, x, y, colour, n=6):
        s = self.s()
        for _ in range(n):
            self.gag_part("dot", x, y, random.uniform(-40, 40) * s, -random.uniform(10, 60) * s, 0.6, colour,
                          g=350 * s)

    def gag_sparkle(self, x, y, n=6):
        s = self.s()
        for i in range(n):
            ang = i / n * 2 * math.pi
            self.gag_part("spark", x, y, math.cos(ang) * 50 * s, math.sin(ang) * 50 * s, 0.5,
                          random.randrange(len(SPARK_C)))

    # ---- every frame ----
    def gag_tick(self, kind, a, t0, t, dt, s):
        side = a["side"]
        pw, ph = self.pet_px

        def cue(at):   # true once, on the frame that passes `at`
            return t0 <= at < t

        def say(lines):
            self.say(self.pick(lines), force=True)

        if kind in FINDS:
            return self.finds_tick(kind, a, t0, t, dt, s, cue, say)
        if kind == "phone":
            if cue(0.05) or cue(0.75):
                self.play("ring")
            if cue(1.6):
                say(PHONE_HELLO)
            if cue(4.6):
                say(PHONE_MORE)
            if cue(7.6):   # hangs up, and the phone goes away
                hx, hy = self.act_hand(side, 0)
                self.gag_puff(hx, hy)
        elif kind == "cookie":
            if cue(0.2):
                say(COOKIE_LINES)
            for at in BITES:
                if cue(at):   # nom
                    self.play("crunch")
                    hx, hy = self.act_hand(side, 1)
                    self.gag_crumbs(hx, hy + 4 * s, COOKIE_C["o"])
            if cue(5.4):
                self.happy_t = 1.5
                say(COOKIE_END)
        elif kind == "duck":
            dx = self.beside(side, len(DUCK[0]) * 2 * s, 8)
            if cue(0.0):
                self.play("pop")
                self.gag_puff(dx + 8 * s, ph - 6 * s)
            if cue(0.4):
                say(DUCK_START)
            if cue(4.0):   # the light goes on
                self.play("chime")
                self.happy_t = 2.5
                say(DUCK_END)
                self.gag_sparkle(pw / 2, -20 * s, 8)
            if cue(6.0):   # squeak!
                self.play("pop")
                self.gag_part("heart", dx, ph - 26 * s, 0.0, -30 * s, 0.8, 0)
            if cue(8.5):
                self.gag_puff(dx + 8 * s, ph - 6 * s)
        elif kind == "coffee":
            if cue(0.3):
                say(COFFEE_LINES)
            if random.random() < dt * 5:   # steam
                mx, my = self.mug_at(t, side)
                self.gag_part("puff", mx + random.uniform(2, 8) * s, my - 2 * s, random.uniform(-6, 6) * s,
                              -random.uniform(15, 25) * s, 0.8, 0)
            if cue(5.0):
                self.happy_t = 2.0
                say(COFFEE_END)
        elif kind == "loop":
            lo, hi = self.gag_bounds()
            amp = 16 * s
            a["x0"] = min(max(a["x0"], lo + amp), hi - amp)
            if t < 5.6:   # round and round, faster and faster
                a["ph"] = a.get("ph", 0.0) + (2.5 + t * 1.5) * dt
                self.x = a["x0"] + math.sin(a["ph"]) * amp
                self.dir = 1 if math.cos(a["ph"]) > 0 else -1
                self.step_t += dt * (1 + t * 0.4)
                if self.step_t >= 0.18:
                    self.step_t, self.step = 0.0, self.step + 1
            if cue(0.2):
                say(LOOP_LINES)
            if cue(5.6):
                self.dizzy_t = 1.8
                say(LOOP_END)
        elif kind == "pancakes":
            if cue(0.1):
                say(PANCAKE_LINES)
            if cue(TOPPLE):   # stack overflow!
                self.play("boing")
                x0 = self.beside(side, 26 * s, 6) + 13 * s
                for i in range(14):
                    self.gag_part("dot", x0 + random.uniform(-10, 10) * s, ph - random.uniform(4, 30) * s,
                                  random.uniform(-90, 90) * s, -random.uniform(40, 140) * s, 0.8,
                                  random.choice((GAG_C["cake"], GAG_C["cake2"])), g=400 * s)
                say(PANCAKE_END)
            if cue(8.2):
                say(PANCAKE_MORE)
        elif kind == "sheep":
            if cue(0.3):
                say(SHEEP_START)
            if cue(2.6):
                self.say("2...", force=True)
            if cue(4.0):
                say(SHEEP_MID)
            if cue(6.9):
                say(SHEEP_DOUBT)
            if cue(8.5):
                say(SHEEP_END)
        elif kind == "fortune":
            if cue(0.2):
                say(FORTUNE_START)
            if cue(1.2):   # crack!
                self.play("crunch")
                hx, hy = self.act_hand(side, 1)
                self.gag_crumbs(hx, hy, FORTUNE_C["o"], 8)
            if cue(2.2):
                say(FORTUNE_LINES)
            if cue(5.4):
                self.worried_t = 2.0
                say(FORTUNE_END)
            if cue(7.6):
                hx, hy = self.act_hand(side, 1)
                self.gag_puff(hx, hy)
        elif kind == "merge":
            if cue(0.3):
                say(MERGE_LINES)
            if 1 < t < 4.8 and int(t0 * 2) != int(t * 2):   # they shove at it from both sides: !
                for d in (-1, 1):
                    self.gag_part("spark", pw / 2 + d * (pw / 2 + 2 * s), 0, d * 20 * s, -40 * s, 0.4, 0)
            if cue(5.0):   # one of them gets thrown away
                self.play("pop")
                self.gag_puff(pw / 2 - a["pick"] * (pw / 2 + 16 * s), 4 * s)
            if cue(5.3):
                say(MERGE_END)
            if cue(7.6):
                self.gag_puff(pw / 2 + a["pick"] * (pw / 2 + 16 * s), 4 * s)
        elif kind == "recursion":
            if cue(0.4):
                say(RECURSION_LINES)
            if cue(4.6):
                say(RECURSION_END)
        elif kind == "keyboard":
            if cue(0.2):
                say(KEY_LINES)
            if cue(0.3) or cue(2.6):
                self.play("typing")
            kx = self.beside(side, 34 * s, 4)
            if t < 4.5 and random.random() < dt * 16:   # bits of code flying up
                self.gag_part("dot", kx + random.uniform(0, 34) * s, ph - 10 * s, random.uniform(-15, 15) * s,
                              -random.uniform(40, 80) * s, 0.7, random.choice((GAG_C["code"], GAG_C["lit"])))
            if cue(4.6):
                say(KEY_UNDO)
            if cue(7.4):
                say(KEY_END)

    # ---- where things are ----
    def mug_at(self, t, side):
        # the mug's top left: in its hand, or up by its face for a sip
        s = self.s()
        gb = max(2, round(3 * s))
        hx, hy = self.act_hand(side, 1)
        x, y = hx - (gb if side > 0 else 5 * gb), hy - 8 * s   # (the handle, 2 blocks wide, is in its hand)
        for t1, t2 in SIPS:
            if t1 <= t <= t2:
                k = smooth(min(t - t1, t2 - t) / 0.25)
                fx, fy = self.pet_px[0] / 2 + side * 4 * s - 6 * s, 2 * s
                x, y = x + (fx - x) * k, y + (fy - y) * k
        return x, y

    # ---- how it looks ----
    def gag_pose(self, kind, t, a, side):
        # overrides for how it looks: {sink, eyes, eye_dir, eye_v, arms, legs}
        up = self.side_arm(side, 1)
        out = self.side_arm(side, 0)
        both = LEFT_WAVE[1] + WAVE[1]
        if kind in FINDS:
            return self.finds_pose(kind, t, a, side)
        if kind == "phone":
            if t < 1.4:
                return {"eyes": "open", "eye_dir": side, "eye_v": 1}
            if t < 7.6:
                return {"eyes": "happy" if int(t * 1.5) % 3 else "open", "eye_dir": 0, "arms": up}
            return {"eyes": "happy", "eye_dir": 0}
        if kind == "cookie":
            chewing = any(at <= t < at + 0.5 for at in BITES)
            return {"eyes": "closed" if chewing else "happy" if t > 5.4 else "open", "eye_dir": side, "arms": out,
                    "sink": "half" if chewing and int(t * 8) % 2 else None}
        if kind == "duck":
            if t < 4.0:   # explaining, waving its arms about
                return {"eyes": "open", "eye_dir": side, "eye_v": 1, "arms": self.side_arm(side, int(t * 3) % 2)}
            return {"eyes": "happy", "eye_dir": side, "eye_v": 0, "arms": up if t < 5 else ARMS}
        if kind == "coffee":
            sip = any(t1 <= t <= t2 for t1, t2 in SIPS)
            return {"eyes": "closed" if sip else "happy" if t > 5 else "open", "eye_dir": side, "arms": up if sip else out}
        if kind == "loop":
            if t < 5.6:
                return {"eyes": "open", "eye_dir": self.dir, "legs": LEGS_STEP if self.step % 2 else LEGS_STAND}
            return {"eyes": "closed"}
        if kind == "pancakes":
            if t < TOPPLE:   # putting pancakes on, one at a time
                return {"eyes": "open", "eye_dir": side, "eye_v": 1, "arms": self.side_arm(side, int(t / 0.55) % 2)}
            return {"eyes": "worried" if t < 8 else "open", "eye_dir": side, "eye_v": 0, "arms": both if t < 7.5 else ARMS}
        if kind == "sheep":
            sh = self.sheep_at(t, side)
            look = 0 if sh is None else (1 if sh[0] > self.pet_px[0] / 2 else -1)
            return {"eyes": "worried" if 4.0 <= t < 8.5 else "open", "eye_dir": look, "eye_v": -1 if sh else 0}
        if kind == "fortune":
            if t < 5.4:
                return {"eyes": "open", "eye_dir": side, "eye_v": 1, "arms": out}
            return {"eyes": "worried" if t < 7.4 else "open", "eye_dir": 0, "arms": out}
        if kind == "merge":
            if t < 5.0:   # looking from one to the other
                return {"eyes": "open", "eye_dir": -1 if int(t * 1.5) % 2 else 1, "eye_v": -1}
            return {"eyes": "happy", "eye_dir": a["pick"], "eye_v": -1}
        if kind == "recursion":
            return {"eyes": "open" if t < 4.6 else "happy", "eye_dir": side, "eye_v": 0, "arms": up}
        # the keyboard
        if t < 4.5:
            return {"eyes": "open", "eye_dir": side, "eye_v": 1, "sink": "half",
                    "arms": (LEFT_WAVE[0] + (ARMS[1],)) if int(t * 10) % 2 else ((ARMS[0],) + WAVE[0])}
        return {"eyes": "closed" if t < 7.4 else "happy", "eye_dir": side, "eye_v": 1, "sink": "half", "arms": out}

    def sheep_at(self, t, side):
        # the sheep jumping the fence right now: (x, y) of its top left, which way it's going, or None
        s = self.s()
        gb = max(2, round(3 * s))
        fx = self.beside(side, 14 * s, 30) + 7 * s   # the fence's middle
        for i, at in enumerate(JUMPS):
            k = (t - at) / 1.0
            if 0 <= k < 1:
                d = -1 if i == 3 else 1   # (the 4th one changes its mind and jumps back)
                x = fx + d * (-30 + 60 * k) * s - len(SHEEP[0]) * gb / 2
                y = (self.pet_px[1] - len(SHEEP) * gb
                     - math.sin(math.pi * min(1.0, max(0.0, (k - 0.2) / 0.6))) * 22 * s)
                return x, y, d
        return None

    def gag_room(self, kind, t):
        # room it needs above its head (so the usage bubble moves up out of the way)
        s, gb = self.s(), max(2, round(3 * self.s()))
        if kind in FINDS:
            return self.finds_room(kind, t)
        if kind == "duck" and 4.0 <= t < 6.5:
            return (len(BULB) + 6) * gb
        if kind == "loop" and t < 5.6:
            return round(24 * s)
        if kind == "recursion":
            return round(26 * s)
        return 0

    def gag_draw(self, kind, t, a, side, px, py, sink, bw, bh, pb, pet_w, pet_h):
        c, s = self.canvas, self.s()
        gb = max(2, round(3 * s))   # (the little pictures are a bit chunkier than the small blocks)
        if kind in FINDS:
            return self.finds_draw(kind, t, a, side, px, py, sink, pb, pet_w, pet_h)

        def rect(x0, y0, x1, y1, col, stipple=None):
            if stipple:
                c.create_rectangle(round(px + x0), round(py + y0), round(px + x1), round(py + y1), fill=col, outline="",
                                   stipple=stipple)
            else:
                c.create_rectangle(round(px + x0), round(py + y0), round(px + x1), round(py + y1), fill=col, outline="")

        def pic(rows, col, x, y, b=pb, flip=False):
            self.glyph([r[::-1] for r in rows] if flip else rows, round(px + x), round(py + y), b, col, shadow=False)

        def hand(row, d=side):
            hx, hy = self.act_hand(d, row)
            return hx, hy + sink

        if kind == "phone":
            pw_, ph_ = len(PHONE[0]) * gb, len(PHONE) * gb
            ring = t < 1.4 and int(t * 12) % 2
            col = dict(PHONE_C, s="#c4e6ff" if ring else PHONE_C["s"])
            if t < 1.4:   # buzzing on the floor, with little sound waves
                x = self.beside(side, pw_, 10) + (pb if ring else 0)
                pic(PHONE, col, x, pet_h - ph_, gb)
                if ring:
                    for d in (-1, 1):
                        wx = x + (pw_ + 2 * pb if d > 0 else -3 * pb)
                        for j in range(3):
                            rect(wx + d * (j % 2) * pb, pet_h - ph_ + j * 2 * pb, wx + d * (j % 2) * pb + pb,
                                 pet_h - ph_ + j * 2 * pb + pb, PHONE_C["s"])
            elif t < 7.6:   # held to its ear
                hx, hy = hand(0)
                pic(PHONE, col, hx - pw_ / 2, hy - 2 * gb, gb)
        elif kind == "cookie":
            bites = sum(1 for at in BITES if t >= at)
            if bites < 4:
                rows = cookie_rows(bites)
                hx, hy = hand(1)
                w = len(rows[0]) * gb
                pic(rows if side > 0 else [r[::-1] for r in rows], COOKIE_C,
                    hx - (gb if side > 0 else w - gb), hy - 4 * gb, gb)
        elif kind == "duck":
            if t < 8.5:
                dw, dh = len(DUCK[0]) * gb, len(DUCK) * gb
                hop = 3 * gb if 6.0 <= t < 6.3 else 0
                pic(DUCK, DUCK_C, self.beside(side, dw, 8), pet_h - dh - hop, gb, flip=side > 0)
            if 4.0 <= t < 6.5:   # the idea!
                bx, by = pet_w / 2 - 2.5 * gb, sink - (len(BULB) + 3) * gb
                pic(BULB, BULB_C, bx, by, gb)
                if int(t * 6) % 2:   # (shining)
                    for ddx, ddy in ((-2, 1), (6, 1), (2, -3), (-1, -2), (5, -2)):
                        rect(bx + ddx * gb, by + ddy * gb, bx + (ddx + 1) * gb, by + (ddy + 1) * gb, BULB_C["w"])
        elif kind == "coffee":
            x, y = self.mug_at(t, side)
            pic(MUG, MUG_C, x, y + sink, gb, flip=side > 0)   # (the handle points back at it)
        elif kind == "loop":
            if t < 5.6:   # a little arrow going round above its head
                cx, cy, r = pet_w / 2, sink - 12 * s, 7 * s
                ang0 = -a.get("ph", 0.0) * 1.5
                for i in range(9):
                    ang = ang0 + i * 0.6
                    x, y = cx + math.cos(ang) * r, cy + math.sin(ang) * r * 0.6
                    rect(x - pb / 2, y - pb / 2, x + pb / 2, y + pb / 2, GAG_C["lit"] if i == 8 else GAG_C["code"])
        elif kind == "pancakes":
            pw_ = 26 * s
            x0 = self.beside(side, pw_, 6)
            rect(x0 - 2 * pb, pet_h - pb, x0 + pw_ + 2 * pb, pet_h, GAG_C["plate2"])   # the plate
            rect(x0 - pb, pet_h - 2 * pb, x0 + pw_ + pb, pet_h - pb, GAG_C["plate"])
            if t < TOPPLE:
                n = sum(1 for i in range(PANCAKES) if t >= 0.5 + 0.55 * i)
                ch = max(2, round(1.5 * pb))   # one pancake. (thin enough that the full stack, butter and all,
                for i in range(n):              # stays below the top of its head, clear of the usage bubble)
                    land = 0.5 + 0.55 * i
                    drop = max(0.0, 1 - (t - land) / 0.2) * 20 * s   # (falling in)
                    wob = math.sin(t * 7 + i * 0.8) * min(1.0, n / 7) * (i / PANCAKES) * 4 * s
                    y = pet_h - 2 * pb - (i + 1) * ch - drop
                    rect(x0 + wob, y, x0 + pw_ + wob, y + ch, GAG_C["cake2"])
                    rect(x0 + pb + wob, y, x0 + pw_ - pb + wob, y + max(1, ch // 2), GAG_C["cake"])
                if n == PANCAKES:   # butter and syrup on top
                    top = pet_h - 2 * pb - PANCAKES * ch
                    wob = math.sin(t * 7 + (PANCAKES - 1) * 0.8) * 4 * s
                    rect(x0 + pw_ / 2 - 2 * pb + wob, top - 2 * pb, x0 + pw_ / 2 + 2 * pb + wob, top, GAG_C["butter"])
                    rect(x0 + 2 * pb + wob, top, x0 + pw_ - 3 * pb + wob, top + pb, GAG_C["syrup"])
        elif kind == "sheep":
            fw, fh = len(FENCE[0]) * gb, len(FENCE) * gb
            fx = self.beside(side, 14 * s, 30) + 7 * s
            pic(FENCE, FENCE_C, fx - fw / 2, pet_h - fh, gb)
            sh = self.sheep_at(t, side)
            if sh:
                x, y, d = sh
                pic(SHEEP, SHEEP_C, x, y, gb, flip=d < 0)
        elif kind == "fortune":
            hx, hy = hand(1)
            w = len(FORTUNE[0]) * gb
            if t < 1.2:   # the whole cookie
                pic(FORTUNE, FORTUNE_C, hx - w / 2 + side * 3 * gb, hy - 3 * gb, gb)
            elif t < 2.0:   # cracked: the halves fall apart
                k = (t - 1.2) / 0.8
                for d in (-1, 1):
                    half = [r[:4] if d < 0 else r[4:] for r in FORTUNE]
                    pic(half, FORTUNE_C, hx - w / 2 + side * 3 * gb + (0 if d < 0 else w / 2) + d * k * 8 * pb,
                        hy - 3 * gb + k * k * 30 * s, gb)
            if 1.6 <= t < 7.6:   # the little slip of paper, unrolling
                k = smooth((t - 1.6) / 0.5)
                sw = 14 * pb * k
                x0 = hx - sw / 2 + side * 4 * pb
                rect(x0, hy - pb, x0 + sw, hy + 2 * pb, GAG_C["paper"])
                if k > 0.9:
                    for i in range(3):
                        rect(x0 + (2 + 4 * i) * pb, hy, x0 + (4 + 4 * i) * pb, hy + pb, GAG_C["red"])
        elif kind == "merge":
            for d in (-1, 1):
                if t >= 5.0 and d == -a["pick"]:
                    continue   # (thrown away)
                if t >= 7.6:
                    continue
                bump = max(0.0, math.sin(t * math.pi * 1.6 + (0 if d < 0 else math.pi))) * 5 * s if 1 < t < 4.8 else 0
                bob = math.sin(t * 2 + d) * 2 * s
                nw = 9 * pb
                x0 = pet_w / 2 + d * (pet_w / 2 + 8 * s + nw / 2 - bump) - nw / 2
                y0 = sink - 4 * s + bob
                col, fold = (GAG_C["note_in"], GAG_C["fold"]) if d < 0 else (GAG_C["note_out"], GAG_C["fold2"])
                rect(x0, y0, x0 + nw, y0 + nw, col)
                rect(x0 + nw - 2 * pb, y0 + nw - 2 * pb, x0 + nw, y0 + nw, fold)   # the curled corner
                pic(MERGE_IN if d < 0 else MERGE_OUT, {"k": GAG_C["ink"]}, x0 + 2.5 * pb, y0 + 3 * pb)
        elif kind == "recursion":
            hx, hy = hand(0)
            self.draw_mirror(hx + side * 6 * s, hy - 16 * s, 16 * pb, side, 0, rect, px, py)
        elif kind == "keyboard":
            kw, kh = 34 * s, 4 * pb
            x0, y0 = self.beside(side, kw, 4), pet_h - kh
            rect(x0, y0, x0 + kw, y0 + kh, GAG_C["dark"])
            cols = int((kw - pb) / (2 * pb))
            seed = int(t * 12)
            for row in range(2):   # keys, a few lit up as they're hit
                for i in range(cols):
                    lit = t < 4.5 and (i * 7 + row * 13 + seed * 5) % 11 == 0
                    kx = x0 + pb + i * 2 * pb
                    rect(kx, y0 + pb + row * pb * 1.4, kx + pb, y0 + pb + row * pb * 1.4 + pb,
                         GAG_C["lit"] if lit else GAG_C["key"])
            if 4.6 <= t < 7.4:   # ctrl+z, ctrl+z, ctrl+z...
                for k in range(min(5, int((t - 4.6) / 0.45) + 1)):
                    age = t - 4.6 - k * 0.45
                    pic(UNDO, {"k": GAG_C["lit"]}, x0 + (4 + k * 6) * pb, y0 - 8 * pb - age * 10 * s)

    def draw_mirror(self, x, y, size, side, depth, rect, px, py):
        # an oval hand mirror with a little mascot in it, holding a little mirror with a littler mascot in it...
        s = self.s()
        w, h = size, size * 1.25
        b = max(1, round(size / 14))
        if depth == 0:   # the handle, down to its hand
            rect(x - size * 0.09, y + h / 2, x + size * 0.09, y + h / 2 + size * 0.5, GAG_C["frame"])
        self.blob(px + x, py + y, w / 2 + b, h / 2 + b, b, GAG_C["frame"])
        self.blob(px + x, py + y, w / 2 - b * 0.5, h / 2 - b * 0.5, b, GAG_C["glass"])
        u = w / 34   # the reflection: the mascot, at whatever size fits
        if u < 0.45:
            rect(x - w * 0.22, y - h * 0.05, x + w * 0.22, y + h * 0.2, ORANGE)
            return
        bx, by = u * 1.3, u * 2.6
        mx, my = x - 9 * bx, y - 2.2 * by
        rect(mx + 3 * bx, my, mx + 15 * bx, my + 2 * by, ORANGE)   # head
        rect(mx + 1 * bx, my + 2 * by, mx + 17 * bx, my + 3 * by, ORANGE)   # arms
        rect(mx + 3 * bx, my + 3 * by, mx + 15 * bx, my + 4 * by, ORANGE)
        for lx in (4, 6, 11, 13):
            rect(mx + lx * bx, my + 4 * by, mx + (lx + 1) * bx, my + 5 * by, ORANGE)
        for ex in (5, 12):
            rect(mx + ex * bx, my + by, mx + (ex + 1) * bx, my + 2 * by, EYE)
        if depth < 3 and size > 6 * s:
            self.draw_mirror(mx + 17 * bx + side * size * 0.05, my - by * 0.2, size * 0.42, side, depth + 1, rect,
                             px, py)

    # ---- finding things: digging up a 404, the bug hunt, the lost semicolon ----
    # ---- drawing helpers ----
    def fsprite(self, rows, colours, x, y, b, flip=False, clip=None, skip=""):
        # a little picture at (x, y) on the canvas. clip: nothing below that y. skip: letters left out.
        c = self.canvas
        for r, line in enumerate(rows):
            y0 = y + r * b
            if clip is not None and y0 >= clip:
                break
            y1 = y0 + b if clip is None else min(y0 + b, clip)
            for i, ch in enumerate(line[::-1] if flip else line):
                if ch != "." and ch not in skip:
                    c.create_rectangle(round(x + i * b), round(y0), round(x + (i + 1) * b), round(y1),
                                       fill=colours[ch], outline="")

    def fblock(self, x, y, b, col):
        self.canvas.create_rectangle(round(x), round(y), round(x + b), round(y + b), fill=col, outline="")

    def foval(self, cx, cy, rx, ry, b, pick, rows=None):
        # an oval of b-sized blocks. pick(dx, dy) gives each block's colour (or None), dx / dy from -1 to 1.
        # rows: "top" or "bottom" for just that half
        for j in range(-math.ceil(ry / b), math.ceil(ry / b) + 1):
            if rows == "top" and j > 0 or rows == "bottom" and j < 0:
                continue
            for i in range(-math.ceil(rx / b), math.ceil(rx / b) + 1):
                dx, dy = i * b / max(rx, 1), j * b / max(ry, 1)
                if dx * dx + dy * dy <= 1:
                    col = pick(dx, dy)
                    if col:
                        self.fblock(cx + i * b - b / 2, cy + j * b - b / 2, b, col)

    def fline(self, x0, y0, x1, y1, b, cols):
        # a line of blocks, cols[0] on one side and cols[1] on the other (so it looks round)
        n = max(1, round(max(abs(x1 - x0), abs(y1 - y0)) / b))
        nx, ny = -(y1 - y0), x1 - x0
        ln = max(1.0, math.hypot(nx, ny))
        for k, col in enumerate(cols):
            off = (k - (len(cols) - 1) / 2) * b
            for i in range(n + 1):
                x = x0 + (x1 - x0) * i / n + nx / ln * off
                y = y0 + (y1 - y0) * i / n + ny / ln * off
                self.fblock(x - b / 2, y - b / 2, b, col)

    # ---- starting ----
    def finds_start(self, kind, a):
        s = self.s()
        if kind == "bughunt":
            a["bug"], a["bv"] = self.x + a["side"] * 70 * s, 0.0   # the bug, on the screen
        a["x0"] = self.x

    # ---- every frame ----
    def finds_tick(self, kind, a, t0, t, dt, s, cue, say):
        side = a["side"]
        pw, ph = self.pet_px
        if kind == "dig":
            sx = self.shaft_x(side)
            if cue(0.2):
                say(DIG_LINES)
                self.gag_puff(sx, ph - 20 * s, 5)
            for at in STROKES:
                if cue(at + 0.5):   # a shovelful of dirt, tossed onto the pile
                    for _ in range(7):
                        self.gag_part("dot", sx + side * 2 * s, ph - 14 * s, side * random.uniform(40, 110) * s,
                                      -random.uniform(70, 150) * s, 0.7, random.choice(DIRT_C[:3]), g=420 * s)
            if cue(CLINK):   # it hit something
                self.play("clink")
                self.gag_sparkle(sx, ph - 2 * s, 6)
            if cue(RISE - 0.2):
                self.gag_puff(sx, ph - 4 * s, 6)
            if cue(OPEN):
                self.play("chime")
                self.gag_sparkle(sx, ph - 26 * s, 8)
            if cue(OPEN + 0.4):
                self.worried_t = 1.6
                say(DIG_END)
            if cue(CLOSE):
                self.gag_puff(sx, ph - 40 * s, 7)
            if cue(9.3):
                self.gag_puff(sx, ph - 4 * s, 8)
        elif kind == "bughunt":
            self.tick_hunt(a, t, dt, s, cue, say)
        elif kind == "semicolon":
            lo, hi = self.gag_bounds()
            reach, back = 44 * s, 18 * s
            if not lo + back + 30 * s <= a["x0"] - side * back and a["x0"] + side * reach <= hi:
                a["x0"] = min(max(a["x0"], lo + reach + back), hi - reach - back)
            if t < 6:   # out one way and back past where it started, looking down through the glass
                x = a["x0"] + side * (reach * math.sin(math.pi * t / 6) - back * smooth(t / 6))
                if abs(x - self.x) > 0.05:
                    self.dir = 1 if x > self.x else -1
                    self.step_t += dt
                    if self.step_t >= 0.25:
                        self.step_t, self.step = 0.0, self.step + 1
                self.x = x
            if cue(0.0):   # where it is (it was there all along): where the glass ends up
                a["semi"] = a["x0"] - side * back - side * self.lens_reach()
            if cue(0.3):
                say(SEMI_LINES)
            if cue(3.4):
                say(SEMI_MORE)
            if cue(FOUND):   # there it is!
                self.play("chime")
                self.happy_t = 2.5
            if cue(PICKED):
                lx, ly = self.lens_at(t)
                self.gag_puff(lx, ly, 6)
                self.gag_sparkle(*self.held_semi(), 8)
            if cue(PICKED + 0.3):
                say(SEMI_END)
            if cue(7.6):
                self.play("pop")

    def tick_hunt(self, a, t, dt, s, cue, say):
        lo, hi = self.gag_bounds()
        lo, hi = max(lo, a["x0"] - 110 * s), min(hi, a["x0"] + 110 * s)   # (the chase stays close)
        if cue(0.2):
            say(BUG_START)
            self.play("pop")
        if t < SWINGS[-1]:
            if t > 1:   # creeping after it, net ready
                want = a["bug"] - self.dir * 46 * s
                self.dir = 1 if a["bug"] > self.x else -1
                step = 70 * s * dt
                if abs(want - self.x) > step:
                    self.x = min(max(self.x + math.copysign(step, want - self.x), lo), hi)
                    self.step_t += dt
                    if self.step_t >= 0.18:
                        self.step_t, self.step = 0.0, self.step + 1
            away = 1 if a["bug"] >= self.x else -1
            if abs(a["bug"] - self.x) < 52 * s:   # too close: it scuttles off
                a["bv"] = away * 95 * s
            else:
                a["bv"] *= max(0.0, 1 - 4 * dt)
            nb = a["bug"] + a["bv"] * dt
            if not lo - 20 * s <= nb <= hi + 50 * s:   # cornered: it doubles back past it
                a["bv"] = -a["bv"]
                nb = a["bug"] + a["bv"] * dt
            a["bug"] = nb
        for at in SWINGS[:-1]:
            if cue(at + SWING * 0.6):   # swish... missed. it hops away
                self.play("whoosh")
                fx, _ = self.net_spot()
                self.gag_puff(fx, self.pet_px[1] - 3 * s, 5)
                a["bug"] += (1 if a["bug"] >= self.x else -1) * 34 * s
        if cue(SWINGS[-1] + SWING * 0.6):   # got it!
            fx, _ = self.net_spot()
            a["caught"] = True
            a["bug"] = self.x - self.pet_px[0] / 2 + fx   # (under the net)
            self.play("pop")
            self.gag_puff(fx, self.pet_px[1] - 3 * s, 6)
        if cue(LIFT):
            self.happy_t = 1.5
            say(BUG_END)
        if cue(FREE):   # off it goes, on its little wings
            bx, by = self.bag_at()
            a["fly"] = [bx, by]
            say(BUG_FREE)
            self.play("flap")
        if a.get("fly"):
            a["fly"][0] += self.dir * 70 * s * dt
            a["fly"][1] -= (45 + 20 * math.sin(t * 9)) * s * dt
        if cue(9.5):
            hx, hy = self.act_hand(self.dir, 1)
            self.gag_puff(hx + self.dir * 14 * s, hy, 5)

    # ---- where things are (relative to the body's top left) ----
    def shaft_x(self, side):
        s = self.s()
        return self.pet_px[0] / 2 + side * (self.pet_px[0] / 2 - 2 * s)   # the shovel's shaft, just past its hand

    def net_spot(self):
        # the middle of the net when it's down on the floor in front of it
        s = self.s()
        hx, _ = self.act_hand(self.dir, 1)
        return hx + self.dir * 18 * s, self.pet_px[1]

    def hoop_at(self):
        # the net's hoop, held up ready in front of it at its middle (below its head, clear of the bubble)
        s = self.s()
        hx, hy = self.act_hand(self.dir, 1)
        return hx + self.dir * 22 * s, hy - 1 * s

    def bag_at(self):
        s, pb = self.s(), max(1, round(2 * self.s()))
        x, y = self.hoop_at()
        return x, y + 6 * pb

    def lens_reach(self):
        # how far in front of its middle the magnifying glass is held
        s = self.s()
        return self.pet_px[0] / 2 + 17 * s

    def lens_at(self, t):
        s = self.s()
        bob = math.sin(t * 5) * 1.5 * s if t < FOUND else 0
        return self.pet_px[0] / 2 + self.dir * self.lens_reach(), self.pet_px[1] - 17 * s + bob

    def held_semi(self):
        # the semicolon held up in its raised hand (its middle)
        s = self.s()
        hx, hy = self.act_hand(self.dir, 0)
        return hx + self.dir * 4 * s, hy - 18 * s

    # ---- how it looks ----
    def finds_pose(self, kind, t, a, side):
        up = self.side_arm(side, 0)
        if kind == "dig":
            if t < CLINK + 0.4:
                ph = next(((t - at) / 0.7 for at in STROKES if at <= t < at + 0.7), None)
                stab = ph is not None and ph < 0.45 or CLINK <= t
                return {"eyes": "open", "eye_dir": side, "eye_v": 1, "arms": up, "sink": "half" if stab else None}
            if t < OPEN:
                return {"eyes": "open", "eye_dir": side, "eye_v": 1}
            if t < CLOSE:
                return {"eyes": "worried", "eye_dir": side, "eye_v": -1}
            return {"eyes": "open", "eye_dir": side, "eye_v": 0}
        if kind == "bughunt":
            d = self.dir
            swing = any(at <= t < at + SWING for at in SWINGS)
            caught = a.get("caught") and t < LIFT
            moving = 1 < t < SWINGS[-1] and not swing
            return {"eyes": "happy" if LIFT <= t < FREE + 0.6 else "open", "eye_dir": d,
                    "eye_v": 1 if t < LIFT else -1 if a.get("fly") else 0,
                    "arms": ARMS if swing or caught else self.side_arm(d, 0),
                    "sink": "half" if swing else None,
                    "legs": LEGS_STEP if moving and self.step % 2 else LEGS_STAND}
        if kind == "semicolon":
            d = self.dir
            if t < PICKED:
                walking = 0.2 < t < 5.9
                return {"eyes": "happy" if t >= FOUND else "open", "eye_dir": d, "eye_v": 1, "arms": ARMS,
                        "legs": LEGS_STEP if walking and self.step % 2 else LEGS_STAND}
            return {"eyes": "happy", "eye_dir": d, "eye_v": -1, "arms": self.side_arm(d, 1)}
        return {}

    def finds_room(self, kind, t):
        # room it needs above its head (so the usage bubble moves up out of the way)
        s = self.s()
        if kind == "dig" and OPEN <= t < CLOSE + 0.3:
            return round(22 * s)   # the 404 page
        if kind == "semicolon" and t >= PICKED:
            return round(36 * s)   # held up high
        return 0

    def finds_draw(self, kind, t, a, side, px, py, sink, pb, pet_w, pet_h):
        if kind == "dig":
            self.draw_dig(t, side, px, py, sink, pb, pet_h)
        elif kind == "bughunt":
            self.draw_hunt(t, a, px, py, sink, pb, pet_w, pet_h)
        elif kind == "semicolon":
            self.draw_search(t, a, px, py, sink, pb, pet_w, pet_h)

    # ---- digging up a 404 ----
    def draw_dig(self, t, side, px, py, sink, pb, pet_h):
        s = self.s()
        sx = self.shaft_x(side)
        hole_x, pile_x = px + sx, px + sx + side * 22 * s
        floor = py + pet_h
        strokes = sum(1 for at in STROKES if t >= at + 0.5)
        k = min(1.0, max(0.0, (t - 0.6) / (CLINK - 0.6)))
        if t >= CLOSE:
            k *= 1 - smooth((t - CLOSE) / 0.7)
        hrx, hry = (6 + 9 * k) * s, (1.5 + 2 * k) * s   # the hole, seen from just above
        hcy = floor - hry

        def hole_back(dx, dy):
            return DIRT_C[4] if dy < -0.55 else DIRT_C[5] if dy < 0 else None

        def hole_front(dx, dy):
            if dx * dx + dy * dy > 0.62:
                return DIRT_C[1] if dy > 0.6 else DIRT_C[0]   # the lip of soil at the front
            return DIRT_C[5]

        if hrx > 6 * s or t < CLOSE:
            self.foval(hole_x, hcy, hrx, hry, pb, hole_back, "top")
        # the shovel: a few strokes, then it's planted in the pile
        sw, sh = len(SHOVEL[0]) * pb, len(SHOVEL) * pb
        hand_y = self.act_hand(side, 1)[1] + sink
        planted = t >= CLINK + 0.4
        if t < 9.5:
            if not planted:
                ph = next(((t - at) / 0.7 for at in STROKES if at <= t < at + 0.7), None)
                if t >= CLINK:
                    drop = 7 * s
                elif ph is None:
                    drop = 0
                elif ph < 0.25:
                    drop = smooth(ph / 0.25) * 7 * s       # down into the ground
                elif ph < 0.45:
                    drop = 7 * s                           # leaning on it
                else:
                    drop = 7 * s - smooth((ph - 0.45) / 0.25) * 11 * s   # up, with a load of dirt
                top = py + hand_y - 5 * pb + drop
                self.fsprite(SHOVEL, SHOVEL_C, hole_x - sw / 2, top, pb, flip=side < 0)
                if ph is not None and 0.45 <= ph < 0.72 and t < CLINK:   # the load on the blade
                    for i, col in enumerate((DIRT_C[0], DIRT_C[1], DIRT_C[0])):
                        self.fblock(hole_x - 2 * pb + i * pb * 1.5, top + sh - 9 * pb, pb * 1.5, col)
            else:   # stuck upright in the pile
                pile_h = (3 + 1.2 * strokes) * s
                self.fsprite(SHOVEL, SHOVEL_C, pile_x + side * 2 * s - sw / 2, floor - sh + 6 * pb - pile_h * 0.3,
                             pb, flip=side < 0)
        # the pile of dirt beside the hole, growing with each toss
        if strokes and t < 9.6:
            grow = 1.0 if t < CLOSE else 1 - smooth((t - CLOSE) / 0.7)
            prx, pry = (4 + 1.8 * strokes) * s * grow, (2 + 1.3 * strokes) * s * grow
            if prx > pb:
                self.foval(pile_x, floor, prx, pry, pb,
                           lambda dx, dy: DIRT_C[2] if dx < -0.35 and dy < -0.3 else DIRT_C[0] if dx < 0.4 else DIRT_C[1],
                           "top")
                for i in range(min(strokes, 5)):   # clods on top
                    cx = pile_x + (i - 2) * prx * 0.35
                    self.fblock(cx, floor - pry * (0.75 - abs(i - 2) * 0.15) - pb, pb, DIRT_C[3])
        # the chest: rises out of the hole, opens, a 404 page floats up, then back down it goes
        if RISE <= t < 9.6:
            cw, chh = len(CHEST[0]) * pb, len(CHEST) * pb
            up = smooth((t - RISE) / 0.8) if t < CLOSE + 0.2 else 1 - smooth((t - CLOSE - 0.2) / 0.5)
            ctop = floor - pb + chh * (1 - up) - chh
            rows = CHEST_OPEN if OPEN <= t < CLOSE + 0.2 else CHEST
            lid = (len(CHEST_OPEN) - len(CHEST)) * pb if rows is CHEST_OPEN else 0
            self.fsprite(rows, CHEST_C, hole_x - cw / 2, ctop - lid, pb, clip=hcy + hry * 0.2)
            if OPEN <= t < CLOSE + 0.2 and int(t * 8) % 2:   # light shining out
                for i in (-2, 0, 2):
                    self.fblock(hole_x + i * 3 * pb - pb / 2, ctop - lid - (3 + abs(i)) * pb, pb, CHEST_C["G"])
        if hrx > 6 * s or t < CLOSE:
            self.foval(hole_x, hcy, hrx, hry, pb, hole_front, "bottom")
        if OPEN + 0.1 <= t < CLOSE:   # the page, floating up out of the chest with 404 on it
            k2 = smooth((t - OPEN - 0.1) / 0.6)
            pw_, ph_ = 15 * pb, 12 * pb
            ctop = floor - pb - len(CHEST) * pb
            x0 = hole_x - pw_ / 2 + math.sin(t * 2.4) * pb * k2
            y0 = ctop - (ph_ + 2 * pb) * k2 + math.sin(t * 3.1) * pb * k2   # (just above the chest, under the bubble)
            self.draw_page(x0, y0, pb, clip=ctop)

    def draw_page(self, x0, y0, b, clip=None):
        # a sheet of paper with a folded corner, 404 in red, and a couple of grey lines of "text".
        # clip: the chest's top. the part still inside the chest isn't drawn
        w, h = 15, 12
        for j in range(h):
            if clip is not None and y0 + (j + 1) * b > clip:
                break
            for i in range(w):
                if i >= w - 3 and j < 3 and i - (w - 3) >= j:
                    col = PAGE_C["f"] if i - (w - 3) == j else None   # the folded corner
                elif i == w - 1 or j == h - 1:
                    col = PAGE_C["d"]
                elif i == 0 or j == 0:
                    col = PAGE_C["l"]
                else:
                    col = PAGE_C["p"]
                if col:
                    self.fblock(x0 + i * b, y0 + j * b, b, col)
        for n, ch in enumerate("404"):
            self.fsprite(DIGITS[ch], {"k": PAGE_C["r"]}, x0 + (2 + 4 * n) * b, y0 + 2 * b, b, clip=clip)
        for row, ln in ((8, 10), (10, 7)):
            if clip is None or y0 + (row + 1) * b <= clip:
                for i in range(ln):
                    self.fblock(x0 + (2 + i) * b, y0 + row * b, b, PAGE_C["t"])

    # ---- the bug hunt ----
    def draw_hunt(self, t, a, px, py, sink, pb, pet_w, pet_h):
        s, d = self.s(), self.dir
        left = self.x - pet_w / 2   # (the bug lives on the screen, the drawing is from the body)
        floor = py + pet_h
        hx, hy = self.act_hand(d, 1)
        hx, hy = px + hx, py + hy + sink
        swing = next((at for at in SWINGS if at <= t < at + SWING), None)
        caught = a.get("caught") and t < LIFT
        frame = int(t * 10) % 2
        bw_ = len(BEETLE[0]) * pb
        bh_ = len(BEETLE[0]) and (len(BEETLE) - 1) * pb
        # the bug, on the floor (when it isn't in the net or flying)
        if not a.get("caught") and not a.get("fly") and t < a["dur"]:
            bx = px + a["bug"] - left
            if -60 * s < bx - px < pet_w + 60 * s:
                rows = BEETLE[:-1] + [BEETLE[-1][frame]]
                self.fsprite(rows, BEETLE_C, bx - bw_ / 2, floor - bh_ - pb, pb, flip=a["bv"] < 0)
        if t >= 9.5:
            return
        fx, _ = self.net_spot()
        fx = px + fx
        if swing is not None or caught:
            k = 1.0 if swing is None else smooth((t - swing) / (SWING * 0.6))
            if k < 0.55:   # on its way down: the hoop swings out and down, with a swoosh behind it
                ox, oy = self.hoop_at()
                cx, cy = px + ox + (fx - px - ox) * k * 1.6, py + oy + sink + (pet_h - 8 * s - oy) * k * 1.6
                self.draw_hoop(hx, hy, cx, cy, pb, None)
                for i in range(1, 4):
                    self.fblock(cx - d * i * 3 * pb, cy - i * 2 * pb, pb, NET_C["w"])
            else:   # down on the floor, over the bug (or nothing)
                self.draw_dome(hx, hy, fx, floor, pb, a.get("caught"), frame)
            return
        if a.get("fly"):   # flown off: an empty net, and the bug buzzing away on little wings
            ox, oy = self.hoop_at()
            self.draw_hoop(hx, hy, px + ox, py + oy + sink, pb, None)
            bx, by = a["fly"]
            wings = [BEETLE_WINGS[frame]] + BEETLE[:-1]
            self.fsprite(wings, BEETLE_C, px + bx - bw_ / 2, py + by - 6 * pb, pb, flip=d < 0)
            return
        ox, oy = self.hoop_at()
        bug = a.get("caught") and t >= LIFT   # lifted up, with the bug wriggling in the bag
        self.draw_hoop(hx, hy, px + ox, py + oy + sink, pb, frame if bug else None)

    def draw_hoop(self, hx, hy, cx, cy, b, bug_frame):
        # the net held up in front of it: the handle from its hand, a round hoop with mesh across it, and the
        # mesh bag drooping below (with the bug in it, once it's caught)
        d = self.dir
        r = 5 * b
        bagx, bagy = cx, cy + 5 * b
        self.fline(hx, hy, cx - d * r * 0.7, cy + r * 0.7, b, (NET_C["h"], NET_C["H"]))   # the handle
        if bug_frame is not None:   # wriggling in the bag
            rows = BEETLE[:-1] + [BEETLE[-1][bug_frame]]
            bw_ = len(BEETLE[0]) * b
            self.fsprite(rows, BEETLE_C, bagx - bw_ / 2 + (b if bug_frame else 0), bagy - b, b, flip=d < 0)
        self.foval(bagx, bagy, 4 * b, 5 * b,   # the bag: every other block, so you can see through it
                   b, lambda dx, dy: NET_C["w"] if dy > -0.2 and ((round(dx * 4) + round(dy * 5)) % 2 == 0
                                                                  or dx * dx + dy * dy > 0.7) else None)
        self.foval(cx, cy, r, r, b,   # the hoop, lit on its top left, and the mesh across it
                   lambda dx, dy: ((NET_C["R"] if dx + dy < 0 else NET_C["r"]) if dx * dx + dy * dy > 0.6
                                   else NET_C["w"] if (round(dx * 5) + round(dy * 5)) % 2 == 0 else None))

    def draw_dome(self, hx, hy, fx, floor, b, caught, frame):
        # the net down on the floor: a dome of mesh with the hoop flat round its bottom, the handle up to its hand
        d = self.dir
        rx, ry = 9 * b, 8 * b
        self.fline(hx, hy, fx - d * rx * 0.55, floor - ry * 0.75, b, (NET_C["h"], NET_C["H"]))
        if caught:   # under the net, wriggling
            rows = BEETLE[:-1] + [BEETLE[-1][frame]]
            bw_ = len(BEETLE[0]) * b
            self.fsprite(rows, BEETLE_C, fx - bw_ / 2 + (b if frame else 0), floor - len(BEETLE) * b, b,
                         flip=d < 0)
        self.foval(fx, floor - b, rx, ry, b,
                   lambda dx, dy: NET_C["w"] if (round(dx * 9) + round(dy * 8)) % 2 == 0 or dx * dx + dy * dy > 0.8
                   else None, "top")
        self.foval(fx, floor - b, rx, 2 * b, b,
                   lambda dx, dy: (NET_C["R"] if dy < 0 else NET_C["r"]) if dx * dx + dy * dy > 0.4 else None)

    # ---- the lost semicolon ----
    def draw_search(self, t, a, px, py, sink, pb, pet_w, pet_h):
        s, d = self.s(), self.dir
        left = self.x - pet_w / 2
        floor = py + pet_h
        semi_x = a.get("semi")
        if t < PICKED and semi_x is not None:   # it's been lying right there all along (with a glint now and then)
            sw = len(SEMI_SMALL[0]) * pb
            x = px + semi_x - left - sw / 2
            self.fsprite(SEMI_SMALL, SEMI_C, x, floor - len(SEMI_SMALL) * pb, pb)
            if int(t * 2.5) % 5 == 0:
                self.fblock(x + pb, floor - len(SEMI_SMALL) * pb - pb, pb, SEMI_C["W"])
        if t < PICKED:
            lx, ly = self.lens_at(t)
            hx, hy = self.act_hand(d, 2)
            over = semi_x is not None and abs(left + lx - semi_x) < 9 * s   # (lx is from the body's left)
            self.draw_glass(px + lx, py + ly + sink, px + hx, py + hy + sink, pb, over, t)
            return
        # picked up and held high, with a green tick: it compiles
        cx, cy = self.held_semi()
        big = max(2, round(pb * 1.5))
        bw_, bh_ = len(SEMI_BIG[0]) * big, len(SEMI_BIG) * big
        self.fsprite(SEMI_BIG, SEMI_C, px + cx - bw_ / 2, py + cy - bh_ / 2 + sink, big)
        if t >= 7.6:
            k = smooth((t - 7.6) / 0.3)
            cw = len(CHECK[0]) * pb
            self.fsprite(CHECK, CHECK_C, px + cx + d * (bw_ / 2 + 2 * pb) - (cw if d < 0 else 0),
                         py + cy - 2 * pb + (1 - k) * 6 * pb + sink, pb)

    def draw_glass(self, lx, ly, hx, hy, b, over, t):
        # a detective's magnifying glass: a chunky wooden handle, a brass collar, a thick brass rim (lit on its
        # top left, shady bottom right) and blue glass with a shine. over = the semicolon's under it: shown big
        r = 7 * b
        ux, uy = lx - hx, ly - hy
        ln = max(1.0, math.hypot(ux, uy))
        ex, ey = lx - ux / ln * (r + b), ly - uy / ln * (r + b)
        self.fline(hx, hy, ex, ey, b, (GAG_C["grip2"], GAG_C["grip"]))
        self.fblock(ex - b, ey - b, 2 * b, GAG_C["brass"])

        def lens(dx, dy):
            q = dx * dx + dy * dy
            if q > 0.56:   # the rim
                return GAG_C["brass_lit"] if dx + dy < -0.5 else GAG_C["brass_dark"] if dx + dy > 0.6 else GAG_C["brass"]
            if dx < -0.15 and dy < -0.15 and q < 0.4:
                return GAG_C["lens_shine"]   # the shine on its top left
            return GAG_C["lens_edge"] if q > 0.38 else GAG_C["lens"]

        self.foval(lx, ly, r + b, r + b, b, lens)
        if over:   # magnified! (without the gap rows, so it fits inside the glass)
            rows = [ln for ln in SEMI_BIG if ln.strip(".")]
            sw, sh = len(rows[0]) * b, len(rows) * b
            self.fsprite(rows, SEMI_C, lx - sw / 2 + b / 2, ly - sh / 2, b)
        g = int(t * 3) % 2
        self.fblock(lx - 3 * b, ly - 4 * b + g * b, b, "#ffffff")   # a glint
        self.fblock(lx - 4 * b + g * b, ly - 3 * b, b, "#ffffff")
