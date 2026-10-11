# part of the Pet: coding jokes it acts out on its own when it's idle (picked alongside sweeping, painting...
# in pet/idle.py): a phone call from the API, cookies, rubber duck debugging, coffee, a bug hunt, an infinite
# loop, a stack overflow of pancakes, counting sheep off by one, a fortune cookie, a merge conflict, a recursive
# mirror, a lost semicolon, digging up a 404, and a tiny keyboard. positions are relative to the body's top
# left, like particles. no dark edges.
import math
import random

from .art import (ARMS, BUG_A, BUG_B, BUG_C, BULB, BULB_C, COOKIE, COOKIE_C, DIGITS, DUCK, DUCK_C, EYE, FENCE, FENCE_C,
    FORTUNE, FORTUNE_C, GAG_C, LEFT_WAVE, LEGS_STAND, LEGS_STEP, MERGE_IN, MERGE_OUT, MUG, MUG_C, ORANGE,
    PHONE, PHONE_C, SEMI, SHEEP, SHEEP_C, SOIL_C, SPARK_C, UNDO, WAVE)
from .lines import (BUG_END, BUG_FREE, BUG_START, COFFEE_END, COFFEE_LINES, COOKIE_END, COOKIE_LINES, DIG_END,
    DIG_LINES, DUCK_END, DUCK_START, FORTUNE_END, FORTUNE_LINES, FORTUNE_START, KEY_END, KEY_LINES, KEY_UNDO,
    LOOP_END, LOOP_LINES, MERGE_END, MERGE_LINES, PANCAKE_END, PANCAKE_LINES, PANCAKE_MORE, PHONE_HELLO, PHONE_MORE,
    RECURSION_END, RECURSION_LINES, SEMI_END, SEMI_LINES, SEMI_MORE, SHEEP_DOUBT, SHEEP_END, SHEEP_MID, SHEEP_START)

GAGS = {"phone": 9.0, "cookie": 7.0, "duck": 9.0, "coffee": 8.0, "bughunt": 10.0, "loop": 7.5, "pancakes": 10.0,
        "sheep": 10.5, "fortune": 8.0, "merge": 9.0, "recursion": 8.0, "semicolon": 10.0, "dig": 10.0,
        "keyboard": 9.0}   # each one, and how long it lasts (seconds)
BITES = (1.5, 2.5, 3.5, 4.5)              # cookie bites
SIPS = ((1.5, 2.3), (4.0, 4.8))           # coffee sips (from, to)
SWIPES = (2.6, 4.6, 6.6)                  # bug net swipes (the last one catches it)
PANCAKES, TOPPLE = 10, 6.5                 # pancakes on the stack, and when it falls over
JUMPS = (0.8, 2.2, 3.6, 5.0, 6.4)         # sheep jumping the fence (the 4th one jumps back)
DIGS = tuple(0.6 + 0.6 * i for i in range(8))   # spade strokes


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
        if kind == "bughunt":
            a["bug"], a["bv"] = self.x + a["side"] * 70 * s, 0.0   # the bug, on the screen
        if kind in ("loop", "semicolon", "bughunt"):
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
        elif kind == "bughunt":
            self.tick_bughunt(a, t0, t, dt, s, cue, say)
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
        elif kind == "semicolon":
            lo, hi = self.gag_bounds()
            reach = 40 * s
            if not lo <= a["x0"] + side * reach <= hi:
                a["x0"] = min(max(a["x0"], lo + reach), hi - reach)
            if t < 6:   # out and back, looking down through the glass
                x = a["x0"] + side * reach * math.sin(math.pi * t / 6)
                if abs(x - self.x) > 0.05:
                    self.dir = 1 if x > self.x else -1
                    self.step_t += dt
                    if self.step_t >= 0.25:
                        self.step_t, self.step = 0.0, self.step + 1
                self.x = x
            if cue(0.3):
                say(SEMI_LINES)
            if cue(3.4):
                say(SEMI_MORE)
            if cue(6.2):   # there it is!
                self.play("chime")
                lx, ly = self.lens_at(side)
                self.gag_sparkle(lx, ly, 8)
            if cue(6.9):
                self.happy_t = 2.0
                say(SEMI_END)
        elif kind == "dig":
            hx = self.beside(side, 28 * s, 10) + 14 * s
            if cue(0.2):
                say(DIG_LINES)
            for at in DIGS:
                if cue(at + 0.25):   # a spadeful of dirt
                    for _ in range(6):
                        self.gag_part("dot", hx, ph - 2 * s, -side * random.uniform(20, 90) * s,
                                      -random.uniform(60, 140) * s, 0.7, random.choice(SOIL_C), g=400 * s)
            if cue(5.6):   # something's down there
                self.play("boing")
            if cue(6.3):
                self.worried_t = 1.5
                say(DIG_END)
            if cue(9.2):
                self.gag_puff(hx, ph - 8 * s)
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

    def tick_bughunt(self, a, t0, t, dt, s, cue, say):
        lo, hi = self.gag_bounds()
        lo, hi = max(lo, a["x0"] - 100 * s), min(hi, a["x0"] + 100 * s)   # (the chase stays close)
        if cue(0.2):
            say(BUG_START)
        if t < SWIPES[-1]:
            if t > 1:   # after it, with the net up
                want = a["bug"] - self.dir * 32 * s
                self.dir = 1 if a["bug"] > self.x else -1
                step = 70 * s * dt
                if abs(want - self.x) > step:
                    self.x = min(max(self.x + math.copysign(step, want - self.x), lo), hi)
                    self.step_t += dt
                    if self.step_t >= 0.18:
                        self.step_t, self.step = 0.0, self.step + 1
            away = 1 if a["bug"] >= self.x else -1
            if abs(a["bug"] - self.x) < 55 * s:   # it scuttles off
                a["bv"] = away * 95 * s
            else:
                a["bv"] *= max(0.0, 1 - 4 * dt)
            nb = a["bug"] + a["bv"] * dt
            if not lo - 20 * s <= nb <= hi + 50 * s:   # cornered: it doubles back past it
                a["bv"] = -a["bv"]
                nb = a["bug"] + a["bv"] * dt
            a["bug"] = nb
        for at in SWIPES[:-1]:
            if cue(at):   # swish... missed. it hops away
                self.play("whoosh")
                a["bug"] += (1 if a["bug"] >= self.x else -1) * 30 * s
        if cue(SWIPES[-1]):
            a["caught"] = True
            self.play("pop")
        if cue(7.2):
            self.happy_t = 1.5
            say(BUG_END)
        if cue(8.6):
            a["caught"], a["free"] = False, True
            a["bug"] = self.x + self.dir * 32 * s
            say(BUG_FREE)
        if a.get("free"):
            a["bug"] += self.dir * 110 * s * dt

    # ---- where things are ----
    def mug_at(self, t, side):
        # the mug's top left: in its hand, or up by its face for a sip
        s = self.s()
        hx, hy = self.act_hand(side, 1)
        x, y = hx - (0 if side > 0 else 12 * s), hy - 8 * s
        for t1, t2 in SIPS:
            if t1 <= t <= t2:
                k = smooth(min(t - t1, t2 - t) / 0.25)
                fx, fy = self.pet_px[0] / 2 + side * 4 * s - 6 * s, 2 * s
                x, y = x + (fx - x) * k, y + (fy - y) * k
        return x, y

    def lens_at(self, side):
        # the magnifying glass's middle: held out low, in front of it
        s = self.s()
        hx, hy = self.act_hand(side, 2)
        return hx + side * 12 * s, self.pet_px[1] - 6 * s

    # ---- how it looks ----
    def gag_pose(self, kind, t, a, side):
        # overrides for how it looks: {sink, eyes, eye_dir, eye_v, arms, legs}
        up = self.side_arm(side, 1)
        out = self.side_arm(side, 0)
        both = LEFT_WAVE[1] + WAVE[1]
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
        if kind == "bughunt":
            moving = 1 < t < SWIPES[-1]
            swipe = any(at <= t < at + 0.35 for at in SWIPES)
            return {"eyes": "happy" if 7 < t < 8.6 else "open", "eye_dir": self.dir, "eye_v": 1,
                    "arms": self.side_arm(self.dir, 0 if swipe else 1),
                    "legs": LEGS_STEP if moving and self.step % 2 else LEGS_STAND}
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
        if kind == "semicolon":
            if t < 6.2:
                walking = 0.2 < t < 5.8
                return {"eyes": "open", "eye_dir": side, "eye_v": 1, "arms": out,
                        "legs": LEGS_STEP if walking and self.step % 2 else LEGS_STAND}
            return {"eyes": "happy", "eye_dir": side, "eye_v": -1, "arms": up}
        if kind == "dig":
            if t < 5.4:
                stroke = any(at <= t < at + 0.3 for at in DIGS)
                return {"eyes": "open", "eye_dir": side, "eye_v": 1, "arms": out if stroke else up,
                        "sink": "half" if stroke else None}
            return {"eyes": "worried" if 6.3 <= t < 8 else "open", "eye_dir": side, "eye_v": 0}
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
        if kind == "duck" and 4.0 <= t < 6.5:
            return (len(BULB) + 6) * gb
        if kind == "loop" and t < 5.6:
            return round(24 * s)
        if kind == "recursion":
            return round(26 * s)
        if kind == "semicolon" and t >= 6.6:
            return 9 * gb
        return 0

    def gag_draw(self, kind, t, a, side, px, py, sink, bw, bh, pb, pet_w, pet_h):
        c, s = self.canvas, self.s()
        gb = max(2, round(3 * s))   # (the little pictures are a bit chunkier than the small blocks)

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
            pic(MUG, MUG_C, x, y + sink, gb, flip=side < 0)
        elif kind == "bughunt":
            self.draw_bughunt(t, a, px, py, sink, bw, pb, pet_w, pet_h, rect, pic)
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
                for i in range(n):
                    land = 0.5 + 0.55 * i
                    drop = max(0.0, 1 - (t - land) / 0.2) * 20 * s   # (falling in)
                    wob = math.sin(t * 7 + i * 0.8) * min(1.0, n / 7) * (i / PANCAKES) * 4 * s
                    y = pet_h - 2 * pb - (i + 1) * 2 * pb - drop
                    rect(x0 + wob, y, x0 + pw_ + wob, y + 2 * pb, GAG_C["cake2"])
                    rect(x0 + pb + wob, y, x0 + pw_ - pb + wob, y + pb, GAG_C["cake"])
                if n == PANCAKES:   # butter and syrup on top
                    top = pet_h - 2 * pb - PANCAKES * 2 * pb
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
        elif kind == "semicolon":
            lx, ly = self.lens_at(side)
            hx, hy = hand(2)
            if t < 6.4:
                self.pixel_line(px + hx, py + hy, px + lx - side * 4 * s, py + ly - 3 * s, pb, GAG_C["wood"])
                r = 5 * s
                for i in range(16):   # the lens: a metal ring, glass, and a glint
                    ang = i / 16 * 2 * math.pi
                    rect(lx + math.cos(ang) * r - pb / 2, ly + math.sin(ang) * r - pb / 2,
                         lx + math.cos(ang) * r + pb / 2, ly + math.sin(ang) * r + pb / 2, GAG_C["metal"])
                rect(lx - r * 0.6, ly - r * 0.6, lx + r * 0.6, ly + r * 0.6, GAG_C["glass"], stipple="gray50")
                if int(t * 3) % 2:
                    rect(lx - r * 0.5, ly - r * 0.5, lx - r * 0.5 + pb, ly - r * 0.5 + pb, "#ffffff")
            if 6.0 <= t < 6.6:   # on the floor, under the glass
                pic(SEMI, {"k": GAG_C["semi"]}, lx - gb, pet_h - 5 * gb, gb)
            elif t >= 6.6:   # held up high
                ux, uy = hand(0)
                pic(SEMI, {"k": GAG_C["semi"]}, ux - gb, uy - 6 * gb, gb)
        elif kind == "dig":
            self.draw_dig(t, side, px, py, sink, pb, pet_w, pet_h, rect, pic, hand)
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

    def draw_bughunt(self, t, a, px, py, sink, bw, pb, pet_w, pet_h, rect, pic):
        s = self.s()
        left = self.x - pet_w / 2   # (the bug lives on the screen, the drawing is from the body)
        d = self.dir
        hx, hy = self.act_hand(d, 0)
        hy += sink
        swipe = next((at for at in SWIPES if at <= t < at + 0.35), None)
        held = 7 <= t < 8.6
        if swipe is not None or a.get("caught"):   # the net swings down in front of it
            k = 1.0 if a.get("caught") and swipe is None else math.sin(math.pi * min(1.0, (t - swipe) / 0.35))
            nx, ny = hx + d * (10 + 6 * k) * s, hy - 10 * s + k * 26 * s
        else:
            nx, ny = hx + d * 6 * s, hy - 14 * s
        if held:
            nx, ny = hx + d * 4 * s, hy - 18 * s
        self.pixel_line(px + hx, py + hy, px + nx, py + ny, pb, GAG_C["wood"])   # the handle
        r = 6 * s
        for i in range(14):   # the hoop, and the net hanging off it
            ang = i / 14 * 2 * math.pi
            x, y = nx + math.cos(ang) * r, ny + math.sin(ang) * r * 0.5
            rect(x - pb / 2, y - pb / 2, x + pb / 2, y + pb / 2, GAG_C["net"])
        rect(nx - r * 0.7, ny, nx + r * 0.7, ny + r * 1.2, GAG_C["net"], stipple="gray25")
        rows = BUG_A if int(t * 10) % 2 else BUG_B
        gb = max(2, round(3 * s))
        bw_, bh_ = len(rows[0]) * gb, len(rows) * gb
        if a.get("caught") or held:   # in the net
            pic(rows, BUG_C, nx - bw_ / 2, ny + pb, gb)
        elif t < a["dur"]:
            bx = a["bug"] - left
            if -60 * s < bx < pet_w + 60 * s:
                pic(rows, BUG_C, bx - bw_ / 2, pet_h - bh_, gb, flip=a["bv"] < 0 or a.get("free") and d < 0)

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

    def draw_dig(self, t, side, px, py, sink, pb, pet_w, pet_h, rect, pic, hand):
        s = self.s()
        hw = 28 * s
        hx = self.beside(side, hw, 10) + hw / 2
        if t < 9.2:   # the hole, getting bigger
            k = min(1.0, max(0.0, (t - 0.6) / 4.5))
            if k > 0:
                self.blob(px + hx, py + pet_h - pb, (6 + 8 * k) * s, 3 * s, pb, GAG_C["soil2"])
                self.blob(px + hx, py + pet_h - pb, (4 + 7 * k) * s, 2.2 * s, pb, GAG_C["hole"])
            for i in range(int(k * 6)):   # a heap of dirt beside it
                rect(hx - side * (hw / 2 + 2 * pb) - i * pb * 0.6, pet_h - (i % 3 + 1) * pb, hx - side * (hw / 2 + 2 * pb)
                     - i * pb * 0.6 + 3 * pb, pet_h, SOIL_C[i % 2])
        if t < 5.4:   # the spade
            gx, gy = hand(1)
            stroke = next((at for at in DIGS if at <= t < at + 0.3), None)
            down = math.sin(math.pi * (t - stroke) / 0.3) if stroke is not None else 0.0
            tx, ty = hx - side * 2 * s, pet_h - 14 * s + down * 10 * s
            self.pixel_line(px + gx, py + gy, px + tx, py + ty, pb, GAG_C["wood"])
            rect(tx - 3 * pb, ty, tx + 3 * pb, ty + 5 * pb, GAG_C["metal"])
        if 5.6 <= t < 9.2:   # a sign comes up out of the hole: 404
            k = smooth((t - 5.6) / 0.5)
            sw, sh = 15 * pb, 9 * pb
            top = pet_h - pb - (sh + 6 * pb) * k
            rect(hx - pb / 2, top + sh, hx + pb / 2, pet_h - pb, GAG_C["wood"])   # the post
            rect(hx - sw / 2, top, hx + sw / 2, top + sh, GAG_C["sign"])
            x = hx - sw / 2 + 1.5 * pb
            for ch in "404":
                pic(DIGITS[ch], {"k": GAG_C["ink"]}, x, top + 2 * pb)
                x += 4 * pb
