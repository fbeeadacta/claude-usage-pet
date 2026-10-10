# the tray icon: a little mascot by the clock, with your usage in its tooltip. click it to call the mascot over.
import ctypes
import queue
import threading
from ctypes import wintypes

from .art import EYE, ORANGE
from .storage import log_error
from .usage import bar_color
from .winapi import u32


LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
CALLBACK = 0x8000 + 2      # WM_APP + 2: what the tray sends us for clicks
NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
NIF_MESSAGE, NIF_ICON, NIF_TIP = 1, 2, 4


class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", wintypes.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HBRUSH), ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT), ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON),
                ("szTip", ctypes.c_wchar * 128), ("dwState", wintypes.DWORD), ("dwStateMask", wintypes.DWORD),
                ("szInfo", ctypes.c_wchar * 256), ("uVersion", wintypes.UINT), ("szInfoTitle", ctypes.c_wchar * 64),
                ("dwInfoFlags", wintypes.DWORD), ("guidItem", ctypes.c_byte * 16), ("hBalloonIcon", wintypes.HICON)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]


class ICONINFO(ctypes.Structure):
    _fields_ = [("fIcon", wintypes.BOOL), ("xHotspot", wintypes.DWORD), ("yHotspot", wintypes.DWORD),
                ("hbmMask", wintypes.HBITMAP), ("hbmColor", wintypes.HBITMAP)]


u32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
u32.DefWindowProcW.restype = LRESULT
u32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HMENU,
                                wintypes.HINSTANCE, wintypes.LPVOID]
u32.CreateWindowExW.restype = wintypes.HWND
u32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
u32.CreateIconIndirect.argtypes = [ctypes.POINTER(ICONINFO)]
u32.CreateIconIndirect.restype = wintypes.HICON
u32.DestroyIcon.argtypes = [wintypes.HICON]
u32.RegisterWindowMessageW.restype = wintypes.UINT
gdi = ctypes.WinDLL("gdi32")
gdi.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT, ctypes.POINTER(ctypes.c_void_p),
                                 wintypes.HANDLE, wintypes.DWORD]
gdi.CreateDIBSection.restype = wintypes.HBITMAP
gdi.CreateBitmap.restype = wintypes.HBITMAP
gdi.DeleteObject.argtypes = [wintypes.HANDLE]
shell = ctypes.WinDLL("shell32")
k32 = ctypes.WinDLL("kernel32")
k32.GetModuleHandleW.restype = wintypes.HMODULE
shell.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]

# the mascot in 16x16: o = orange, e = eye, and a usage dot (u) in the corner
ICON = ["................",
        "................",
        "..############..",
        "..############..",
        "..##e######e##..",
        "..##e######e##..",
        ".##############.",
        ".##############.",
        "..############..",
        "..############..",
        "...#.#....#.#...",
        "...#.#....#.#.uu",
        "..............uu",
        "................",
        "................",
        "................"]


def make_icon(dot):
    # draws ICON at 32x32 (windows scales it to the tray's size) and turns it into a windows icon
    size, k = 32, 2
    colours = {"#": ORANGE, "e": EYE, "u": dot}
    bmi = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), size, -size, 1, 32, 0, 0, 0, 0, 0, 0)   # top-down
    bits = ctypes.c_void_p()
    color = gdi.CreateDIBSection(None, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
    px = (ctypes.c_uint32 * (size * size)).from_address(bits.value)
    for y in range(size):
        for x in range(size):
            ch = ICON[y // k][x // k]
            if ch == "u" and not dot:
                ch = "."
            if ch == ".":
                px[y * size + x] = 0
            else:
                c = colours[ch]
                px[y * size + x] = 0xFF000000 | int(c[1:3], 16) << 16 | int(c[3:5], 16) << 8 | int(c[5:7], 16)
    mask = gdi.CreateBitmap(size, size, 1, 1, None)
    info = ICONINFO(True, 0, 0, mask, color)
    icon = u32.CreateIconIndirect(ctypes.byref(info))
    gdi.DeleteObject(mask)
    gdi.DeleteObject(color)
    return icon


class Tray:
    # its own thread with a hidden window, because the tray talks to us through window messages.
    # clicks come back to the pet through self.events (read 10 times a second).
    def __init__(self):
        self.events = queue.Queue()
        self.hwnd, self.shown, self.tip, self.dot = None, False, "Claude usage pet", None
        self.icon = None
        self.ready = threading.Event()
        self.lock = threading.Lock()
        threading.Thread(target=self.run, daemon=True).start()
        self.ready.wait(3)

    def run(self):
        try:
            self.proc = WNDPROC(self.wndproc)   # (kept on self, so python doesn't throw it away)
            inst = k32.GetModuleHandleW(None)
            wc = WNDCLASSW(0, self.proc, 0, 0, inst, None, None, None, None, "ClaudeUsagePetTray")
            u32.RegisterClassW(ctypes.byref(wc))
            self.restart_msg = u32.RegisterWindowMessageW("TaskbarCreated")   # explorer restarted
            self.hwnd = u32.CreateWindowExW(0, "ClaudeUsagePetTray", "Claude usage pet", 0, 0, 0, 0, 0,
                                            None, None, inst, None)
        except Exception:
            log_error("making the tray icon")
        self.ready.set()
        msg = wintypes.MSG()
        while self.hwnd and u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            u32.TranslateMessage(ctypes.byref(msg))
            u32.DispatchMessageW(ctypes.byref(msg))

    def wndproc(self, hwnd, msg, wp, lp):
        if msg == CALLBACK:
            what = {0x0202: "left", 0x0205: "right"}.get(lp & 0xFFFF)   # button up
            if what:
                self.events.put(what)
            return 0
        if msg == getattr(self, "restart_msg", None) and self.shown:
            self.shown = False   # the taskbar was rebuilt: put the icon back
            self.show()
            return 0
        return u32.DefWindowProcW(hwnd, msg, wp, lp)

    def data(self, flags):
        d = NOTIFYICONDATAW()
        d.cbSize, d.hWnd, d.uID, d.uFlags = ctypes.sizeof(d), self.hwnd, 1, flags
        d.uCallbackMessage, d.hIcon, d.szTip = CALLBACK, self.icon, self.tip[:127]
        return d

    def show(self):
        if not self.hwnd:
            return
        with self.lock:
            if self.icon is None:
                self.icon = make_icon(self.dot)
            d = self.data(NIF_MESSAGE | NIF_ICON | NIF_TIP)
            ok = self.shown and shell.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(d))
            self.shown = bool(ok or shell.Shell_NotifyIconW(NIM_ADD, ctypes.byref(d)))   # (re-adds it if it went)

    def hide(self):
        if self.hwnd and self.shown:
            with self.lock:
                shell.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self.data(0)))
                self.shown = False

    def update(self, tip, pct):
        # new tooltip text, and the corner dot in the usage colour (none before the first numbers)
        dot = bar_color(pct) if pct is not None else None
        if tip == self.tip and dot == self.dot:
            return
        self.tip, old = tip, None
        if dot != self.dot:
            self.dot = dot
            with self.lock:
                old, self.icon = self.icon, make_icon(dot)
        if self.shown:
            self.show()
        if old:
            u32.DestroyIcon(old)
