# a small always-on-top window that shows your claude usage limits (5-hour, weekly, ...).
#
# how it works: claude code keeps your login token in ~/.claude/.credentials.json.
# this reads that token and asks https://api.anthropic.com/api/oauth/usage for your
# limits, the same endpoint the open source "usage-monitor-for-claude" tool uses.
# that endpoint is not documented, so it can change or stop working without notice.
#
# the token is only ever sent to api.anthropic.com. it is never printed, logged or saved.
# you need to be logged in to claude code on this computer.
#
# run it:      pythonw usage_widget.py          (no console window)
#              python usage_widget.py           (with a console, to see errors)
# start with windows:   python usage_widget.py --startup
# undo that:            python usage_widget.py --no-startup
# right click the window for refresh / quit. drag it to move it (it remembers where).
# no pip installs needed. it only uses python's standard library.

import os
import sys
import json
import math
import time
import queue
import argparse
import threading
import subprocess
import urllib.request
import urllib.error
import datetime
import tkinter as tk
from pathlib import Path

# ---- settings ----
POLL_SECONDS = 120         # how often to ask the api
ONLY_KNOWN_LIMITS = True   # show only the 5-hour and weekly limits. False shows everything the api lists.
RATE_LIMITED_SECONDS = 180 # wait this long after the api says "slow down"
USER_AGENT = "usage-widget/0.1"
WIDTH = 270
# pace messages
AHEAD_BY = 10          # used% this far above the clock = "ahead of pace"
SLOW_BELOW = 0.5       # used under half of what the clock says = "way under pace"
IDLE_MIN_5H = 45       # 5-hour number unchanged this long = "not moving"
IDLE_HOURS_WEEKLY = 12 # weekly number unchanged this long = "not moving"
# ------------------

URL = "https://api.anthropic.com/api/oauth/usage"
CONFIG_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
CREDENTIALS = CONFIG_DIR / ".credentials.json"
HERE = Path(__file__).resolve().parent
POS_FILE = HERE / "usage_widget_pos.json"
STARTUP_NAME = "Claude Usage Widget.lnk"

NICE = {"five_hour": "5-hour", "seven_day": "Weekly"}


def read_token():
    try:
        creds = json.loads(CREDENTIALS.read_text())
        return creds["claudeAiOauth"]["accessToken"] or None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def fetch_usage():
    """returns (data, error). error is a short plain message, never the token."""
    token = read_token()
    if not token:
        return None, "no login found. run 'claude' once and sign in."
    req = urllib.request.Request(URL, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "anthropic-beta": "oauth-2025-04-20",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return None, "login expired. open claude code to refresh it."
        if e.code == 429:
            return None, "rate limited. will retry."
        return None, f"api error {e.code}."
    except Exception as e:
        return None, f"no connection ({type(e).__name__})."


def nice_name(key):
    if key in NICE:
        return NICE[key]
    return key.replace("seven_day_", "weekly ").replace("_", " ").strip()


def parse_rows(data):
    """api answer -> [{key, label, pct, resets}], most important first."""
    rows = []
    for key, v in data.items():
        if isinstance(v, dict) and v.get("utilization") is not None and v.get("resets_at"):
            if ONLY_KNOWN_LIMITS and period_seconds(key) is None:
                continue   # a field the api lists that is not a 5-hour or weekly limit
            rows.append({"key": key, "label": nice_name(key),
                         "pct": float(v["utilization"]), "resets": v["resets_at"]})
    order = {"five_hour": 0, "seven_day": 1}
    rows.sort(key=lambda r: (order.get(r["key"], 9), r["key"]))
    return rows


def parse_time(iso):
    try:
        return datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def reset_text(iso, now=None):
    reset = parse_time(iso)
    if reset is None:
        return ""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    mins = max(0, int((reset - now).total_seconds() // 60))
    if mins >= 24 * 60:
        return f"resets in {mins // 1440}d {(mins % 1440) // 60}h"
    return f"resets in {mins // 60}h {mins % 60:02d}m"


def period_seconds(key):
    """how long the window is, or None when we do not know."""
    if key == "five_hour":
        return 5 * 3600
    if key.startswith("seven_day"):
        return 7 * 24 * 3600
    return None


def elapsed_pct(key, resets_iso, now):
    """how far through the window the clock is, 0 to 100 (None if unknown)."""
    period, reset = period_seconds(key), parse_time(resets_iso)
    if not period or reset is None:
        return None
    remaining = max(0.0, (reset - now).total_seconds())
    return min(100.0, max(0.0, (period - remaining) / period * 100))


def pace_info(key, pct, resets_iso, now, unchanged_seconds):
    """returns (elapsed_pct_or_None, message_or_None, kind) where kind is
    'fast', 'slow' or None. compares what you used with how much time has passed."""
    el = elapsed_pct(key, resets_iso, now)
    if el is None or el < 10:   # too early in the window to say anything
        return el, None, None
    idle_limit = (IDLE_MIN_5H * 60) if key == "five_hour" else (IDLE_HOURS_WEEKLY * 3600)
    if unchanged_seconds >= idle_limit and pct < el:
        return el, "no usage lately. put it to work!", "slow"
    if pct >= el + AHEAD_BY:
        # used more than the clock allows, so at this rate it runs out before the reset
        return el, "ahead of pace. may hit the limit early", "fast"
    if el >= 20 and pct <= el * SLOW_BELOW:
        return el, "way under pace. use more!", "slow"
    return el, None, None


def bar_color(p):
    return "#e5534b" if p >= 85 else "#d9a441" if p >= 60 else "#4caf7d"


# ---- start with windows ----

def startup_path():
    return Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup" / STARTUP_NAME


def set_startup(enable):
    lnk = startup_path()
    if not enable:
        try:
            lnk.unlink()
            print("removed from startup.")
        except OSError:
            print("it was not in startup.")
        return
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    target = pyw if pyw.exists() else exe
    script = Path(__file__).resolve()
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
          "$s.TargetPath='{t}';$s.Arguments='\"{sc}\"';$s.WorkingDirectory='{d}';$s.Save()"
          ).format(lnk=lnk, t=target, sc=script, d=script.parent)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    print("added to startup." if r.returncode == 0 else f"could not add it: {r.stderr.strip()}")


# ---- the window ----

MIN_SCALE, MAX_SCALE = 0.6, 2.6


class Widget:
    BG, FG, DIM, TRACK = "#1c1c1e", "#f2f2f7", "#8e8e93", "#3a3a3c"
    FASTC, SLOWC = "#d9a441", "#5ea1ff"

    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)           # no title bar
        self.root.attributes("-topmost", True)     # always on top
        self.root.configure(bg=self.BG)
        x, y, self.scale, self.collapsed = self.load_state()
        self.root.geometry(f"{round(WIDTH * self.scale)}x90+{x}+{y}")
        self.canvas = tk.Canvas(self.root, width=WIDTH, height=90, bg=self.BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.inbox = queue.Queue()
        self.data, self.error, self.updated = None, None, None
        self.busy = False
        self.next_at = 0.0          # unix time of the next check. 0 = check right away.
        self.seen = {}              # key -> (percent, when it last changed, resets_at)
        self.hits = []              # clickable areas from the last draw: (name, x1, y1, x2, y2) in pixels
        self.mode, self.moved = None, False
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Refresh now", command=self.refresh)
        self.menu.add_command(label="Collapse / expand", command=self.toggle)
        self.menu.add_command(label="Quit", command=self.root.destroy)
        c = self.canvas
        c.bind("<Button-1>", self.press)
        c.bind("<B1-Motion>", self.motion)
        c.bind("<ButtonRelease-1>", self.release)
        c.bind("<Motion>", self.hover)
        c.bind("<Button-3>", lambda e: self.menu.tk_popup(e.x_root, e.y_root))
        self.tick()

    # saved position, size and collapsed state
    def load_state(self):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        x, y, scale, collapsed = sw - WIDTH - 24, 24, 1.0, False
        try:
            p = json.loads(POS_FILE.read_text())
            scale = min(MAX_SCALE, max(MIN_SCALE, float(p.get("scale", 1.0))))
            collapsed = bool(p.get("collapsed", False))
            px, py = int(p["x"]), int(p["y"])
            if 0 <= px < sw - 40 and 0 <= py < sh - 40:   # still on a visible screen
                x, y = px, py
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return x, y, scale, collapsed

    def save_state(self):
        try:
            POS_FILE.write_text(json.dumps({"x": self.root.winfo_x(), "y": self.root.winfo_y(),
                                            "scale": round(self.scale, 3), "collapsed": self.collapsed}))
        except OSError:
            pass

    # mouse: drag to move, drag the corner to resize, click the buttons
    def hit(self, x, y):
        for name, x1, y1, x2, y2 in self.hits:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return name
        return None

    def hover(self, e):
        self.canvas.configure(cursor="size_nw_se" if self.hit(e.x, e.y) == "grip" else "")

    def press(self, e):
        self.moved = False
        self.sx, self.sy = e.x_root, e.y_root
        if self.hit(e.x, e.y) == "grip":
            self.mode, self.start_width = "resize", self.root.winfo_width()
        else:
            self.mode = "drag"
            self.dx, self.dy = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()

    def motion(self, e):
        if abs(e.x_root - self.sx) + abs(e.y_root - self.sy) > 3:
            self.moved = True
        if self.mode == "resize":
            new_w = self.start_width + (e.x_root - self.sx)
            self.scale = min(MAX_SCALE, max(MIN_SCALE, new_w / WIDTH))
            self.draw()
        elif self.mode == "drag":
            self.root.geometry(f"+{e.x_root - self.dx}+{e.y_root - self.dy}")

    def release(self, e):
        name = self.hit(e.x, e.y)
        if not self.moved:
            if self.collapsed:
                self.toggle()
            elif name == "min":
                self.toggle()
            elif name == "close":
                self.root.destroy()
                return
        self.mode = None
        self.save_state()

    def toggle(self):
        self.collapsed = not self.collapsed
        self.draw()
        self.root.update_idletasks()
        # keep it on screen when it grows back
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = min(self.root.winfo_x(), self.root.winfo_screenwidth() - w - 4)
        y = min(self.root.winfo_y(), self.root.winfo_screenheight() - h - 40)
        self.root.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        self.save_state()

    # data
    def refresh(self):
        if self.busy:
            return
        self.busy = True
        threading.Thread(target=lambda: self.inbox.put(fetch_usage()), daemon=True).start()

    def take_result(self):
        try:
            data, err = self.inbox.get_nowait()
        except queue.Empty:
            return
        now = time.time()
        self.busy = False
        if data is not None:
            self.data, self.error = data, None
            self.updated = datetime.datetime.now()
            for r in parse_rows(data):
                prev = self.seen.get(r["key"])
                if prev is None or prev[0] != r["pct"] or prev[2] != r["resets"]:
                    self.seen[r["key"]] = (r["pct"], now, r["resets"])
            self.next_at = now + POLL_SECONDS
        else:
            self.error = err
            self.next_at = now + (RATE_LIMITED_SECONDS if "rate limited" in err else POLL_SECONDS)

    def tick(self):
        self.take_result()
        if not self.busy and time.time() >= self.next_at:
            self.refresh()
        self.draw()
        self.root.after(1000, self.tick)

    # drawing. everything is laid out in base units (WIDTH wide) and multiplied by self.scale.
    def font(self, size, bold=False):
        px = max(6, round(size * self.scale))
        return ("Segoe UI", px, "bold") if bold else ("Segoe UI", px)

    def text(self, x, y, text, fill, size, bold=False, anchor="nw", width=None):
        s = self.scale
        kw = {"width": width * s} if width else {}
        self.canvas.create_text(x * s, y * s, anchor=anchor, fill=fill, font=self.font(size, bold),
                                text=text, **kw)

    def rect(self, x1, y1, x2, y2, fill):
        s = self.scale
        self.canvas.create_rectangle(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=0)

    def line(self, x1, y1, x2, y2, fill, width=1):
        s = self.scale
        self.canvas.create_line(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=max(1, round(width * s)))

    def add_hit(self, name, x1, y1, x2, y2):
        s = self.scale
        self.hits.append((name, x1 * s, y1 * s, x2 * s, y2 * s))

    def draw(self):
        c = self.canvas
        c.delete("all")
        self.hits = []
        rows = parse_rows(self.data) if self.data else []
        if self.collapsed:
            self.draw_chip(rows)
            return
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = time.time()
        W = WIDTH
        self.text(12, 10, "CLAUDE USAGE", self.DIM, 8)
        self.text(W - 34, 6, "\u2013", self.DIM, 12, True, "n")     # collapse button
        self.text(W - 15, 7, "\u00d7", self.DIM, 11, True, "n")      # close button
        self.add_hit("min", W - 46, 3, W - 24, 24)
        self.add_hit("close", W - 24, 3, W - 4, 24)
        if self.updated:
            self.text(W - 12, 26, f"updated {self.updated:%H:%M}", self.DIM, 8, anchor="ne")
        wait = "updating..." if self.busy else f"next update in {max(0, math.ceil(self.next_at - now))}s"
        self.text(W - 12, 40, wait, self.DIM, 8, anchor="ne")
        y = 58
        for r in rows:
            seen = self.seen.get(r["key"])
            unchanged = now - seen[1] if seen else 0
            el, msg, kind = pace_info(r["key"], r["pct"], r["resets"], now_dt, unchanged)
            self.text(12, y, r["label"], self.FG, 9, True)
            self.text(W - 12, y, f"{r['pct']:.0f}%", self.FG, 9, True, "ne")
            self.rect(12, y + 20, W - 12, y + 26, self.TRACK)
            self.rect(12, y + 20, 12 + (W - 24) * min(r["pct"], 100) / 100, y + 26, bar_color(r["pct"]))
            if el is not None:   # the pace tick: where the clock is in this window
                tx = 12 + (W - 24) * el / 100
                self.line(tx, y + 16, tx, y + 30, self.FG, 2)
            self.text(12, y + 32, reset_text(r["resets"], now_dt), self.DIM, 8)
            h = 54
            if msg:
                self.text(12, y + 46, msg, self.FASTC if kind == "fast" else self.SLOWC, 8, True, width=W - 24)
                h = 68
            y += h
        if self.error:
            self.text(12, y, self.error, "#e5534b", 8, width=W - 24)
            y += 30
        elif not rows:
            self.text(12, y, "loading...", self.DIM, 8)
            y += 20
        H = y + 12
        for i in range(3):   # resize grip, bottom right corner
            self.line(W - 4 - i * 4, H - 3, W - 3, H - 4 - i * 4, self.DIM)
        self.add_hit("grip", W - 20, H - 20, W + 2, H + 2)
        px_w, px_h = round(W * self.scale), round(H * self.scale)
        self.root.geometry(f"{px_w}x{px_h}")
        c.configure(width=px_w, height=px_h)

    def draw_chip(self, rows):
        """the collapsed form: a tiny pill with the first limit's percent. click it to expand."""
        k = min(1.6, max(0.8, self.scale))
        w, h = round(92 * k), round(26 * k)
        if rows:
            r = rows[0]
            label = "5h" if r["key"] == "five_hour" else r["label"][:8]
            txt, color = f"{label} {r['pct']:.0f}%", bar_color(r["pct"])
        else:
            txt, color = ("!" if self.error else "..."), self.DIM
        c = self.canvas
        c.create_rectangle(0, 0, w, h, fill="#2a2a2d", outline=self.TRACK)
        d = round(8 * k)
        c.create_oval(round(9 * k), (h - d) // 2, round(9 * k) + d, (h - d) // 2 + d, fill=color, width=0)
        c.create_text(round(24 * k), h // 2, anchor="w", fill=self.FG,
                      font=("Segoe UI", max(7, round(9 * k)), "bold"), text=txt)
        self.root.geometry(f"{w}x{h}")
        c.configure(width=w, height=h)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--startup", action="store_true", help="start the widget when you sign in to windows")
    ap.add_argument("--no-startup", action="store_true", help="stop starting with windows")
    a = ap.parse_args()
    if a.startup or a.no_startup:
        set_startup(a.startup)
        sys.exit(0)
    Widget().root.mainloop()
