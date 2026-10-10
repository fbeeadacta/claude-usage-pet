# part of the Pet: things it does on its own when it's idle (besides walking, hopping, dancing and napping):
# sweeping the floor, painting a little picture, fishing through a hole in the taskbar, blowing up balloons
# that float off and pop, and throwing a paper plane that flies off on its own (a little window, like the ball).
# positions are relative to the body's top left (px, py), like particles.
import math
import random

from .art import (ARMS, BALLOON_C, BOBBER_C, BRISTLE_C, CANVAS_C, CATCHES, DUST_C, EASEL_C, HAY_C, ICE_C, LEFT_WAVE,
    LEGS_STAND, LEGS_STEP, PAINT_C, PAINTINGS, PLANE, PLANE_C, RIPPLE_C, SMOKE_C, STRING_C, TIE_C, WAND_C, WATER_C, WAVE)
from .config import ACT_CHANCE
from .lines import (BALLOON_LINES, CATCH_LINES, FISH_LINES, PAINT_DONE, PAINT_LINES, PLANE_FAR, PLANE_FLOP,
    PLANE_LAND, PLANE_LINES, POP_LINES, SWEEP_DONE, SWEEP_LINES)
from .sprites import Sprite

KINDS = ("sweep", "paint", "fish", "balloon", "plane")
TALLY = {"sweep": "sweeps", "paint": "paintings", "fish": "catches", "balloon": "balloons", "plane": "planes"}
START_LINES = {"sweep": SWEEP_LINES, "paint": PAINT_LINES, "fish": FISH_LINES, "balloon": BALLOON_LINES,
               "plane": PLANE_LINES}
CATCH_ODDS = {"fish": 45, "gold": 5, "boot": 15, "crab": 12, "bug": 12, "sock": 11}
FISH_CUT, REEL, SHOW, DROP = 1.4, 0.6, 2.6, 0.35   # fishing (seconds): cutting the hole, reeling in, showing it off, back it goes
STROKE = 0.9             # one sweep of the broom (seconds)
BLOW, TIE = 3.0, 3.4      # a balloon: blown up by 3 s, tied off and let go at 3.4 s
FOLD, THROW = 1.5, 2.0    # the paper plane: folded by 1.5 s, thrown at 2 s
PLANE_STAY = 8.0          # how long a landed plane stays on the taskbar
TURNS = 24                # the plane's picture is turned in steps of 15 degrees
SHEET = ["########"] * 6
HALF_FOLD = ["########", ".######.", "..####..", "...##..."]
turned_cache = {}


def turned(rows, k, flip):
    # the picture turned by k steps (clockwise), on a square big enough for any angle. a few samples
    # per block, so thin bits don't break up.
    key = (tuple(rows), k, flip)
    if key not in turned_cache:
        src = rows[::-1] if flip else rows   # flying left: upside down first, so it comes out the right way up
        h, w = len(src), len(src[0])
        n = math.ceil(math.hypot(w, h)) + 1
        nx, ny = n + (n - w) % 2, n + (n - h) % 2   # (so the blocks line up when it isn't turned)
        a = k * 2 * math.pi / TURNS
        ca, sa = math.cos(a), math.sin(a)
        out = []
        for j in range(ny):
            line = ""
            for i in range(nx):
                ch = "."
                for ox, oy in ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75), (0.5, 0.5)):
                    x, y = i + ox - nx / 2, j + oy - ny / 2
                    sx, sy = x * ca + y * sa + w / 2, -x * sa + y * ca + h / 2
                    if 0 <= sx < w and 0 <= sy < h and src[int(sy)][int(sx)] != ".":
                        ch = src[int(sy)][int(sx)]
                        break
                line += ch
            out.append(line)
        turned_cache[key] = out
    return turned_cache[key]


class IdleMixin:
    def start_act(self, kind=None):
        # picks something to do. returns True if it started.
        if not self.anim.get() or self.held or not self.grounded():
            return False
        if kind is None:
            kind = random.choice([k for k in KINDS if k != "plane" or self.plane is None])
        elif kind == "plane" and self.plane is not None:
            return False   # (one plane at a time)
        a = {"side": self.job_side(), "said": False}
        if kind == "sweep":
            a["dur"] = random.uniform(10, 16)
            self.tally("sweeps")
        elif kind == "paint":
            pic = a["pic"] = random.choice(list(PAINTINGS))
            rows = PAINTINGS[pic]
            first = {}
            for row in rows:
                for ch in row:
                    if ch != ".":
                        first.setdefault(ch, len(first))
            # one colour at a time, roughly top to bottom
            cells = [(first[ch], j + random.uniform(0, 3), i, j, ch) for j, row in enumerate(rows)
                     for i, ch in enumerate(row) if ch != "."]
            a["cells"] = [c[2:] for c in sorted(cells)]
            a["done_at"] = random.uniform(9, 14)
            a["dur"] = a["done_at"] + 4.5
        elif kind == "fish":
            a["bite"] = FISH_CUT + random.uniform(5, 14)
            a["catch"] = random.choices(list(CATCH_ODDS), weights=list(CATCH_ODDS.values()))[0]
            a["dur"] = a["bite"] + REEL + SHOW + DROP + 1.5
        elif kind == "balloon":
            a["balloons"], t, last = [], 0.0, None
            for _ in range(random.choice((2, 3))):
                c = random.choice([i for i in range(len(BALLOON_C)) if i != last])
                pop = t + TIE + random.uniform(1.6, 2.6)
                a["balloons"].append({"at": t, "pop": pop, "c": c})
                t, last = pop + 0.9, c
            a["dur"] = t
        else:   # the plane: ends once it lands
            a["dir"] = a["side"] if random.random() > 0.15 else -a["side"]   # (sometimes the wrong way)
            a["dur"] = 30.0
        self.state, self.act, self.act_t, self.act_info = "act", kind, 0.0, a
        self.state_t = a["dur"]
        self.say(self.pick(START_LINES[kind]))
        return True

    def maybe_act(self):
        # (when it's done standing about) now and then, one of these instead
        return random.random() < ACT_CHANCE and not self.full() and self.start_act()

    # ---- where things are (relative to the body's top left) ----
    def act_dims(self):
        s = self.s()
        bw, bh = max(1, round(4 * s)), max(2, round(8 * s))
        return s, bw, bh, max(1, round(2 * s)), 18 * bw, 5 * bh

    def act_hand(self, side, row):
        _, bw, bh, _, _, _ = self.act_dims()
        return (16.5 if side > 0 else 1.5) * bw, (row + 0.5) * bh

    def side_arm(self, side, frame):
        return (ARMS[0],) + WAVE[frame] if side > 0 else LEFT_WAVE[frame] + (ARMS[1],)

    def broom(self, t, side):
        # where it holds the broom (just outside its hand), how far it's tilted (it swings back and forth
        # about that grip, forward on each push) and how far down it is from the grip to the bristles
        _, bw, _, pb, _, ph = self.act_dims()
        gx, gy = self.act_hand(side, 2)
        swing = side * 0.4 * math.sin(2 * math.pi * (t % STROKE) / STROKE) if t < self.act_info["dur"] - 1.5 else 0.0
        return gx + side * (bw + pb) / 2, gy, swing, ph - 7 * pb - gy

    def broom_at(self, t, side):
        # the bottom middle of the broom's head
        gx, gy, swing, down = self.broom(t, side)
        reach = down + 7 * self.act_dims()[3]
        return gx + math.sin(swing) * reach, gy + math.cos(swing) * reach

    def pushing(self, t):
        # sweeping goes in strokes: a quick push forward, then a pause to bring the broom back
        return (t % STROKE) / STROKE < 0.45

    def easel_at(self, side):
        # the canvas's top left (inside its frame) and the size of one painted block
        s, _, _, _, pw, ph = self.act_dims()
        cell = max(3, round(2.5 * s))
        cw = 14 * cell
        x0 = pw + 8 * s if side > 0 else -8 * s - cw
        return x0 + cell, ph - 12 * s - cw + cell, cell

    def hole_at(self, side):
        # the fishing hole's middle and size, and the rod's tip above it
        s, _, _, _, pw, ph = self.act_dims()
        hx = (pw if side > 0 else 0) + side * 28 * s
        return hx, ph - s, 14 * s, 4.5 * s, (hx, -12 * s)

    def balloon_at(self, b, t, side):
        # (middle x, middle y, radius) of a balloon, or None when it isn't out
        rel = t - b["at"]
        if rel < 0 or t >= b["pop"]:
            return None
        s = self.s()
        big = 13 * s
        if rel < 0.3:
            r = 0.25 * big
        elif rel < BLOW:
            puff = (rel - 0.3) / ((BLOW - 0.3) / 5)   # five big breaths
            r = big * (0.3 + 0.7 * min(1.0, (int(puff) + min(1.0, (puff % 1) * 2)) / 5))
        else:
            r = big
        kx, ky = self.act_hand(side, 1)
        if rel > TIE:   # let go: it drifts up and away
            up = rel - TIE
            kx += side * up * 15 * s + math.sin(up * 2.5) * 3 * s
            ky -= up * 12 * s + up * up * 2 * s
        return kx + side * (r * 0.9 + 3 * s), ky - r * 0.8, r

    # ---- every frame ----
    def act_tick(self, dt, s):
        t0, self.act_t = self.act_t, self.act_t + dt
        t, kind, a = self.act_t, self.act, self.act_info
        side = a["side"]
        self.state_t -= dt
        pb = max(1, round(2 * s))
        if kind == "sweep":
            if t < a["dur"] - 1.5 and self.pushing(t):   # sweeping its way along
                lo, hi = self.x_limits()
                if self.plat is not None:   # (not off the end of a window)
                    lo, hi = max(lo, self.plat_box[1] + 20 * s), min(hi, self.plat_box[3] - 20 * s)
                nx = self.x + side * 45 * s * dt
                if lo <= nx <= hi:
                    self.x = nx
                if int(t0 / STROKE) != int(t / STROKE) or t0 == 0:   # each push flicks dust out ahead
                    x, y = self.broom_at(t, side)
                    for _ in range(3):
                        self.parts.append({"kind": "puff", "x": x, "y": y - 2 * pb, "vx": side * random.uniform(40, 80) * s,
                                           "vy": -random.uniform(5, 25) * s, "life": random.uniform(0.35, 0.6),
                                           "c": random.randrange(len(SMOKE_C))})
                    for _ in range(3):
                        self.parts.append({"kind": "dot", "x": x, "y": y - pb, "vx": side * random.uniform(50, 110) * s,
                                           "vy": -random.uniform(30, 70) * s, "g": 300 * s, "life": 0.4, "c": DUST_C})
            if not a["said"] and t > a["dur"] - 2.2:
                a["said"] = True
                self.say(self.pick(SWEEP_DONE))
        elif kind == "paint":
            done = a["done_at"]
            if 1 < t < done:
                self.part_t -= dt
                if self.part_t <= 0:   # a fleck of paint off the brush
                    x0, y0, cell = self.easel_at(side)
                    i, j, ch = a["cells"][self.painted(t) - 1] if self.painted(t) else a["cells"][0]
                    self.parts.append({"kind": "dot", "x": x0 + (i + 0.5) * cell, "y": y0 + (j + 0.5) * cell,
                                       "vx": random.uniform(-20, 20) * s, "vy": -random.uniform(10, 40) * s, "g": 160 * s,
                                       "life": 0.5, "c": PAINT_C[ch]})
                    self.part_t = random.uniform(0.3, 0.6)
            if t0 < done <= t:   # finished: steps back to admire it
                self.happy_t = 2.0
                self.spawn("heart")
                self.tally("paintings")
                self.say(self.pick(PAINT_DONE[a["pic"]]), force=True)
        elif kind == "fish":
            hx, hy, rx, ry, _ = self.hole_at(side)
            bite = a["bite"]
            if t < FISH_CUT and random.random() < dt * 14:   # ice chips flying out of the cut
                ang = t / FISH_CUT * 2 * math.pi
                self.parts.append({"kind": "dot", "x": hx + math.cos(ang) * rx, "y": hy + math.sin(ang) * ry,
                                   "vx": random.uniform(-40, 40) * s, "vy": -random.uniform(40, 90) * s, "g": 300 * s,
                                   "life": 0.5, "c": ICE_C})
            if t0 < FISH_CUT <= t:
                self.play("pop")
            if t0 < bite <= t:   # a bite!
                self.play("boing")
                self.tally("catches")
            if t0 < bite + REEL <= t:
                if a["catch"] == "gold":
                    self.spawn("heart")
                self.happy_t = 1.5 if a["catch"] in ("fish", "gold", "crab") else 0.0
                self.say(self.pick(CATCH_LINES[a["catch"]]), force=True)
            if t0 < bite + REEL + SHOW + DROP <= t:   # splash, back it goes
                for _ in range(10):
                    self.parts.append({"kind": "dot", "x": hx + random.uniform(-0.6, 0.6) * rx, "y": hy,
                                       "vx": random.uniform(-45, 45) * s, "vy": -random.uniform(50, 110) * s,
                                       "g": 350 * s, "life": 0.55, "c": random.choice((RIPPLE_C, ICE_C))})
        elif kind == "balloon":
            for b in a["balloons"]:
                if t0 < b["pop"] <= t:   # pop!
                    cx, cy, r = self.balloon_at(b, b["pop"] - 1e-6, side)
                    self.play("pop")
                    self.tally("balloons")
                    colour = BALLOON_C[b["c"]][0]
                    for i in range(14):
                        ang = i / 14 * 2 * math.pi + random.uniform(-0.2, 0.2)
                        sp = random.uniform(50, 90) * s
                        self.parts.append({"kind": "dot", "x": cx + math.cos(ang) * r * 0.6,
                                           "y": cy + math.sin(ang) * r * 0.6, "vx": math.cos(ang) * sp,
                                           "vy": math.sin(ang) * sp, "g": 120 * s, "life": 0.6, "c": colour})
                    if random.random() < 0.6:
                        self.say(self.pick(POP_LINES), force=True)
        else:   # the plane
            if t0 < THROW <= t:
                hx, hy = self.act_hand(side, 0)
                pw, ph = self.pet_px
                self.launch_plane(self.x - pw / 2 + hx, self.y - ph + hy - 4 * pb, a["dir"])
                self.play("whoosh")
                self.tally("planes")
            elif t > THROW and not a["said"]:
                p = self.plane
                if p is None or p.get("gone"):
                    a["said"], self.state_t = True, 0.0   # (it disappeared, e.g. something went full screen)
                elif p["landed"]:
                    a["said"] = True
                    far = abs(p["x"] - p["x0"]) / s
                    a["result"] = "flop" if far < 160 else "far" if far > 900 else "ok"
                    lines = {"flop": PLANE_FLOP, "far": PLANE_FAR, "ok": PLANE_LAND}[a["result"]]
                    self.say(self.pick(lines), force=True)
                    self.state_t = min(self.state_t, 2.0)
        if self.state_t <= 0:
            self.state, self.state_t, self.act = "idle", 2.0, None

    def painted(self, t):
        # how many blocks of the picture are painted so far
        a = self.act_info
        return round(len(a["cells"]) * min(1.0, max(0.0, (t - 1) / (a["done_at"] - 1))))

    # ---- the paper plane, flying on its own ----
    def launch_plane(self, x, y, d):
        # a paper plane glider: speed turns into lift (so a fast throw climbs, or even loops), gravity bends
        # its path down, and drag slowly wins. every throw gets its own trim speed, glide and wobble.
        s = self.s()
        if self.plane_sprite is None:
            self.plane_sprite = Sprite(self.root)
        g, trim, glide = 380 * s, random.uniform(160, 240) * s, random.uniform(7, 11)
        up = random.uniform(0.1, 0.6)
        self.plane = {"x": x, "y": y, "x0": x, "v": trim * random.uniform(0.9, 2.0),
                      "th": -up if d > 0 else math.pi + up, "c": d, "g": g, "lift": g / trim ** 2,
                      "drag": g / (glide * trim ** 2), "wobble": (random.uniform(0, 0.6), random.uniform(1, 3),
                                                                 random.uniform(0, 6.3)),
                      "t": 0.0, "landed": False, "vx": 0.0, "rest": PLANE_STAY, "si": self.si}

    def plane_tick(self, dt):
        p = self.plane
        if p is None:
            return
        if self.hidden:
            self.plane_sprite.hide()
            p["gone"] = True
            self.plane = None
            return
        s = self.s()
        sc = self.screens[min(p["si"], len(self.screens) - 1)]
        b = max(2, round(2 * s))
        wall = 6 * s
        if not p["landed"]:
            p["t"] += dt
            h = dt / 3
            for _ in range(3):
                v, th, g = p["v"], p["th"], p["g"]
                drag = p["drag"] * (1 + max(0.0, p["t"] - 10) * 0.5)   # (after 10 s it comes down for sure)
                v = max(25 * s, v + (g * math.sin(th) - drag * v * v) * h)
                amp, freq, phase = p["wobble"]
                th += (g * math.cos(th) / v - p["c"] * p["lift"] * v + amp * math.sin(freq * p["t"] + phase)) * h
                p["v"], p["th"] = v, th
                p["x"] += v * math.cos(th) * h
                p["y"] += v * math.sin(th) * h
                if p["x"] < sc.wl + wall or p["x"] > sc.wr - wall:   # bonk off the side of the screen
                    p["x"] = min(max(p["x"], sc.wl + wall), sc.wr - wall)
                    p["th"], p["v"], p["c"] = math.pi - th, v * 0.5, -p["c"]
                if p["y"] < sc.mt + wall:   # and the top
                    p["y"] = sc.mt + wall
                    p["th"], p["v"], p["c"] = -th, v * 0.6, -p["c"]
                if p["y"] >= sc.wb - 2 * b:   # down on the taskbar
                    p["y"], p["landed"] = sc.wb - 2 * b, True
                    p["vx"] = v * math.cos(p["th"]) * 0.6
                    p["c"] = 1 if math.cos(p["th"]) >= 0 else -1   # (lands the right way up)
                    p["th"] = 0.0 if p["c"] > 0 else math.pi
                    break
        else:   # sliding to a stop, then lying there for a bit
            p["vx"] -= math.copysign(min(abs(p["vx"]), 500 * s * dt), p["vx"])
            p["x"] = min(max(p["x"] + p["vx"] * dt, sc.wl + wall), sc.wr - wall)
            p["rest"] -= dt
            if p["rest"] <= 0:
                self.plane_sprite.hide()
                p["gone"] = True
                self.plane = None
                return
        k = round(p["th"] / (2 * math.pi) * TURNS) % TURNS
        rows = turned(PLANE, k, p["c"] < 0)
        self.plane_sprite.show(rows, PLANE_C, b, p["x"], p["y"] + len(rows) * b / 2)

    # ---- how it looks ----
    def act_frame(self):
        # what the drawing needs (20 steps a second), or None
        if self.state != "act" or not self.act:
            return None
        return (self.act, int(self.act_t * 20), self.act_info["side"])

    def act_pose(self, act):
        # overrides for how it looks: {sink, eyes, eye_dir, eye_v, arms, legs, shift}
        kind, step, side = act
        t, a = step / 20, self.act_info
        if kind == "sweep":   # looking down at the broom, stepping along on each push
            push = self.pushing(t) and t < a["dur"] - 1.5
            return {"eyes": "open", "eye_dir": side, "eye_v": 1, "arms": ARMS,
                    "legs": LEGS_STEP if push and int(t * 10) % 2 else LEGS_STAND}
        if kind == "paint":
            if t < a["done_at"]:   # dabbing away, eyes on the canvas
                return {"eyes": "open", "eye_dir": side, "eye_v": 0, "arms": self.side_arm(side, int(t * 4) % 2)}
            return {"eyes": "happy", "eye_dir": side, "eye_v": 0, "arms": ARMS}   # admiring it
        if kind == "fish":
            bite = a["bite"]
            if t < FISH_CUT:   # cutting the hole
                return {"eyes": "open", "eye_dir": side, "eye_v": 1, "arms": self.side_arm(side, int(t * 6) % 2)}
            if t < bite:       # sat by the hole, rod out, watching the bobber
                return {"sink": "half", "eyes": "open", "eye_dir": side, "eye_v": 1, "arms": self.side_arm(side, 0)}
            if t < bite + REEL + SHOW:   # reeling it in and looking at it
                good = a["catch"] in ("fish", "gold", "crab")
                eyes = "happy" if good and t > bite + REEL else "open"
                return {"eyes": eyes, "eye_dir": side, "eye_v": -1, "arms": self.side_arm(side, 1)}
            return {"sink": "half", "eyes": "open", "eye_dir": side, "eye_v": 1, "arms": self.side_arm(side, 0)}
        if kind == "balloon":
            for b in a["balloons"]:
                rel = t - b["at"]
                if 0.3 <= rel < BLOW:   # blowing: eyes squeezed shut on each breath out
                    puff = (rel - 0.3) / ((BLOW - 0.3) / 5)
                    return {"eyes": "closed" if puff % 1 < 0.5 else "open", "eye_dir": side, "eye_v": 0,
                            "arms": self.side_arm(side, 0), "sink": "half" if puff % 1 >= 0.5 else None}
                if 0 <= rel < TIE:
                    return {"eyes": "open", "eye_dir": side, "eye_v": 0, "arms": self.side_arm(side, 0)}
                if TIE <= rel and t < b["pop"]:   # watching it float away
                    return {"eyes": "open", "eye_dir": side, "eye_v": -1, "arms": ARMS}
            return {"eyes": "open", "eye_dir": side, "eye_v": 0}
        # the plane
        if t < FOLD:   # folding it, looking down at it
            return {"eyes": "open", "eye_dir": 0, "eye_v": 1, "arms": LEFT_WAVE[0] + WAVE[0]}
        if t < THROW:  # winding up
            return {"eyes": "open", "eye_dir": a["dir"], "eye_v": -1, "arms": self.side_arm(side, 1)}
        arms = self.side_arm(side, 0) if t < THROW + 0.3 else ARMS
        p = self.plane
        if a.get("result"):
            return {"eyes": "open" if a["result"] == "flop" else "happy", "eye_dir": 0, "eye_v": 0, "arms": arms}
        if p is None:
            return {"arms": arms}
        s, ph = self.s(), self.pet_px[1]
        dx = p["x"] - self.x
        look = 1 if dx > 24 * s else -1 if dx < -24 * s else 0
        return {"eyes": "open", "eye_dir": look, "eye_v": -1 if p["y"] < self.y - ph - 40 * s else 0, "arms": arms}

    def pixel_line(self, x0, y0, x1, y1, b, colour):
        # a line made of b-sized blocks
        n = max(1, round(max(abs(x1 - x0), abs(y1 - y0)) / b))
        for i in range(n + 1):
            x, y = round(x0 + (x1 - x0) * i / n - b / 2), round(y0 + (y1 - y0) * i / n - b / 2)
            self.canvas.create_rectangle(x, y, x + b, y + b, fill=colour, outline="")

    def blob(self, cx, cy, rx, ry, b, colour):
        # a filled oval made of b-sized blocks
        for j in range(-math.ceil(ry / b), math.ceil(ry / b) + 1):
            for i in range(-math.ceil(rx / b), math.ceil(rx / b) + 1):
                if (i * b / max(rx, 1)) ** 2 + (j * b / max(ry, 1)) ** 2 <= 1:
                    x, y = round(cx + i * b - b / 2), round(cy + j * b - b / 2)
                    self.canvas.create_rectangle(x, y, x + b, y + b, fill=colour, outline="")

    def draw_act(self, act, px, py, sink, bw, bh, pb, pet_w, pet_h):
        kind, step, side = act
        t, c, a = step / 20, self.canvas, self.act_info
        s = self.s()
        if kind == "sweep":
            gx, gy, swing, down = self.broom(t, side)
            gx, gy = px + gx, py + sink + gy
            ca, sa = math.cos(swing), math.sin(swing)

            def cell(lx, ly, w, h, col):
                # a block of the broom, lx across and ly down along it from the grip, turned with the swing
                pts = []
                for x, y in ((lx - 0.5, ly - 0.5), (lx + w + 0.5, ly - 0.5), (lx + w + 0.5, ly + h + 0.5), (lx - 0.5, ly + h + 0.5)):
                    pts += [gx + x * ca + y * sa, gy - x * sa + y * ca]
                c.create_polygon(pts, fill=col, outline="")

            cell(-pb / 2, -26 * s, pb, 26 * s + down, WAND_C)   # the handle, up past its hand
            for r, w in enumerate((3, 3, 4, 5, 6, 6, 7)):   # the head: a red band, then straw, a bit wider at the bottom
                for i in range(w):
                    if r == 6 and i % 2:
                        continue   # (a ragged edge)
                    col = TIE_C if r == 1 else HAY_C[2] if r >= 2 and i % 2 else BRISTLE_C
                    cell(-w * pb / 2 + i * pb, down + r * pb, pb, pb, col)
        elif kind == "paint":
            x0, y0, cell = self.easel_at(side)
            x0, y0 = px + x0, py + y0
            size = 12 * cell
            mid, floor = x0 + size / 2, py + pet_h
            lw = max(2, round(1.5 * s))
            c.create_line(mid, y0, mid, floor, fill=EASEL_C, width=lw)   # the back leg
            for lean in (-1, 1):   # the front legs
                c.create_line(mid + lean * size * 0.3, y0 + size, mid + lean * size * 0.5, floor, fill=EASEL_C,
                              width=lw)
            c.create_rectangle(round(mid - pb), round(y0 - cell - 2 * pb), round(mid + pb), round(y0 - cell),
                               fill=EASEL_C, outline="")   # the peg on top
            c.create_rectangle(round(x0 - cell), round(y0 - cell), round(x0 + size + cell), round(y0 + size + cell),
                               fill=EASEL_C, outline="")   # the frame
            c.create_rectangle(round(x0), round(y0), round(x0 + size), round(y0 + size), fill=CANVAS_C, outline="")
            c.create_rectangle(round(x0 - 2 * cell), round(y0 + size + cell), round(x0 + size + 2 * cell),
                               round(y0 + size + cell + pb), fill=EASEL_C, outline="")   # the ledge
            n = self.painted(t)
            for i, j, ch in a["cells"][:n]:
                c.create_rectangle(round(x0 + i * cell), round(y0 + j * cell), round(x0 + (i + 1) * cell),
                                   round(y0 + (j + 1) * cell), fill=PAINT_C[ch], outline="")
            if 1 <= t < a["done_at"] and n:   # the brush: always the same size, in its raised hand, pointing at the canvas
                ch = a["cells"][n - 1][2]
                hx, hy = self.act_hand(side, 1 - int(t * 4) % 2)
                hx, hy = px + hx, py + sink + hy
                tx, ty = hx + side * 13 * s, hy - 2 * s
                self.pixel_line(hx, hy, tx, ty, pb, WAND_C)
                c.create_rectangle(round(tx - pb), round(ty - pb), round(tx + pb), round(ty + pb), fill=PAINT_C[ch],
                                   outline="")
        elif kind == "fish":
            hx, hy, rx, ry, (tx, ty) = self.hole_at(side)
            hx, hy, tx, ty = px + hx, py + hy, px + tx, py + ty
            bite = a["bite"]
            if t < FISH_CUT:   # cutting round the hole
                k = t / FISH_CUT
                for i in range(int(k * 24) + 1):
                    ang = i / 24 * 2 * math.pi
                    x, y = round(hx + math.cos(ang) * rx - pb / 2), round(hy + math.sin(ang) * ry - pb / 2)
                    c.create_rectangle(x, y, x + pb, y + pb, fill=WATER_C, outline="")
                return
            self.blob(hx, hy, rx + pb, ry + pb, pb, ICE_C)   # an icy rim, and dark water
            self.blob(hx, hy, rx, ry, pb, WATER_C)
            rip = (t * 0.8) % 1   # a ripple spreading out from the line
            if rip < 0.7:
                for i in range(12):
                    ang = i / 12 * 2 * math.pi
                    x, y = hx + math.cos(ang) * rx * rip, hy + math.sin(ang) * ry * rip
                    c.create_rectangle(round(x), round(y), round(x + pb), round(y + pb), fill=RIPPLE_C, outline="")
            rel = t - bite
            if rel < 0:   # waiting: the bobber bobs, with a couple of nibbles just before the bite
                nibble = -1.2 < rel < -1.05 or -0.6 < rel < -0.45
                ex, ey = hx, hy - pb + (1.5 * pb if nibble else round(math.sin(t * 2.5) * 0.6 * pb))
            elif rel < REEL:   # reeling it in
                k = rel / REEL
                ex, ey = hx + math.sin(t * 30) * pb, hy + (ty + 10 * s - hy) * k
                ty += 3 * s * (1 - k)   # (the rod bends)
            elif rel < REEL + SHOW:   # holding it up, swinging on the line
                ex, ey = hx + math.sin(t * 3) * 2 * s, ty + 10 * s
            elif rel < REEL + SHOW + DROP:   # back down the hole it goes
                k = (rel - REEL - SHOW) / DROP
                ex, ey = hx, ty + 10 * s + (hy - ty - 10 * s) * k * k
            else:
                ex, ey = hx, hy - pb
            ax, ay = self.act_hand(side, 0 if REEL <= rel < REEL + SHOW or 0 <= rel < REEL else 1)
            ax, ay = px + ax, py + sink + ay
            self.pixel_line(ax - side * 2 * pb, ay + 2 * pb, tx, ty, pb, WAND_C)   # the rod
            c.create_line(tx, ty, ex, ey, fill=STRING_C, width=max(1, round(s)))  # the line
            if 0 <= rel < REEL + SHOW + DROP:   # the catch, hanging off the end of the line
                rows, colours = CATCHES[a["catch"]]
                self.glyph(rows, round(ex - len(rows[0]) * pb / 2), round(ey), pb, colours)
            else:   # the bobber: red on top, white underneath
                c.create_rectangle(round(ex - pb), round(ey - pb), round(ex + pb), round(ey), fill=BOBBER_C[0],
                                   outline="")
                c.create_rectangle(round(ex - pb), round(ey), round(ex + pb), round(ey + pb), fill=BOBBER_C[1],
                                   outline="")
        elif kind == "balloon":
            for b in a["balloons"]:
                at = self.balloon_at(b, t, side)
                if not at:
                    continue
                cx, cy, r = at
                cx, cy = px + cx, py + cy + (sink if t - b["at"] < TIE else 0)
                colour, shine = BALLOON_C[b["c"]]
                self.blob(cx, cy, r * 0.85, r, pb, colour)
                if r > 4 * pb:   # a shiny spot
                    x, y = round(cx - r * 0.4), round(cy - r * 0.55)
                    c.create_rectangle(x, y, x + pb, y + 2 * pb, fill=shine, outline="")
                kx, ky = round(cx - pb / 2), round(cy + r)   # the knot
                c.create_rectangle(kx, ky, kx + pb, ky + pb, fill=colour, outline="")
                if t - b["at"] <= TIE:   # held by its neck
                    hx, hy = self.act_hand(side, 1)
                    self.pixel_line(kx + pb / 2, ky + pb, px + hx, py + sink + hy, pb, colour)
                else:   # let go: a wiggly string hangs down
                    for i in range(1, 7):
                        x = kx + round(math.sin(t * 6 + i * 0.9) * 0.6) * pb
                        c.create_rectangle(x, ky + i * pb, x + pb, ky + (i + 1) * pb, fill=STRING_C, outline="")
        else:   # the plane, before it's thrown
            d = a["dir"]
            plane = PLANE if d > 0 else [row[::-1] for row in PLANE]
            if t < FOLD:   # folding: a sheet, then folded in half, then a plane
                rows = SHEET if t < 0.5 else HALF_FOLD if t < 1.0 else plane
                self.glyph(rows, round(px + pet_w / 2 - len(rows[0]) * pb / 2), round(py + sink + 1.5 * bh), pb, PLANE_C)
            elif t < THROW:   # held up high, ready to go
                hx, hy = self.act_hand(side, 0)
                self.glyph(plane, round(px + hx - len(plane[0]) * pb / 2), round(py + sink + hy - 6 * pb), pb, PLANE_C)
