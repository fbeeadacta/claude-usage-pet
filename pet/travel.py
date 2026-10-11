# part of the Pet: getting somewhere it can't walk or jump to: a taskbar too high to jump to, a monitor stacked
# above or below, or a window too high to jump onto. it climbs a rope, a ladder, a beanstalk or a tower of boxes,
# flies with wings, a jetpack, balloons or a ufo, fires itself out of a cannon, shoots portals, teleports,
# or drops through a trapdoor in the taskbar.
# things away from the mascot (the rope, ladder, beanstalk, boxes, cannon, portals, and the dust and smoke)
# are drawn on a see-through "stage" window over the whole trip, in screen pixels. things on the mascot
# (wings, jetpack, balloons, hat, the ufo above it) are drawn in its own window, from the body's top left.
import math
import random

from .art import (ARMS, BALLOON_C, BEAM_C, BOX_C, CANNON_C, FLASH_C, GUN, GUN_C, HAT, HAT_COLOURS, HATCH_C, HOOK,
    HOOK_C, JET_C, LADDER_C, LEFT_WAVE, LEGS_AIR, LEGS_STAND, LEGS_STEP, PORTAL_C, ROPE_C, SMOKE_C, SOIL_C, SPARK_C,
    STALK_C, STAR_C, STRING_C, UFO, UFO_C, UFO_LIGHTS, WAND_C, WAVE, WING_C, WINGS)
from .config import GRAVITY, WALK_EASE, WALK_SPEED
from .lines import (BALLOON_DROP, BALLOON_RIDE, BEAN_LINES, BEAN_TOP, BOX_LINES, BOX_TOP, CANNON_LAND,
    CANNON_LINES, HATCH_LINES, JET_LAND, JET_LINES, LADDER_LINES, LADDER_TOP, PORTAL_LINES, PORTAL_OUT,
    ROPE_LINES, ROPE_TOP, TELE_END, TELE_LINES, UFO_RIDE, UFO_RIDE_END, WING_LAND, WING_LINES)
from .sprites import Stage
from .winapi import window_box

CLIMBERS = ("rope", "ladder", "beanstalk", "boxes")   # go straight up from the floor it's standing on
PULL = 0.42           # one hand-over-hand pull on the rope (seconds)
BALLOONS = ((-11, -50), (1, -60), (12, -47))   # where the balloons float, from above its right hand (x 1x px)
# flying: (top speed, how quickly it speeds up and slows down, longest flight in seconds). pixels at 1x.
FLIGHT = {"wings": (170, 420, 9), "jetpack": (330, 520, 7), "balloon": (85, 55, 12), "ufo": (260, 330, 8)}
UFO_LIFT = 62         # how far the beam lifts it up into the saucer
DUSTS = ("#cfc6b4", "#a39a88")
FADES = {1: "gray75", 2: "gray50", 3: "gray25"}   # see-through steps while it teleports (4 = gone)


def smooth(k):
    k = min(1.0, max(0.0, k))
    return k * k * (3 - 2 * k)


def ease_out(k):
    k = min(1.0, max(0.0, k))
    return 1 - (1 - k) ** 2


def path_at(pts, d):
    # the point d along a path of straight bits, and whether that's the end of it
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if d <= seg:
            k = d / seg if seg else 1.0
            return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, False
        d -= seg
    return pts[-1][0], pts[-1][1], True


def portal_rows(k, glint):
    # a portal on the floor seen from the side: a flat glowing oval, k = how far open (0 to 1)
    w, h = max(4, round(28 * k / 2) * 2), max(2, round(8 * k / 2) * 2)
    rows = []
    for j in range(h):
        line = ""
        for i in range(w):
            nx, ny = (i + 0.5 - w / 2) / (w / 2), (j + 0.5 - h / 2) / (h / 2)
            r = nx * nx + ny * ny
            if r > 1:
                line += "."
            elif r > 0.6:   # the rim, with a glint that runs round it
                ang = math.atan2(ny, nx)
                line += "w" if abs((ang - glint + math.pi) % (2 * math.pi) - math.pi) < 0.35 else "l"
            else:
                line += "o" if r > 0.25 else "d"
        rows.append(line)
    return rows


class TravelMixin:
    # ---- deciding to go ----
    def try_stacked_trip(self):
        # now and then, off to a monitor above or below this one
        to = self.stacked()
        return bool(to) and self.start_trip(random.choice(to))

    def start_trip(self, to, how=None, win=None, tx=None, exact=False):
        # off to screen `to` (or onto window `win`, a (hwnd, left, top, right, bottom) on this screen), one way
        # or another. everything is worked out from where the screens and windows are right now.
        # returns True if it set off.
        if (not self.anim.get() or self.trip or self.held or self.hidden or self.ufo or not self.grounded()
                or (win is None and self.plat is not None)):
            return False
        s = self.s()
        sc, o = self.screens[self.si], self.screens[to]
        pw, ph = self.pet_px
        room = max(self.half, pw / 2 + 24 * s)   # (far enough in that the screen edge doesn't push it)
        m = pw / 2 + 10 * s
        here = (self.plat_box[1] + m, self.plat_box[3] - m) if self.plat is not None else (sc.wl + m, sc.wr - m)
        side, edge, span = 1, None, None
        if win is not None:   # a window too high to jump onto
            kind, ty, span = "window", win[2], (win[1] + m, win[3] - m)
            if span[0] > span[1]:
                return False
            tx = min(max(self.x if tx is None else tx, span[0]), span[1])
        elif o.ml >= sc.mr - 2 or o.mr <= sc.ml + 2:   # side by side: up over the screen edge
            side = 1 if o.ml >= sc.mr - 2 else -1
            edge = sc.mr if side > 0 else sc.ml
            kind, tx, ty = "side", edge + side * room, o.wb
            if ty >= self.y:
                return False   # lower: it just walks off and drops (or parachutes) down
        else:   # stacked: somewhere over the part both screens share
            span = (max(sc.wl, o.wl) + room, min(sc.wr, o.wr) - room)
            if span[0] > span[1]:
                return False
            tx = min(max(self.x + random.uniform(-90, 90) * s, span[0]), span[1])
            kind, ty = ("up" if o.wb < sc.wb else "down"), o.wb
        if kind != "side":
            side = 1 if tx >= self.x else -1
        rise = self.y - ty
        cx = None
        ways = ["portal", "teleport"]   # these go anywhere
        if kind == "down":
            ways += ["wings", "jetpack", "ufo"] + (["hatch"] if span[0] <= self.x <= span[1] else [])
        elif kind != "side" or ty - ph - 80 * s > sc.mt:   # (room on this screen to get up level with the ledge)
            ways += ["wings", "jetpack", "balloon", "ufo", "cannon"]
            # the climbs go straight up from the floor it's on: beside the screen edge, or right under the target
            if kind == "side":
                cx = edge - side * m
            else:
                lo, hi = max(span[0], here[0]), min(span[1], here[1])
                cx = min(max(self.x, lo), hi) if lo <= hi else None
            if cx is not None and here[0] - 1 <= cx <= here[1] + 1:
                ways += ["rope", "ladder", "beanstalk"] + (["boxes"] if rise < 800 * s else [])
        if exact and how not in ways:
            return False   # (dev mode: that way or not at all)
        how = how if how in ways else random.choice(ways)
        if how in CLIMBERS and kind != "side":
            tx = cx   # it climbs right up onto the spot
        if how == "rope" and kind == "side":   # (its hand on the rope, right by the edge)
            cx = edge - side * (7.5 * max(1, round(4 * s)) + 2 * s)
        a = {"how": how, "stage": "walk", "t": 0.0, "st": 0.0, "to": to, "kind": kind, "side": side, "edge": edge,
             "x0": self.x, "y0": self.y, "tx": tx, "ty": ty, "cx": cx, "s": s, "clip": None, "fade": 0, "fx": [],
             "win": win[0] if win else None, "wbox": tuple(win[1:5]) if win else None, "on_win": False,
             "sx": cx if how in CLIMBERS else self.x, "v": 0.0}
        self.wake(hop=False)
        self.stop_fetch()
        self.goto_x = self.goto_why = None
        self.state, self.act, self.vx, self.vy, self.walk_v = "trip", None, 0.0, 0.0, 0.0
        self.plat, self.through = None, False
        self.trip = a
        self.tally("trips")
        if self.trip_stage is None:
            self.trip_stage = Stage(self.root)
        xs, ys = (a["x0"], tx) + ((cx,) if cx is not None else ()), (a["y0"], ty)
        if self.trip_stage.place(min(xs) - 230 * s, min(ys) - 340 * s, max(xs) + 230 * s, max(ys) + 70 * s):
            self.root.lift()   # (the mascot in front of its props)
        if abs(a["sx"] - self.x) < 1:
            self.begin(a)
        return True

    def begin(self, a):
        a["x0"] = self.x   # (where it ended up after walking over)
        self.next_stage(a, "")
        getattr(self, "begin_" + a["how"])(a, a["s"])

    def end_trip(self, landed=False):
        # done (or interrupted: picked up, hidden, screens changed). tidies the props away.
        a = self.trip
        if not a:
            return
        self.trip = None
        if self.trip_stage is not None:
            self.trip_stage.hide()
        if self.state == "trip":
            self.state, self.state_t = "idle", 2.0
        if not landed:
            self.angle = 0.0
        i = self.find_screen(self.x, self.y - 1)
        self.si = i if i is not None else self.nearest_screen(self.x, self.y - 1)
        if not (landed and a["on_win"]):
            self.plat = None
            self.y = min(self.y, self.screens[self.si].wb)
        self.through = not landed   # (left up in the air: straight down to the taskbar)

    def next_stage(self, a, stage):
        a["stage"], a["st"] = stage, 0.0

    # ---- every frame ----
    def trip_tick(self, dt, s):
        a = self.trip
        a["t"] += dt
        a["st"] += dt
        if a["win"]:
            box = window_box(a["win"])
            if box is None or any(abs(p - q) > 2 for p, q in zip(box, a["wbox"])):   # its window moved or went
                self.end_trip(landed=a["on_win"])
                return
        if a["stage"] == "walk":
            self.trip_walk(a, dt, a["s"])
        else:
            getattr(self, "tick_" + a["how"])(a, dt, a["s"])
        if self.trip is not a:
            return
        if a["clip"] is None and not a["on_win"]:   # (keeps track of which screen it's over, for its floor)
            i = self.find_screen(self.x, self.y - 1)
            if i is not None:
                self.si = i
        for p in a["fx"]:
            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += p["g"] * dt
            if p["drag"]:
                p["vx"] *= max(0.0, 1 - p["drag"] * dt)
                p["vy"] *= max(0.0, 1 - p["drag"] * dt)
        a["fx"] = [p for p in a["fx"] if p["life"] > 0]
        self.draw_stage(a)

    def trip_walk(self, a, dt, s):
        # walks to where it'll start from: speeds up, and slows down to stop right there
        dx = a["sx"] - self.x
        full = WALK_SPEED * 2.2 * s
        acc = full / WALK_EASE
        a["v"] = min(full, a["v"] + acc * dt, math.sqrt(2 * acc * abs(dx)) + 4 * s)
        step = min(abs(dx), a["v"] * dt)
        self.x += math.copysign(step, dx)
        if abs(dx) > 0.5:
            self.dir = 1 if dx > 0 else -1
        self.walk_steps(dt)
        if abs(a["sx"] - self.x) < 0.5:
            self.x = a["sx"]
            self.dir = a["side"]
            self.begin(a)

    def walk_steps(self, dt):
        self.step_t += dt
        if self.step_t >= 0.18:
            self.step_t, self.step = 0.0, self.step + 1

    def arrive(self, a, lines, x=None):
        # standing on the new taskbar (or window)
        self.x, self.y, self.si = a["tx"] if x is None else x, a["ty"], a["to"]
        self.vx = self.vy = 0.0
        self.squash_t, self.happy_t = 0.07, 1.5
        if a["win"]:
            box = window_box(a["win"])
            if box and box[0] <= self.x <= box[2]:
                self.plat, self.plat_box, self.y = a["win"], (a["win"],) + tuple(box), box[1]
                a["on_win"] = True
        if lines and random.random() < 0.8:
            self.say(self.pick(lines), force=True)

    def hop_over(self, a, s, lines, t=0.55):
        # the last little hop: from the top of its climb over onto the ledge (or the window right there)
        k = min(1.0, a["st"] / t)
        x0, y0 = a["m0"]
        self.x = x0 + (a["tx"] - x0) * smooth(k)
        self.y = y0 + (a["ty"] - y0) * k - 4 * 26 * s * k * (1 - k)
        if k >= 1:
            self.arrive(a, lines)
            return True
        return False

    def hand_at(self, side, raised=True):
        # where its hand is on the screen (the right hand for side 1)
        s = self.trip["s"]
        bw, bh = max(1, round(4 * s)), max(2, round(8 * s))
        pw, ph = self.pet_px
        return (self.x - pw / 2 + (16.5 if side > 0 else 1.5) * bw,
                self.y - ph + (0.5 if raised else 2.5) * bh)

    def fx(self, a, x, y, colour, vx=0.0, vy=0.0, life=0.6, size=None, g=0.0, drag=0.0, shrink=True):
        # a speck of dust, smoke, spark or leaf on the stage (in screen pixels, so it stays where it was made)
        a["fx"].append({"x": x, "y": y, "vx": vx, "vy": vy, "life": life, "max": life, "c": colour,
                        "size": size or max(1, round(2 * a["s"])), "g": g, "drag": drag, "shrink": shrink})

    def burst(self, a, x, y, colours, n, speed, life=0.5, size=None, g=0.0, up=0.0, drag=2.0):
        # n bits flying out of (x, y) every which way (up = a push upwards)
        for _ in range(n):
            ang = random.uniform(0, 2 * math.pi)
            v = random.uniform(0.4, 1.0) * speed
            self.fx(a, x, y, random.choice(colours), math.cos(ang) * v, math.sin(ang) * v - up,
                    random.uniform(0.6, 1.0) * life, size, g, drag)

    def smoke(self, a, x, y, n=1, spread=6, up=20, life=0.9):
        s = a["s"]
        for _ in range(n):
            self.fx(a, x + random.uniform(-spread, spread) * s, y, random.choice(SMOKE_C),
                    random.uniform(-15, 15) * s, -random.uniform(0.5, 1.0) * up * s, random.uniform(0.6, 1.0) * life,
                    max(2, round(random.choice((4, 5, 6)) * s)), drag=1.0)

    # ---- flying along a path, with a speed curve ----
    def flight(self, a, pts, how):
        # sets up a path. it speeds up from a standstill, slows into each corner and slows to a stop at the end.
        clean = [pts[0]]
        for p in pts[1:]:
            if math.dist(p, clean[-1]) > 1:
                clean.append(p)
        if len(clean) == 1:
            clean.append(clean[0])
        marks, d = [0.0], 0.0
        for p, q in zip(clean, clean[1:]):
            d += math.dist(p, q)
            marks.append(d)
        top, acc, longest = FLIGHT[how]
        s = a["s"]
        a.update(pts=clean, marks=marks, d=0.0, len=d, acc=acc * s, vmax=max(top * s, 1.6 * d / longest))

    def fly(self, a, dt):
        # one frame along the path. returns (x, y, done, speed)
        near = min(abs(a["d"] - m) for m in a["marks"])   # (distance to the nearest corner, start or end)
        v = max(a["vmax"] * 0.07, min(a["vmax"], math.sqrt(2 * a["acc"] * near)))
        a["d"] = min(a["len"], a["d"] + v * dt)
        x, y, done = path_at(a["pts"], a["d"])
        return x, y, done or a["d"] >= a["len"] - 0.5, v

    def flight_path(self, a, clear):
        # up (or down), across, and onto the spot
        x0, y0, tx, ty, s = a["x0"], a["y0"], a["tx"], a["ty"], a["s"]
        if a["kind"] == "side":
            return [(x0, y0), (x0, ty - clear), (tx, ty - clear), (tx, ty)]
        if a["kind"] == "up":   # over to the shared part, then straight up through the gap
            return [(x0, y0), (tx, y0 - 70 * s), (tx, ty - clear), (tx, ty)]
        if a["kind"] == "down":
            return [(x0, y0), (x0, y0 - 25 * s), (tx, y0 - 25 * s), (tx, ty)]
        return [(x0, y0), (x0, min(y0, ty) - clear), (tx, ty - clear), (tx, ty)]   # onto a window

    # ---- a grappling hook and a rope ----
    def begin_rope(self, a, s):
        bw, b = max(1, round(4 * s)), max(1, round(2 * s))
        side, ty = a["side"], a["ty"]
        a["rx"] = self.x + side * 7.5 * bw   # the rope hangs from its hand
        if a["kind"] == "side":
            # the hook bites on the corner of the higher taskbar, just past the screen edge, and the rope
            # comes back over that corner and hangs straight down this side of it
            hx = a["edge"] + side * 7 * s
            a["drape"] = [(hx, ty - b), (a["edge"] - side * b / 2, ty + b / 2)]
        else:   # (onto a window or a stacked taskbar: the hook bites on the top edge right above it)
            hx = a["rx"]
            a["drape"] = [(hx, ty + b)]
        a["anchor"] = (hx, ty + 2 * b)   # where the hook sits: its ring a little below the top, prongs over it
        a["rate"] = max(80 * s, (a["y0"] - ty) / 8)   # climbing speed (faster up very long ropes)
        a["hook"] = a["rope"] = None
        self.next_stage(a, "swing")
        if random.random() < 0.8:
            self.say(self.pick(ROPE_LINES), force=True)

    def hanging(self, a, bottom):
        # the rope once the hook has caught: over the corner and straight down to `bottom`
        top = a["drape"][-1][1]
        return a["drape"] + [(a["rx"], top), (a["rx"], bottom)] if bottom > top + 1 else None

    def tick_rope(self, a, dt, s):
        st, side, b = a["st"], a["side"], max(1, round(2 * s))
        ax, ay = a["anchor"]
        if a["stage"] == "swing":   # whirling the hook round over its head
            if st >= 1.3:
                a["from"] = self.hand_at(side)
                a["fly"] = max(0.35, math.dist(a["from"], (ax, ay)) / (1500 * s))
                self.next_stage(a, "throw")
        elif a["stage"] == "throw":   # up it goes, prongs first, trailing the rope
            k = ease_out(st / a["fly"])
            (x0, y0) = a["from"]
            hx, hy = x0 + (ax - x0) * k, y0 + (ay - y0) * k - math.sin(math.pi * k) * 30 * s
            hand = self.hand_at(side)
            a["hook"], a["rope"] = (hx, hy), [(hx, hy - b), hand]
            if st >= a["fly"]:
                self.play("clink")
                a["hook"], a["rope"] = (ax, ay), self.hanging(a, a["y0"])
                self.burst(a, ax, a["ty"], (SPARK_C[0], "#ffffff"), 8, 90 * s, 0.35)
                self.next_stage(a, "tug")
        elif a["stage"] == "tug":   # a couple of tugs to check it holds
            if st >= 0.7:
                self.next_stage(a, "climb")
        elif a["stage"] == "climb":   # hand over hand: each pull speeds up and slows down
            n, frac = divmod(st / PULL, 1)
            self.y = a["y0"] - a["rate"] * PULL * (n + smooth(frac))
            if self.y <= a["ty"] - 3 * s:
                self.y = a["ty"] - 3 * s
                a["m0"] = (self.x, self.y)
                self.next_stage(a, "mantle")
        elif a["stage"] == "mantle":   # hauls itself up over the edge
            if self.hop_over(a, s, ROPE_TOP, 0.6):
                self.burst(a, self.x, self.y, DUSTS, 6, 60 * s, 0.4)
                self.next_stage(a, "reel")
        elif a["stage"] == "reel":   # pulls the rope up, and the hook flies back to its hand
            if st < 0.45:
                a["rope"] = self.hanging(a, a["y0"] + (a["ty"] - a["y0"]) * smooth(st / 0.45))
            elif st < 0.75:
                a["rope"] = None
                k = smooth((st - 0.45) / 0.3)
                hx, hy = self.hand_at(-side, raised=False)
                a["hook"] = (ax + (hx - ax) * k, ay + (hy - ay) * k - math.sin(math.pi * k) * 20 * s)
            else:
                self.end_trip(landed=True)

    def stage_rope(self, a, c, ox, oy, s, b):
        if a["rope"]:   # a twisted rope: straight strands, with darker twists along them
            i = 0
            for (x0, y0), (x1, y1) in zip(a["rope"], a["rope"][1:]):
                n = max(1, round(math.hypot(x1 - x0, y1 - y0) / b))
                if abs(x1 - x0) < 1:   # (straight down: one long block, then the twists on top)
                    c.create_rectangle(round(x0 - b / 2 - ox), round(min(y0, y1) - oy), round(x0 + b / 2 - ox),
                                       round(max(y0, y1) - oy), fill=ROPE_C["a"], outline="")
                for k in range(n + 1):
                    i += 1
                    if abs(x1 - x0) < 1 and i % 3:
                        continue
                    x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                    c.create_rectangle(round(x - b / 2 - ox), round(y - b / 2 - oy), round(x + b / 2 - ox),
                                       round(y + b / 2 - oy), fill=ROPE_C["b"] if i % 3 == 0 else ROPE_C["a"],
                                       outline="")
        if a["hook"]:
            self.stage_glyph(c, ox, oy, HOOK, HOOK_C, b, *a["hook"])

    def stage_glyph(self, c, ox, oy, rows, colours, b, x, y):
        # a block picture on the stage, by its bottom middle (no dark edge)
        x0, y0 = round(x - len(rows[0]) * b / 2 - ox), round(y - len(rows) * b - oy)
        for j, row in enumerate(rows):
            i = 0
            while i < len(row):   # (runs of one colour as one block)
                ch, k = row[i], i
                while k < len(row) and row[k] == ch:
                    k += 1
                if ch != ".":
                    c.create_rectangle(x0 + i * b, y0 + j * b, x0 + k * b, y0 + (j + 1) * b,
                                       fill=colours.get(ch, colours.get("#")), outline="")
                i = k

    # ---- a ladder that unfolds upwards ----
    def begin_ladder(self, a, s):
        b = max(1, round(2 * s))
        a["lx"], a["top"] = a["cx"], a["ty"] - 8 * b   # (sticks up a little past the ledge)
        full = a["y0"] - a["top"]
        a["sec"] = 26 * b   # one section of the ladder
        a["n"] = max(1, math.ceil(full / a["sec"]))
        a["ext"] = min(2.4, max(0.8, full / 420 / s))   # how long it takes to unfold
        a["h"] = 0.0
        steps = max(1, math.ceil((a["y0"] - a["ty"]) / (14 * b)))
        a["step_t"] = min(0.32, 6.5 / steps)
        self.next_stage(a, "pull")
        self.play("pop")
        if random.random() < 0.8:
            self.say(self.pick(LADDER_LINES), force=True)

    def tick_ladder(self, a, dt, s):
        st, b = a["st"], max(1, round(2 * s))
        full = a["y0"] - a["top"]
        if a["stage"] == "pull":   # out comes a short ladder
            a["h"] = min(full, a["sec"]) * ease_out(st / 0.4)
            if st >= 0.5:
                self.burst(a, a["lx"], a["y0"], DUSTS, 6, 50 * s, 0.4, up=20 * s)
                self.next_stage(a, "extend")
        elif a["stage"] == "extend":   # each section slides up and clicks into place
            per = a["ext"] / a["n"]
            i, frac = divmod(st / per, 1)
            h = min(full, a["sec"] + (full - a["sec"]) * min(1.0, (i + ease_out(frac)) / a["n"]))
            if int(st / per) != int((st - dt) / per) and h < full:   # click!
                self.burst(a, a["lx"], a["y0"] - h, (SPARK_C[0], "#ffffff"), 3, 50 * s, 0.25)
            a["h"] = h
            if st >= a["ext"]:
                a["h"] = full
                self.next_stage(a, "climb")
        elif a["stage"] == "climb":   # two rungs at a time, each step speeding up and slowing down
            n, frac = divmod(st / a["step_t"], 1)
            self.y = max(a["ty"], a["y0"] - 14 * b * (n + smooth(frac)))
            if self.y <= a["ty"]:
                a["m0"] = (self.x, self.y)
                self.next_stage(a, "over")
        elif a["stage"] == "over":
            if self.hop_over(a, s, LADDER_TOP, 0.5 if a["kind"] == "side" else 0.3):
                self.next_stage(a, "fold")
        elif a["stage"] == "fold":   # pulls the ladder up after itself, and it folds away
            a["h"] = full * (1 - smooth(st / 0.6))
            if st >= 0.6:
                self.burst(a, a["lx"], a["top"], DUSTS, 8, 70 * s, 0.4)
                self.next_stage(a, "done")
        elif st >= 0.4:
            self.end_trip(landed=True)

    def stage_ladder(self, a, c, ox, oy, s, b):
        h = a["h"]
        if h < 1:
            return
        rail, rung = LADDER_C
        x = a["lx"] - ox
        if a["stage"] == "fold":   # (folding: the bottom comes up to the top)
            y0, y1 = a["top"] - oy, a["top"] + h - oy
        else:
            y1 = a["y0"] - oy
            y0 = y1 - h
        half = 6 * b
        for k in range(int((y1 - y0) / (7 * b))):   # the rungs
            ry = round(y1 - (k + 0.6) * 7 * b)
            c.create_rectangle(round(x - half), ry, round(x + half), ry + b, fill=rung, outline="")
        for sx in (-half - b, half):   # the rails
            c.create_rectangle(round(x + sx), round(y0), round(x + sx + b), round(y1), fill=rail, outline="")

    # ---- a magic beanstalk ----
    def begin_beanstalk(self, a, s):
        a["bx"], a["h"], a["leaves"] = a["cx"], 0.0, []
        a["full"] = a["y0"] - a["ty"]
        a["grow"] = min(4.5, max(1.4, a["full"] / 260 / s))
        y, i = 22 * s, 0
        while y < a["full"] - 10 * s:   # where the leaves will come out, left and right in turn
            a["leaves"].append((y, -1 if i % 2 else 1))
            y, i = y + random.uniform(24, 34) * s, i + 1
        self.next_stage(a, "plant")
        if random.random() < 0.8:
            self.say(self.pick(BEAN_LINES), force=True)

    def sway(self, a, up):
        # how far the stalk leans at `up` pixels above its root: more towards the tip
        s, h = a["s"], max(a["h"], 1)
        tip = math.sin(a["t"] * 2.1) * 6 * s * min(1.0, h / (120 * s))
        return tip * (min(up, h) / h) ** 1.5 + math.sin(up / (16 * s) + a["t"] * 3) * 1.2 * s

    def tick_beanstalk(self, a, dt, s):
        st = a["st"]
        if a["stage"] == "plant":   # pokes a bean into the floor, and dirt flies
            if 0.45 <= st < 0.45 + dt:
                self.play("pop")
                self.burst(a, a["bx"], a["y0"], SOIL_C, 12, 80 * s, 0.5, g=300 * s, up=60 * s, drag=0.5)
            if st >= 1.0:
                self.next_stage(a, "grow")
        elif a["stage"] == "grow":   # up it shoots, with the mascot riding the top leaf
            a["h"] = a["full"] * smooth(st / a["grow"])
            self.x, self.y = a["bx"] + self.sway(a, a["h"]), a["y0"] - a["h"]
            if random.random() < dt * 8:   # bits of leaf drifting off
                up = random.uniform(0.2, 1.0) * a["h"]
                self.fx(a, a["bx"] + self.sway(a, up), a["y0"] - up, random.choice(STALK_C[1:]),
                        random.uniform(-25, 25) * s, random.uniform(-10, 10) * s, 1.2, g=40 * s, drag=1.0)
            if st >= a["grow"]:
                a["m0"] = (self.x, self.y)
                self.next_stage(a, "over")
        elif a["stage"] == "over":
            if self.hop_over(a, s, BEAN_TOP, 0.5 if a["kind"] == "side" else 0.25):
                self.next_stage(a, "wither")
        elif a["stage"] == "wither":   # back down into the ground it goes
            a["h"] = a["full"] * (1 - smooth(st / 1.0))
            if st >= 1.0:
                self.burst(a, a["bx"], a["y0"], SOIL_C, 8, 60 * s, 0.4, g=300 * s, up=40 * s)
                self.next_stage(a, "done")
        elif st >= 0.6:
            self.end_trip(landed=True)

    def stage_beanstalk(self, a, c, ox, oy, s, b):
        stalk, streak, leaf = STALK_C
        h, bx, y0 = a["h"], a["bx"] - ox, a["y0"] - oy
        if a["stage"] in ("plant", "grow", "done") or h > 0:   # a little mound of soil
            c.create_rectangle(round(bx - 4 * b), round(y0 - b), round(bx + 4 * b), round(y0), fill=SOIL_C[0],
                               outline="")
        step = 2 * b
        for k in range(int(h / step)):   # the stalk, a block at a time
            up = k * step
            x = bx + self.sway(a, up)
            c.create_rectangle(round(x - 1.5 * b), round(y0 - up - step), round(x + 1.5 * b), round(y0 - up),
                               fill=streak if k % 5 == 0 else stalk, outline="")
        for up, d in a["leaves"]:   # leaves unfurl as the stalk grows past them
            k = min(1.0, (h - up) / (30 * s))
            if k <= 0:
                continue
            x = bx + self.sway(a, up) + d * 1.5 * b
            for j, w in enumerate((2, 4, 5, 4, 2)):
                ww = max(1, round(w * k)) * b
                xx = x + d * j * b * k
                yy = y0 - up - j * b * 0.7
                c.create_rectangle(round(min(xx, xx + d * ww)), round(yy - b), round(max(xx, xx + d * ww)), round(yy),
                                   fill=leaf if j % 2 else stalk, outline="")
        if h > 4 * b and a["stage"] in ("grow", "over"):   # a big flat leaf at the top to stand on
            x = bx + self.sway(a, h)
            c.create_rectangle(round(x - 9 * b), round(y0 - h), round(x + 9 * b), round(y0 - h + b), fill=leaf,
                               outline="")
            c.create_rectangle(round(x - 6 * b), round(y0 - h + b), round(x + 6 * b), round(y0 - h + 2 * b),
                               fill=stalk, outline="")

    # ---- a tower of cardboard boxes ----
    def begin_boxes(self, a, s):
        rise = a["y0"] - a["ty"]
        n = max(1, min(14, math.ceil(rise / (34 * s))))
        a["n"], a["hb"], a["boxes"], a["vy"], a["air"] = n, rise / n, [], 0.0, False
        a["bw"] = self.pet_px[0] * 0.8
        a["floor"] = a["y0"]
        specs, dx = [], 0.0
        for _ in range(n):   # no two boxes alike: a bit off to one side, wider or narrower, different markings
            dx = max(-9 * s, min(9 * s, dx + random.uniform(-5, 5) * s))
            specs.append({"dx": dx, "ang": 0.0, "w": a["bw"] * random.uniform(0.82, 1.06),
                          "kind": random.choice(("plain", "label", "arrows", "handle", "tape", "label"))})
        a["specs"] = specs
        self.next_stage(a, "stack")
        if random.random() < 0.8:
            self.say(self.pick(BOX_LINES), force=True)

    def tick_boxes(self, a, dt, s):
        st, g = a["st"], GRAVITY * s
        if a["stage"] == "stack":   # a hop, a box slides in underneath, land on it. again.
            i = len(a["boxes"])
            if not a["air"]:
                if st >= 0.14:
                    a["vy"], a["air"] = -math.sqrt(2 * g * (a["hb"] + 14 * s)), True
                    a["hop"] = (self.x, a["cx"] + a["specs"][min(i, a["n"] - 1)]["dx"], 0.0,
                                -a["vy"] / g + math.sqrt(2 * 14 * s / g))
                return
            x0, x1, t0, tt = a["hop"]
            a["hop"] = (x0, x1, t0 + dt, tt)
            self.x = x0 + (x1 - x0) * smooth((t0 + dt) / tt)   # (a little sideways, onto the middle of the next box)
            self.y += a["vy"] * dt + 0.5 * g * dt * dt
            a["vy"] += g * dt
            top = a["y0"] - (i + 1) * a["hb"]
            if a["vy"] >= 0 and i < a["n"] and self.y <= top + 1:   # top of the hop: box!
                a["boxes"].append(top)
                a["floor"] = top
                bx = a["cx"] + a["specs"][i]["dx"]
                for d in (-1, 1):
                    self.burst(a, bx + d * a["bw"] / 2, top + a["hb"] / 2, (BOX_C[2], "#d8c3a0"), 3, 60 * s, 0.35)
            if a["vy"] > 0 and self.y >= a["floor"]:   # landed on it
                self.y, a["air"] = a["floor"], False
                self.squash_t = 0.06
                self.play("thud")
                self.next_stage(a, "stack")
                if len(a["boxes"]) >= a["n"]:
                    a["m0"] = (self.x, self.y)
                    self.next_stage(a, "over")
        elif a["stage"] == "over":
            if self.hop_over(a, s, BOX_TOP, 0.5 if a["kind"] == "side" else 0.2):
                a["falling"] = [dict(a["specs"][i], x=a["cx"] + a["specs"][i]["dx"], y=top + a["hb"] / 2,
                                     vx=random.uniform(-150, 150) * s, vy=-random.uniform(0, 120) * s,
                                     va=random.uniform(-5, 5)) for i, top in enumerate(a["boxes"])]
                a["boxes"] = []
                self.next_stage(a, "topple")
        elif a["stage"] == "topple":   # timber! the boxes tumble down and squash flat
            for bx in a["falling"]:
                bx["vy"] += g * dt
                bx["x"] += bx["vx"] * dt
                bx["y"] += bx["vy"] * dt
                bx["ang"] += bx["va"] * dt
                if bx["y"] >= a["y0"] - a["hb"] / 3:
                    bx["down"] = True
                    self.burst(a, bx["x"], a["y0"], (BOX_C[0], BOX_C[2], "#d8c3a0"), 6, 80 * s, 0.45, up=40 * s)
            a["falling"] = [bx for bx in a["falling"] if not bx.get("down")]
            if not a["falling"] or st > 3:
                self.next_stage(a, "done")
        elif st >= 0.5:
            self.end_trip(landed=True)

    def stage_boxes(self, a, c, ox, oy, s, b):
        hb = a["hb"]
        for i, top in enumerate(a["boxes"]):
            sp = a["specs"][i]
            self.draw_box(c, a["cx"] + sp["dx"] - ox, top + hb / 2 - oy, sp["w"], hb, sp["ang"], sp["kind"], b)
        for bx in a.get("falling", ()):   # tumbling
            self.draw_box(c, bx["x"] - ox, bx["y"] - oy, bx["w"], hb, bx["ang"], bx["kind"], b)

    def draw_box(self, c, x, y, w, h, ang, kind, b):
        # one cardboard box, its middle at (x, y), turned by ang: a shady side, the lid's edge and its seam, tape,
        # and maybe a shipping label, "this way up" arrows, a handle slot or an extra strip of tape
        face, lid, tape = BOX_C
        ca, sa = math.cos(ang), math.sin(ang)
        hw, hh = w / 2, h / 2

        def r(x1, y1, x2, y2, col):
            pts = []
            for lx, ly in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
                pts += [x + lx * ca - ly * sa, y + lx * sa + ly * ca]
            c.create_polygon(pts, fill=col, outline="")

        r(-hw, -hh, hw, hh, face)
        r(hw - w * 0.16, -hh, hw, hh, "#b3854a")       # the side in the shade
        r(-hw, -hh, hw, -hh + 2 * b, lid)               # the lid's edge
        r(-hw, hh - b, hw, hh, lid)                     # and the bottom's
        tb = -hh + min(h * 0.38, 11 * b)
        r(-1.2 * b, -hh, 1.2 * b, tb, tape)             # tape down over the seam
        r(-1.2 * b, tb - b * 0.6, 1.2 * b, tb, "#d4b67c")
        r(-0.3 * b, -hh, 0.3 * b, -hh + 2 * b, "#8f6634")   # the seam between the flaps
        if h < 12 * b:
            return
        if kind == "label":   # a shipping label: two lines of writing and a red stripe
            lx0, lx1, ly0, ly1 = -hw * 0.82, -hw * 0.18, hh * 0.0, hh * 0.62
            r(lx0, ly0, lx1, ly1, "#f2efe8")
            r(lx0 + b, ly0 + b, lx1 - 2 * b, ly0 + 1.6 * b, "#8e8a82")
            r(lx0 + b, ly0 + 2.6 * b, lx1 - 4 * b, ly0 + 3.2 * b, "#8e8a82")
            r(lx0, ly1 - 1.4 * b, lx1, ly1, "#e5534b")
        elif kind == "arrows":   # "this way up"
            for ax in (-hw * 0.62, -hw * 0.25):
                y0 = hh * 0.05
                for k, half in enumerate((0.5, 1.5, 2.5)):   # the arrowhead, widening down
                    r(ax - half * b, y0 + (k - 2) * b, ax + half * b, y0 + (k - 1) * b, "#6b4a2b")
                r(ax - 0.5 * b, y0 + b, ax + 0.5 * b, y0 + 4 * b, "#6b4a2b")
        elif kind == "handle":   # a hand hole
            r(-hw * 0.24, -hh * 0.02, hw * 0.2, -hh * 0.02 + 2 * b, "#5a3d22")
        elif kind == "tape":     # taped all the way round as well
            r(-hw, -b, hw, b, tape)
            r(-hw, b * 0.4, hw, b, "#d4b67c")

    # ---- little wings ----
    def begin_wings(self, a, s):
        self.flight(a, self.flight_path(a, 30 * s), "wings")
        self.next_stage(a, "sprout")
        if random.random() < 0.8:
            self.say(self.pick(WING_LINES), force=True)

    def tick_wings(self, a, dt, s):
        if a["stage"] == "sprout":
            if a["st"] >= 0.6:
                self.play("flap")
                self.next_stage(a, "fly")
        elif a["stage"] == "fly":
            x, y, done, v = self.fly(a, dt)
            if done:
                self.arrive(a, WING_LAND)
                self.next_stage(a, "fold")
                return
            if abs(x - self.x) > 0.05:
                self.dir = 1 if x > self.x else -1
            self.x, self.y = x, y - abs(math.sin(a["t"] * 5)) * 4 * s * min(1.0, v / (60 * s))   # bobbing
            if random.random() < dt * 3:   # a feather drifts off now and then
                self.fx(a, self.x + random.uniform(-25, 25) * s, self.y - self.pet_px[1] * 0.6, WING_C["#"],
                        random.uniform(-20, 20) * s, random.uniform(5, 25) * s, 1.4, g=20 * s, drag=0.5)
        elif a["stage"] == "fold" and a["st"] >= 0.5:
            self.end_trip(landed=True)

    # ---- a jetpack ----
    def begin_jetpack(self, a, s):
        self.flight(a, self.flight_path(a, 34 * s), "jetpack")
        a["v"] = 0.0
        self.next_stage(a, "strap")
        if random.random() < 0.8:
            self.say(self.pick(JET_LINES), force=True)

    def nozzles(self):
        # where the two jets come out, on the screen
        s = self.trip["s"]
        bw, bh = max(1, round(4 * s)), max(2, round(8 * s))
        pw, ph = self.pet_px
        return [(self.x + d * 9 * bw, self.y - ph + bh // 2 + 3 * bh + 2 * max(1, round(2 * s))) for d in (-1, 1)]

    def tick_jetpack(self, a, dt, s):
        st = a["st"]
        if a["stage"] == "strap":   # a few coughs of smoke, then it roars
            if random.random() < dt * 10:
                for x, y in self.nozzles():
                    self.smoke(a, x, y, up=10, life=0.6)
            if st >= 0.8:
                self.play("jet")
                self.next_stage(a, "fly")
        elif a["stage"] == "fly":
            x, y, done, v = self.fly(a, dt)
            a["v"] = v
            if abs(x - self.x) > 0.05:
                self.dir = 1 if x > self.x else -1
            self.x, self.y = x + math.sin(a["t"] * 13) * 0.8 * s, y   # (a little shudder)
            for nx, ny in self.nozzles():   # sparks off the flames, and a trail of smoke
                if random.random() < dt * 25:
                    self.fx(a, nx + random.uniform(-2, 2) * s, ny + 8 * s, random.choice(FLASH_C),
                            random.uniform(-25, 25) * s, random.uniform(80, 160) * s, 0.25)
                if random.random() < dt * 22:
                    self.smoke(a, nx, ny + 12 * s, up=-30, life=1.1)
            if done:
                self.arrive(a, JET_LAND)
                for nx, ny in self.nozzles():
                    self.smoke(a, nx, a["ty"], n=4, spread=10, up=15, life=0.8)
                self.next_stage(a, "land")
        elif a["stage"] == "land" and st >= 0.6:
            self.end_trip(landed=True)

    # ---- a bunch of balloons ----
    def begin_balloon(self, a, s):
        a["clear"] = 45 * s   # it lets go a little above the floor and drops the last bit
        self.flight(a, self.flight_path(a, a["clear"])[:-1], "balloon")
        a["popped"], a["colours"], a["t0"] = 0, random.sample(range(len(BALLOON_C)), 3), a["t"]
        self.next_stage(a, "out")
        if random.random() < 0.8:
            self.say(self.pick(BALLOON_RIDE), force=True)

    def tick_balloon(self, a, dt, s):
        if a["stage"] == "out":   # three balloons puff up, one after another
            if a["st"] >= 1.2:
                self.next_stage(a, "rise")
        elif a["stage"] == "rise":   # a gentle start, a gentle stop
            x, y, done, v = self.fly(a, dt)
            sway = math.sin(a["st"] * 1.4) * 5 * s * min(1.0, a["st"]) * min(1.0, v / (30 * s))
            self.x, self.y = x + sway, y
            if done:
                self.next_stage(a, "pop")
        elif a["stage"] == "pop":   # pop, pop, pop
            while a["popped"] < 3 and a["st"] >= 0.3 + a["popped"] * 0.3:
                self.pop_balloon(a, s)
            if a["popped"] >= 3:
                if random.random() < 0.6:
                    self.say(self.pick(BALLOON_DROP), force=True)
                a["vy"] = 0.0
                self.next_stage(a, "drop")
        elif a["stage"] == "drop":   # the last little drop
            g = GRAVITY * s
            self.y += a["vy"] * dt + 0.5 * g * dt * dt
            a["vy"] += g * dt
            if self.y >= a["ty"]:
                self.arrive(a, (), x=self.x)
                self.end_trip(landed=True)

    def ride_balloon_at(self, a, i):
        # where balloon i is (middle x, middle y, radius), from the body's top left, or None
        s = a["s"]
        bw = max(1, round(4 * s))
        t = a["t"] - a["t0"]
        r = 11 * s * smooth((t - i * 0.35) / 0.6)
        if r < 2 * s or i < a["popped"]:
            return None
        dx, dy = BALLOONS[i]
        wob = math.sin(a["t"] * 2 + i * 1.7) * 2 * s
        return 16.5 * bw + dx * s + wob, dy * s * (0.5 + 0.5 * smooth(t / 1.0)), r

    def pop_balloon(self, a, s):
        at = self.ride_balloon_at(a, a["popped"])
        a["popped"] += 1
        self.play("pop")
        if not at:
            return
        cx, cy, r = at
        colour = BALLOON_C[a["colours"][a["popped"] - 1]][0]
        for i in range(12):
            ang = i / 12 * 2 * math.pi
            sp = random.uniform(50, 90) * s
            self.parts.append({"kind": "dot", "x": cx + math.cos(ang) * r * 0.6, "y": cy + math.sin(ang) * r * 0.6,
                               "vx": math.cos(ang) * sp, "vy": math.sin(ang) * sp, "g": 120 * s, "life": 0.5,
                               "c": colour})

    # ---- a ride in the ufo ----
    def begin_ufo(self, a, s):
        lift = UFO_LIFT * s
        x0, y0, tx, ty = a["x0"], a["y0"], a["tx"], a["ty"]
        top = min(y0, ty) - lift - 40 * s
        if a["kind"] == "down":
            pts = [(x0, y0 - lift), (tx, y0 - lift), (tx, ty - lift)]
        elif a["kind"] == "up":
            pts = [(x0, y0 - lift), (tx, y0 - lift - 60 * s), (tx, ty - lift)]
        else:
            pts = [(x0, y0 - lift), (x0, top), (tx, top), (tx, ty - lift)]
        self.flight(a, pts, "ufo")
        a["ux"], a["uy"] = x0, y0 - lift - 110 * s   # the saucer's bottom middle, on the screen
        self.play("whoosh")
        self.next_stage(a, "arrive")
        if random.random() < 0.8:
            self.say(self.pick(UFO_RIDE), force=True)

    def tick_ufo(self, a, dt, s):
        st, lift = a["st"], UFO_LIFT * s
        above = self.pet_px[1] - 6 * s   # the saucer's bottom, above the feet of whoever's inside
        if a["stage"] == "arrive":   # flies in and hovers over it
            k = ease_out(st / 1.3)
            a["uy"] = a["y0"] - lift - above - (1 - k) * 110 * s
            a["ux"] = a["x0"] + (1 - k) * 100 * s * a["side"]
            if st >= 1.4:
                self.next_stage(a, "beam")
        elif a["stage"] == "beam":   # up the beam and inside
            self.y = a["y0"] - lift * smooth(st / 1.6)
            if random.random() < dt * 14:
                self.parts.append({"kind": "spark", "x": random.uniform(0, self.pet_px[0]),
                                   "y": self.pet_px[1] + random.uniform(0, 20) * s, "vx": 0.0,
                                   "vy": -random.uniform(30, 60) * s, "life": 0.6, "c": random.randrange(len(SPARK_C))})
            if st >= 1.6:
                a["fade"] = 4
                self.next_stage(a, "fly")
        elif a["stage"] == "fly":   # off it goes, with the mascot inside
            x, y, done, v = self.fly(a, dt)
            self.x, self.y = x, y
            a["ux"], a["uy"] = x, y - above + math.sin(a["t"] * 3) * 2 * s
            if done:
                a["fade"] = 0
                self.si = a["to"]
                self.next_stage(a, "drop")
        elif a["stage"] == "drop":   # and back down the beam
            self.y = a["ty"] - lift * (1 - smooth(st / 1.3))
            if st >= 1.3:
                self.arrive(a, UFO_RIDE_END)
                self.next_stage(a, "leave")
        elif a["stage"] == "leave":   # up and away (it waves)
            k = smooth(st / 1.4) ** 1.5
            a["ux"] = a["tx"] - k * 110 * s * a["side"]
            a["uy"] = a["ty"] - lift - above - k * 70 * s
            if st >= 1.4:
                self.end_trip(landed=True)

    # ---- a cannon ----
    def begin_cannon(self, a, s):
        sc = self.screens[self.si]
        side = 1 if a["tx"] >= a["x0"] else -1
        kx = a["x0"] - side * 46 * s   # it stands behind the cannon, which points the way it's going
        if not sc.wl + 20 * s <= kx <= sc.wr - 20 * s:
            kx = a["x0"] + side * 46 * s
        g = GRAVITY * s
        px, py = kx, a["y0"] - 20 * s
        ang = math.atan2(a["ty"] - 120 * s - py, a["tx"] - px)   # (a first guess, to find the muzzle)
        mx, my = px + math.cos(ang) * 44 * s, py + math.sin(ang) * 44 * s
        apex = min(my, a["ty"]) - (90 + 0.12 * abs(a["tx"] - mx) / s) * s
        vy = -math.sqrt(2 * g * (my - apex))
        t = -vy / g + math.sqrt(2 * (a["ty"] - apex) / g)
        vx = (a["tx"] - mx) / t
        a.update(kx=kx, pivot=(px, py), ang=math.atan2(vy, vx), aim=0.0, launch=(vx, vy), recoil=0.0, spin=0.0)
        self.dir = 1 if kx > a["x0"] else -1
        self.next_stage(a, "roll")
        if random.random() < 0.8:
            self.say(self.pick(CANNON_LINES), force=True)

    def muzzle(self, a, extra=0.0):
        px, py = a["pivot"]
        r = 44 * a["s"] + extra - a["recoil"]
        return px + math.cos(a["aim"]) * r, py + math.sin(a["aim"]) * r

    def tick_cannon(self, a, dt, s):
        st, g = a["st"], GRAVITY * s
        flat = 0.0 if a["ang"] > -math.pi / 2 else -math.pi   # (lying flat, pointing its way)
        if a["stage"] == "roll":   # pops out, and the barrel swings up to aim
            if st <= dt * 1.5:
                self.burst(a, a["kx"], a["y0"], DUSTS, 8, 60 * s, 0.4, up=30 * s)
            a["aim"] = flat + (a["ang"] - flat) * smooth((st - 0.3) / 0.6)
            if st >= 1.0:
                a["from"] = (self.x, self.y)
                self.next_stage(a, "load")
        elif a["stage"] == "load":   # a hop up and into the barrel
            k = min(1.0, st / 0.5)
            (x0, y0), (mx, my) = a["from"], self.muzzle(a)
            self.x = x0 + (mx - x0) * k
            self.y = y0 + (my + 10 * s - y0) * k - 4 * 30 * s * k * (1 - k)
            if k >= 1:
                a["fade"] = 4
                self.next_stage(a, "fuse")
        elif a["stage"] == "fuse":   # the fuse fizzes, the cannon trembles
            if random.random() < dt * 30:
                fx, fy = self.fuse_at(a)
                self.fx(a, fx, fy, random.choice((FLASH_C[0], FLASH_C[1], "#ffffff")),
                        random.uniform(-40, 40) * s, -random.uniform(20, 70) * s, 0.35, g=200 * s)
            if st >= 1.1:
                self.play("boom")
                mx, my = self.muzzle(a, 4 * s)
                self.x, self.y = mx, my + 10 * s
                self.vx, self.vy = a["launch"]
                a["fade"] = 0
                for col in FLASH_C:   # the flash, and a big puff of smoke
                    self.burst(a, mx, my, (col,), 6, 220 * s, 0.25, size=max(2, round(4 * s)))
                self.smoke(a, mx, my, n=10, spread=12, up=30, life=1.4)
                self.next_stage(a, "fly")
        elif a["stage"] == "fly":   # wheee (tumbling)
            a["recoil"] = 8 * s * math.exp(-st * 6) * min(1.0, st * 30)
            self.x += self.vx * dt
            self.y += self.vy * dt + 0.5 * g * dt * dt
            self.vy += g * dt
            a["spin"] += math.copysign(10, self.vx or 1) * dt
            self.angle = (a["spin"] + math.pi) % (2 * math.pi) - math.pi
            if random.random() < dt * 25:
                self.smoke(a, self.x, self.y - self.pet_px[1] / 2, spread=3, up=5, life=0.7)
            if self.vy > 0 and self.y >= a["ty"]:
                self.vx = self.vy = 0.0
                self.arrive(a, CANNON_LAND, x=self.x)
                self.dizzy_t = 1.4
                self.burst(a, self.x, a["ty"], DUSTS, 8, 70 * s, 0.4, up=30 * s)
                self.next_stage(a, "after")
        elif a["stage"] == "after":   # the cannon goes away in a puff of smoke
            a["recoil"] = 0.0
            if 0.6 <= st < 0.6 + dt * 1.5:
                self.smoke(a, a["kx"], a["y0"] - 10 * s, n=12, spread=16, up=25, life=1.0)
            if st >= 1.4:
                self.end_trip(landed=True)

    def fuse_at(self, a):
        # the end of the fuse, sticking up out of the back of the barrel
        s, (px, py) = a["s"], a["pivot"]
        return px - math.cos(a["aim"]) * 18 * s, py - math.sin(a["aim"]) * 18 * s - 13 * s

    def stage_cannon(self, a, c, ox, oy, s, b):
        if a["stage"] == "after" and a["st"] >= 0.65:
            return
        barrel, ring, wheel, hub = CANNON_C
        shake = math.sin(a["t"] * 60) * s if a["stage"] == "fuse" else 0.0
        px, py = a["pivot"]
        px, py = px + shake - ox, py - oy
        ca, sa = math.cos(a["aim"]), math.sin(a["aim"])
        rc = a["recoil"]

        def part(x1, x2, half, col):   # a block along the barrel, from x1 to x2 (back to front), half as thick
            pts = []
            for lx, ly in ((x1, -half), (x2, -half), (x2, half), (x1, half)):
                lx -= rc
                pts += [px + lx * ca - ly * sa, py + lx * sa + ly * ca]
            c.create_polygon(pts, fill=col, outline="")

        if a["stage"] in ("roll", "load", "fuse"):   # the fuse
            fx, fy = self.fuse_at(a)
            c.create_rectangle(round(fx - b / 2 + shake - ox), round(fy - oy), round(fx + b / 2 + shake - ox),
                               round(fy + 9 * s - oy), fill=STRING_C, outline="")
        part(-24 * s, 44 * s, 9.5 * s, barrel)
        part(-30 * s, -21 * s, 7 * s, barrel)   # the round back end
        part(26 * s, 31 * s, 11 * s, ring)
        part(39 * s, 45 * s, 12 * s, ring)      # the muzzle
        part(-9 * s, -4 * s, 11 * s, ring)
        r = 13 * s   # the wheel (resting on the floor), and its hub
        wy = a["y0"] - oy - r
        n = max(1, int(r // b))
        for j in range(-n, n + 1):
            w = math.sqrt(max(0.0, r * r - (j * b) ** 2))
            c.create_rectangle(round(px - w), round(wy + j * b - b / 2), round(px + w), round(wy + j * b + b / 2),
                               fill=wheel, outline="")
        c.create_rectangle(round(px - 1.5 * b), round(wy - 1.5 * b), round(px + 1.5 * b), round(wy + 1.5 * b),
                           fill=hub, outline="")

    # ---- a portal gun ----
    def begin_portal(self, a, s):
        sc, pw = self.screens[self.si], self.pet_px[0]
        side = a["side"]
        bx = a["x0"] + side * 46 * s
        if not sc.wl + pw / 2 <= bx <= sc.wr - pw / 2:   # (no room that way: the other side)
            side = -side
            bx = a["x0"] + side * 46 * s
        a["gun_side"], a["bx"], a["blue"], a["orange"], a["shot"], a["ox"] = side, bx, 0.0, 0.0, None, a["tx"]
        self.dir = side
        self.next_stage(a, "aim")
        if random.random() < 0.8:
            self.say(self.pick(PORTAL_LINES), force=True)

    def gun_tip(self, a):
        hx, hy = self.hand_at(a["gun_side"], raised=False)
        return hx + a["gun_side"] * 8 * a["s"], hy - 2 * a["s"]

    def tick_portal(self, a, dt, s):
        st, stage = a["st"], a["stage"]
        if stage == "aim":   # blue one on the floor beside it...
            if 0.5 <= st < 0.5 + dt:
                self.play("zap")
            k = (st - 0.5) / 0.15
            x0, y0 = self.gun_tip(a)
            a["shot"] = (x0 + (a["bx"] - x0) * k, y0 + (a["y0"] - y0) * k, "blue") if 0 <= k < 1 else None
            a["blue"] = smooth((st - 0.65) / 0.3)
            if st >= 1.6:   # ...then orange, over on the other floor
                a["fly"] = max(0.15, math.dist((x0, y0), (a["tx"], a["ty"])) / (2600 * s))
                a["from"] = (x0, y0)
                self.play("zap")
                self.next_stage(a, "aim2")
        elif stage == "aim2":
            k = st / a["fly"]
            (x0, y0) = a["from"]
            a["shot"] = (x0 + (a["tx"] - x0) * k, y0 + (a["ty"] - y0) * k, "orange") if k < 1 else None
            a["orange"] = smooth((st - a["fly"]) / 0.3)
            if st >= a["fly"] + 0.7:   # a little hop, into the blue one
                a["vy"] = -math.sqrt(2 * GRAVITY * s * 40 * s)
                a["vx"] = (a["bx"] - self.x) / (2 * -a["vy"] / (GRAVITY * s))
                self.dir = a["gun_side"]
                self.next_stage(a, "in")
        elif stage == "in":
            g = GRAVITY * s
            self.x = min(self.x + a["vx"] * dt, a["bx"]) if a["vx"] > 0 else max(self.x + a["vx"] * dt, a["bx"])
            self.y += a["vy"] * dt + 0.5 * g * dt * dt
            a["vy"] += g * dt
            if a["vy"] > 0 and self.y > a["y0"]:
                a["clip"] = a["y0"]   # going in: the floor hides what's through the portal
            if self.y > a["y0"] + self.pet_px[1] + 2 * s:   # all the way in. out it comes, over there
                speed = max(a["vy"], math.sqrt(2 * g * (self.pet_px[1] + 120 * s)))
                sc = self.screens[a["to"]]
                self.si, self.x, self.y = a["to"], a["tx"], a["ty"] + self.pet_px[1] + 2 * s
                a["vy"], a["clip"] = -speed, a["ty"]
                if a["win"]:   # (onto a window: straight up and back down onto it)
                    a["vx"] = 0.0
                else:          # (lands beside the portal, towards the middle of the screen)
                    a["vx"] = (1 if a["tx"] < (sc.wl + sc.wr) / 2 else -1) * 60 * s
                self.dir = 1 if a["vx"] >= 0 else -1
                self.play("pop")
                self.burst(a, a["tx"], a["ty"], (PORTAL_C["orange"]["l"], "#ffffff"), 12, 160 * s, 0.4, up=80 * s)
                self.next_stage(a, "out")
        elif stage == "out":   # speedy thing comes out
            g = GRAVITY * s
            self.x += a["vx"] * dt
            self.y += a["vy"] * dt + 0.5 * g * dt * dt
            a["vy"] += g * dt
            if a["vy"] > 0 and self.y >= a["ty"]:
                a["clip"] = None
                self.arrive(a, PORTAL_OUT, x=self.x)
                self.next_stage(a, "close")
        elif stage == "close":
            a["blue"] = a["orange"] = 1 - smooth(st / 0.5)
            if st >= 0.6:
                self.end_trip(landed=True)
                return
        for which, x, y in (("blue", a["bx"], a["y0"]), ("orange", a["ox"], a["ty"])):   # sparkles round the rims
            if a[which] > 0.5 and random.random() < dt * 12:
                self.fx(a, x + random.uniform(-26, 26) * s, y, random.choice((PORTAL_C[which]["l"], "#ffffff")),
                        0.0, -random.uniform(20, 50) * s, 0.5)

    def stage_portal(self, a, c, ox, oy, s, b):
        glint = round(a["t"] * 3, 1)
        for which, x, y in (("blue", a["bx"], a["y0"]), ("orange", a["ox"], a["ty"])):
            k = a[which]
            if k > 0.02:
                rows = portal_rows(round(k * 6) / 6, glint)
                self.stage_glyph(c, ox, oy, rows, PORTAL_C[which], b, x, y + len(rows) * b / 2)
        if a["shot"]:
            x, y, which = a["shot"]
            c.create_rectangle(round(x - b - ox), round(y - b - oy), round(x + b - ox), round(y + b - oy),
                               fill=PORTAL_C[which]["o"], outline="")

    # ---- a wizard's teleport ----
    def begin_teleport(self, a, s):
        self.next_stage(a, "hat")
        if random.random() < 0.8:
            self.say(self.pick(TELE_LINES), force=True)

    def sparkle(self, s, inward=False, n=1):
        # sparkles swirling round it (out from it, or gathering in)
        pw, ph = self.pet_px
        for _ in range(n):
            ang, r = random.uniform(0, 2 * math.pi), random.uniform(20, 46) * s
            x, y = pw / 2 + math.cos(ang) * r, ph / 2 + math.sin(ang) * r * 0.7
            v = random.uniform(40, 80) * s * (-1 if inward else 1)
            self.parts.append({"kind": "spark", "x": x, "y": y, "vx": math.cos(ang) * v - math.sin(ang) * 30 * s,
                               "vy": math.sin(ang) * v * 0.7 + math.cos(ang) * 30 * s, "life": random.uniform(0.4, 0.7),
                               "c": random.randrange(len(SPARK_C))})

    def tick_teleport(self, a, dt, s):
        st = a["st"]
        if a["stage"] == "hat":   # on goes the hat
            if st >= 0.5:
                self.play("spell")
                self.next_stage(a, "cast")
        elif a["stage"] == "cast":   # sparkles swirl round it
            if random.random() < dt * 30:
                self.sparkle(s)
            if st >= 1.1:
                self.next_stage(a, "vanish")
        elif a["stage"] == "vanish":   # it fades away...
            a["fade"] = min(4, 1 + int(st / 0.15))
            if random.random() < dt * 40:
                self.sparkle(s)
            if st >= 0.65:
                self.sparkle(s, n=12)
                self.arrive(a, ())
                a["fade"] = 4
                self.next_stage(a, "appear")
        elif a["stage"] == "appear":   # ...and fades in over there
            if random.random() < dt * 40:
                self.sparkle(s, inward=True)
            a["fade"] = max(0, 4 - int(st / 0.15))
            if st >= 0.7:
                a["fade"] = 0
                self.happy_t = 1.5
                if random.random() < 0.8:
                    self.say(self.pick(TELE_END), force=True)
                self.next_stage(a, "done")
        elif a["stage"] == "done" and st >= 0.6:
            self.end_trip(landed=True)

    # ---- a trapdoor in the taskbar (down to a monitor below) ----
    def begin_hatch(self, a, s):
        self.next_stage(a, "knock")
        if random.random() < 0.8:
            self.say(self.pick(HATCH_LINES), force=True)

    def tick_hatch(self, a, dt, s):
        if a["stage"] == "knock":   # two stomps, and the trapdoor swings open
            if a["st"] >= 0.9:
                self.play("clink")
                self.burst(a, a["x0"], a["y0"], (HATCH_C[0], "#a87445"), 8, 70 * s, 0.4, g=300 * s, up=50 * s)
                self.next_stage(a, "open")
        elif a["stage"] == "open":
            if a["st"] >= 0.35:
                a["vy"], a["clip"] = 0.0, a["y0"]
                self.next_stage(a, "drop")
        elif a["stage"] == "drop":
            g = GRAVITY * s
            self.y += a["vy"] * dt + 0.5 * g * dt * dt
            a["vy"] += g * dt
            if self.y > a["y0"] + self.pet_px[1] + 2 * s:   # through: it falls out of the top of the screen below
                sc = self.screens[a["to"]]
                vy = a["vy"]
                self.si, self.y = a["to"], sc.mt + self.pet_px[1] + 2 * s
                self.end_trip()
                self.vy = vy   # (the parachute opens on the way down, as usual)

    def stage_hatch(self, a, c, ox, oy, s, b):
        bw = max(1, round(4 * s))
        half = self.pet_px[0] / 2 + bw
        hx, fy = a["x0"] - ox, a["y0"] - oy
        wood, hole = HATCH_C
        if a["stage"] == "knock":
            c.create_rectangle(round(hx - half), round(fy), round(hx + half), round(fy + b), fill=wood, outline="")
            for x in (hx - half, hx + half - b):
                c.create_rectangle(round(x), round(fy), round(x + b), round(fy + 3 * b), fill=wood, outline="")
        else:   # open: a dark hole, the door hanging down from one side
            c.create_rectangle(round(hx - half), round(fy - b), round(hx + half), round(fy + 2 * b), fill=hole,
                               outline="")
            c.create_rectangle(round(hx - half - b), round(fy - b), round(hx - half), round(fy + 10 * b), fill=wood,
                               outline="")

    # ---- the stage: props and dust away from the mascot ----
    def draw_stage(self, a):
        st = self.trip_stage
        c = st.canvas
        c.delete("all")
        ox, oy = st.origin
        s = a["s"]
        b = max(1, round(2 * s))
        draw = getattr(self, "stage_" + a["how"], None)
        if draw and a["stage"] != "walk":
            draw(a, c, ox, oy, s, b)
        for p in a["fx"]:
            k = p["life"] / p["max"] if p["shrink"] else 1.0
            r = max(1.0, p["size"] * (0.4 + 0.6 * k)) / 2
            c.create_rectangle(round(p["x"] - r - ox), round(p["y"] - r - oy), round(p["x"] + r - ox),
                               round(p["y"] + r - oy), fill=p["c"], outline="")

    # ---- how the mascot looks ----
    def trip_frame(self):
        # what the drawing needs (30 steps a second), or None
        a = self.trip
        if not a:
            return None
        clip = round(a["clip"] - (self.y - self.pet_px[1])) if a["clip"] is not None else None
        return (a["how"], a["stage"], int(a["t"] * 30), round(self.x), round(self.y), a["fade"], clip)

    def trip_room(self, trip, pb):
        # room above the head (so the usage bubble floats above the balloons or the hat)
        if trip[0] == "balloon" and trip[1] != "walk":
            return round(70 * self.trip["s"])
        return (len(HAT) - 1) * pb if trip[0] == "teleport" else 0

    def trip_pose(self, trip):
        # overrides for how it looks: {sink, eyes, eye_dir, eye_v, arms, legs}
        how, stage = trip[0], trip[1]
        a = self.trip
        st, side = a["st"], a["side"]
        both = LEFT_WAVE[1] + WAVE[1]

        def up(f, d=side):   # its arm on side d raised (f 1) or out (f 0)
            return (ARMS[0],) + WAVE[f] if d > 0 else LEFT_WAVE[f] + (ARMS[1],)

        if stage == "walk":
            return {"legs": LEGS_STEP if self.step % 2 else LEGS_STAND, "eye_dir": self.dir}
        if how in ("rope", "ladder"):
            if stage in ("swing", "throw", "pull"):
                return {"arms": up(1), "eyes": "open", "eye_dir": side, "eye_v": -1}
            if stage == "extend":
                return {"arms": up(0), "eyes": "open", "eye_dir": 0, "eye_v": -1}
            if stage == "tug":
                return {"arms": up(int(st * 6) % 2), "sink": "half" if int(st * 6) % 2 else None, "eye_dir": side,
                        "eye_v": -1}
            if stage == "climb":   # hand over hand, legs dangling (or stepping up the rungs)
                n = int(st / (PULL if how == "rope" else a["step_t"])) % 2
                legs = LEGS_AIR if how == "rope" else (LEGS_STEP if n else LEGS_AIR)
                return {"arms": up(1, 1 if n else -1), "legs": legs, "eyes": "open",
                        "eye_dir": 0 if how == "ladder" else side, "eye_v": -1}
            if stage in ("mantle", "over"):
                return {"arms": both, "legs": LEGS_AIR, "eyes": "happy", "eye_dir": side}
            return {"eyes": "happy", "eye_dir": 0}
        if how == "beanstalk":
            if stage == "plant":
                return {"sink": "half" if 0.25 < st < 0.6 else None, "arms": up(0), "eyes": "open", "eye_dir": 0,
                        "eye_v": 1}
            if stage == "grow":
                return {"arms": both, "eyes": "happy", "eye_dir": 0}
            if stage == "over":
                return {"arms": both, "legs": LEGS_AIR, "eyes": "happy", "eye_dir": side}
            return {"eyes": "open", "eye_dir": -side, "eye_v": 1}
        if how == "boxes":
            if stage in ("stack", "over"):
                air = a.get("air") or stage == "over"
                return {"legs": LEGS_AIR if air else LEGS_STAND, "arms": both if air else ARMS, "eyes": "open",
                        "eye_dir": side if stage == "over" else 0, "eye_v": -1}
            return {"eyes": "open", "eye_dir": -side, "eye_v": 1}
        if how in ("wings", "jetpack"):
            if stage == "fly":
                return {"legs": LEGS_AIR, "eyes": "happy" if int(a["t"]) % 3 == 0 else "open", "eye_dir": self.dir,
                        "eye_v": -1 if a["kind"] != "down" else 1, "arms": both if how == "jetpack" else ARMS}
            return {"eyes": "open", "eye_dir": 0, "eye_v": -1 if stage in ("sprout", "strap") else 0}
        if how == "balloon":
            arms = (ARMS[0],) + WAVE[1]
            if stage == "out":
                return {"arms": arms, "eyes": "open", "eye_dir": 1, "eye_v": -1}
            return {"arms": arms, "legs": LEGS_AIR, "eyes": "happy" if stage == "rise" else "open", "eye_dir": 0,
                    "eye_v": 1 if stage in ("pop", "drop") else 0}
        if how == "ufo":
            if stage == "arrive":
                return {"eyes": "open", "eye_dir": 0, "eye_v": -1}
            if stage in ("beam", "drop"):
                return {"arms": both, "legs": LEGS_AIR, "eyes": "happy", "eye_dir": 0}
            return {"arms": up(int(st * 5) % 2, 1), "eyes": "happy", "eye_dir": 0, "eye_v": -1}   # waving bye
        if how == "cannon":
            if stage == "roll":
                return {"eyes": "open", "eye_dir": 1 if a["kx"] > self.x else -1, "eye_v": 0}
            return {"arms": both, "legs": LEGS_AIR, "eyes": "happy", "eye_dir": 0}
        if how == "teleport":
            if stage in ("hat", "cast", "vanish"):
                return {"arms": up(1 if stage != "hat" or st > 0.25 else 0, 1),
                        "eyes": "closed" if stage != "hat" else "open", "eye_dir": 0, "eye_v": -1}
            return {"eyes": "happy", "eye_dir": 0}
        if how == "portal":
            g = a["gun_side"]
            if stage == "aim":
                return {"arms": up(0, g), "eyes": "open", "eye_dir": g, "eye_v": 1}
            if stage == "aim2":
                return {"arms": up(0, g), "eyes": "open", "eye_dir": side, "eye_v": -1}
            if stage in ("in", "out"):
                return {"arms": both, "legs": LEGS_AIR, "eyes": "happy", "eye_dir": 0}
            return {"eyes": "happy", "eye_dir": 0}
        # the trapdoor
        if stage == "knock":
            return {"sink": "half" if 0.15 < st < 0.3 or 0.5 < st < 0.65 else None, "eyes": "open", "eye_dir": 0,
                    "eye_v": 1}
        if stage == "open":
            return {"eyes": "worried", "eye_dir": 0, "eye_v": 1}
        return {"arms": both, "legs": LEGS_AIR, "eyes": "open", "eye_dir": 0, "eye_v": -1}

    def draw_trip(self, trip, layer, px, py, sink, bw, bh, pb, pet_w, pet_h):
        # the bits that go with the mascot, drawn in its own window (no dark edges)
        how, stage = trip[0], trip[1]
        a, c = self.trip, self.canvas
        s, st, side = a["s"], a["st"], a["side"]
        if stage == "walk":
            return

        def at(x, y):   # a point on the screen, in the window
            return px + x - (self.x - pet_w / 2), py + y - (self.y - pet_h)

        if layer == "back":
            if how == "ufo" and stage in ("beam", "drop"):   # the tractor beam, behind it: see-through stripes
                ux, uy = at(a["ux"], a["uy"])
                floor = at(0, a["y0"] if stage == "beam" else a["ty"])[1]
                c.create_polygon(ux - 8 * pb, uy, ux + 8 * pb, uy, ux + pet_w // 2 + 3 * bw, floor,
                                 ux - pet_w // 2 - 3 * bw, floor, fill=BEAM_C, outline="", stipple="gray50")
            if how == "wings":   # one each side, flapping
                look = ("up" if int(a["t"] * 7) % 2 else "down") if stage == "fly" else "small"
                rows, root = WINGS[look]
                y0 = py + sink + round(0.6 * bh) - root * pb
                self.glyph(rows, px + 14 * bw, y0, pb, WING_C, shadow=False)
                self.glyph([r[::-1] for r in rows], px + 4 * bw - len(rows[0]) * pb, y0, pb, WING_C, shadow=False)
            elif how == "jetpack" and (stage != "land" or st < 0.3):   # strapped on: a frame and a tank each side
                tank, stripe, dark = JET_C
                top = py + sink + bh // 2
                c.create_rectangle(px + bw, top, px + 17 * bw, top + 3 * bh, fill=dark, outline="")   # (behind it)
                for d in (-1, 1):
                    x0 = round(px + (16.5 if d > 0 else -1.5) * bw)
                    w = 3 * bw
                    c.create_rectangle(x0, top - pb, x0 + w, top + 3 * bh, fill=tank, outline="")
                    c.create_rectangle(x0 + bw // 2, top - 2 * pb, x0 + w - bw // 2, top - pb, fill=tank, outline="")
                    c.create_rectangle(x0, top + bh, x0 + w, top + bh + pb, fill=stripe, outline="")
                    c.create_rectangle(x0 + bw // 2, top + 3 * bh, x0 + w - bw // 2, top + 3 * bh + 2 * pb, fill=dark,
                                       outline="")
                    if stage == "fly":   # flames, longer the faster it goes
                        n = 2 + int(min(1.0, a["v"] / (200 * s)) * 4) + int(a["t"] * 20) % 2
                        for j in range(n):
                            col = FLASH_C[min(2, j * 3 // n)]
                            fw = max(pb, round(2 * bw * (1 - j / (n + 1))))
                            fx = x0 + w / 2 - fw / 2
                            fy = top + 3 * bh + 2 * pb + j * pb
                            c.create_rectangle(round(fx), fy, round(fx + fw), fy + pb, fill=col, outline="")
            return
        if how == "jetpack" and (stage != "land" or st < 0.3):   # its straps: over the shoulders and round its middle
            dark, tank = JET_C[2], JET_C[0]
            sw = max(1, round(bw * 0.75))
            for col in (3.5, 13.75):
                x0 = round(px + col * bw)
                c.create_rectangle(x0, py + sink, x0 + sw, py + sink + 3 * bh, fill=dark, outline="")
            yb = round(py + sink + 2.6 * bh)
            c.create_rectangle(px + 2 * bw, yb, px + 16 * bw, yb + pb, fill=dark, outline="")
            c.create_rectangle(round(px + 9 * bw - pb), yb - pb // 2, round(px + 9 * bw + pb), yb + pb + pb // 2,
                               fill=tank, outline="")   # the buckle
        if how == "rope" and stage == "swing":   # whirling the hook round over its head, like a lasso
            hx, hy = px + (16.5 if side > 0 else 1.5) * bw, py + sink + 0.5 * bh
            ang = st * 11
            kx, ky = px + pet_w / 2 + math.cos(ang) * 20 * s, py + sink - 16 * s + math.sin(ang) * 5 * s
            self.pixel_line(hx, hy, kx, ky, pb, ROPE_C["a"])
            self.glyph(HOOK, round(kx - 3.5 * pb), round(ky - 6 * pb), pb, HOOK_C, shadow=False)
        elif how == "balloon":
            hx, hy = px + 16.5 * bw, py + sink + 0.3 * bh
            for i in range(3):
                b = self.ride_balloon_at(a, i)
                if not b:
                    continue
                cx, cy, r = b
                cx, cy = px + cx, py + sink + cy
                colour, shine = BALLOON_C[a["colours"][i]]
                c.create_line(cx, cy + r, hx, hy, fill=STRING_C, width=max(1, round(s)))
                self.blob(cx, cy, r * 0.85, r, pb, colour)
                if r > 4 * pb:
                    x, y = round(cx - r * 0.4), round(cy - r * 0.55)
                    c.create_rectangle(x, y, x + pb, y + 2 * pb, fill=shine, outline="")
        elif how == "portal" and stage in ("aim", "aim2"):   # the gun, in the hand on the portal's side
            g = a["gun_side"]
            tip = PORTAL_C["blue" if stage == "aim" and st < 0.55 else "orange"]["o"]
            rows = GUN if g > 0 else [r[::-1] for r in GUN]
            hx, hy = px + (16.5 if g > 0 else 1.5) * bw, py + sink + 2.5 * bh
            x0 = hx - (1 if g > 0 else len(GUN[0]) - 1) * pb
            self.glyph(rows, round(x0), round(hy - 3 * pb), pb, dict(GUN_C, t=tip), shadow=False)
        elif how == "teleport" and a["fade"] < 2 and stage in ("hat", "cast", "vanish", "appear", "done"):
            k = min(1.0, st / 0.3) if stage == "hat" else 1 - min(1.0, st / 0.4) if stage == "done" else 1.0
            if k > 0.3:   # the wizard hat drops on (and comes off at the end), and a wand in the raised hand
                hx = px + 3 * bw + (12 * bw - len(HAT[0]) * pb) // 2
                self.glyph(HAT, hx, py + sink - (len(HAT) - 1) * pb - round((1 - k) * 12 * s), pb,
                           HAT_COLOURS, shadow=False)
            if stage != "done":
                hy = py + sink
                for i in range(5):
                    x1, y1 = px + 17 * bw + i * pb, hy - (i + 1) * pb
                    c.create_rectangle(x1, y1, x1 + pb, y1 + pb, fill=WAND_C, outline="")
                x1, y1 = px + 17 * bw + 4 * pb, hy - 7 * pb
                c.create_rectangle(x1, y1, x1 + 2 * pb, y1 + 2 * pb, fill=STAR_C, outline="")
        elif how == "ufo":
            ux, uy = at(a["ux"], a["uy"])
            ub = 2 * pb   # (the saucer goes in front, so the mascot disappears up into it)
            lights = UFO_LIGHTS[int(a["t"] * 4) % 2]
            self.glyph(UFO, round(ux - len(UFO[0]) * ub / 2), round(uy - len(UFO) * ub), ub, dict(UFO_C, l=lights),
                       shadow=False)
