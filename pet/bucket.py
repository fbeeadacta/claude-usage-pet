# part of the Pet: the minecraft water bucket jump (an "mlg"), the other way to leap off a window's edge.
# it hops off holding a full bucket, looks down, tips it out just before it hits the ground, and lands in the
# water without a scratch (the bucket's empty now). it stands in it a moment, then scoops it back up the
# minecraft way: the source block goes at once, the flowing water round it drains away, and the bucket's full.
# the water has its own see-through window (it's there before the mascot lands). while the mascot stands in
# it, render.py also draws a see-through strip of water over its legs, so it stands in the water, not on it.
import math
import random

from .art import BLOCK_H, BLOCK_W, BUCKET, MC_WATER
from .config import WATER_TIME
from .lines import BUCKET_FAIL, BUCKET_LINES, WATER_LINES
from .sprites import Stage

POUR_AHEAD = 0.16             # tips the bucket out this many seconds before it lands
FLOW = 5                      # the water flows this many steps out each side of the source block
STEP_T = 0.045                # seconds for the water to flow one step further (draining is a bit slower)
SCOOP_T, HOLD_T = 0.35, 0.8   # dipping the bucket in, then showing off the full bucket
IN_WATER = ("stand", "scoop", "hold")   # (standing still in its puddle for these)


class BucketMixin:
    def start_bucket(self):
        floor = self.edge_drop()
        if floor is None:
            return False
        self.spring_off(floor)
        self.bucket = {"phase": "fall", "t": 0.0, "lead": 1 if self.dir > 0 else 0, "floor": floor, "full": True}
        self.state, self.state_t = "idle", 2.0
        self.tally("buckets")
        if random.random() < 0.75:
            self.say(self.pick(BUCKET_LINES), force=True)
        return True

    def bucket_stop(self):
        # put away (picked up, hidden, dev mode): the bucket goes, and any water drains
        self.bucket = None
        if self.water and self.water["phase"] != "drain":
            self.water.update(phase="drain", t=0.0)

    def bucket_tick(self, dt):
        self.water_tick(dt)
        b = self.bucket
        if b is None:
            return
        if self.held or self.hidden or self.trip:
            self.bucket_stop()
            return
        b["t"] += dt
        if b["phase"] == "fall":
            if self.vy > 0 and b["floor"] - self.y <= self.vy * POUR_AHEAD:   # nearly down: tip it out
                b.update(phase="pour", t=0.0)
                lo, hi = self.x_limits()
                x = min(max(self.x + self.vx * POUR_AHEAD, lo), hi)
                self.water = {"x": x, "base": b["floor"], "t": 0.0, "phase": "spread", "bits": []}
                self.water_bits(x, b["floor"], 6, 90)
                self.play("splash")
        elif b["phase"] == "stand" and b["t"] >= WATER_TIME:
            b.update(phase="scoop", t=0.0)
        elif b["phase"] == "scoop":
            if not b["full"] and b["t"] >= SCOOP_T * 0.5:   # bloop: the source block's back in the bucket
                b["full"] = True
                if self.water:
                    self.water.update(phase="drain", t=0.0)
                self.play("bloop")
            if b["t"] >= SCOOP_T:
                b.update(phase="hold", t=0.0)
                self.happy_t = HOLD_T
        elif b["phase"] == "hold" and b["t"] >= HOLD_T:   # back in the inventory
            self.bucket = None
            for _ in range(3):
                self.spawn("glint")

    def bucket_landed(self):
        # it's come down. True = in its water, safe and sound; False = it never got the bucket out (it came
        # down somewhere it didn't expect), so it's an ordinary landing and a bit of a bump
        b = self.bucket
        if b["phase"] == "fall":
            self.bucket = None
            self.dizzy_t = max(self.dizzy_t, 2.0)
            self.say(self.pick(BUCKET_FAIL), force=True)
            return False
        self.vx = self.vy = self.walk_v = 0.0
        self.chute, self.bounces = False, 0
        b.update(phase="stand", t=0.0, full=False)   # (all poured out now)
        if self.water:
            self.water_bits(self.x, self.y, 14, 170)
        if random.random() < 0.7:
            self.say(self.pick(WATER_LINES), force=True)
        return True

    # ---- what render.py draws on the mascot ----
    def bucket_frame(self):
        # (look, full, lead hand, how far it's dipped, looking down) or None
        b = self.bucket
        if b is None:
            return None
        dip = round(3 * math.sin(math.pi * min(1.0, b["t"] / SCOOP_T))) if b["phase"] == "scoop" else 0
        return ("pour" if b["phase"] == "pour" else "hold", b["full"], b["lead"], dip,
                b["phase"] in ("fall", "pour", "scoop"))

    def bucket_xy(self, look, lead, dip=0):
        # where the bucket picture's top left goes, from the mascot's top left. held, it hangs from the hand by
        # its handle; tipped out, it's upside down (no handle showing), out a bit further and lower
        s = self.s()
        bw, bh, pb = max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s)), max(1, round(2 * s))
        if look == "pour":
            x0, y0 = 17 * bw - pb, 3 * bh - 2 * pb
        else:
            x0, y0 = 17 * bw - 2 * pb, 2 * bh - pb + dip * pb
        if not lead:   # (the left hand: mirrored)
            x0 = 18 * bw - x0 - len(BUCKET[0]) * pb
        return x0, y0

    def water_depth(self):
        # how deep the water is round its legs (pixels), while it's standing in it
        w, b = self.water, self.bucket
        if not w or w["phase"] == "drain" or not b or b["phase"] not in IN_WATER:
            return 0
        return 6 * max(1, round(2 * self.s()))

    # ---- the water, on its own window ----
    def water_cols(self, w, s):
        # the water as (left, right, height) runs from its middle: the source block, then flowing water stepping
        # down each side. it spreads a step at a time, and when the source is scooped up it drains middle first.
        bw, pb = max(1, round(BLOCK_W * s)), max(1, round(2 * s))
        half, step, t = 10 * bw, 5 * pb, w["t"]
        if w["phase"] == "drain":
            out, steps = [], [i for i in range(FLOW) if t < (i + 1) * STEP_T * 1.5]
        else:
            out, steps = [(-half, half, 6 * pb)], range(min(FLOW, int(t / STEP_T)))
        for i in steps:
            x0, h = half + i * step, (FLOW - i) * pb
            out += [(x0, x0 + step, h), (-x0 - step, -x0, h)]
        return out

    def water_bits(self, x, base, n, speed):
        s = self.s()
        for _ in range(n):   # droplets flying up
            ang = random.uniform(math.pi * 1.1, math.pi * 1.9)
            v = random.uniform(0.4, 1.0) * speed * s
            self.water["bits"].append([x + random.uniform(-30, 30) * s, base - random.uniform(4, 12) * s,
                                       math.cos(ang) * v, math.sin(ang) * v, random.choice(MC_WATER), 0.6])

    def water_tick(self, dt):
        w = self.water
        if w is None:
            return
        if self.hidden:
            if self.water_stage is not None:
                self.water_stage.hide()
            self.water = None
            return
        w["t"] += dt
        s = self.s()
        for bit in w["bits"]:
            bit[0] += bit[2] * dt
            bit[1] += bit[3] * dt
            bit[3] += 700 * s * dt
            bit[5] -= dt
        w["bits"] = [bit for bit in w["bits"] if bit[5] > 0 and bit[1] < w["base"]]
        cols = self.water_cols(w, s)
        if not cols and not w["bits"]:   # all drained away
            self.water_stage.hide()
            self.water = None
            return
        if self.water_stage is None:
            self.water_stage = Stage(self.root)
        st = self.water_stage
        x, base = w["x"], w["base"]
        if st.place(x - 130 * s, base - 220 * s, x + 130 * s, base + 4 * s):
            self.root.lift()   # (the mascot in front of it)
        c = st.canvas
        c.delete("all")
        ox, oy = st.origin
        cx, by = x - ox, base - oy
        pb = max(1, round(2 * s))
        b = self.bucket
        if b and b["phase"] == "pour":   # the water pouring out of the bucket, down to the puddle
            lx, ly = self.bucket_xy("pour", b["lead"])
            mx = self.x - 9 * max(1, round(BLOCK_W * s)) + lx + len(BUCKET[0]) * pb / 2 - ox
            my = self.y + self.vy * dt - self.pet_px[1] + ly + (len(BUCKET) - 3) * pb - oy   # (where it's about to be)
            bottom = by - 6 * pb
            if my < bottom:   # a thick stream: dark edges, a light middle, wider where it hits the puddle
                for half, col in ((3.5, MC_WATER[0]), (2.5, MC_WATER[1]), (1, MC_WATER[2])):
                    c.create_rectangle(round(mx - half * pb), round(my), round(mx + half * pb), round(bottom),
                                       fill=col, outline="")
                c.create_rectangle(round(mx - 5 * pb), round(bottom - 2 * pb), round(mx + 5 * pb), round(bottom),
                                   fill=MC_WATER[1], outline="")
                for i in range(4):   # drips flying off the sides
                    dy = (w["t"] * 400 * s + i * 23 * pb) % max(1, bottom - my)
                    dx = (4.5 + i % 2) * pb * (1 if i % 2 else -1)
                    c.create_rectangle(round(mx + dx), round(my + dy), round(mx + dx + pb), round(my + dy + pb),
                                       fill=MC_WATER[2], outline="")
        for x0, x1, h in cols:   # see-through like minecraft water (every fourth pixel's a gap), a lighter top
            l, r, top = round(cx + x0), round(cx + x1), round(by - h)
            c.create_rectangle(l, top, r, round(by), fill=MC_WATER[1], outline="", stipple="gray75")
            c.create_rectangle(l, top, r, top + pb, fill=MC_WATER[2], outline="")
        span = max((abs(x0) for x0, _, _ in cols), default=0)
        for k in range(6):   # little glints drifting along the surface
            gx = -span + (k * 37 * pb + w["t"] * 22 * s) % (2 * span or 1)
            h = max((h for x0, x1, h in cols if x0 <= gx < x1 - 2 * pb), default=0)
            if h > 2 * pb:
                c.create_rectangle(round(cx + gx), round(by - h), round(cx + gx + 2 * pb), round(by - h + pb),
                                   fill=MC_WATER[3], outline="")
        for bx, bit_y, _, _, col, _ in w["bits"]:
            c.create_rectangle(round(bx - ox), round(bit_y - oy), round(bx - ox + pb), round(bit_y - oy + pb),
                               fill=col, outline="")
