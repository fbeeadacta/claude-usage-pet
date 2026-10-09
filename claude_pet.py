# claude usage pet: a tiny claude mascot that lives on your taskbar and shows your
# plan usage (5-hour and weekly limits) in a bubble above its head.
#
# the numbers are for your whole plan, so they include claude.ai chat, the desktop app
# and claude code. they come from https://api.anthropic.com/api/oauth/usage, an
# undocumented endpoint that can change or stop working without notice.
#
# your login token is read from ~/.claude/.credentials.json (claude code puts it there).
# it is only ever sent to api.anthropic.com. it is never printed, logged or saved.
#
# run it:      pythonw claude_pet.py          (no console window)
#              python claude_pet.py           (with a console, to see errors)
# start with windows:   right click the mascot > start with windows
#                       (or: python claude_pet.py --startup / --no-startup)
# hover the mascot for details. click it to poke it. right click for the menu.
# drag it to pick it up. ctrl + mouse wheel over the mascot changes its size.
# no pip installs needed. it only uses python's standard library.

import os
import sys
import json
import math
import time
import queue
import random
import ctypes
import argparse
import datetime
import threading
import subprocess
import urllib.request
import urllib.error
import tkinter as tk
import tkinter.font as tkfont
from collections import namedtuple
from ctypes import wintypes
from pathlib import Path

# ---- settings ----
DEFAULT_SCALE = 1.0        # starting size. after that the size you pick in the menu is remembered.
SIZES = [0.75, 1.0, 1.25, 1.5, 2.0, 3.0]   # choices in the right-click size menu
MIN_SCALE, MAX_SCALE = 0.5, 4.0            # limits for ctrl + mouse wheel
POLL_SECONDS = 120         # how often to ask the api
ONLY_KNOWN_LIMITS = True   # show only the 5-hour and weekly limits. False shows everything the api lists.
RATE_LIMITED_SECONDS = 180 # wait this long after the api says "slow down"
USER_AGENT = "usage-widget/0.1"  # if the api refuses this, try "claude-code/2.1.204"
# how it moves (pixels are at 1x size)
WALK_SPEED = 28            # pixels per second
JUMP_EVERY = 30            # on average one hop every this many seconds
HOP_HEIGHT = 34            # pixels
GRAVITY = 1150             # pixels per second per second
MAX_STEP_UP = 400          # tallest ledge (onto a higher monitor) it will jump up
# moods
SLEEP_AFTER_MIN = 5        # falls asleep when you've been away from the computer this long
NAP_CHANCE = 0.06          # chance of a short nap whenever it stops walking
SWEAT_AT = 85              # sweats when a limit is at or above this %
HOVER_DELAY = 0.3          # seconds of hovering before the details panel shows
FADE_SECONDS = 0.18        # how long the details panel takes to fade in or out
# pace messages (details panel)
AHEAD_BY = 10          # used% this far above the clock = "ahead of pace"
SLOW_BELOW = 0.5       # used under half of what the clock says = "way under pace"
IDLE_MIN_5H = 45       # 5-hour number unchanged this long = "not moving"
IDLE_HOURS_WEEKLY = 12 # weekly number unchanged this long = "not moving"
# ------------------

URL = "https://api.anthropic.com/api/oauth/usage"
CONFIG_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
CREDENTIALS = CONFIG_DIR / ".credentials.json"
HERE = Path(__file__).resolve().parent
SETTINGS_FILE = HERE / "pet_settings.json"
STARTUP_NAME = "Claude Usage Pet.lnk"

NICE = {"five_hour": "5-hour", "seven_day": "Weekly"}
SHORT = {"five_hour": "5h", "seven_day": "wk"}

# the mascot. same shape as claude code's welcome screen:
#    ▐▛███▜▌
#   ▝▜█████▛▘
#     ▘▘ ▝▝
# every terminal character is 2x2 small blocks, so it is 18 blocks wide and 5 tall.
# each block is a solid rectangle (not text) so the edges stay sharp on a see-through window.
BODY = [
    "...############...",
    "...############...",
    "..##############..",
    "...############...",
]
ARMS = ((1, 2), (16, 2))
WAVE = (((15, 1), (16, 1)), ((15, 1), (16, 0)))   # right arm, two waving frames
LEGS_STAND = (4, 6, 11, 13)
LEGS_STEP = (5, 7, 10, 12)
LEGS_AIR = (3, 5, 12, 14)
EYES = (5, 12)             # columns on row 1
BLUSH = (4, 13)            # columns on row 2, when it's happy
BLOCK_W, BLOCK_H = 4, 8    # one block at 1x. terminal blocks are twice as tall as wide.

# little pictures made of small square blocks
HEART = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
ZZZ = ["####", "..#.", ".#..", "####"]
SWEAT = [".#.", "###", "###", ".#."]

ORANGE, EYE, BLUSH_C = "#d77757", "#2b1a14", "#f4a08f"
BUBBLE, BUBBLE_TEXT = "#1f1e1d", "#f2efe8"
HEART_C, ZZZ_C, SWEAT_C, SHADOW = "#ff6f8a", "#f2efe8", "#7cc4ff", "#2b1a14"
DIM, RED = "#8e8e93", "#e5534b"
KEY = "#010203"            # this exact colour becomes see-through (and click-through)
PARK = -32000              # hidden windows are parked way off screen


# ---- talking to the api ----

def read_token():
    try:
        creds = json.loads(CREDENTIALS.read_text())
        return creds["claudeAiOauth"]["accessToken"] or None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def fetch_usage():
    # returns (data, error). error is a short plain message, never the token.
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


def short_error(err):
    # a few words for the bubble. the details panel shows the whole message.
    for start, short in (("no login", "no login"), ("login expired", "login expired"),
                         ("rate limited", "slow down"), ("no connection", "offline")):
        if err.startswith(start):
            return short
    return err.rstrip(".")


def nice_name(key):
    if key in NICE:
        return NICE[key]
    return key.replace("seven_day_", "weekly ").replace("_", " ").strip()


def parse_rows(data):
    # api answer -> [{key, label, pct, resets}], most important first
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
    # how long the window is, or None when we do not know
    if key == "five_hour":
        return 5 * 3600
    if key.startswith("seven_day"):
        return 7 * 24 * 3600
    return None


def elapsed_pct(key, resets_iso, now):
    # how far through the window the clock is, 0 to 100 (None if unknown)
    period, reset = period_seconds(key), parse_time(resets_iso)
    if not period or reset is None:
        return None
    remaining = max(0.0, (reset - now).total_seconds())
    return min(100.0, max(0.0, (period - remaining) / period * 100))


def pace_info(key, pct, resets_iso, now, unchanged_seconds):
    # returns (elapsed_pct_or_None, message_or_None, kind) where kind is 'fast', 'slow' or None.
    # compares what you used with how much time has passed.
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


# ---- settings file ----

DEFAULTS = {"scale": DEFAULT_SCALE, "walk": True, "jump": True, "naps": True, "anim": True,
            "bubble": "both", "hide_fs": True, "one_monitor": False, "x": None, "y": None}


def load_settings():
    st = dict(DEFAULTS)
    try:
        saved = json.loads(SETTINGS_FILE.read_text())
        if isinstance(saved, dict):
            st.update({k: saved[k] for k in DEFAULTS if k in saved})
    except (OSError, ValueError):
        pass   # missing or broken file: just use the defaults
    try:
        st["scale"] = min(MAX_SCALE, max(MIN_SCALE, float(st["scale"])))
    except (TypeError, ValueError):
        st["scale"] = DEFAULT_SCALE
    for k in ("walk", "jump", "naps", "anim", "hide_fs", "one_monitor"):
        st[k] = st[k] if isinstance(st[k], bool) else DEFAULTS[k]
    if st["bubble"] not in ("both", "5h", "hover"):
        st["bubble"] = "both"
    for k in ("x", "y"):
        if isinstance(st[k], bool) or not isinstance(st[k], (int, float)):
            st[k] = None
    return st


def save_settings(st):
    # write to a temp file first, then swap it in, so a crash mid-write can't leave a broken file
    tmp = SETTINGS_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(st, indent=1))
        os.replace(tmp, SETTINGS_FILE)
    except OSError:
        pass


# ---- windows bits (ctypes is part of python, no installs) ----

u32 = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
try:
    dwm = ctypes.WinDLL("dwmapi")
    dwm.DwmGetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    dwm.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
except OSError:
    dwm = None


class MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


MONITORENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC,
                                     ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
u32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), MONITORENUMPROC, wintypes.LPARAM]
u32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
u32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
for _f in (u32.IsWindowVisible, u32.IsIconic, u32.IsZoomed):
    _f.argtypes = [wintypes.HWND]
u32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
u32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
u32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
u32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
u32.GetWindowThreadProcessId.restype = wintypes.DWORD
u32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
u32.GetParent.argtypes = [wintypes.HWND]
u32.GetParent.restype = wintypes.HWND
k32.GetTickCount.restype = wintypes.DWORD

# a screen: its full rectangle (m...) and the part not covered by the taskbar (w...).
# the bottom of the work part (wb) is the floor the pet stands on.
Screen = namedtuple("Screen", "ml mt mr mb wl wt wr wb")

WS_CAPTION = 0x00C00000
WS_EX_TRANSPARENT, WS_EX_TOOLWINDOW = 0x20, 0x80
NOT_APPS = {"Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"}   # desktop and taskbars


def make_dpi_aware():
    # without this, windows blurs the pet when display scaling is above 100%,
    # and positions on a second monitor with different scaling come out wrong
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def list_screens():
    found = []

    def cb(hmon, hdc, rect, lp):
        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if u32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            m, w = mi.rcMonitor, mi.rcWork
            found.append(Screen(m.left, m.top, m.right, m.bottom, w.left, w.top, w.right, w.bottom))
        return True

    u32.EnumDisplayMonitors(None, None, MONITORENUMPROC(cb), 0)
    return sorted(found)   # left to right


def is_cloaked(hwnd):
    # windows hides some apps without really hiding them (other virtual desktops, suspended store apps)
    if dwm is None:
        return False
    val = ctypes.c_int(0)
    dwm.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(val), ctypes.sizeof(val))
    return val.value != 0


def fullscreen_screens(screens):
    # for each screen: is a full-screen window (video, game, ...) showing on it?
    # goes through windows front to back. for each screen the first big window decides:
    # one covering the whole screen = full screen. a normal big or maximized window = not.
    result = [None] * len(screens)
    me = os.getpid()

    def cb(hwnd, lp):
        try:
            if not u32.IsWindowVisible(hwnd) or u32.IsIconic(hwnd):
                return True
            pid = wintypes.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == me or u32.GetWindowLongW(hwnd, -20) & (WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW):
                return True   # our own windows, and click-through overlays
            name = ctypes.create_unicode_buffer(64)
            u32.GetClassNameW(hwnd, name, 64)
            if name.value in NOT_APPS or is_cloaked(hwnd):
                return True
            r = wintypes.RECT()
            if not u32.GetWindowRect(hwnd, ctypes.byref(r)):
                return True
            for i, sc in enumerate(screens):
                if result[i] is not None:
                    continue
                w = min(r.right, sc.mr) - max(r.left, sc.ml)
                h = min(r.bottom, sc.mb) - max(r.top, sc.mt)
                if w <= 0 or h <= 0:
                    continue
                if r.left <= sc.ml and r.top <= sc.mt and r.right >= sc.mr and r.bottom >= sc.mb:
                    maximized = u32.IsZoomed(hwnd) and u32.GetWindowLongW(hwnd, -16) & WS_CAPTION == WS_CAPTION
                    result[i] = not maximized
                elif w * h >= 0.85 * (sc.mr - sc.ml) * (sc.mb - sc.mt):
                    result[i] = False
            return None in result   # keep going until every screen is decided
        except Exception:
            return True

    u32.EnumWindows(WNDENUMPROC(cb), 0)
    return [bool(x) for x in result]


def idle_seconds():
    # how long since you last touched the mouse or keyboard
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(lii)
    if not u32.GetLastInputInfo(ctypes.byref(lii)):
        return 0.0
    return ((k32.GetTickCount() - lii.dwTime) & 0xFFFFFFFF) / 1000


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


_lock = None


def already_running():
    # a named lock so starting it twice doesn't give you two pets
    global _lock
    k32.CreateMutexW.restype = wintypes.HANDLE
    _lock = k32.CreateMutexW(None, False, "claude-usage-pet")
    return ctypes.get_last_error() == 183   # ERROR_ALREADY_EXISTS


def startup_path():
    return Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Startup" / STARTUP_NAME


def set_startup(enable):
    # returns a short message saying what happened
    lnk = startup_path()
    if not enable:
        try:
            lnk.unlink()
            return "removed from startup."
        except OSError:
            return "it was not in startup."
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    target = pyw if pyw.exists() else exe
    script = Path(__file__).resolve()
    q = lambda p: str(p).replace("'", "''")   # powershell quoting
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
          "$s.TargetPath='{t}';$s.Arguments='\"{sc}\"';$s.WorkingDirectory='{d}';$s.Save()"
          ).format(lnk=q(lnk), t=q(target), sc=q(script), d=q(script.parent))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return "added to startup." if r.returncode == 0 else f"could not add it: {r.stderr.strip()}"


def round_rect(c, x1, y1, x2, y2, r, fill):
    c.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="")
    c.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline="")
    for ox, oy in ((x1, y1), (x2 - 2 * r, y1), (x1, y2 - 2 * r), (x2 - 2 * r, y2 - 2 * r)):
        c.create_oval(ox, oy, ox + 2 * r, oy + 2 * r, fill=fill, outline="")


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


# ---- the pet ----

class Pet:
    def __init__(self):
        make_dpi_aware()
        self.root = tk.Tk()
        self.root.overrideredirect(True)            # no title bar, no taskbar button
        self.root.attributes("-topmost", True)      # always on top
        self.root.configure(bg=KEY)
        self.root.attributes("-transparentcolor", KEY)
        self.dpi = self.root.winfo_fpixels("1i") / 96   # 1.0 at 100% display scaling, 1.5 at 150%
        self.canvas = tk.Canvas(self.root, bg=KEY, highlightthickness=0, bd=0)
        self.canvas.pack()
        self.fonts = {}

        st = load_settings()
        self.scale = st["scale"]
        self.walk = tk.BooleanVar(value=st["walk"])
        self.jump = tk.BooleanVar(value=st["jump"])
        self.naps = tk.BooleanVar(value=st["naps"])
        self.anim = tk.BooleanVar(value=st["anim"])
        self.hide_fs = tk.BooleanVar(value=st["hide_fs"])
        self.one_monitor = tk.BooleanVar(value=st["one_monitor"])
        self.bubble_mode = tk.StringVar(value=st["bubble"])
        self.size_var = tk.DoubleVar(value=self.scale)
        self.pin_var = tk.BooleanVar(value=False)
        self.startup_var = tk.BooleanVar(value=startup_path().exists())

        # usage data
        self.inbox = queue.Queue()
        self.data, self.error, self.updated = None, None, None
        self.busy = False
        self.next_at = 0.0          # unix time of the next check. 0 = check right away.
        self.seen = {}              # key -> (percent, when it last changed, resets_at)
        self.last_5h = None

        # screens. x is the pet's centre and y its feet, both in screen pixels.
        self.screens = self.get_screens()
        self.fs = [False] * len(self.screens)
        self.size, self.half, self.top_margin, self.bubble_top = (1, 1), 60, 0, 0
        sx, sy = st["x"], st["y"]
        if sx is not None and sy is not None and self.find_screen(sx, sy - 1) is not None:
            self.si = self.find_screen(sx, sy - 1)
            self.x, self.y = sx, self.screens[self.si].wb
        else:
            self.si = self.find_screen(0, 0) or 0
            sc = self.screens[self.si]
            self.x, self.y = sc.wr - 160 * self.dpi, sc.wb
        self.screens_at = time.time()

        # what it's doing
        self.vy = 0.0
        self.dir = random.choice((-1, 1))
        self.state, self.state_t = "idle", 2.0    # idle, walk or sleep
        self.sleep_reason = None
        self.step, self.step_t = 0, 0.0
        self.blink_t, self.next_blink = 0.0, 3.0
        self.look_t, self.look_d = 0.0, 0         # glancing left or right while standing
        self.squash_t, self.pending_v = 0.0, 0.0  # crouch before a jump / squish after landing
        self.happy_t = self.wave_t = 0.0
        self.celebrate = 0                        # hops left to celebrate a reset
        self.parts, self.part_t = [], 0.0         # floating hearts and z's
        self.clock = 0.0
        self.held = self.moved = self.pressed = False
        self.hidden = False                       # hidden because something is full screen
        self.hovering, self.hover_since, self.leave_at, self.hover_until = False, None, None, 0.0
        self.geo, self.last_frame, self.rects = None, None, {}
        self.anim_job, self.last_t = None, time.perf_counter()
        self.saved_at = time.time()
        self.next_fs_check = self.next_slow_check = 0.0

        self.fader = Fader(self.root, 1.0, 1.0, self.place)
        self.details = Details(self)
        self.build_menu()
        c = self.canvas
        c.bind("<Button-1>", self.press)
        c.bind("<B1-Motion>", self.motion)
        c.bind("<ButtonRelease-1>", self.release)
        c.bind("<Button-3>", self.show_menu)
        self.root.bind_all("<Control-MouseWheel>", self.wheel)

        self.redraw()
        self.data_tick()
        self.ui_tick()
        if self.anim.get():
            self.start_anim()

    def build_menu(self):
        m = self.menu = tk.Menu(self.root, tearoff=0)
        m.add_command(label="Refresh now", command=self.refresh)
        m.add_checkbutton(label="Keep details open", variable=self.pin_var, command=self.pin_changed)
        m.add_separator()
        m.add_checkbutton(label="Walk around", variable=self.walk, command=self.changed)
        m.add_checkbutton(label="Jump now and then", variable=self.jump, command=self.changed)
        m.add_checkbutton(label="Take naps", variable=self.naps, command=self.naps_changed)
        m.add_checkbutton(label="Animations", variable=self.anim, command=self.anim_changed)
        sizes = tk.Menu(m, tearoff=0)
        for v in SIZES:
            sizes.add_radiobutton(label=f"{v:g}x", variable=self.size_var, value=v,
                                  command=lambda v=v: self.set_scale(v))
        m.add_cascade(label="Size", menu=sizes)
        bub = tk.Menu(m, tearoff=0)
        for val, label in (("both", "Both limits"), ("5h", "5-hour only"), ("hover", "Only when I hover")):
            bub.add_radiobutton(label=label, variable=self.bubble_mode, value=val, command=self.changed)
        m.add_cascade(label="Bubble", menu=bub)
        m.add_separator()
        m.add_checkbutton(label="Hide during full screen", variable=self.hide_fs, command=self.hide_fs_changed)
        m.add_checkbutton(label="Stay on one monitor", variable=self.one_monitor, command=self.changed)
        m.add_checkbutton(label="Start with Windows", variable=self.startup_var, command=self.startup_changed)
        m.add_separator()
        m.add_command(label="Quit", command=self.quit)

    def show_menu(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    # settings
    def s(self):
        return self.scale * self.dpi   # your size setting times windows' display scaling

    def save(self):
        save_settings({"scale": self.scale, "walk": self.walk.get(), "jump": self.jump.get(),
                       "naps": self.naps.get(), "anim": self.anim.get(), "bubble": self.bubble_mode.get(),
                       "hide_fs": self.hide_fs.get(), "one_monitor": self.one_monitor.get(),
                       "x": round(self.x), "y": round(self.y)})
        self.saved_at = time.time()

    def changed(self):
        self.redraw()
        self.save()

    def set_scale(self, v):
        self.scale = round(min(MAX_SCALE, max(MIN_SCALE, v)), 3)
        self.size_var.set(self.scale)
        self.redraw()
        if self.details.visible:
            self.details.draw()
        self.save()

    def wheel(self, e):
        self.set_scale(self.scale * (1.1 if e.delta > 0 else 1 / 1.1))

    def anim_changed(self):
        if self.anim.get():
            self.start_anim()
        else:
            if self.anim_job:
                self.root.after_cancel(self.anim_job)
                self.anim_job = None
            self.wake(hop=False)
            self.y, self.vy = self.screens[self.si].wb, 0.0   # land and stand still
            self.state, self.squash_t, self.pending_v, self.parts = "idle", 0.0, 0.0, []
            self.happy_t = self.wave_t = self.look_t = 0.0
            self.celebrate = 0
        self.changed()

    def naps_changed(self):
        if not self.naps.get():
            self.wake()
        self.changed()

    def hide_fs_changed(self):
        self.check_fullscreen()
        self.changed()

    def pin_changed(self):
        if self.pin_var.get():
            self.details.show(pinned=True)
        else:
            self.details.hide()

    def startup_changed(self):
        set_startup(self.startup_var.get())
        self.startup_var.set(startup_path().exists())   # show what really happened

    def quit(self):
        self.save()
        self.root.destroy()

    # screens
    def get_screens(self):
        try:
            found = list_screens()
        except OSError:
            found = []
        if not found:
            w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            found = [Screen(0, 0, w, h, 0, 0, w, h - 48)]
        return found

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

    def refresh_screens(self):
        new = self.get_screens()
        self.screens_at = time.time()
        if new == self.screens:
            return
        self.screens, self.fs = new, [False] * len(new)
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
        else:
            if not self.held:
                self.clamp_x()
            geo = (w, h, round(self.x - w / 2), round(self.y - h))
        if geo != self.geo:
            self.root.geometry("{}x{}+{}+{}".format(*geo))   # "+-50" = 50 left of the main screen
            self.geo = geo

    def set_hidden(self, hide):
        if hide == self.hidden:
            return
        self.hidden = hide
        if hide:
            self.held = self.pressed = False
            self.details.hide()
        self.fader.to(0.0 if hide else 1.0, instant=not self.anim.get())

    # mouse
    def press(self, e):
        self.moved, self.pressed = False, True
        self.press_at = (e.x_root, e.y_root)
        self.grab = (e.x_root - self.x, e.y_root - self.y)
        self.redraw()

    def motion(self, e):
        if not self.moved and abs(e.x_root - self.press_at[0]) + abs(e.y_root - self.press_at[1]) > 4:
            self.moved, self.held, self.pressed = True, True, False
            self.vy, self.squash_t, self.pending_v = 0.0, 0.0, 0.0
            self.wake(hop=False)
            self.details.hide()
        if self.held:
            self.x, self.y = e.x_root - self.grab[0], e.y_root - self.grab[1]
            i = self.floor_below(self.x, self.y)
            if i is not None:
                self.y = min(self.y, self.screens[i].wb)   # not into the taskbar
            self.redraw()

    def release(self, e):
        self.pressed = False
        if self.held:
            self.held, self.vy = False, 0.0
            i = self.floor_below(self.x, self.y)
            self.si = i if i is not None else self.nearest_screen(self.x, self.y)
            sc = self.screens[self.si]
            self.x = min(max(self.x, sc.wl + self.half), sc.wr - self.half)
            self.y = min(self.y, sc.wb) if self.anim.get() else sc.wb   # it falls from where you let go
            self.state, self.state_t = "idle", 2.0
            self.save()
        elif not self.moved:
            self.poke()
        self.redraw()

    def check_hover(self, now):
        mx, my = self.root.winfo_pointerxy()
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
            elif not d.visible and now - self.hover_since >= HOVER_DELAY:
                d.show()
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

    # reactions
    def greet(self):
        # you pointed at it: it wakes up, or stops and waves
        if not self.anim.get():
            return
        if self.state == "sleep":
            self.wake()
        else:
            self.wave_t = 1.1
            if self.state == "walk":
                self.state, self.state_t = "idle", 2.0

    def poke(self):
        # you clicked it: squish, hop, happy face and a heart
        if not self.anim.get():
            return
        self.wake()
        self.happy_t = 1.1
        self.spawn("heart")
        if self.grounded() and self.squash_t <= 0:
            self.jump_now(HOP_HEIGHT * 0.7 * self.s())
        if self.state == "walk":
            self.state, self.state_t = "idle", 1.5

    def fall_asleep(self, reason):
        self.state, self.sleep_reason = "sleep", reason
        self.state_t = random.uniform(20, 60) if reason == "nap" else 0
        self.part_t, self.wave_t, self.look_t = 0.4, 0.0, 0.0

    def wake(self, hop=True):
        if self.state != "sleep":
            return
        self.state, self.state_t, self.sleep_reason = "idle", 2.0, None
        self.parts = [p for p in self.parts if p["kind"] == "heart"]
        if hop:
            self.jump_now(HOP_HEIGHT * 0.5 * self.s())

    def check_away(self):
        if not (self.anim.get() and self.naps.get()) or self.hidden:
            return
        away = idle_seconds()
        if self.state == "sleep":
            if self.sleep_reason == "away" and away < 2:
                self.wake()          # you're back
                self.wave_t = 1.4
        elif away >= SLEEP_AFTER_MIN * 60 and self.grounded() and not self.held and not self.details.visible:
            self.fall_asleep("away")

    def check_fullscreen(self):
        if self.hide_fs.get():
            try:
                self.fs = fullscreen_screens(self.screens)
            except OSError:
                self.fs = [False] * len(self.screens)
        else:
            self.fs = [False] * len(self.screens)
        self.set_hidden(self.fs[self.si])

    def spawn(self, kind):
        s = self.s()
        bw, bh = max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s))
        if kind == "heart":   # pops out just above the bubble so it never covers the numbers
            pb = max(1, round(2 * s))
            self.parts.append({"kind": "heart", "x": (18 * bw - 7 * pb) / 2 + random.uniform(-2, 2) * bw,
                               "y": self.bubble_top - 7 * pb, "vx": random.uniform(-10, 10) * s,
                               "vy": -30 * s, "life": 0.8})
        else:
            big = sum(p["kind"] == "Z" for p in self.parts) <= sum(p["kind"] == "z" for p in self.parts)
            pb = max(1, round(2 * s))
            self.parts.append({"kind": "Z" if big else "z", "x": 15 * bw, "y": bh - 4 * pb,
                               "vx": random.uniform(5, 9) * s, "vy": -20 * s, "life": 2.4})

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
                if r["key"] == "five_hour":
                    if self.last_5h is not None and self.last_5h >= 15 and r["pct"] <= self.last_5h - 15:
                        self.celebrate = 3    # the 5-hour limit just reset. party.
                    self.last_5h = r["pct"]
            self.next_at = now + POLL_SECONDS
        else:
            self.error = err
            self.next_at = now + (RATE_LIMITED_SECONDS if "rate limited" in err else POLL_SECONDS)

    def data_tick(self):
        self.take_result()
        now = time.time()
        if not self.busy and now >= self.next_at:
            self.refresh()
        if now - self.saved_at >= 60:
            self.save()
        if self.details.visible:
            self.details.draw()
        self.root.after(1000, self.data_tick)

    def ui_tick(self):
        # 10 times a second: hover. twice a second: full screen. every second: are you away.
        now = time.time()
        self.check_hover(now)
        if now >= self.next_fs_check:
            self.next_fs_check = now + 0.5
            self.check_fullscreen()
        if now >= self.next_slow_check:
            self.next_slow_check = now + 1
            self.check_away()
            if now - self.screens_at >= 5:
                self.refresh_screens()
        self.redraw()
        self.root.after(100, self.ui_tick)

    def shown_rows(self):
        rows = parse_rows(self.data) if self.data else []
        by_key = {r["key"]: r for r in rows}
        return [by_key[k] for k in ("five_hour", "seven_day") if k in by_key] or rows[:2]

    def bubble_segments(self):
        picks = self.shown_rows()
        if self.bubble_mode.get() == "5h":
            picks = picks[:1]
        segs = [(f"{SHORT.get(r['key'], r['label'])} {r['pct']:.0f}%", bar_color(r["pct"])) for r in picks]
        if self.error:
            segs.append(("!" if segs else short_error(self.error), RED))
        return segs or [("...", DIM)]

    def sweaty(self):
        return any(r["pct"] >= SWEAT_AT for r in self.shown_rows())

    # movement
    def walking_allowed(self):
        return self.walk.get() and not self.details.visible and not self.hidden

    def grounded(self):
        return self.vy >= 0 and self.y >= self.screens[self.si].wb - 0.5

    def jump_now(self, height):
        # crouch for a moment, then jump high enough to rise `height` pixels
        if not self.anim.get():
            return
        self.squash_t = 0.08
        self.pending_v = math.sqrt(2 * GRAVITY * self.s() * height)

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

    def anim_tick(self):
        now = time.perf_counter()
        dt, self.last_t = min(0.05, now - self.last_t), now
        self.physics(dt)
        self.redraw()
        self.anim_job = self.root.after(self.frame_ms(), self.anim_tick)

    def frame_ms(self):
        # fast while moving, slower while standing around, very slow while hidden
        if self.hidden:
            return 500
        if (self.held or self.pressed or self.squash_t > 0 or not self.grounded()
                or (self.state == "walk" and self.walking_allowed())):
            return 15
        if self.parts or self.wave_t > 0:
            return 30
        return 80

    def physics(self, dt):
        s = self.s()
        self.clock += dt
        self.happy_t -= dt
        self.wave_t -= dt
        self.look_t -= dt
        if self.state != "sleep":
            self.next_blink -= dt
            if self.next_blink <= 0:
                self.blink_t, self.next_blink = 0.15, random.uniform(2.5, 6)
            self.blink_t -= dt
        for p in self.parts:
            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
        self.parts = [p for p in self.parts if p["life"] > 0]
        if self.held or self.hidden or self.pressed:
            return
        if self.squash_t > 0:   # crouching or squished: hold still for a moment
            self.squash_t -= dt
            if self.squash_t <= 0 and self.pending_v:
                self.vy, self.pending_v = -self.pending_v, 0.0
            return
        walking = self.state == "walk" and self.walking_allowed()
        if not self.grounded():   # in the air: a proper curve, the same whatever the frame rate
            g = GRAVITY * s
            self.y += self.vy * dt + 0.5 * g * dt * dt
            self.vy += g * dt
            if walking:
                self.move_x(self.dir * WALK_SPEED * s * dt)
            floor = self.screens[self.si].wb
            if self.y >= floor:
                if self.vy > 350 * s:
                    self.squash_t = 0.07   # landing squish
                self.y, self.vy = floor, 0.0
            return
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
        self.state_t -= dt
        if walking:
            self.move_x(self.dir * WALK_SPEED * s * dt)
            self.step_t += dt
            if self.step_t >= 0.18:
                self.step_t, self.step = 0.0, self.step + 1
        if self.jump.get() and random.random() < dt / JUMP_EVERY:
            self.jump_now(HOP_HEIGHT * s)
        if self.state_t <= 0:
            if self.state == "walk" or not self.walking_allowed():
                if self.naps.get() and random.random() < NAP_CHANCE and not self.details.visible:
                    self.fall_asleep("nap")
                else:
                    self.state, self.state_t = "idle", random.uniform(3, 8)
            else:
                self.state, self.state_t = "walk", random.uniform(2, 5)
                self.dir = random.choice((-1, 1))
        if self.state == "idle" and self.look_t <= 0 and random.random() < dt / 4:
            self.look_d, self.look_t = random.choice((-1, 1)), random.uniform(0.6, 1.4)

    # drawing. only redraws when something visible changed; moving is just moving the window.
    def frame(self):
        anim = self.anim.get()
        grounded = self.grounded()
        airborne = self.held or not grounded
        sleeping = anim and self.state == "sleep"
        squash = anim and grounded and not self.held and (self.squash_t > 0 or self.pressed)
        walking = anim and self.state == "walk" and self.walking_allowed() and grounded and not squash
        if sleeping:
            legs = ()
        elif self.held:
            legs = LEGS_STEP if int(self.clock / 0.12) % 2 else LEGS_AIR   # wiggling
        elif airborne:
            legs = LEGS_AIR
        else:
            legs = LEGS_STEP if walking and self.step % 2 else LEGS_STAND
        if sleeping:
            eyes = "closed"
        elif anim and self.happy_t > 0:
            eyes = "happy"
        elif anim and self.blink_t > 0:
            eyes = "closed"
        else:
            eyes = "open"
        eye_dir = self.dir if walking else (self.look_d if anim and self.look_t > 0 and not sleeping else 0)
        breath = sleeping and int(self.clock / 1.4) % 2 == 1
        arm = (int(self.wave_t / 0.18) % 2 + 1) if anim and self.wave_t > 0 and not sleeping else 0
        sweat = 0
        if self.sweaty() and not sleeping:
            sweat = 1 + (int(self.clock / 0.5) % 2 if anim else 0)
        parts = tuple((p["kind"], round(p["x"]), round(p["y"])) for p in self.parts) if anim else ()
        show = (self.bubble_mode.get() != "hover" or self.hovering or self.held
                or self.details.visible or time.time() < self.hover_until)
        return (self.scale, legs, eyes, eye_dir, squash, sleeping, breath, arm, sweat, parts,
                tuple(self.bubble_segments()), show)

    def redraw(self):
        f = self.frame()
        if f != self.last_frame:
            self.draw(f)
            self.last_frame = f
        self.place()

    def font(self, px):
        if px not in self.fonts:
            self.fonts[px] = tkfont.Font(root=self.root, family="Segoe UI", size=-px, weight="bold")
        return self.fonts[px]

    def glyph(self, rows, x, y, b, color):
        # a little picture made of b-sized squares, with a dark shadow so it shows on any wallpaper
        sh = max(1, b // 2)
        for d, col in ((sh, SHADOW), (0, color)):
            for r, line in enumerate(rows):
                for i, ch in enumerate(line):
                    if ch == "#":
                        self.canvas.create_rectangle(x + i * b + d, y + r * b + d, x + (i + 1) * b + d,
                                                     y + (r + 1) * b + d, fill=col, outline="")

    def draw(self, f):
        _, legs, eyes, eye_dir, squash, lying, breath, arm, sweat, parts, segs, show_bubble = f
        c = self.canvas
        c.delete("all")
        s = self.s()
        bw, bh = max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s))
        pb = max(1, round(2 * s))     # small blocks for hearts, z's and sweat
        pet_w, pet_h = 18 * bw, 5 * bh
        font = self.font(max(8, round(11 * s)))
        pad, dot, dgap, sgap = round(7 * s), max(4, round(6 * s)), round(4 * s), round(9 * s)
        bub_w = 2 * pad + sum(dot + dgap + font.measure(t) for t, _ in segs) + sgap * (len(segs) - 1)
        bub_h = font.metrics("linespace") + round(6 * s)
        tail, gap = max(2, round(4 * s)), round(2 * s)
        side, top = round(22 * s), round(40 * s)   # room around it for hearts and z's
        W = max(pet_w + 2 * side, bub_w) + 2
        H = top + bub_h + tail + gap + pet_h
        px, py = (W - pet_w) // 2, H - pet_h
        sink = bh if lying else bh // 2 if squash else 0   # lying down or squished

        def block(col, row, cols=1, color=ORANGE):
            y1 = py + row * bh + sink
            c.create_rectangle(px + col * bw, y1, px + (col + cols) * bw, min(y1 + bh, H), fill=color, outline="")

        # the mascot, standing on the bottom edge of the window
        for row, line in enumerate(BODY):
            start, end = line.index("#"), line.rindex("#") + 1
            if row == 0 and breath:
                start, end = start + 1, end - 1   # breathing out while asleep
            block(start, row, end - start)
        arms = (ARMS[0],) + WAVE[arm - 1] if arm else ARMS
        for col, row in arms:
            block(col, row)
        for col in legs:
            block(col, 4)
        for col in EYES:
            x1, y1 = px + (col + eye_dir) * bw, py + bh + sink
            if eyes == "open":
                c.create_rectangle(x1, y1, x1 + bw, y1 + bh, fill=EYE, outline="")
            else:   # a thin line: low for closed, high for a happy squint
                ly = y1 + (bh // 5 if eyes == "happy" else bh // 2)
                c.create_rectangle(x1, ly, x1 + bw, ly + max(1, bh // 4), fill=EYE, outline="")
        if eyes == "happy":
            for col in BLUSH:
                block(col, 2, color=BLUSH_C)
        if sweat:
            self.glyph(SWEAT, px - 3 * pb - max(1, bw // 2), py + sink + (pb if sweat == 2 else 0), pb, SWEAT_C)

        # z's drift up behind the bubble, so they never cover the numbers
        for kind, x, y in parts:
            if kind != "heart":
                self.glyph(ZZZ, px + x, py + y, pb + (pb // 2 + 1 if kind == "Z" else 0), ZZZ_C)

        # the bubble. text only ever sits on the solid bubble, so there's no fuzzy edge
        # against the see-through colour.
        bx = (W - bub_w) // 2
        if show_bubble:
            round_rect(c, bx, top, bx + bub_w, top + bub_h, round(5 * s), BUBBLE)
            mid = W // 2
            c.create_polygon(mid - tail, top + bub_h - 1, mid + tail, top + bub_h - 1, mid, top + bub_h + tail,
                             fill=BUBBLE, outline="")
            x, ym = bx + pad, top + bub_h // 2
            for i, (text, color) in enumerate(segs):
                if i:
                    x += sgap
                c.create_oval(x, ym - dot // 2, x + dot, ym - dot // 2 + dot, fill=color, outline="")
                x += dot + dgap
                c.create_text(x, ym, anchor="w", text=text, fill=BUBBLE_TEXT, font=font)
                x += font.measure(text)

        # hearts pop up in front of everything
        for kind, x, y in parts:
            if kind == "heart":
                self.glyph(HEART, px + x, py + y, pb, HEART_C)

        c.configure(width=W, height=H)
        self.size, self.half, self.top_margin = (W, H), max(pet_w, bub_w) / 2 + 2, top
        self.bubble_top = (top if show_bubble else py) - py   # relative to the head, for hearts
        self.rects = {"pet": (px, py, px + pet_w, py + pet_h),
                      "bubble": (bx, top, bx + bub_w, top + bub_h + tail) if show_bubble else None}


# ---- details panel (hover the mascot) ----

PANEL_W = 270


class Details:
    BG, FG, DIM, TRACK = "#1c1c1e", "#f2f2f7", "#8e8e93", "#3a3a3c"
    FASTC, SLOWC = "#d9a441", "#5ea1ff"

    def __init__(self, pet):
        self.pet = pet
        self.win = tk.Toplevel(pet.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        self.win.configure(bg=self.BG)
        self.win.geometry(f"10x10+{PARK}+{PARK}")   # starts parked off screen
        self.canvas = tk.Canvas(self.win, bg=self.BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonRelease-1>", self.click)
        self.canvas.bind("<Button-3>", pet.show_menu)
        self.visible = self.pinned = self.rounded = False
        self.hits, self.rect, self.px_size = [], None, (10, 10)
        self.anchor_x = self.anchor_bottom = 0
        self.fader = Fader(self.win, 0.0, 1.0, self.place)

    def show(self, pinned=False):
        p = self.pet
        self.pinned = self.pinned or pinned
        p.pin_var.set(self.pinned)
        if self.visible:
            return
        self.visible = True
        self.anchor_x = p.x   # opens just above the bubble
        self.anchor_bottom = (p.geo[3] if p.geo else p.screens[p.si].wb) + p.top_margin - round(6 * p.dpi)
        self.draw()
        if not self.rounded:
            round_corners(self.win)
            self.rounded = True
        self.fader.to(1.0, instant=not p.anim.get())

    def hide(self):
        if not self.visible:
            return
        self.visible = self.pinned = False
        self.pet.pin_var.set(False)
        self.fader.to(0.0, instant=not self.pet.anim.get())

    def place(self):
        p = self.pet
        if not self.visible and self.fader.alpha <= 0.001:
            self.win.geometry(f"+{PARK}+{PARK}")
            self.rect = None
            return
        pw, ph = self.px_size
        sc = p.screens[p.si]
        x = min(max(sc.wl + 4, round(self.anchor_x - pw / 2)), sc.wr - pw - 4)
        y = max(sc.wt + 4, self.anchor_bottom - ph)
        self.rect = (x, y, x + pw, y + ph)
        y += round((1 - self.fader.alpha) * 10 * p.dpi)   # slides up a little as it fades in
        self.win.geometry(f"{pw}x{ph}+{x}+{y}")

    def click(self, e):
        for name, x1, y1, x2, y2 in self.hits:
            if name == "close" and x1 <= e.x <= x2 and y1 <= e.y <= y2:
                self.hide()
                return

    def text(self, x, y, text, fill, size, bold=False, anchor="nw", width=None):
        s = self.s
        kw = {"width": width * s} if width else {}
        font = ("Segoe UI", -max(8, round(size * 4 / 3 * s)), "bold" if bold else "normal")
        self.canvas.create_text(x * s, y * s, anchor=anchor, fill=fill, font=font, text=text, **kw)

    def rect_(self, x1, y1, x2, y2, fill):
        s = self.s
        self.canvas.create_rectangle(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=0)

    def line(self, x1, y1, x2, y2, fill, width=1):
        s = self.s
        self.canvas.create_line(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=max(1, round(width * s)))

    def draw(self):
        p = self.pet
        self.s = s = p.dpi * min(1.6, max(1.0, p.scale))
        c = self.canvas
        c.delete("all")
        rows = parse_rows(p.data) if p.data else []
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = time.time()
        W = PANEL_W
        self.text(12, 10, "CLAUDE USAGE", self.DIM, 8)
        self.text(W - 15, 7, "×", self.DIM, 11, True, "n")      # close button
        self.hits = [("close", (W - 28) * s, 2 * s, (W - 2) * s, 26 * s)]
        if p.updated:
            self.text(W - 12, 26, f"updated {p.updated:%H:%M}", self.DIM, 8, anchor="ne")
        wait = "updating..." if p.busy else f"next update in {max(0, math.ceil(p.next_at - now))}s"
        self.text(W - 12, 40, wait, self.DIM, 8, anchor="ne")
        y = 58
        for r in rows:
            seen = p.seen.get(r["key"])
            unchanged = now - seen[1] if seen else 0
            el, msg, kind = pace_info(r["key"], r["pct"], r["resets"], now_dt, unchanged)
            self.text(12, y, r["label"], self.FG, 9, True)
            self.text(W - 12, y, f"{r['pct']:.0f}%", self.FG, 9, True, "ne")
            self.rect_(12, y + 20, W - 12, y + 26, self.TRACK)
            self.rect_(12, y + 20, 12 + (W - 24) * min(r["pct"], 100) / 100, y + 26, bar_color(r["pct"]))
            if el is not None:   # the pace tick: where the clock is in this window
                tx = 12 + (W - 24) * el / 100
                self.line(tx, y + 16, tx, y + 30, self.FG, 2)
            self.text(12, y + 32, reset_text(r["resets"], now_dt), self.DIM, 8)
            h = 54
            if msg:
                self.text(12, y + 46, msg, self.FASTC if kind == "fast" else self.SLOWC, 8, True, width=W - 24)
                h = 68
            y += h
        if p.error:
            self.text(12, y, p.error, RED, 8, width=W - 24)
            y += 30
        elif not rows:
            self.text(12, y, "loading...", self.DIM, 8)
            y += 20
        H = y + 12
        self.px_size = (round(W * s), round(H * s))
        c.configure(width=self.px_size[0], height=self.px_size[1])
        self.place()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--startup", action="store_true", help="start the pet when you sign in to windows")
    ap.add_argument("--no-startup", action="store_true", help="stop starting with windows")
    a = ap.parse_args()
    if a.startup or a.no_startup:
        print(set_startup(a.startup))
        sys.exit(0)
    if already_running():
        sys.exit(0)
    Pet().root.mainloop()
