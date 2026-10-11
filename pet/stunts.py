# part of the Pet: more ways off a window's edge: a zipline, a fireman's pole and a spider-man web swing.
# (the leap of faith is in movement.py and hay.py, the water bucket in bucket.py, the bungee in bungee.py.)
#   zipline: a post pops up on the window's corner and a cable shoots out to a post far off near the floor.
#            it hops up, grabs the trolley's handlebar and whizzes down, swinging back as it speeds up, brakes
#            at the end, lets go and drops onto the floor. the cable reels in and the posts sink away.
#   pole:    a brass fireman's pole slides down from the window's corner to the floor. it hops onto it, hugs it
#            and slides down, spinning round it, lands, and the pole slides back up.
#   web:     it jumps off, shoots a web from its raised hand up to the ceiling ahead (thwip!), swings down
#            under it, and lets go at the top of the swing. staying on this screen, it then shoots a second web
#            down at the ground ahead and is yanked down by it; going over to the next monitor, it flips and
#            flies across. either way it comes down in a superhero landing.
# the props are drawn on their own see-through window. while it's on them they're drawn after it moves, so
# they keep up with it. render.py draws the bit of the pole in front of it, and its hands round the pole.
import math
import random

from .art import ARMS, BLOCK_H, BLOCK_W, LEFT_WAVE, POLE_C, WAVE, WEB_C, ZIP_C
from .config import GRAVITY
from .lines import POLE_DONE, POLE_LINES, WEB_DONE, WEB_LINES, ZIP_DONE, ZIP_LINES
from .sprites import Stage

# the phases where the stunt moves it (the rest is ordinary falling and standing)
MOVES = {"zip": ("set", "grab", "ride", "end"), "pole": ("set", "hop", "slide", "land"),
         "web": ("fall", "swing", "air", "zip", "pull")}
SET_T = 0.7          # zipline / pole: setting up before it goes
HOP_T = 0.3          # hopping up to the trolley, or across to the pole
PACK_T = 0.5         # packing it all away again
RELEASE = 0.4        # web: lets go this far (radians) past the bottom of the swing, on the way up


def ease(k):
    k = min(1.0, max(0.0, k))
    return k * k * (3 - 2 * k)


class StuntsMixin:
    def stunt_sizes(self):
        s = self.s()
        return s, max(1, round(2 * s)), max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s)), self.pet_px[1]

    def stunt_room(self):
        # how far left and right a stunt can take it: this screen only (the floor's somewhere else on the next),
        # and no nearer the edge than the screen's own clamp lets it go (clamp_x keeps self.half from the edge).
        # self.half grows to fit the speech bubble, so this allows for a long line: if the stunt went nearer,
        # the clamp would shove it back every frame while the stunt pulled it out again (it jittered there).
        s = self.s()
        sc = self.screens[self.si]
        m = max(self.half, 112 * s)
        return sc.wl + m, sc.wr - m

    def cross_target(self):
        # a monitor next door it could zipline or web-swing over to (only if "stay on one monitor" is off, which
        # neighbour() checks): the one the way it's facing, if the window it's on is higher than that monitor's
        # taskbar. its number, or None.
        if self.plat is None:
            return None
        nb = self.neighbour(self.dir)
        if nb is None or self.screens[nb].wb - self.plat_box[2] < 120 * self.s():
            return None
        return nb

    def stunt_begin(self, kind, lines, **info):
        self.stunt = dict(kind=kind, phase="set", t=0.0, x0=self.x, top=self.plat_box[2], said=False, **info)
        self.walk_v = 0.0
        self.state, self.state_t = "idle", 2.0
        self.tally({"zip": "ziplines", "pole": "poles", "web": "webs"}[kind])
        if random.random() < 0.75:
            self.say(self.pick(lines), force=True)
        return True

    # ---- starting each one ----
    def start_zipline(self, cross=None):
        # cross: True = only over to the next monitor, False = never, None = sometimes, when it can
        if self.plat is None or not self.anim.get():
            return False
        s, pb, bw, bh, ph = self.stunt_sizes()
        sc = self.screens[self.si]
        edge = self.plat_box[3] if self.dir > 0 else self.plat_box[1]
        hang = ph + 7 * pb   # (from the cable down to its feet: the trolley's straps, then the mascot)
        ax, ay = edge - self.dir * 6 * s, self.plat_box[2] - hang - 14 * s   # the top of the post on the corner
        to = self.cross_target() if cross is not False else None
        if cross and to is None:
            return False
        border = sc.mr if self.dir > 0 else sc.ml
        if to is not None and (cross or random.random() < 0.6):   # over to the monitor next door
            o = self.screens[to]
            floor = o.wb
            bx = min(max(border + self.dir * 220 * s, o.wl + 9 * bw + 10 * s), o.wr - 9 * bw - 10 * s)
        else:
            to, floor = None, self.edge_drop()
            if floor is None:
                return False
            lo, hi = self.stunt_room()
            room = (hi - ax) if self.dir > 0 else (ax - lo)
            bx = ax + self.dir * min((floor - hang - 14 * s - ay) * 1.4, room, 900 * s)
        by = floor - hang - 14 * s   # the far post: low enough that it lets go just above the floor
        dx = abs(bx - ax)
        if by - ay < 60 * s or dx < max(150 * s, 0.7 * (by - ay)) or dx > 1600 * s:
            return False   # no room for a cable that isn't too steep (it'd run right behind it), or too flat
        return self.stunt_begin("zip", ZIP_LINES, ax=ax, ay=ay, bx=bx, by=by, floor=floor, edge=edge, hang=hang,
                                u=0.0, v=0.0, to=to, border=border, sag=min(0.06 * math.hypot(dx, by - ay), 45 * s))

    def start_pole(self):
        floor = self.edge_drop()
        if floor is None:
            return False
        s, pb, bw, bh, ph = self.stunt_sizes()
        edge = self.plat_box[3] if self.dir > 0 else self.plat_box[1]
        xp = edge + self.dir * (9 * bw + 6 * s)   # far enough out that it can hug it without touching the window
        lo, hi = self.stunt_room()
        if not lo <= xp <= hi:
            return False
        return self.stunt_begin("pole", POLE_LINES, xp=xp, floor=floor, edge=edge, v=0.0, y0=self.y)

    def start_web(self, cross=None):
        # cross: True = only over to the next monitor, False = never, None = sometimes, when it can
        to = self.cross_target() if cross is not False else None
        if cross and to is None:
            return False
        if to is not None and not (cross or random.random() < 0.6):
            to = None
        floor = self.edge_drop()
        if floor is None:
            return False
        sc = self.screens[self.si]
        self.stunt_begin("web", WEB_LINES, floor=floor, anchor=None, rope=0.0, shot=0.0, ground=None, shot2=0.0,
                         to=to,
                         border=sc.mr if self.dir > 0 else sc.ml)
        self.stunt["phase"] = "fall"
        self.spring_off(floor)
        return True

    def stunt_stop(self):
        # cut short (picked up, hidden, a trip, dev mode): everything's put away, and it's free
        st = self.stunt
        if st and st["phase"] in MOVES[st["kind"]]:
            st.update(phase="gone" if st["kind"] == "web" else "pack", t=0.0, said=True)

    # ---- moving it ----
    def stunt_move(self, dt, s):
        # True = the stunt moved it this frame (nothing else does)
        st = self.stunt
        if st["phase"] not in MOVES[st["kind"]]:
            return False
        getattr(self, "move_" + st["kind"])(st, dt)
        self.draw_stunt(st)   # (drawn after it moves, so the props keep up with it)
        return True

    def move_zip(self, st, dt):
        s, pb, bw, bh, ph = self.stunt_sizes()
        ax, ay, bx, by = st["ax"], st["ay"], st["bx"], st["by"]
        if st["phase"] == "set":
            if st["t"] >= SET_T:
                st.update(phase="grab", t=0.0)
                self.plat, self.through = None, False
                self.vx = self.vy = 0.0
            return
        if st["phase"] == "grab":   # a hop up to the handlebar
            k = ease(st["t"] / HOP_T)
            self.x = st["x0"] + (ax - st["x0"]) * k
            self.y = st["top"] + (ay + st["hang"] - st["top"]) * k - math.sin(k * math.pi) * 18 * s
            if st["t"] >= HOP_T:
                st.update(phase="ride", t=0.0)
                self.play("zip")
            return
        length = math.hypot(bx - ax, by - ay)
        if st["phase"] == "ride":
            u = st["u"]
            if u < 0.86:   # downhill, with a bit of drag from the wheel
                st["v"] += (GRAVITY * s * (by - ay) / length * 0.8 - 1.1 * st["v"]) * dt
                st["v"] = max(st["v"], 90 * s)   # (a gentle cable still gets it there)
            else:          # braking into the far post
                st["v"] = max(70 * s, st["v"] - 1500 * s * dt)
            st["u"] = min(1.0, u + st["v"] * dt / length)
            if st["u"] >= 1.0:
                st.update(phase="end", t=0.0)
                self.spin -= self.dir * 5   # its legs swing on forward as it stops
                self.play("clink")
        elif st["phase"] == "end" and st["t"] >= 0.45:   # lets go
            st.update(phase="pack", t=0.0)
            self.vx = self.vy = 0.0
            return
        self.x, self.y = self.zip_point(st, st["u"])
        self.y += st["hang"]
        if st["to"] is not None and self.si != st["to"] and (self.x - st["border"]) * self.dir > 0:
            self.si = st["to"]   # (over onto the other monitor now)

    def zip_point(self, st, u):
        # where the trolley is on the cable (screen pixels): the cable sags under the mascot's weight, most in
        # the middle and not at all at the posts
        sag = st["sag"] * math.sin(math.pi * u) if st["phase"] in ("ride", "end") else 0.0
        return st["ax"] + (st["bx"] - st["ax"]) * u, st["ay"] + (st["by"] - st["ay"]) * u + sag

    def move_pole(self, st, dt):
        s, pb, bw, bh, ph = self.stunt_sizes()
        if st["phase"] == "set":
            if st["t"] >= SET_T:
                st.update(phase="hop", t=0.0)
                self.plat, self.through = None, False
                self.vx = self.vy = 0.0
            return
        if st["phase"] == "hop":   # across onto the pole, a little way down it
            k = ease(st["t"] / HOP_T)
            self.x = st["x0"] + (st["xp"] - st["x0"]) * k
            self.y = st["top"] + ph * 0.6 * k - math.sin(k * math.pi) * 16 * s
            if st["t"] >= HOP_T:
                st.update(phase="slide", t=0.0)
                self.play("slide")
            return
        if st["phase"] == "slide":
            left = st["floor"] - self.y
            if left > 50 * s:
                st["v"] += (GRAVITY * s * 0.7 - 0.9 * st["v"]) * dt
            else:   # squeezes to slow down at the bottom
                st["v"] = max(90 * s, st["v"] - 1800 * s * dt)
            self.y = min(st["floor"], self.y + st["v"] * dt)
            self.x = st["xp"]
            if self.y >= st["floor"]:
                st.update(phase="land", t=0.0)
                self.squash_t = 0.08
                self.play("thud")
        elif st["phase"] == "land" and st["t"] >= 0.45:   # lets go of the pole
            st.update(phase="pack", t=0.0)
            self.vx = self.vy = 0.0

    def move_web(self, st, dt):
        s, pb, bw, bh, ph = self.stunt_sizes()
        g = GRAVITY * s
        if st["phase"] == "pull":   # being yanked down the second web
            self.web_pull(st, dt, s)
            return
        self.vy += g * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if st["phase"] == "air" and st["t"] >= 0.2:   # a moment after letting go: a second web, at the ground
            self.web_ground(st)
        if st["phase"] == "zip":   # the second web flying down
            st["shot2"] = min(1.0, st["shot2"] + dt / 0.1)
            if st["shot2"] >= 1:
                st.update(phase="pull", t=0.0, pull=max(200 * s, math.hypot(self.vx, self.vy) * 0.5))
        if st["phase"] == "fall" and st["t"] >= 0.28 and st["anchor"] is None:
            self.web_aim(st)
        if st["anchor"] is not None and st["shot"] < 1:   # the web flying up to the ceiling
            st["shot"] = min(1.0, st["shot"] + dt / 0.1)
            if st["shot"] >= 1:   # it's stuck: swing from here
                ax, ay = st["anchor"]
                st.update(phase="swing", t=0.0, rope=math.hypot(self.x - ax, self.y - ph / 2 - ay))
        if st["phase"] == "swing":
            ax, ay = st["anchor"]
            cx, cy = self.x, self.y - ph / 2
            d = math.hypot(cx - ax, cy - ay) or 1.0
            if d > st["rope"]:   # the web's tight: back onto the circle, and no more moving outwards
                ux, uy = (cx - ax) / d, (cy - ay) / d
                self.x, self.y = ax + ux * st["rope"], ay + uy * st["rope"] + ph / 2
                out = self.vx * ux + self.vy * uy
                if out > 0:
                    self.vx, self.vy = self.vx - out * ux, self.vy - out * uy
            swing = math.atan2(self.x - ax, self.y - ph / 2 - ay)   # 0 = straight below the web
            lo, hi = self.stunt_room()
            near_edge = (self.x - (hi if self.dir > 0 else lo)) * self.dir > -20 * s
            if (swing * self.dir > RELEASE and self.vy < 0) or near_edge or st["t"] > 3:   # let go
                # over to the next monitor: a flip and a flight across. staying here: a moment in the air, then
                # the second web (it's that one that brings it down, so it never ends up flung against the edge)
                st.update(phase="fly" if st["to"] is not None else "air", t=0.0)
                self.spin = self.dir * (9.0 if st["to"] is not None else 4.0)
                self.vy -= 120 * s   # (a little extra hop off it)
                if st["to"] is not None:   # over to the next monitor: just fast enough to land a bit past its edge
                    o = self.screens[st["to"]]
                    t = (self.vy + math.sqrt(self.vy ** 2 + 2 * g * max(0.0, o.wb - self.y))) / g
                    aim = min(max(st["border"] + self.dir * 140 * s, o.wl + 9 * bw + 10 * s), o.wr - 9 * bw - 10 * s)
                    self.vx = (aim - self.x) / max(t, 0.05)
                else:   # not so fast that it flies off this screen: it comes down by the edge at the furthest
                    t = (self.vy + math.sqrt(self.vy ** 2 + 2 * g * max(0.0, st["floor"] - self.y))) / g
                    most = ((hi if self.dir > 0 else lo) - self.x) / max(t, 0.05)
                    if (self.vx - most) * self.dir > 0:
                        self.vx = most
                self.play("whoosh")
        lo, hi = self.stunt_room()
        if not lo <= self.x <= hi:   # (at the edge: no more pushing into it)
            self.x, self.vx = min(max(self.x, lo), hi), 0.0
        if self.y > st["floor"] - 2:   # (never scrapes the floor mid-swing)
            self.y, self.vy = st["floor"] - 2, min(self.vy, 0.0)

    def web_ground(self, st):
        # the second web: at the ground a little way ahead (kept on this screen, so near the edge it pulls it back
        # in), on the floor or a window below
        s, pb, bw, bh, ph = self.stunt_sizes()
        sc = self.screens[self.si]
        lo, hi = self.stunt_room()
        gx = min(max(self.x + self.dir * 90 * s, lo), hi)
        below = self.platform_under(self.y + 2, sc.wb, gx)
        st.update(phase="zip", t=0.0, ground=(gx, below[2] if below else sc.wb), shot2=0.0)
        self.play("thwip")

    def web_pull(self, st, dt, s):
        # yanked down the second web, faster and faster, feet first. at the bottom it hands back to ordinary
        # falling for the last pixel, so land() does the superhero landing (on the floor or a window)
        lo, hi = self.stunt_room()
        gx, gy = st["ground"]
        gx = min(max(gx, lo), hi)   # (where the clamp would let it be, so it can always get there)
        st["ground"] = (gx, gy)
        dx, dy = gx - self.x, gy - self.y
        d = math.hypot(dx, dy)
        st["pull"] = min(st["pull"] + 2600 * s * dt, 1200 * s)
        step = st["pull"] * dt
        if d <= step + 1 or gy - self.y <= 1 or st["t"] > 2:
            self.x, self.y = gx, gy - 1
            self.vx, self.vy = 0.0, 300 * s
            st.update(phase="fly", t=0.0)
            return
        self.x += dx / d * step
        self.y += dy / d * step
        self.vx, self.vy = dx / d * st["pull"], dy / d * st["pull"]

    def low_hand(self):
        # where its web hand is when it points down and out (the arm in stunt_pose), on the screen, tilted or not
        s, pb, bw, bh, ph = self.stunt_sizes()
        hx, hy = self.dir * 8.5 * bw, 2 * bh   # (from its middle)
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        return self.x + hx * ca - hy * sa, self.y - ph / 2 + hx * sa + hy * ca

    def web_aim(self, st):
        # picks the spot up ahead to stick the web to: up and forward at a steep angle, so it swings down and
        # forward under it. if the bottom of that swing would hit the floor (counting what it falls while the web
        # flies), the spot moves up until it just clears it.
        s, pb, bw, bh, ph = self.stunt_sizes()
        sc = self.screens[self.si]
        cx, cy = self.x, self.y - ph / 2
        low = st["floor"] - ph / 2 - 30 * s - (self.vy * 0.1 + 0.5 * GRAVITY * s * 0.01)
        lo, hi = self.stunt_room()
        room = max(0.0, (hi - cx) if self.dir > 0 else (cx - lo))
        dx = max(30 * s, min(room * 0.6, 220 * s))
        if st["to"] is not None:   # going over to the next monitor: stay above its taskbar, aim near the edge
            low = min(low, self.screens[st["to"]].wb - ph / 2 - 40 * s)
            dx = max(30 * s, min(room * 0.8, 260 * s))
        if low - cy < 60 * s:   # too near the floor for a swing: just the web at the ground
            st.update(phase="air", t=0.2, to=None)
            return
        ay = cy - 1.2 * dx
        if ay + math.hypot(dx, cy - ay) > low:   # (the bottom of the swing would hit the floor: higher up)
            ay = min(cy - 30 * s, (low * low - cy * cy - dx * dx) / (2 * (low - cy)))
        if ay < sc.mt + 12 * s:   # not above the top of the screen: lower, and nearer, so it still clears the floor
            ay = sc.mt + 12 * s
            dx = min(dx, math.sqrt(max(0.0, (low - ay) ** 2 - (cy - ay) ** 2)))
        st["anchor"] = (cx + self.dir * dx, ay)
        self.play("thwip")

    def stunt_landed(self):
        # it's come down (land() asks). True = handled: the web swing ends in a superhero landing.
        st = self.stunt
        if st["kind"] == "web" and st["phase"] == "fly":
            self.vx = self.vy = self.angle = self.spin = 0.0
            self.squash_t, self.bounces = 0.18, 0
            st.update(phase="gone", t=0.0)
            self.stunt_done(WEB_DONE)
            self.play("thud")
            return True
        return False

    def stunt_done(self, lines):
        st = self.stunt
        if not st["said"]:
            st["said"] = True
            self.happy_t = 1.0
            if random.random() < 0.7:
                self.say(self.pick(lines), force=True)

    def stunt_tick(self, dt):
        st = self.stunt
        if st is None:
            return
        if self.hidden:
            if self.stunt_stage is not None:
                self.stunt_stage.hide()
            self.stunt = None
            return
        if self.held or self.trip:
            self.stunt_stop()
        st["t"] += dt
        if st["kind"] == "web" and st["phase"] == "fly" and self.grounded() and not self.held:
            self.stunt_landed()   # (already down without land() noticing, e.g. the screens were re-read just then)
        if st["phase"] == "pack" and self.grounded():
            self.stunt_done(ZIP_DONE if st["kind"] == "zip" else POLE_DONE)
        if ((st["phase"] == "pack" and st["t"] > PACK_T and (st["said"] or st["t"] > 3))
                or (st["phase"] == "gone" and st["t"] > 1.0)):
            if self.stunt_stage is not None:
                self.stunt_stage.hide()
            self.stunt = None
            return
        if st["phase"] not in MOVES[st["kind"]] or self.held:   # (otherwise stunt_move draws it)
            self.draw_stunt(st)

    # ---- how it looks (render.py asks) ----
    def stunt_pose(self):
        # changes to how the mascot's drawn: arms, legs, eyes, and the pole in front of it
        st = self.stunt
        if st is None:
            return None
        kind, ph = st["kind"], st["phase"]
        if kind == "zip" and ph in ("grab", "ride", "end"):
            return {"arms": LEFT_WAVE[1] + WAVE[1], "eye_dir": self.dir}   # both hands up on the handlebar
        if kind == "pole" and ph == "hop":   # reaching out for it
            return {"arms": (ARMS[0],) + WAVE[1] if self.dir > 0 else LEFT_WAVE[1] + (ARMS[1],)}
        if kind == "pole" and ph in ("slide", "land"):   # on it: hugging it
            pose = {"arms": (), "pole": (round(st["top"] - 6 * self.s() - self.y), round(st["floor"] - self.y))}
            if ph == "slide":   # spinning round the pole as it slides
                pose["eye_dir"] = (1, 0, -1, 0)[int(st["t"] / 0.12) % 4]
            return pose
        if kind == "web" and ph in ("fall", "swing"):   # the web hand up
            return {"arms": (ARMS[0],) + WAVE[1] if self.dir > 0 else LEFT_WAVE[1] + (ARMS[1],)}
        if kind == "web" and ph in ("zip", "pull"):   # the web hand down and out, at the ground
            return {"arms": (ARMS[0], (16, 3), (17, 4)) if self.dir > 0 else (ARMS[1], (1, 3), (0, 4))}
        return None

    def stunt_lean(self):
        # (for turn()) how it tilts, or None to stand up straight
        st = self.stunt
        if st is None:
            return None
        if st["kind"] == "zip" and st["phase"] == "ride":   # legs trail behind as it picks up speed
            return self.dir * min(0.35, st["v"] / (1400 * self.s()))   # (going right, that's clockwise)
        if st["kind"] == "web" and st["phase"] == "swing":   # lined up with the web
            ax, ay = st["anchor"]
            return -math.atan2(self.x - ax, self.y - self.pet_px[1] / 2 - ay) * 0.8
        if st["kind"] == "web" and st["phase"] in ("zip", "pull"):   # feet first, towards where the web's stuck
            gx, gy = st["ground"]
            return math.atan2(-(gx - self.x), gy - (self.y - self.pet_px[1] / 2)) * 0.7
        return None

    def raised_hand(self, side, up=0.0):
        # where a raised hand is on the screen (side -1 left, 1 right), tilted or not. up = that much higher.
        s, pb, bw, bh, ph = self.stunt_sizes()
        hx, hy = side * 7.5 * bw, -2 * bh - up   # (from its middle)
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        return self.x + hx * ca - hy * sa, self.y - ph / 2 + hx * sa + hy * ca

    # ---- the props, on their own window ----
    def draw_stunt(self, st):
        s, pb, bw, bh, ph = self.stunt_sizes()
        if self.stunt_stage is None:
            self.stunt_stage = Stage(self.root)
        stage = self.stunt_stage
        kind = st["kind"]
        if kind == "zip":
            box = (min(st["ax"], st["bx"]) - 60 * s, st["ay"] - 30 * s, max(st["ax"], st["bx"]) + 60 * s,
                   st["floor"] + 4 * s)
        elif kind == "pole":
            box = (min(st["edge"], st["xp"]) - 60 * s, st["top"] - 30 * s, max(st["edge"], st["xp"]) + 60 * s,
                   st["floor"] + 4 * s)
        else:
            if st["anchor"] is None and st["ground"] is None:
                return
            # its window stays one size: set once, and only made bigger if a web lands outside it. (it used to
            # follow the mascot, so it grew every frame as it flew across to the next monitor, and a window
            # resized every frame flashes its dark background at the new edge: a black border on the right.)
            box = st.get("box")
            pts = [p for p in (st["anchor"], st["ground"]) if p is not None]
            if box is None or any(not (box[0] + 20 * s <= x <= box[2] - 20 * s and box[1] + 20 * s <= y <= box[3])
                                  for x, y in pts):
                xs, ys = [x for x, _ in pts] + [st["x0"]], [y for _, y in pts]
                box = st["box"] = (min(xs) - 350 * s, min(min(ys), st["top"]) - 30 * s, max(xs) + 350 * s,
                                   max(max(ys), st["floor"], self.screens[self.si].wb) + 4 * s)
        if stage.place(*box):
            self.root.lift()   # (the mascot in front of it)
        c = stage.canvas
        c.delete("all")
        ox, oy = stage.origin
        getattr(self, "draw_" + kind)(c, st, ox, oy, s, pb, bw, bh, ph)

    def draw_zip(self, c, st, ox, oy, s, pb, bw, bh, ph):
        ax, ay, bx, by = st["ax"] - ox, st["ay"] - oy, st["bx"] - ox, st["by"] - oy
        t, phase = st["t"], st["phase"]
        # how far the posts are up, and how much of the cable is out
        if phase == "set":
            up, out, back = ease(t / 0.25), ease((t - 0.2) / 0.4), 0.0
        elif phase == "pack":
            up, out, back = 1 - ease((t - 0.3) / 0.2), 1.0, ease(t / 0.3)
        else:
            up, out, back = 1.0, 1.0, 0.0
        for px, base in ((ax, st["top"] - oy), (bx, st["floor"] - oy)):   # the two posts, rising up
            post_top = base - (base - (ay if px == ax else by) + 4 * s) * up
            c.create_rectangle(round(px - pb), round(post_top), round(px + pb), round(base), fill=ZIP_C[2], outline="")
            c.create_rectangle(round(px - 3 * pb), round(base - pb), round(px + 3 * pb), round(base), fill=ZIP_C[1],
                               outline="")
        if up < 1 and phase == "set":
            return
        x0, y0 = ax + (bx - ax) * back, ay + (by - ay) * back   # (reeling in towards the far post)
        x1, y1 = ax + (bx - ax) * out, ay + (by - ay) * out
        tx, ty = self.zip_point(st, st["u"])
        tx, ty = tx - ox, ty - oy
        if phase in ("ride", "end"):   # pulled down into a V where the trolley is
            pts = [ax, ay, tx, ty, bx, by]
        else:   # hanging in a gentle curve
            droop = 0.012 * math.hypot(x1 - x0, y1 - y0)
            pts = [x0, y0, (x0 + x1) / 2, (y0 + y1) / 2 + 2 * droop, x1, y1]
        if out > back:
            w = max(1, round(1.5 * s))
            smooth = phase not in ("ride", "end")
            c.create_line(*[v + (w if i % 2 else 0) for i, v in enumerate(pts)], fill=ZIP_C[1], width=w,
                          smooth=smooth)   # (a dark edge, for light wallpapers)
            c.create_line(*pts, fill=ZIP_C[0], width=w, smooth=smooth)
        if phase in ("grab", "ride", "end"):   # the trolley: two wheels on the cable, straps down to a handlebar
            # the handlebar's in its raised hands, tilting with it (while it hops up, it's waiting up there)
            if phase == "grab":
                (x0, y0), (x1, y1) = [(tx + side * 7.5 * bw, ty + st["hang"] - ph - pb / 2) for side in (-1, 1)]
            else:
                (x0, y0), (x1, y1) = [(x - ox, y - oy) for x, y in
                                      (self.raised_hand(side, bh / 2 + pb / 2) for side in (-1, 1))]
            for x, y in ((x0, y0), (x1, y1)):
                c.create_line(tx, ty, x, y, fill=ZIP_C[1], width=max(1, round(s)))
            c.create_line(x0, y0, x1, y1, fill=ZIP_C[1], width=pb)
            c.create_rectangle(round(tx - 3 * pb), round(ty - 2 * pb), round(tx + 3 * pb), round(ty + pb),
                               fill=ZIP_C[3], outline="")
            for sx in (-2, 1):   # (the wheels)
                x = tx + sx * pb
                c.create_rectangle(round(x), round(ty - 3 * pb), round(x + pb), round(ty - 2 * pb), fill=ZIP_C[2],
                                   outline="")

    def draw_pole(self, c, st, ox, oy, s, pb, bw, bh, ph):
        xp, top, floor, edge = st["xp"] - ox, st["top"] - oy, st["floor"] - oy, st["edge"] - ox
        t, phase = st["t"], st["phase"]
        if phase == "set":
            k = ease(t / 0.35)
        elif phase == "pack":
            k = 1 - ease(t / 0.4)
        else:
            k = 1.0
        bottom = top + (floor - top) * k
        side = 1 if xp > edge else -1
        wall = edge - side * 4 * s   # a steel bracket from the window's corner out to the pole, with a brace under it
        c.create_line(wall, top + 9 * pb, xp - side * 2 * pb, top + 2 * pb, fill=POLE_C[6], width=pb)
        c.create_rectangle(round(min(wall, xp)), round(top), round(max(wall, xp)), round(top + 2 * pb),
                           fill=POLE_C[3], outline="")
        c.create_rectangle(round(min(wall, xp)), round(top + 1.5 * pb), round(max(wall, xp)), round(top + 2 * pb),
                           fill=POLE_C[6], outline="")
        c.create_rectangle(round(wall - pb), round(top - pb), round(wall + pb), round(top + 10 * pb), fill=POLE_C[3],
                           outline="")   # (the plate bolted to the window)
        if k <= 0:
            return
        cap = top - 7 * s
        self.pole_strip(c, xp, cap + 2 * pb, bottom, pb)
        c.create_rectangle(round(xp - 2.5 * pb), round(top - pb), round(xp + 2.5 * pb), round(top + 3 * pb),
                           fill=POLE_C[3], outline="")   # the collar where the bracket holds it
        c.create_rectangle(round(xp - 2.5 * pb), round(top + 2 * pb), round(xp + 2.5 * pb), round(top + 3 * pb),
                           fill=POLE_C[6], outline="")
        c.create_rectangle(round(xp - 2 * pb), round(cap), round(xp + 2 * pb), round(cap + 2 * pb), fill=POLE_C[0],
                           outline="")   # a round brass knob on top
        c.create_rectangle(round(xp - pb), round(cap - pb), round(xp + pb), round(cap), fill=POLE_C[1], outline="")
        if bottom >= floor - 1:   # at the bottom: a base, and a round red landing mat
            c.create_rectangle(round(xp - 9 * pb), round(floor - 2 * pb), round(xp + 9 * pb), round(floor),
                               fill=POLE_C[4], outline="")
            c.create_rectangle(round(xp - 8 * pb), round(floor - 2.5 * pb), round(xp + 8 * pb), round(floor - 1.5 * pb),
                               fill=POLE_C[5], outline="")
            c.create_rectangle(round(xp - 2.5 * pb), round(floor - 3.5 * pb), round(xp + 2.5 * pb),
                               round(floor - 2.5 * pb), fill=POLE_C[2], outline="")

    def pole_strip(self, c, x, y0, y1, pb):
        # (also used by render.py for the bit in front of the mascot) a round brass pole: a bright shine down the
        # left, the brass, and a shady right side
        if y1 <= y0:
            return
        l, r, q = round(x - 1.5 * pb), round(x + 1.5 * pb), max(1, pb // 2)
        c.create_rectangle(l, round(y0), r, round(y1), fill=POLE_C[0], outline="")
        c.create_rectangle(l + q, round(y0), l + 2 * q, round(y1), fill=POLE_C[1], outline="")
        c.create_rectangle(r - 2 * q, round(y0), r, round(y1), fill=POLE_C[2], outline="")

    def draw_web(self, c, st, ox, oy, s, pb, bw, bh, ph):
        w = max(2, round(2 * s))
        if st["anchor"] is not None:
            self.draw_first_web(c, st, ox, oy, s, pb, w)
        self.draw_ground_web(c, st, ox, oy, s, pb, w)

    def draw_first_web(self, c, st, ox, oy, s, pb, w):
        ax, ay = st["anchor"]
        ax, ay = ax - ox, ay - oy
        for i in range(6):   # the splat of web stuck to the ceiling
            a = i / 6 * 2 * math.pi
            c.create_line(ax, ay, ax + math.cos(a) * 5 * pb, ay + math.sin(a) * 3 * pb, fill=WEB_C[1],
                          width=max(1, round(s)))
        if st["phase"] in ("fall", "swing"):
            hx, hy = self.raised_hand(self.dir)
            hx, hy = hx - ox, hy - oy
            k = st["shot"]
            ex, ey = hx + (ax - hx) * k, hy + (ay - hy) * k
            c.create_line(hx, hy, ex, ey, fill=WEB_C[1], width=w + max(1, round(s)))
            c.create_line(hx, hy, ex, ey, fill=WEB_C[0], width=max(1, round(s)))
        else:   # let go: the strand hangs from the ceiling, swaying, and fades (shorter and shorter)
            k = max(0.0, 1 - st["t"] / 1.0) if st["phase"] == "gone" else 1.0
            length = st["rope"] * 0.5 * k
            sway = math.sin(st["t"] * 5) * 0.3
            ex, ey = ax + math.sin(sway) * length, ay + math.cos(sway) * length
            if length > 2:
                c.create_line(ax, ay, ex, ey, fill=WEB_C[1], width=w)

    def draw_ground_web(self, c, st, ox, oy, s, pb, w):
        if st["ground"] is not None:   # the second web, from its hand down to the ground
            gx, gy = st["ground"]
            gx, gy = gx - ox, gy - oy
            if st["shot2"] >= 1:   # its splat on the ground, fanning out
                k = max(0.0, 1 - st["t"] / 1.0) if st["phase"] == "gone" else 1.0
                for i in range(5):
                    a = math.pi * (1.1 + 0.2 * i)
                    c.create_line(gx, gy, gx + math.cos(a) * 5 * pb * k, gy + math.sin(a) * 3 * pb * k,
                                  fill=WEB_C[1], width=max(1, round(s)))
            if st["phase"] in ("zip", "pull"):
                hx, hy = self.low_hand()
                hx, hy = hx - ox, hy - oy
                k = st["shot2"]
                ex, ey = hx + (gx - hx) * k, hy + (gy - hy) * k
                c.create_line(hx, hy, ex, ey, fill=WEB_C[1], width=w + max(1, round(s)))
                c.create_line(hx, hy, ex, ey, fill=WEB_C[0], width=max(1, round(s)))
