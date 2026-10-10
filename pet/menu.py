# the small right-click menu.
import time
import tkinter as tk
import tkinter.font as tkfont

from .art import PARK, TRACK
from .ui import Fader, move_window, round_corners, round_rect
from .winapi import u32


# ---- the right-click menu ----

class PopupMenu:
    # a small menu drawn in the same style as the details panel
    BG, FG = "#1c1c1e", "#f2f2f7"
    ITEMS = (("Refresh now", "refresh"), ("Settings", "settings"), None, ("Quit", "quit"))

    def __init__(self, pet):
        self.pet = pet
        w = self.win = tk.Toplevel(pet.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.attributes("-alpha", 0.0)
        w.configure(bg=self.BG)
        w.geometry(f"10x10+{PARK}+{PARK}")
        self.canvas = tk.Canvas(w, bg=self.BG, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Motion>", lambda e: self.set_hover(self.row_at(e.y)))
        self.canvas.bind("<Leave>", lambda e: self.set_hover(None))
        self.canvas.bind("<ButtonRelease-1>", self.click)
        self.canvas.bind("<Button-3>", lambda e: self.hide())   # right-clicking the menu closes it too
        w.bind("<Escape>", lambda e: self.hide())
        self.visible, self.hover, self.rows, self.rect, self.rounded = False, None, [], None, False
        self.opened_at, self.was_down, self.s, self.size = 0.0, True, 1.0, (10, 10)
        self.fader = Fader(w, 0.0, 1.0, lambda: None)

    def show(self, x, y, avoid=None):
        p = self.pet
        self.s, self.hover = p.dpi, None
        self.draw()
        w, h = self.size
        si = p.find_screen(x, y)
        sc = p.screens[si if si is not None else p.nearest_screen(x, y)]
        gap = round(10 * self.s)
        if avoid and (avoid[0] <= x <= avoid[2] and avoid[1] <= y <= avoid[3]):
            # clicked on the mascot: open to its right (or left if there's no room), bottom level with its feet
            x = avoid[2] + gap if avoid[2] + gap + w <= sc.wr - 4 else avoid[0] - gap - w
            y = avoid[3] - h
        elif y + h > sc.wb - 4:
            y -= h   # near the taskbar it opens upward
        x = min(max(sc.wl + 4, x), sc.wr - w - 4)
        y = min(max(sc.wt + 4, y), sc.wb - h - 4)
        move_window(self.win, x, y, w, h)
        self.rect = (x, y, x + w, y + h)
        if not self.rounded:
            round_corners(self.win)
            self.rounded = True
        self.visible, self.opened_at, self.was_down = True, time.time(), True
        self.fader.to(1.0, instant=not p.anim.get())
        self.win.lift()
        self.win.focus_force()

    def hide(self):
        if not self.visible:
            return
        self.visible = False
        self.fader.to(0.0, instant=True)
        move_window(self.win, PARK, PARK)

    def watch(self):
        # called 10 times a second: a click anywhere outside the menu closes it
        if not self.visible:
            return
        down = any(u32.GetAsyncKeyState(k) & 0x8001 for k in (0x01, 0x02))
        if down and not self.was_down and time.time() - self.opened_at > 0.15:
            mx, my = self.pet.root.winfo_pointerxy()
            r = self.rect
            if not (r[0] <= mx < r[2] and r[1] <= my < r[3]):
                self.hide()
        self.was_down = down

    def draw(self):
        s, c = self.s, self.canvas
        c.delete("all")
        W, rh, pad = round(170 * s), round(30 * s), round(6 * s)
        font = tkfont.Font(root=self.win, family="Segoe UI", size=-max(8, round(12 * s)))
        y, self.rows = pad, []
        for item in self.ITEMS:
            if item is None:   # a thin divider
                c.create_rectangle(round(12 * s), y + round(4 * s), W - round(12 * s), y + round(4 * s) + max(1, round(s)),
                                   fill=TRACK, width=0)
                y += round(9 * s)
                continue
            label, action = item
            if self.hover == action:
                round_rect(c, pad, y, W - pad, y + rh, round(5 * s), TRACK, self.BG, True)
            c.create_text(round(16 * s), y + rh // 2, anchor="w", text=label, fill=self.FG, font=font)
            self.rows.append((action, y, y + rh))
            y += rh
        self.size = (W, y + pad)
        c.configure(width=W, height=y + pad)

    def row_at(self, y):
        return next((a for a, y0, y1 in self.rows if y0 <= y < y1), None)

    def set_hover(self, action):
        if action != self.hover:
            self.hover = action
            self.draw()

    def click(self, e):
        action = self.row_at(e.y)
        if action:
            self.hide()
            p = self.pet
            {"refresh": p.refresh, "settings": p.settings.open, "quit": p.quit}[action]()
