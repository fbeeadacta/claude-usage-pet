# small drawing helpers shared by every window: rounded boxes, smooth corners, fading, wrapping.
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
