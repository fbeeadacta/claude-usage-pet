# part of the Pet: the bungee jump, another way to leap off a window's edge. a plank slides out from the
# window's corner, it puts on a harness and hooks the cord on (from the plank's end to the harness ring between
# its legs), and off it goes. it falls head first, the cord goes tight and stretches, and it bounces up and
# down a few times, swinging a little, hanging upside down. then the cord's let out until it's dangling just
# above the floor, it waves, unclips, flips over and lands on its feet. the cord springs back up and the plank
# slides away.
# the plank and cord are drawn on their own see-through window (they stretch from the window down to it).
import math
import random

from .art import BLOCK_H, CORD_C, WOOD_C
from .config import GRAVITY
from .lines import BUNGEE_DONE, BUNGEE_LINES
from .sprites import Stage

TIE_T = 0.9          # standing on the plank tying the cord on, before it jumps
SLIDE_T = 0.3        # the plank sliding out (and back in at the end)
BACK_T = 0.35        # the cord springing back up after it unclips
HANG_T = 0.8         # dangling just above the floor, waving, before it unclips
REACH = 36           # how far the plank's end sticks out past the window's edge (pixels at 1x)
ON_CORD = ("fall", "lower", "hang")
HARNESS_RING = 1.8   # how far below its middle the harness ring is, in body rows


class BungeeMixin:
    def start_bungee(self):
        floor = self.edge_drop()
        if floor is None:
            return False
        s, ph = self.s(), self.pet_px[1]
        edge = self.plat_box[3] if self.dir > 0 else self.plat_box[1]
        ax, ay = edge + self.dir * REACH * s, self.plat_box[2]
        # the cord: slack for the first part of the fall, then a spring. its stiffness is worked out so the
        # lowest point of the first bounce just misses the floor (falling from the top of the hop, D + extra),
        # and the damping takes a few bounces to settle
        low = floor - ph / 2 - 8 * s - ay     # (how far below the anchor its middle gets, at the lowest)
        rest = 0.45 * low
        k = 2 * GRAVITY * s * (low + 45 * s + ph / 2) / (low - rest) ** 2
        self.bungee = {"phase": "tie", "t": 0.0, "ax": ax, "ay": ay, "edge": edge, "floor": floor, "rest": rest,
                       "k": k, "damp": 0.18 * math.sqrt(k), "twang": False, "said": False, "end": None}
        self.walk_v = 0.0
        self.state, self.state_t = "idle", 2.0
        self.tally("bungees")
        if random.random() < 0.75:
            self.say(self.pick(BUNGEE_LINES), force=True)
        return True

    def bungee_stop(self):
        # cut short (picked up, hidden, a trip, dev mode): the cord springs back and the plank goes
        b = self.bungee
        if b and b["phase"] not in ("back", "done"):
            b.update(phase="back", t=0.0, end=self.harness_xy())

    def harness_xy(self):
        # where the harness ring is on the screen (the cord hooks onto it), tilted or not: low in the middle,
        # between its legs (render.py draws the harness: HARNESS_RING blocks below the body's middle)
        ph, bh = self.pet_px[1], max(2, round(BLOCK_H * self.s()))
        d = HARNESS_RING * bh
        return (self.x - math.sin(self.angle) * d, self.y - ph / 2 + math.cos(self.angle) * d)

    def bungee_lean(self):
        # (for turn()) which way it hangs: feet pointing up the cord, near upside down
        b = self.bungee
        cx, cy = self.x, self.y - self.pet_px[1] / 2
        dx, dy = b["ax"] - cx, b["ay"] - cy
        if math.hypot(dx, dy) < b["rest"]:
            return self.dir * 2.3   # still slack: tipping over head first, like a swan dive
        a = math.atan2(-dx, dy)
        return a + 2 * math.pi * round((self.dir * math.pi - a) / (2 * math.pi))

    def bungee_move(self, dt, s):
        # moves it while it's on the cord. True = it did (nothing else moves it this frame)
        b = self.bungee
        if b["phase"] == "tie":   # stands on the plank, tying the cord on
            if b["t"] >= TIE_T:
                self.spring_off(b["floor"])
                self.vx = self.dir * 110 * s
                b.update(phase="fall", t=0.0)
                self.play("whoosh")
            return True
        if b["phase"] not in ON_CORD:
            return False
        g, ph = GRAVITY * s, self.pet_px[1]
        if b["phase"] == "lower":   # let the cord out until it dangles just above the floor
            want = b["floor"] - 34 * s - ph / 2 - b["ay"] - g / b["k"]
            b["rest"] += max(-100 * s * dt, min(100 * s * dt, want - b["rest"]))
            speed = math.hypot(self.vx, self.vy)
            if (abs(want - b["rest"]) < 1 and speed < 25 * s) or b["t"] > 4:
                b.update(phase="hang", t=0.0)
        ax_, ay_ = 0.0, g
        dx, dy = self.x - b["ax"], self.y - ph / 2 - b["ay"]
        d = math.hypot(dx, dy) or 1.0
        if d > b["rest"]:   # tight: the cord pulls back, and soaks up some of the bounce
            ux, uy = dx / d, dy / d
            radial = self.vx * ux + self.vy * uy
            if b["phase"] == "fall" and not b["twang"] and radial < 0:   # the bottom of the first stretch
                b["twang"] = True
                self.play("twang")
            damp = b["damp"] * (1 if b["phase"] == "fall" else 4)   # (let out gently, no more bouncing)
            f = -b["k"] * (d - b["rest"]) - damp * radial
            ax_, ay_ = ax_ + f * ux, ay_ + f * uy
        self.vx = (self.vx + ax_ * dt) * max(0.0, 1 - 0.5 * dt)   # (a bit of air, so the swing dies down)
        self.vy += ay_ * dt
        lo, hi = self.x_limits()
        self.x = min(max(self.x + self.vx * dt, lo), hi)
        self.y += self.vy * dt
        if self.y > b["floor"] - 2:   # (never quite touches)
            self.y, self.vy = b["floor"] - 2, min(self.vy, 0.0)
        if b["phase"] == "fall" and b["twang"] and ((b["t"] > 3.5 and math.hypot(self.vx, self.vy) < 120 * s)
                                                    or b["t"] > 5.5):
            b.update(phase="lower", t=0.0)
        elif b["phase"] == "hang" and b["t"] >= HANG_T:   # unclips: a little hop, and it flips onto its feet
            b.update(phase="back", t=0.0, end=self.harness_xy())
            self.vx, self.vy = 0.0, -math.sqrt(2 * g * 40 * s)
            self.play("clink")
        self.draw_bungee(b)   # (drawn after it moves, so the cord keeps up with it)
        return True

    def bungee_tick(self, dt):
        b = self.bungee
        if b is None:
            return
        if self.hidden:
            if self.bungee_stage is not None:
                self.bungee_stage.hide()
            self.bungee = None
            return
        if self.held or self.trip:
            self.bungee_stop()
        b["t"] += dt
        if b["phase"] == "back":
            if self.grounded() and not b["said"] and abs(self.angle) < 0.3:   # landed it
                b["said"] = True
                self.happy_t = 1.0
                if random.random() < 0.7:
                    self.say(self.pick(BUNGEE_DONE), force=True)
            if b["t"] > BACK_T + SLIDE_T and (b["said"] or b["t"] > 3):
                b["phase"] = "done"
        if b["phase"] == "done":
            self.bungee_stage.hide()
            self.bungee = None
            return
        if b["phase"] not in ON_CORD or self.held:   # (on the cord, bungee_move draws it)
            self.draw_bungee(b)

    def bungee_frame(self):
        # (for render) waving while it dangles
        b = self.bungee
        return b is not None and b["phase"] == "hang"

    def draw_bungee(self, b):
        s = self.s()
        pb = max(1, round(2 * s))
        if self.bungee_stage is None:
            self.bungee_stage = Stage(self.root)
        st = self.bungee_stage
        ax, ay, side = b["ax"], b["ay"], 1 if b["ax"] > b["edge"] else -1
        if st.place(ax - 300 * s, ay - 30 * s, ax + 300 * s, b["floor"] + 4 * s):
            self.root.lift()   # (the mascot in front of it)
        c = st.canvas
        c.delete("all")
        ox, oy = st.origin
        # how far out the plank is: sliding out at the start, back in at the end
        if b["phase"] == "tie":
            k = min(1.0, b["t"] / SLIDE_T)
        elif b["phase"] == "back":
            k = 1 - min(1.0, max(0.0, b["t"] - BACK_T) / SLIDE_T)
        else:
            k = 1.0
        if k <= 0:
            return
        inner = b["edge"] - side * 16 * s   # (its back end rests on the window, clamped down)
        outer = inner + ((ax - inner) + side * 4 * s) * k
        l, r = sorted((inner, outer))
        top = ay - oy
        c.create_rectangle(round(l - ox), round(top), round(r - ox), round(top + 2 * pb), fill=WOOD_C[0], outline="")
        c.create_rectangle(round(l - ox), round(top + 2 * pb), round(r - ox), round(top + 3 * pb), fill=WOOD_C[1],
                           outline="")
        for i in range(1, 4):   # the gaps between boards
            x = inner + side * i * 9 * s
            if l < x < r:
                c.create_rectangle(round(x - ox), round(top), round(x - ox + max(1, pb // 2)), round(top + 3 * pb),
                                   fill=WOOD_C[2], outline="")
        cx0 = inner + side * 3 * s   # a clamp holding it to the window
        c.create_rectangle(round(cx0 - ox - 2 * pb), round(top - pb), round(cx0 - ox + 2 * pb), round(top + 5 * pb),
                           fill=CORD_C[2], outline="")
        if k < 1:
            return
        hx, hy = ax - ox, top + 3 * pb   # the ring the cord's tied to, under the plank's end
        c.create_rectangle(round(hx - pb), round(hy - pb), round(hx + pb), round(hy + pb), fill=CORD_C[2], outline="")
        if b["phase"] == "back":   # springing back up, wiggling
            e = min(1.0, b["t"] / BACK_T)
            ex, ey = b["end"]
            q = 1 - (1 - e) ** 3
            fx, fy = ex + (ax - ex) * q, ey + (ay - ey) * q
            if e >= 1:
                return
        else:
            fx, fy = self.harness_xy()
        d = math.hypot(fx - ax, fy - ay)
        sag = max(0.0, b["rest"] - d) * 0.6 if b["phase"] != "back" else d * 0.15 * math.sin(b["t"] * 40)
        mx, my = (ax + fx) / 2 - ox, (ay + fy) / 2 + sag - oy
        ex, ey = fx - ox, fy - oy

        def at(k):   # a point along the cord (a curve from the ring, bowed through the middle, to its end)
            return ((1 - k) ** 2 * hx + 2 * (1 - k) * k * mx + k * k * ex,
                    (1 - k) ** 2 * hy + 2 * (1 - k) * k * my + k * k * ey)

        n = 32
        pts = [at(k / n) for k in range(n + 1)]
        along = [0.0]   # how far along the cord each point is
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            along.append(along[-1] + math.hypot(x1 - x0, y1 - y0))
        flat = [v for p in pts for v in p]
        w = max(4, round(5 * s))
        c.create_line(*flat, fill=CORD_C[3], width=w + 2)   # (a dark edge, so it shows on any wallpaper)
        c.create_line(*flat, fill=CORD_C[0], width=w)
        c.create_line(*flat, fill=CORD_C[1], width=max(1, round(s)))   # a shine down the middle
        step, step_at = 3 * pb, 0.0
        for i in range(n):   # braid marks: short slanted ticks every few pixels, so it looks woven
            (x0, y0), (x1, y1), seg = pts[i], pts[i + 1], along[i + 1] - along[i]
            if seg <= 0:
                continue
            ux, uy = (x1 - x0) / seg, (y1 - y0) / seg
            while step_at <= along[i + 1]:
                f = (step_at - along[i]) / seg
                cx, cy = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                h = w * 0.45
                c.create_line(cx - uy * h - ux * h * 0.6, cy + ux * h - uy * h * 0.6,
                              cx + uy * h + ux * h * 0.6, cy - ux * h + uy * h * 0.6, fill=CORD_C[6], width=1)
                step_at += step
        if b["phase"] == "back":
            return
        # the thick end at the harness: a black sleeve over the bundle of cords, always the same length, with a
        # metal ferrule where the cord goes in and a clip onto the harness ring
        total, size = along[-1], 12 * pb
        if total < 1:
            return
        start = max(0.0, total - size)
        end = [p for p, a in zip(pts, along) if a >= start]
        i = next(j for j, a in enumerate(along) if a >= start)
        if i > 0:   # (begin exactly where the sleeve starts)
            (x0, y0), (x1, y1) = pts[i - 1], pts[i]
            f = (start - along[i - 1]) / max(1e-6, along[i] - along[i - 1])
            end = [(x0 + (x1 - x0) * f, y0 + (y1 - y0) * f)] + end
        if len(end) < 2:
            return
        sx, sy = end[0]
        tx, ty = end[1]
        d = math.hypot(tx - sx, ty - sy) or 1.0
        ux, uy = (tx - sx) / d, (ty - sy) / d
        flat_end = [v for p in end for v in p]
        sleeve = round(w * 1.6)
        c.create_line(*flat_end, fill=CORD_C[3], width=sleeve + 2)
        c.create_line(*flat_end, fill=CORD_C[4], width=sleeve)
        off = sleeve * 0.25   # (a sheen down one side)
        c.create_line(*[v for x, y in end for v in (x - uy * off, y + ux * off)], fill=CORD_C[5],
                      width=max(1, round(s)))
        fx2, fy2 = sx + ux * 1.5 * pb, sy + uy * 1.5 * pb   # the ferrule: a short metal band at the top
        c.create_line(sx, sy, fx2, fy2, fill=CORD_C[7], width=sleeve + 2)
        c.create_line(sx, sy, fx2, fy2, fill=CORD_C[2], width=sleeve)
        c.create_rectangle(round(ex - 1.5 * pb), round(ey - 1.5 * pb), round(ex + 1.5 * pb), round(ey + 1.5 * pb),
                           fill=CORD_C[7], outline="")   # the clip
        c.create_rectangle(round(ex - pb), round(ey - pb), round(ex + pb), round(ey + pb), fill=CORD_C[2],
                           outline="")
