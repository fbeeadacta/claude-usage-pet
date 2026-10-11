# little see-through windows for things that wander away from the mascot: the fetch ball, the cat, and the
# stage that a trip to another monitor is drawn on.
import tkinter as tk

from .art import KEY, PARK, SHADOW
from .ui import Canvas, move_window


class Sprite:
    # a borderless, always-on-top window showing one small block picture. its (x, y) is the bottom middle
    # of the picture, in screen pixels, like the mascot's feet.
    def __init__(self, root):
        w = self.win = tk.Toplevel(root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=KEY)
        w.attributes("-transparentcolor", KEY)
        w.geometry(f"1x1+{PARK}+{PARK}")
        self.canvas = Canvas(w, bg=KEY, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.look, self.size, self.geo = None, (1, 1), None

    def show(self, rows, colours, b, x, y, flip=False):
        look = (tuple(rows), b, flip)
        if look != self.look:   # only redraw when the picture changes; moving is just moving the window
            self.look = look
            c = self.canvas
            c.delete("all")
            d = max(1, b // 2)
            w, h = len(rows[0]) * b + d, len(rows) * b + d
            for dd, col in ((d, None), (0, colours)):   # a dark shadow first, so it shows on any wallpaper
                for r, line in enumerate(rows):
                    for i, ch in enumerate(line[::-1] if flip else line):
                        if ch != ".":
                            fill = SHADOW if col is None else col.get(ch, col.get("#", SHADOW))
                            c.create_rectangle(i * b + dd, r * b + dd, (i + 1) * b + dd, (r + 1) * b + dd,
                                               fill=fill, outline="")
            c.configure(width=w, height=h)
            self.size = (w, h)
        w, h = self.size
        geo = (w, h, round(x - w / 2), round(y - h))
        if geo != self.geo:
            self.win.geometry("{}x{}+{}+{}".format(*geo))   # ("+-50" works left of the main screen too)
            if self.geo is None or self.geo[2] == PARK:
                self.win.lift()
            self.geo = geo

    def hide(self):
        if self.geo is None or self.geo[2] != PARK:
            self.win.geometry(f"1x1+{PARK}+{PARK}")
            self.geo = (1, 1, PARK, PARK)

    def contains(self, mx, my):
        g = self.geo
        return g is not None and g[2] != PARK and g[2] <= mx < g[2] + g[0] and g[3] <= my < g[3] + g[1]


class Stage:
    # a see-through, click-through window over part of the screen, for drawing whatever's needed there
    # (the props and dust of a trip). draw on .canvas in screen pixels minus .origin.
    # hidden, it's just empty and 1x1 where it was (moving it back from the parking spot didn't always work).
    def __init__(self, root):
        w = self.win = tk.Toplevel(root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=KEY)
        w.attributes("-transparentcolor", KEY)
        w.geometry(f"1x1+{PARK}+{PARK}")
        self.canvas = Canvas(w, bg=KEY, highlightthickness=0, bd=0, width=1, height=1)
        self.canvas.pack()
        self.origin, self.geo, self.shown = (PARK, PARK), None, False

    def place(self, x0, y0, x1, y1):
        # covers (x0, y0) to (x1, y1). returns True if it just appeared (so whatever goes in front can be lifted)
        geo = (max(1, round(x1 - x0)), max(1, round(y1 - y0)), round(x0), round(y0))
        fresh = not self.shown
        if geo != self.geo:
            self.canvas.configure(width=geo[0], height=geo[1])
            move_window(self.win, geo[2], geo[3], geo[0], geo[1])   # (tk sometimes holds a move back)
            self.geo, self.origin = geo, (geo[2], geo[3])
        if fresh:
            self.win.lift()
            self.shown = True
        return fresh

    def hide(self):
        self.canvas.delete("all")
        if self.shown:
            self.canvas.configure(width=1, height=1)
            self.geo = (1, 1) + self.geo[2:]
            self.win.geometry("1x1+{}+{}".format(*self.geo[2:]))
            self.shown = False
