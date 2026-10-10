# little see-through windows for things that wander away from the mascot: the fetch ball and the cat.
import tkinter as tk

from .art import KEY, PARK, SHADOW
from .ui import Canvas


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
