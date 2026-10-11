# part of the Pet: which monitor it's on, the work areas, hiding.
import time

from .art import PARK
from .winapi import Screen, autohide_floors, list_screens, taskbar_autohides, taskbar_boxes


class ScreensMixin:
    # screens
    def get_screens(self):
        try:
            found = list_screens()
        except OSError:
            found = []
        if not found:
            w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            found = [Screen(0, 0, w, h, 0, 0, w, h - 48)]
        self.raw_screens, self.autohide = found, taskbar_autohides()
        return autohide_floors(found, taskbar_boxes()) if self.autohide else found

    def find_screen(self, x, y):
        for i, sc in enumerate(self.screens):
            if sc.ml <= x < sc.mr and sc.mt <= y < sc.mb:
                return i
        return None

    def nearest_screen(self, x, y):
        def dist(sc):
            dx = max(sc.ml - x, 0, x - sc.mr + 1)
            dy = max(sc.mt - y, 0, y - sc.mb + 1)
            return dx * dx + dy * dy
        return min(range(len(self.screens)), key=lambda i: dist(self.screens[i]))

    def floor_below(self, x, y):
        # the screen whose floor is nearest under (x, y), or None
        best = None
        for i, sc in enumerate(self.screens):
            if sc.ml <= x < sc.mr and sc.wb >= y - 1 and (best is None or sc.wb < self.screens[best].wb):
                best = i
        return best

    def neighbour(self, side):
        # the screen right next to this one (side -1 = left, 1 = right), if the pet may go there
        if self.one_monitor.get():
            return None
        sc = self.screens[self.si]
        for i, o in enumerate(self.screens):
            if i == self.si or (self.hide_fs.get() and self.fs[i]):
                continue   # a screen showing something full screen counts as a wall
            touching = abs(o.ml - sc.mr) <= 2 if side > 0 else abs(o.mr - sc.ml) <= 2
            if touching and o.mt < sc.mb and o.mb > sc.mt:
                return i
        return None

    def stacked(self):
        # screens right above or below this one (sharing at least a bit of width), if the pet may go there
        if self.one_monitor.get():
            return []
        sc, out = self.screens[self.si], []
        for i, o in enumerate(self.screens):
            if i == self.si or (self.hide_fs.get() and self.fs[i]):
                continue
            if (abs(o.mb - sc.mt) <= 2 or abs(o.mt - sc.mb) <= 2) and min(o.mr, sc.mr) - max(o.ml, sc.ml) > 200:
                out.append(i)
        return out

    def refresh_screens(self):
        self.screens_at = time.time()
        self.apply_screens(self.get_screens())

    def taskbar_tick(self):
        self.apply_screens(autohide_floors(self.raw_screens, taskbar_boxes()))

    def apply_screens(self, new):
        if new == self.screens:
            return
        self.end_trip()   # (a monitor came or went mid-trip: it just drops where it is)
        if len(new) != len(self.screens):
            self.fs = [False] * len(new)
        self.screens = new
        self.si = self.find_screen(self.x, self.y - 1)
        if self.si is None:
            self.si = self.nearest_screen(self.x, self.y - 1)
        sc = self.screens[self.si]
        self.x = min(max(self.x, sc.wl + self.half), sc.wr - self.half)
        self.y = min(self.y, sc.wb)

    def clamp_x(self):
        sc = self.screens[self.si]
        if self.neighbour(-1) is None:
            self.x = max(self.x, sc.wl + self.half)
        if self.neighbour(1) is None:
            self.x = min(self.x, sc.wr - self.half)

    def place(self):
        w, h = self.size
        if self.hidden and self.fader.alpha <= 0.001:
            geo = (w, h, PARK, PARK)
        else:   # always placed by the body, the same way in every state, so nothing jumps
            if not self.held and not self.trip:   # (a trip goes where it's going)
                self.clamp_x()
            geo = (w, h, round(self.x - self.center_x), round(self.y - self.feet_win))
        if geo != self.geo:
            self.root.geometry("{}x{}+{}+{}".format(*geo))   # "+-50" = 50 left of the main screen
            self.geo = geo

    def set_hidden(self, hide):
        if hide == self.hidden:
            return
        self.hidden = hide
        if hide:
            self.end_trip()
            self.held = self.pressed = False
            self.details.hide()
            self.popup.hide()
        self.fader.to(0.0 if hide else 1.0, instant=not self.anim.get())
