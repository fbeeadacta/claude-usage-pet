# part of the Pet: walking, jumping, physics, standing on windows.
import datetime
import math
import os
import random
import time

from .config import (CHUTE_HEIGHT, CHUTE_SPEED, DANCE_CHANCE, DIVE_MIN, FPS, GRAVITY, GROUND_FRICTION,
    HAY_TIME, HOP_HEIGHT, LEAP_POWER, LEAP_REACH, MAX_STEP_UP, NAP_CHANCE, TASKBAR_PUSH, THROW_DRAG,
    WALK_SPEED)
from .lines import (CHUTE_LINES, DANCE_LINES, DIVE_LINES, DIZZY_LINES, FALL_LINES, HAY_LINES, LEAP_FAIL,
    LEAP_OK, LEAP_TRY, SLAP_LINES, SQUISH_LINES, UFO_BACK_LINES)
from .winapi import list_platforms, own_usage, u32, window_box, winmm


class MovementMixin:
    # movement
    def walking_allowed(self):
        return self.walk.get() and not self.details.visible and not self.hidden and not self.full()

    def floor(self):
        # the taskbar (or screen bottom), or the top of the window it's standing on
        return self.plat_box[2] if self.plat is not None else self.screens[self.si].wb

    def grounded(self):
        return self.vy >= 0 and self.y >= self.floor() - 0.5

    def update_platforms(self):
        # refreshes the list of windows. if it's standing on one, it rides along when the window moves,
        # and falls when the window closes, minimizes, maximizes or slides out from under it.
        self.plats, self.plats_at = list_platforms(), time.time()
        if self.plat is None and not TASKBAR_PUSH:
            self.near = []
            return
        if self.plat is None:
            # on the taskbar: the windows that reach down near it, which can push it about
            sc, reach = self.screens[self.si], self.half + 400 * self.s()
            # a window that goes down behind the taskbar is behind its floor, so it stands in front of it.
            # one that ends on or above the taskbar is in its way.
            self.near = [w[0] for w in self.plats if w[1] < self.x + reach and w[3] > self.x - reach
                         and sc.wb - self.pet_px[1] - 40 < w[4] <= sc.wb + 2 and w[2] < sc.wb]
            return
        self.near = []
        box = next((w for w in self.plats if w[0] == self.plat), None)
        if self.held:
            self.plat = None
            return
        if box is None or u32.IsZoomed(self.plat):
            self.drop_off()
            return
        dx, dy = box[1] - self.plat_box[1], box[2] - self.plat_box[2]
        self.plat_box = box
        if self.grounded() or abs(self.y - box[2] + dy) < 1:
            self.x, self.y = self.x + dx, box[2]
        if not box[1] <= self.x <= box[3]:
            self.plat = None

    def drop_off(self, through=False):
        # off its window. `through` = squeezed out with nowhere to go: falls past every ledge to the taskbar
        self.plat, self.through = None, through
        self.y = min(self.y, self.screens[self.si].wb)

    def x_limits(self):
        # how far left and right it may go: this screen, plus a screen right next to it if it may cross
        sc = self.screens[self.si]
        l, r = self.neighbour(-1), self.neighbour(1)
        return ((self.screens[l].wl if l is not None else sc.wl) + self.half,
                (self.screens[r].wr if r is not None else sc.wr) - self.half)

    def ride(self, s, dt):
        # every frame while it's on a window: follows that window smoothly when you drag it, and gets
        # shoved aside by windows in front of it (the window list itself only refreshes 5 times a second)
        hwnd = self.plat
        ok = u32.IsWindowVisible(hwnd) and not u32.IsIconic(hwnd) and not u32.IsZoomed(hwnd)
        box = window_box(hwnd) if ok else None
        if box is None:
            self.drop_off()
            return
        box = (hwnd,) + box
        if box != self.plat_box:
            on = self.grounded()
            self.x += box[1] - self.plat_box[1]
            self.plat_box, self.ride_until = box, time.perf_counter() + 0.4
            if on:
                self.y = box[2]
        lo, hi = self.x_limits()
        self.x = min(max(self.x, lo), hi)   # the screen edges are hard walls, even if the window goes past them
        i = self.find_screen(self.x, self.y - 1)
        if i is not None:
            self.si = i
        sc = self.screens[self.si]
        if box[2] < sc.mt + self.pet_px[1] or box[2] > sc.wb:
            self.drop_off()   # dragged too high to fit under the top of the screen, or down past the taskbar
        elif not box[1] <= self.x <= box[3]:
            self.plat = None   # the window slid out from under it (or it got pinned at the screen edge)
        else:
            self.push_out(s, dt)

    def push_floor(self, s, dt):
        # on the taskbar, windows that come down to the floor push it aside as well
        front = [b for b in (window_box(h) for h in self.near) if b]
        if front:
            self.push_out(s, dt, front)

    def push_out(self, s, dt, front=None):
        # windows in front of the one it stands on are solid: it scoots out the nearer side. pushed past
        # the edge of its window, it falls off. cornered (screen edge or more windows), it drops to the taskbar.
        # on the taskbar (`front` = the windows near it) there's nowhere lower, so cornered there it stays put.
        on_window = front is None
        if on_window:
            front = []
            for w in self.plats:   # front to back, so everything before its own window is in front of it
                if w[0] == self.plat:
                    break
                box = window_box(w[0])   # fresh, so a window sliding over pushes smoothly
                if box:
                    front.append(box)
            else:
                return   # its window isn't in the list yet
        pw, ph = self.pet_px
        half, top, bottom = pw / 2, self.y - ph, self.y

        def hits(x):
            return [o for o in front if o[0] < x + half - 1 and o[2] > x - half + 1
                    and o[1] < bottom - 1 and o[3] > top + 1]

        h = hits(self.x)
        if not h:
            return
        lo, hi = self.x_limits()
        # out the side it's nearer to, never through the window to the far side
        side = -1 if self.x < (min(o[0] for o in h) + max(o[2] for o in h)) / 2 else 1
        target = self.x
        for _ in range(12):
            h = hits(target)
            if not h:
                break
            target = min(o[0] for o in h) - half - 1 if side < 0 else max(o[2] for o in h) + half + 1
        if hits(target) or not lo <= target <= hi:
            if not on_window:
                return   # boxed in on the taskbar (a maximized window, say): it just carries on
            self.drop_off(through=True)   # cornered: nowhere to go but down
            self.vy = max(self.vy, 0.0)
            if random.random() < 0.5:
                self.say(self.pick(SQUISH_LINES))
            return
        self.x += side * min(abs(target - self.x), 2000 * s * dt)   # a quick scoot, not a teleport
        self.dir = side
        self.ride_until = time.perf_counter() + 0.4   # smooth frames while it's being shoved
        if on_window and not self.plat_box[1] <= self.x <= self.plat_box[3]:
            self.plat = None   # shoved off the edge of its window

    def drop_left(self):
        # how far it still has to fall: to the next window top below it, or the taskbar
        floor = self.floor()
        if self.platforms.get() and self.plat is None and self.plats and not self.through:
            ledge = self.platform_under(self.y, floor)
            if ledge:
                floor = ledge[2]
        return floor - self.y

    def platform_under(self, y0, y1, x=None):
        # the first window top it passes while falling from y0 to y1, if its middle (or x) is over that
        # window and nothing in front of the window is covering that spot
        s = self.s()
        x = self.x if x is None else x
        for i, w in enumerate(self.plats):
            _, left, top, right, _ = w
            if not (y0 - 1 <= top <= y1 + 1 and left + 12 * s <= x <= right - 12 * s):
                continue
            sc = self.screens[self.si]
            if top < sc.mt + self.pet_px[1] or top > sc.wb - 30 * s:
                continue
            if any(o[1] <= x < o[3] and o[2] <= top - 2 < o[4] for o in self.plats[:i]):
                continue
            return w
        return None

    def jump_now(self, height):
        # crouch for a moment, then jump high enough to rise `height` pixels
        if not self.anim.get():
            return
        self.squash_t, self.leap_plan = 0.08, None
        self.pending_v = math.sqrt(2 * GRAVITY * self.s() * height)

    def try_leap(self, prefer=0):
        # looks for another window nearby and goes for it. it's confident. it's not always right.
        # prefer = -1 / 1: rather a window that way (it's at the edge of one, walking that way)
        if not self.anim.get():
            return False
        s = self.s()
        self.update_platforms()
        sc = self.screens[self.si]
        here = self.floor()
        lo, hi = self.x_limits()
        options = []
        for i, w in enumerate(self.plats):
            hwnd, left, top, right, _ = w
            if hwnd == self.plat:
                continue
            a, b = max(left + 30 * s, lo), min(right - 30 * s, hi)
            if a > b:
                continue
            tx = min(max(self.x, a), b)
            if tx in (a, b) and b - a > 80 * s:   # aim a little way in from the edge
                tx += 40 * s if tx == a else -40 * s
            dx, rise = tx - self.x, here - top
            if abs(dx) > LEAP_REACH * s or not -LEAP_POWER * s < rise < LEAP_POWER * 1.4 * s:
                continue   # too far, or way too high even for its ego
            if abs(rise) < 25 * s and abs(dx) < 60 * s:
                continue   # that's basically where it already is
            if top < sc.mt + self.pet_px[1] + 20 * s or top > sc.wb - 40 * s:
                continue
            if any(o[1] <= tx < o[3] and o[2] <= top - 2 < o[4] for o in self.plats[:i]):
                continue   # that spot is under another window
            options.append((hwnd, top, dx, rise, left, right))
        if prefer:
            options = [o for o in options if o[2] * prefer > 0] or options
        if not options:
            return False
        hwnd, top, dx, rise, left, right = random.choice(options)
        g = GRAVITY * s
        apex = max(rise, 0) + random.uniform(30, 70) * s           # how high it means to go
        apex = min(apex, LEAP_POWER * s * random.uniform(0.9, 1.1))  # how high its legs actually go
        vy0 = math.sqrt(2 * g * apex)
        fall = apex - rise   # from the top of the jump down to the window's top (negative: falls short)
        t = vy0 / g + (math.sqrt(2 * fall / g) if fall > 0 else 0)
        vx = dx / max(t, 0.15)
        # starting off to the side of a higher window: don't reach its side before its feet are above the top,
        # or it hits the wall. (if that would make it land short of the window anyway, it just goes for it.)
        half = self.pet_px[0] / 2
        to_side = (left - self.x if dx > 0 else self.x - right) - half
        if rise > 0 and to_side > 0 and vx and vy0 * vy0 > 2 * g * rise:
            t_up = (vy0 - math.sqrt(vy0 * vy0 - 2 * g * rise)) / g   # when its feet pass the top
            slower = to_side / t_up
            if to_side / abs(vx) < t_up and slower * t > to_side + half + 20 * s:
                vx = math.copysign(slower, vx)
        aim = random.uniform(0.85, 1.2) if random.random() > 0.15 else random.choice((0.55, 1.6))
        vx *= aim   # eyeballed. now and then it really misjudges it.
        if dx:
            self.dir = 1 if dx > 0 else -1
        self.state, self.state_t = "idle", 2.0
        self.leap_plan = (hwnd, vx)
        self.squash_t, self.pending_v = 0.14, vy0   # a big crouch first
        self.tally("leaps")
        if random.random() < 0.6:
            self.say(self.pick(LEAP_TRY), force=True)
        return True

    def leap_wall(self, x_before, s):
        # a jump that comes up short slaps into the side of the window, like a wall, and slides down it
        box = window_box(self.leaping)
        if not box:
            return
        left, top, right, bottom = box
        half = self.pet_px[0] / 2
        if self.y <= top + 1 or self.y - self.pet_px[1] >= bottom:
            return   # its feet are above the top (it can land there), or it's below the window
        if x_before + half <= left < self.x + half:
            self.x, side = left - half, -1
        elif x_before - half >= right > self.x - half:
            self.x, side = right + half, 1
        else:
            return   # it was already in front of the window, not beside it
        self.vx = side * min(abs(self.vx) * 0.25, 120 * s)   # bounces back a little
        self.spin += side * 5
        self.leaping, self.slapped = None, True   # (no parachute: it slides down the wall)
        self.dizzy_t = max(self.dizzy_t, 1.2)
        self.play("splat")
        self.tally("splats")
        if random.random() < 0.8:
            self.say(self.pick(SLAP_LINES), force=True)

    def start_dive(self):
        # the leap of faith: off the edge of its window in a swan dive, into a pile of hay at the bottom
        if not self.anim.get() or self.plat is None:
            return False
        s = self.s()
        sc = self.screens[self.si]
        x = (self.plat_box[3] if self.dir > 0 else self.plat_box[1]) + self.dir * 60 * s
        lo, hi = self.x_limits()
        if not lo <= x <= hi:
            return False   # the screen edge is right there
        below = self.platform_under(self.y + 2, sc.wb, x)
        if (below[2] if below else sc.wb) - self.y < DIVE_MIN * s:
            return False   # not much of a drop. it'll just walk off.
        self.plat, self.through, self.diving = None, False, True
        self.vy, self.vx = -math.sqrt(2 * GRAVITY * s * 45 * s), self.dir * 160 * s   # a little spring off the edge
        self.state, self.state_t = "idle", 2.0
        self.play("eagle")
        self.tally("dives")
        if random.random() < 0.75:
            self.say(self.pick(DIVE_LINES), force=True)
        return True

    def move_x(self, dx):
        # sideways. crosses onto the next screen when it may, otherwise turns around.
        if dx == 0:
            return
        side = 1 if dx > 0 else -1
        sc = self.screens[self.si]
        nx = self.x + dx
        limit = sc.wr - self.half if side > 0 else sc.wl + self.half
        if (nx - limit) * side <= 0:
            self.x = nx
            return
        nb = self.neighbour(side)
        if nb is None:
            self.x, self.dir = limit, -side
            return
        edge = sc.mr if side > 0 else sc.ml
        if (nx - edge) * side < 0:   # half way over, not across yet
            self.x = nx
            return
        nsc = self.screens[nb]
        if self.y <= nsc.wb + 0.5:   # its floor is level or lower: walk (or drop) onto it
            self.x, self.si = nx, nb
            return
        self.x = edge - side         # its floor is higher: jump up onto it, or give up
        if self.grounded() and self.squash_t <= 0:
            rise = self.y - nsc.wb
            if rise <= MAX_STEP_UP * self.s():
                self.jump_now(rise + 12 * self.s())
            else:
                self.dir = -side

    def start_anim(self):
        if self.anim_job is None:
            self.last_t = time.perf_counter()
            self.anim_tick()

    def perf_tick(self):
        # every 2 seconds: how much cpu and memory this program uses, and how many frames it drew
        now, (cpu, mem) = time.perf_counter(), own_usage()
        t0, cpu0, f0 = self.perf_prev
        span = max(0.001, now - t0)
        self.perf = {"cpu": 100 * (cpu - cpu0) / span / (os.cpu_count() or 1), "mem": mem,
                     "fps": (self.frames - f0) / span, "cpu_core": 100 * (cpu - cpu0) / span}
        self.perf_prev = (now, cpu, self.frames)
        self.perf_hist.append((self.perf["cpu"], mem, self.perf["fps"]))
        if self.settings.win is not None and self.settings.tab == "about" and not self.settings.query and not self.settings.drag:
            self.settings.draw()
        self.root.after(2000, self.perf_tick)

    def anim_tick(self):
        self.frames += 1
        now = time.perf_counter()
        dt, self.last_t = min(0.05, now - self.last_t), now
        self.physics(dt)
        self.redraw()
        ms = self.frame_ms()
        fast = ms <= 16
        if fast != self.fine_timer:
            # windows' clock normally ticks every 15.6 ms, so "wait 16 ms" sometimes became 31 ms and
            # throws looked jittery. while it's moving, ask for a 1 ms clock; give it back when it stops.
            try:
                (winmm.timeBeginPeriod if fast else winmm.timeEndPeriod)(1)
                self.fine_timer = fast
            except (AttributeError, OSError):
                pass
        if fast:   # a steady 60 frames a second: aim each frame at the next 1/60 s mark
            self.next_frame = max(self.next_frame + 1 / FPS, now)
            ms = max(1, round((self.next_frame - time.perf_counter()) * 1000))
        else:
            self.next_frame = now
        self.anim_job = self.root.after(ms, self.anim_tick)

    def frame_ms(self):
        # fast while moving, slower while standing around, very slow while hidden
        if self.hidden:
            return 500
        if (self.held or self.pressed or self.squash_t > 0 or not self.grounded() or self.angle or self.vx
                or (self.state == "walk" and self.walking_allowed()) or self.goto_x is not None or self.ufo
                or (self.ball and self.ball["phase"] in ("fly", "pet")) or (self.plane and not self.plane["landed"])
                or (self.plat is not None and time.perf_counter() < self.ride_until)):
            return 16
        if (self.plat is not None or self.near or self.hay_t > 0 or self.parts or self.cat or self.wave_t > 0 or self.state in ("work", "dance", "act") or self.speech
                or self.dizzy_t > 0 or self.stretch_t > 0):
            return 30
        return 80

    def physics(self, dt):
        s = self.s()
        self.clock += dt
        for name in ("happy_t", "wave_t", "look_t", "dizzy_t", "stretch_t", "worried_t"):
            setattr(self, name, getattr(self, name) - dt)
        if self.state != "sleep":
            self.next_blink -= dt
            if self.next_blink <= 0:
                self.blink_t, self.next_blink = 0.15, random.uniform(2.5, 6)
            self.blink_t -= dt
        for p in self.parts:
            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += p.get("g", 0.0) * dt   # (some fall, like paint and splashes)
        self.parts = [p for p in self.parts if p["life"] > 0]
        self.turn(dt, s)
        self.ball_tick(dt)
        self.plane_tick(dt)
        self.cat_tick(dt)
        if self.ufo and self.ufo_tick(dt):
            return   # beamed up
        if self.held or self.hidden or self.pressed:
            return
        if self.plat is not None:
            self.ride(s, dt)
        elif self.near and self.grounded() and self.leaping is None and not self.diving:
            self.push_floor(s, dt)
        if self.squash_t > 0:   # crouching or squished: hold still for a moment
            self.squash_t -= dt
            if self.squash_t <= 0 and self.pending_v:
                self.vy, self.pending_v = -self.pending_v, 0.0
                if self.leap_plan:   # off it goes, towards the other window
                    self.leaping, self.vx = self.leap_plan
                    self.leap_plan, self.plat, self.through = None, None, False
            return
        if self.hay_t > 0:   # sitting in the hay pile for a moment, then out it pops
            self.hay_t -= dt
            if self.hay_t <= 0:
                for _ in range(8):
                    self.spawn("straw")
                self.jump_now(HOP_HEIGHT * 1.2 * s)
            return
        walking = self.state == "walk" and self.walking_allowed()
        sc = self.screens[self.si]
        if not self.grounded():   # in the air
            g = GRAVITY * s
            y_before, x_before = self.y, self.x
            if (not self.chute and self.vy > 150 * s and self.drop_left() > CHUTE_HEIGHT * s
                    and abs(self.angle) < 0.4 and self.leaping is None and not self.diving and not self.slapped):   # a failed jump just plops
                self.chute = True   # a long way down: open the parachute
                self.play("whoosh")
                self.tally("chutes")
                if random.random() < 0.6:
                    self.say(self.pick(CHUTE_LINES), force=True)
            if self.chute:
                self.vy = min(self.vy + g * dt, CHUTE_SPEED * s)
                self.y += self.vy * dt
                self.vx *= max(0.0, 1 - 2.5 * dt)
                self.x += math.sin(self.clock * 1.6) * 14 * s * dt   # drifting in the breeze
            else:   # a proper curve, the same whatever the frame rate
                self.y += self.vy * dt + 0.5 * g * dt * dt
                self.vy += g * dt
                if self.leaping is None and not self.diving:   # a jump keeps its aim; a throw slows down
                    self.vx *= max(0.0, 1 - THROW_DRAG * dt)
            if self.y - self.pet_px[1] < sc.mt:   # bonk on the top of the screen
                self.y, self.vy = sc.mt + self.pet_px[1], abs(self.vy) * 0.3
            if abs(self.vx) > 1:
                self.slide(dt)
            elif walking:
                self.move_x(self.dir * WALK_SPEED * self.prof()["speed"] * s * dt)
            if self.leaping is not None:
                self.leap_wall(x_before, s)
            if self.platforms.get() and self.plat is None and self.vy > 0 and self.plats and not self.through:
                hit = self.platform_under(y_before, self.y)
                if hit:
                    self.plat, self.plat_box = hit[0], hit
            if self.y >= self.floor():
                self.land(s)
            return
        if abs(self.vx) > 5 * s:   # still sliding after a throw
            self.slide(dt)
            if self.plat is not None and not self.plat_box[1] <= self.x <= self.plat_box[3]:
                self.plat = None   # slid off the window
            self.vx -= math.copysign(min(abs(self.vx), GROUND_FRICTION * s * dt), self.vx)
            return
        self.vx = 0.0
        if self.goto_x is not None and self.chase(dt, s):
            return   # called over, or after the ball
        if self.shiny and random.random() < dt / 3:
            self.spawn("glint")
        if self.state == "sleep":
            if self.sleep_reason == "nap":
                self.state_t -= dt
                if self.state_t <= 0:
                    self.wake()
            self.part_t -= dt
            if self.part_t <= 0:
                self.spawn("z")
                self.part_t = 1.2
            return
        if self.celebrate:
            self.celebrate -= 1
            self.happy_t = 1.2
            self.spawn("heart")
            self.jump_now(HOP_HEIGHT * 1.3 * s)
            return
        casting = self.wizard.get() and time.time() < self.working_until
        if casting and self.state in ("idle", "walk", "dance", "act"):
            self.state, self.cast_t, self.next_spell = "work", 0.0, 0.0
        if self.state == "work":
            if not casting:
                self.state, self.state_t = "idle", 2.0
            else:   # stand still, wave the wand (or read the spell tome), make sparkles
                job = self.job()
                if self.cast_t >= self.next_spell:   # and a bit of magic now and then
                    self.play("spell")
                    self.next_spell = self.cast_t + random.uniform(12, 25)
                self.cast_t += dt
                self.tally("wizard_s", dt)
                self.part_t -= dt
                if self.part_t <= 0:   # each job has its own sparkles (pet/magic.py)
                    if job:
                        self.part_t = self.job_spawn(job)
                    else:
                        self.spawn("spark")
                        self.part_t = random.uniform(0.08, 0.2)
                return
        if self.state == "act":   # sweeping, painting, fishing, balloons, a paper plane (pet/idle.py)
            self.act_tick(dt, s)
            return
        if self.state == "dance":
            self.dance_t += dt
            self.state_t -= dt
            self.part_t -= dt
            if self.part_t <= 0:
                self.spawn("note")
                self.part_t = 0.45
            if self.state_t <= 0:
                self.state, self.state_t = "idle", 2.0
            return
        self.state_t -= dt
        if walking and self.plat is not None:
            # on a window: at its edge, either turn around or walk off and fall
            _, left, _, right, _ = self.plat_box
            near = self.x + self.dir * 10 * s
            if left <= near <= right:
                self.edge_turn = None
            else:
                if self.edge_turn is None:   # just got to the edge: another window? a leap of faith? or not
                    pr = self.prof()
                    if self.jump.get() and random.random() < pr["edge_leap"] and self.try_leap(prefer=self.dir):
                        return
                    if self.jump.get() and random.random() < pr["dive"] and self.start_dive():
                        return
                    self.edge_turn = random.random() < pr["turn"]
                if self.edge_turn:
                    self.dir, self.edge_turn = -self.dir, None
        if walking:
            night = not 6 <= datetime.datetime.now().hour < 23
            x0 = self.x
            self.move_x(self.dir * WALK_SPEED * self.prof()["speed"] * (0.7 if night else 1) * s * dt)
            self.tally("walked", abs(self.x - x0) / self.screens[self.si].dpi)
            if self.plat is not None and not self.plat_box[1] <= self.x <= self.plat_box[3]:
                self.plat = None   # walked off the edge
                if random.random() < 0.5:
                    self.say(self.pick(FALL_LINES))
            self.step_t += dt
            if self.step_t >= 0.18:
                self.step_t, self.step = 0.0, self.step + 1
        if (self.jump.get() and self.walk.get() and self.platforms.get() and not self.full()
                and not self.details.visible and random.random() < dt / self.prof()["leap"] and self.try_leap()):
            return
        if self.jump.get() and not self.full() and random.random() < dt / self.prof()["hop"]:
            self.jump_now(HOP_HEIGHT * s)
            self.tally("hops")
        if self.state_t <= 0:
            pr = self.prof()
            if random.random() < DANCE_CHANCE and not self.full():
                self.start_dance()
            elif self.state != "walk" and self.maybe_act():
                pass
            elif self.state == "walk" and self.walking_allowed() and random.random() < pr["keep"]:
                self.state_t = random.uniform(*pr["walk_t"])   # keeps going, maybe the other way
                if random.random() < 0.3:
                    self.dir = -self.dir
            elif self.state == "walk" or not self.walking_allowed():
                night = not 6 <= datetime.datetime.now().hour < 23
                if (self.naps.get() and random.random() < NAP_CHANCE * pr["nap"] * (3 if night else 1)
                        and not self.details.visible):
                    self.fall_asleep("nap")
                else:
                    self.state, self.state_t = "idle", random.uniform(*pr["idle"])
            else:
                self.state, self.state_t = "walk", random.uniform(*pr["walk_t"])
                self.dir = random.choice((-1, 1))
        if self.state == "idle" and self.look_t <= 0 and random.random() < dt / 4:
            self.look_d, self.look_t = random.choice((-1, 1)), random.uniform(0.6, 1.4)

    def start_dance(self):
        if self.anim.get():
            self.state, self.state_t, self.dance_t, self.part_t = "dance", random.uniform(8, 12), 0.0, 0.2
            self.play("dance", loop=True)
            self.tally("dances")
            if random.random() < 0.4:
                self.say(self.pick(DANCE_LINES))

    def turn(self, dt, s):
        # tilting: hangs from where you grabbed it and swings as you move, then rights itself
        if self.held:
            self.drag_vx *= max(0.0, 1 - 5 * dt)
            target, k, damp = self.hang + max(-0.7, min(0.7, -self.drag_vx * 0.0011 / s)), 40, 6
        elif self.diving:
            target, k, damp = self.dir * 2.3, 16, 5   # tips over head first: a swan dive
        elif self.angle or self.spin:
            target, k, damp = 0.0, 22, 5
        else:
            return
        self.spin += ((target - self.angle) * k - self.spin * damp) * dt
        self.angle += self.spin * dt
        if self.held:
            self.follow_grip()
        elif abs(self.angle) < 0.02 and abs(self.spin) < 0.2:
            self.angle = self.spin = 0.0

    def slide(self, dt):
        # moves sideways with the throw speed. bounces off the screen edge.
        want = self.x + self.vx * dt
        self.move_x(self.vx * dt)
        if abs(self.x - want) > 1:
            self.vx = -self.vx * 0.5

    def land(self, s):
        impact = self.vy
        self.y = self.floor()
        self.through = self.slapped = False
        if self.dropping_in:   # parachuted in after being called: hello!
            self.dropping_in, self.wave_t = False, 1.4
        if self.ufo_fall:      # back from the ufo
            self.ufo_fall, self.dizzy_t = False, 2.0
            self.say(self.pick(UFO_BACK_LINES), force=True)
        if self.diving:   # the leap of faith ends in a pile of hay. no bounce, no dizziness.
            self.diving, self.chute = False, False
            self.vx = self.vy = self.angle = self.spin = 0.0
            self.hay_t, self.bounces = HAY_TIME, 0
            for _ in range(10):
                self.spawn("straw")
            self.play("hay")
            if random.random() < 0.7:
                self.say(self.pick(HAY_LINES), force=True)
            return
        if self.leaping is not None:   # how did that jump go?
            made_it = self.plat == self.leaping
            self.leaping = None
            self.tally("leaps_made" if made_it else "leaps_missed")
            if made_it:
                self.happy_t = 1.0
            if random.random() < 0.75:
                self.say(random.choice(LEAP_OK if made_it else LEAP_FAIL), force=True)
            self.vx = 0.0
        if self.chute:
            self.chute, self.vy, self.squash_t = False, 0.0, 0.07
            return
        if impact > 700 * s and self.bounces < 1:
            self.bounces += 1
            self.play("boing")
            self.vy = -impact * 0.35   # boing
        else:
            self.vy = 0.0
            if impact > 350 * s:
                self.squash_t = 0.07   # landing squish
        if impact > 1100 * s and self.dizzy_t <= 0:
            self.dizzy_t = 2.4   # that was a hard landing: seeing stars
            self.tally("dizzy")
            if random.random() < 0.7:
                self.say(self.pick(DIZZY_LINES), force=True)
        self.vx *= 0.6
