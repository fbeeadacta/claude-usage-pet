# small drawing helpers shared by every window: the canvas they all use, rounded boxes, smooth corners, fading, wrapping.
import ctypes
import time
import tkinter as tk

from .art import KEY
from .config import FADE_SECONDS
from .winapi import dwm, u32


def round_corners(win):
    # windows 11 rounds the panel's corners. older windows just ignores this.
    if dwm is None:
        return
    try:
        win.update_idletasks()
        hwnd = u32.GetParent(win.winfo_id()) or win.winfo_id()
        pref = ctypes.c_int(2)   # DWMWCP_ROUND
        dwm.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(pref), ctypes.sizeof(pref))
    except (OSError, tk.TclError):
        pass


class Canvas(tk.Canvas):
    # a canvas that reuses its items. tk 9 (python 3.15+) leaks a little memory for every canvas item
    # that's deleted, and the pet redraws everything up to 30 times a second, so it kept growing.
    # here delete("all") only hides the items, and the next create_* of the same kind (same options)
    # takes one of those back: moved, restyled and put on top, so it looks just like a new one.
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.pools, self.used, self.real = {}, {}, []   # (kind, option names) -> items, how many in use, window items

    def _create(self, kind, args, kw):
        if kind == "window":   # (holds a real widget, so it's made and deleted for real)
            item = super()._create(kind, args, kw)
            self.real.append(item)
            return item
        key = (kind, tuple(sorted(kw)))
        pool, n = self.pools.setdefault(key, []), self.used.get(key, 0)
        self.used[key] = n + 1
        if n == len(pool):
            pool.append(super()._create(kind, args, kw))
            return pool[n]
        item = pool[n]
        self.tk.call(self._w, "coords", item, *tk._flatten(args))
        self.tk.call(self._w, "itemconfigure", item, "-state", "normal", *self._options(kw))
        self.tk.call(self._w, "raise", item)
        return item

    def delete(self, *items):
        if items != ("all",):
            return super().delete(*items)
        if self.real:
            super().delete(*self.real)
            self.real = []
        self.tk.call(self._w, "itemconfigure", "all", "-state", "hidden")
        self.used = {}


_corners = {}


def mix(a, b, t):
    # colour a blended toward colour b by t (0 to 1)
    pa, pb_ = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb_))


def corner(c, r, fill, bg, smooth, q):
    # one rounded corner as a tiny image (q: 0 top-left, 1 top-right, 2 bottom-left, 3 bottom-right).
    # smooth = blend the edge into bg (anti-aliasing). on the see-through window that would leave
    # a coloured fringe, so there each pixel is either fully in or fully out.
    key = (r, fill, bg, smooth, q)
    if key not in _corners:
        rows = []
        for j in range(r):
            row = []
            for i in range(r):
                inside = sum((i + (a + 0.5) / 4 - r) ** 2 + (j + (b + 0.5) / 4 - r) ** 2 <= r * r
                             for a in range(4) for b in range(4)) / 16
                row.append(mix(bg, fill, inside) if smooth else (fill if inside >= 0.5 else bg))
            rows.append(row[::-1] if q in (1, 3) else row)
        if q in (2, 3):
            rows.reverse()
        img = tk.PhotoImage(master=c, width=r, height=r)
        img.put(" ".join("{" + " ".join(row) + "}" for row in rows))
        _corners[key] = img
    return _corners[key]


def move_window(win, x, y, w=None, h=None):
    # moves a window and makes sure it really went there. tk sometimes holds a move back
    # (seen with the right-click menu after it had been parked off screen), so if it didn't
    # arrive, move it directly with windows.
    win.geometry(f"{w}x{h}+{x}+{y}" if w else f"+{x}+{y}")
    win.update_idletasks()
    if (win.winfo_rootx(), win.winfo_rooty()) != (x, y):
        hwnd = u32.GetParent(win.winfo_id()) or win.winfo_id()
        flags = 0x0014 | (0x0001 if not w else 0)   # no z-order change, no activation, (keep size)
        u32.SetWindowPos(hwnd, None, x, y, w or 0, h or 0, flags)


def to_front(win):
    # puts a topmost window back at the very front of the topmost windows, without taking focus.
    # "-topmost" alone isn't enough: any always-on-top window opened later (task manager, a video
    # player...) goes in front of ours, and tk's lift() doesn't always beat it.
    hwnd = u32.GetParent(win.winfo_id()) or win.winfo_id()
    u32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0013)   # HWND_TOPMOST; no move, no resize, no activation


def round_rect(c, x1, y1, x2, y2, r, fill, bg=KEY, smooth=False, tag=""):
    # a rounded box: three rectangles plus four corner images, all on whole pixels so nothing steps
    x1, y1, x2, y2 = round(x1), round(y1), round(x2), round(y2)
    r = max(1, min(round(r), (x2 - x1) // 2, (y2 - y1) // 2))
    c.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="", tags=tag)
    c.create_rectangle(x1, y1 + r, x1 + r, y2 - r, fill=fill, outline="", tags=tag)
    c.create_rectangle(x2 - r, y1 + r, x2, y2 - r, fill=fill, outline="", tags=tag)
    for q, (x, y) in enumerate(((x1, y1), (x2 - r, y1), (x1, y2 - r), (x2 - r, y2 - r))):
        c.create_image(x, y, image=corner(c, r, fill, bg, smooth, q), anchor="nw", tags=tag)


def wrap(text, font, maxw):
    # split text into lines that fit maxw pixels
    lines, cur = [], ""
    for word in text.split():
        t = f"{cur} {word}".strip()
        if cur and font.measure(t) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = t
    return lines + ([cur] if cur else [])


class Fader:
    # fades a window in or out smoothly (fast at first, gentle at the end).
    # calls on_step after every change so the owner can move the window too.
    def __init__(self, win, alpha, peak, on_step):
        self.win, self.alpha, self.peak, self.on_step = win, alpha, peak, on_step
        self.target, self.job = alpha, None

    def to(self, target, instant=False):
        self.target, self.start_alpha, self.start = target, self.alpha, time.perf_counter()
        if instant:
            if self.job:
                self.win.after_cancel(self.job)
                self.job = None
            self.alpha = target
            self.apply()
        elif self.job is None:
            self.step()

    def step(self):
        t = min(1.0, (time.perf_counter() - self.start) / FADE_SECONDS)
        self.alpha = self.start_alpha + (self.target - self.start_alpha) * (1 - (1 - t) ** 3)
        self.apply()
        self.job = self.win.after(15, self.step) if t < 1 else None

    def apply(self):
        self.win.attributes("-alpha", max(0.0, min(1.0, self.alpha)) * self.peak)
        self.on_step()


class Tooltip:
    # a little card just under the mouse, styled like the panel: a bold title, then the explanation in grey.
    # text is "Title: explanation". font(size, bold) gives the owner's fonts (already scaled).
    def __init__(self, owner, card, fg, dim, font):
        self.owner, self.card, self.fg, self.dim, self.font = owner, card, fg, dim, font
        self.win, self.text = None, None

    def show(self, text, x_root, y_root, s):
        title, _, body = text.partition(": ")
        if self.win is None:
            self.win = tk.Toplevel(self.owner)
            self.win.overrideredirect(True)
            self.win.attributes("-topmost", True)
            self.win.configure(bg=self.card)
            self.title = tk.Label(self.win, bg=self.card, fg=self.fg, justify="left", anchor="w")
            self.body = tk.Label(self.win, bg=self.card, fg=self.dim, justify="left", anchor="w")
        if text != self.text:
            self.text = text
            self.title.configure(text=title, font=self.font(8, True))
            self.body.configure(text=body, font=self.font(7.5), wraplength=round(220 * s))
            self.title.pack_forget()
            self.body.pack_forget()
            self.title.pack(fill="x", padx=round(12 * s), pady=(round(9 * s), round(2 * s)))
            self.body.pack(fill="x", padx=round(12 * s), pady=(0, round(10 * s)))
            round_corners(self.win)
        self.win.geometry(f"+{x_root + 12}+{y_root + 16}")
        self.win.deiconify()
        self.win.lift()

    def hide(self):
        if self.win is not None and self.text is not None:
            self.win.withdraw()
            self.text = None
