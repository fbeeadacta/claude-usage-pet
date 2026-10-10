# part of the Pet: hovering, poking, dragging and throwing.
import math
import random
import time

from .art import PARK
from .config import HOVER_DELAY, THROW_KEEP, THROW_MAX, THROW_MIN
from .lines import DRAG_LINES, THROW_LINES


class MouseMixin:
    # mouse
    def press(self, e):
        self.moved, self.pressed = False, True
        self.press_at = (e.x_root, e.y_root)
        self.trail = [(time.perf_counter(), e.x_root, e.y_root)]
        # where on its body you grabbed it, in body pixels (it will hang from that spot)
        pw, ph = self.pet_px
        gx = e.x_root - (self.geo[2] if self.geo else 0) - self.body_at[0]
        gy = e.y_root - (self.geo[3] if self.geo else 0) - self.body_at[1]
        self.grab_local = (min(max(gx, 0), pw), min(max(gy, 0), ph))
        self.redraw()

    def motion(self, e):
        now = time.perf_counter()
        self.trail = [t for t in self.trail if now - t[0] < 0.1] + [(now, e.x_root, e.y_root)]
        if not self.moved and abs(e.x_root - self.press_at[0]) + abs(e.y_root - self.press_at[1]) > 4:
            self.moved, self.held, self.pressed = True, True, False
            self.vx = self.vy = self.squash_t = self.pending_v = 0.0
            self.leap_plan = self.leaping = None
            self.diving, self.hay_t = False, 0.0
            self.chute, self.bounces, self.last_touch = False, 0, time.time()
            if self.state in ("dance", "act"):
                self.state, self.act = "idle", None
            self.wake(hop=False)
            self.details.hide()
            self.stop_fetch()
            self.goto_x = self.goto_why = None
            self.dropping_in = False
            if self.ufo:
                self.ufo["dropped"] = True   # snatched back from the ufo, which flies off
            self.tally("pickups")
            self.hang = self.hang_angle() if self.anim.get() else 0.0
            if random.random() < 0.5:
                self.say(self.pick(DRAG_LINES), force=True)
        if self.held:
            first, last = self.trail[0], self.trail[-1]
            if last[0] - first[0] > 0.01:
                self.drag_vx = (last[1] - first[1]) / (last[0] - first[0])
            self.grip = (e.x_root, e.y_root)
            self.follow_grip()
            self.redraw()

    def hang_angle(self):
        # how far it tips so its middle hangs straight below the spot you grabbed
        pw, ph = self.pet_px
        vx, vy = pw / 2 - self.grab_local[0], ph / 2 - self.grab_local[1]
        if math.hypot(vx, vy) < 0.12 * pw:
            return 0.0   # grabbed near the middle: it just dangles upright
        return (math.pi / 2 - math.atan2(vy, vx) + math.pi) % (2 * math.pi) - math.pi

    def follow_grip(self):
        # works out where its body is from your grip and its tilt
        pw, ph = self.pet_px
        dx, dy = pw / 2 - self.grab_local[0], ph / 2 - self.grab_local[1]
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        self.x = self.grip[0] + dx * ca - dy * sa
        self.y = self.grip[1] + dx * sa + dy * ca + ph / 2

    def release(self, e):
        self.pressed = False
        if self.held:
            self.held = False
            s = self.s()
            now = time.perf_counter()
            trail = [t for t in self.trail if now - t[0] < 0.12]
            vx = vy = 0.0
            if len(trail) >= 2 and trail[-1][0] - trail[0][0] > 0.02:
                d = trail[-1][0] - trail[0][0]
                vx, vy = (trail[-1][1] - trail[0][1]) / d, (trail[-1][2] - trail[0][2]) / d
            speed = math.hypot(vx, vy)
            if speed < THROW_MIN * s:
                vx = vy = 0.0   # a small flick just drops it
            else:   # it's heavy: it keeps only part of your mouse speed, up to a limit
                k = min(THROW_KEEP * speed, THROW_MAX * s) / speed
                vx, vy = vx * k, vy * k
                self.tally("throws")
            self.follow_grip()
            self.angle = (self.angle + math.pi) % (2 * math.pi) - math.pi   # rights itself the short way
            self.plat, self.through, self.leaping, self.diving = None, False, None, False
            i = self.floor_below(self.x, self.y)
            self.si = i if i is not None else self.nearest_screen(self.x, self.y)
            sc = self.screens[self.si]
            self.x = min(max(self.x, sc.wl + self.half), sc.wr - self.half)
            self.y = min(self.y, sc.wb)
            if self.anim.get():   # it keeps the speed you threw it with
                self.vx, self.vy, self.bounces = vx, vy, 0
                self.spin += vx * 0.003 / s
                if math.hypot(vx, vy) > 650 * s:
                    self.play("scream")
                    self.say(self.pick(THROW_LINES), force=True)
            else:
                self.y, self.angle, self.spin = sc.wb, 0.0, 0.0
            self.state, self.state_t = "idle", 2.0
            self.save()
        elif not self.moved:
            self.poke()
        self.trail = []
        self.redraw()

    def check_hover(self, now):
        mx, my = self.root.winfo_pointerxy()
        self.mouse = (mx, my)   # (its eyes follow it)
        over_pet = False
        if not self.hidden and self.geo and self.geo[2] != PARK:
            ox, oy = self.geo[2], self.geo[3]
            for r in (self.rects.get("pet"), self.rects.get("bubble")):
                if r and ox + r[0] <= mx < ox + r[2] and oy + r[1] <= my < oy + r[3]:
                    over_pet = True
        d = self.details
        over_panel = d.visible and d.rect is not None and d.rect[0] <= mx < d.rect[2] and d.rect[1] <= my < d.rect[3]
        was = self.hovering
        self.hovering = over_pet or over_panel
        if was and not self.hovering:
            self.hover_until = now + 1.5   # keeps a hover-only bubble up a moment longer
        if over_pet and not self.held and not self.pressed:
            if self.hover_since is None:
                self.hover_since = now
                self.greet()
            elif not d.visible and now - self.hover_since >= HOVER_DELAY and not self.popup.visible:
                d.show()   # (not while the right-click menu is open)
        elif not over_pet:
            self.hover_since = None
        if d.visible and not d.pinned:
            if self.hovering:
                self.leave_at = None
            elif self.leave_at is None:
                self.leave_at = now
            elif now - self.leave_at >= 0.35:
                d.hide()
                self.leave_at = None
