# windows bits through ctypes: screens, windows, idle time, notifications, shortcuts, startup.
import ctypes
import os
import shutil
import subprocess
import sys
import threading
from collections import namedtuple
from ctypes import wintypes
from pathlib import Path

from .config import HERE, SHORTCUTS, STARTUP_NAME
from .storage import log_error


# ---- windows bits (ctypes is part of python, no installs) ----

u32 = ctypes.WinDLL("user32", use_last_error=True)
k32 = ctypes.WinDLL("kernel32", use_last_error=True)


class MEMINFO(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]


def own_usage():
    # (seconds of cpu time used so far, megabytes of memory in use) for this program
    k32.GetCurrentProcess.restype = ctypes.c_void_p
    me = ctypes.c_void_p(k32.GetCurrentProcess())   # (a full-size handle, not a 32-bit number)
    times = [wintypes.FILETIME() for _ in range(4)]
    cpu = 0.0
    if k32.GetProcessTimes(me, *[ctypes.byref(x) for x in times]):
        cpu = sum((x.dwHighDateTime << 32 | x.dwLowDateTime) for x in times[2:]) / 1e7   # kernel + user
    mem = MEMINFO()
    mem.cb = ctypes.sizeof(mem)
    ok = k32.K32GetProcessMemoryInfo(me, ctypes.byref(mem), mem.cb)
    return cpu, (mem.WorkingSetSize / 2 ** 20 if ok else 0.0)
try:
    winmm = ctypes.WinDLL("winmm")   # for a finer timer while the mascot is moving
except OSError:
    winmm = None
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
u32.GetAsyncKeyState.restype = ctypes.c_short
u32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
k32.GetTickCount.restype = wintypes.DWORD

# a screen: its full rectangle (m...) and the part not covered by the taskbar (w...).
# the bottom of the work part (wb) is the floor the pet stands on.
Screen = namedtuple("Screen", "ml mt mr mb wl wt wr wb dpi", defaults=(1.0,))   # dpi: 1.0 = 100% scaling

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
            dx, dy = wintypes.UINT(96), wintypes.UINT(96)
            try:   # this monitor's own display scaling (windows 8.1 and newer)
                ctypes.windll.shcore.GetDpiForMonitor(hmon, 0, ctypes.byref(dx), ctypes.byref(dy))
            except (AttributeError, OSError):
                pass
            found.append(Screen(m.left, m.top, m.right, m.bottom, w.left, w.top, w.right, w.bottom,
                                (dx.value or 96) / 96))
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


def window_box(hwnd):
    # a window's visible edges (windows adds invisible borders, so ask the compositor first)
    r = wintypes.RECT()
    if dwm is not None and dwm.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(r), ctypes.sizeof(r)) == 0:
        return r.left, r.top, r.right, r.bottom
    if u32.GetWindowRect(hwnd, ctypes.byref(r)):
        return r.left, r.top, r.right, r.bottom
    return None


def list_platforms():
    # normal app windows, front to back, as (id, left, top, right, bottom): their top edges are ledges
    found, me = [], os.getpid()

    def cb(hwnd, lp):
        try:
            # maximized windows stay in the list: they're never ledges (their top is the screen top),
            # but they still count as walls that shove the pet off a window behind them
            if not u32.IsWindowVisible(hwnd) or u32.IsIconic(hwnd):
                return True
            pid = wintypes.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value == me or u32.GetWindowLongW(hwnd, -20) & (WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW):
                return True
            name = ctypes.create_unicode_buffer(64)
            u32.GetClassNameW(hwnd, name, 64)
            if name.value in NOT_APPS or is_cloaked(hwnd):
                return True
            box = window_box(hwnd)
            if box and box[2] - box[0] >= 150 and box[3] - box[1] >= 100:
                found.append((int(hwnd or 0),) + box)
        except Exception:
            pass
        return True

    u32.EnumWindows(WNDENUMPROC(cb), 0)
    return found


def idle_seconds():
    # how long since you last touched the mouse or keyboard
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(lii)
    if not u32.GetLastInputInfo(ctypes.byref(lii)):
        return 0.0
    return ((k32.GetTickCount() - lii.dwTime) & 0xFFFFFFFF) / 1000


def notify(title, body):
    # a windows notification in the corner of the screen, sent through powershell (no installs needed)
    esc = lambda s_: (s_.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                      .replace('"', "&quot;").replace("'", "''"))
    ps = ("[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
          "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null;"
          "$x = New-Object Windows.Data.Xml.Dom.XmlDocument;"
          f"$x.LoadXml('<toast><visual><binding template=\"ToastGeneric\"><text>{esc(title)}</text>"
          f"<text>{esc(body)}</text></binding></visual></toast>');"
          "$t = New-Object Windows.UI.Notifications.ToastNotification $x;"
          "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
          "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe').Show($t)")

    def run():
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=20,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:
            log_error("showing a notification")

    threading.Thread(target=run, daemon=True).start()


def hotkey_thread(inbox, wanted):
    # listens for the shortcuts anywhere in windows. needs its own thread with a message loop.
    # wanted() gives the shortcuts to use right now; a WM_APP message means "they changed, register again".
    u = ctypes.WinDLL("user32", use_last_error=True)
    msg = wintypes.MSG()
    u.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)   # makes this thread's message queue
    inbox.put(("thread", k32.GetCurrentThreadId()))

    def register():
        got = {}
        for i, (name, _, _) in enumerate(SHORTCUTS, 1):
            u.UnregisterHotKey(None, i)
            combo = wanted().get(name)
            if combo:
                got[name] = bool(u.RegisterHotKey(None, i, combo[0] | 0x4000, combo[1]))   # 0x4000: no repeats
        inbox.put(("registered", got))

    register()
    while u.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        if msg.message == 0x0312:   # WM_HOTKEY
            inbox.put(("hotkey", msg.wParam))
        elif msg.message == 0x8001:   # WM_APP + 1: the shortcuts changed
            register()


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
    # the pyw launcher always picks the newest python, so the shortcut survives python updates.
    # without it, point at this python's own pythonw (breaks when that python is removed)
    launcher = shutil.which("pyw")
    exe = Path(sys.executable)
    pyw = exe.with_name("pythonw.exe")
    target = launcher or (pyw if pyw.exists() else exe)
    script = HERE / "claude_pet.py"   # the file you start
    q = lambda p: str(p).replace("'", "''")   # powershell quoting
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
          "$s.TargetPath='{t}';$s.Arguments='\"{sc}\"';$s.WorkingDirectory='{d}';$s.Save()"
          ).format(lnk=q(lnk), t=q(target), sc=q(script), d=q(script.parent))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return "added to startup." if r.returncode == 0 else f"could not add it: {r.stderr.strip()}"
