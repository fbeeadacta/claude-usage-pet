# settings you can tweak: speeds, timings, limits, personalities, file locations, shortcut keys.
import os
from pathlib import Path


# ---- settings ----
DEFAULT_SCALE = 1.0        # starting size. after that the size you pick in the menu is remembered.
SIZES = [0.75, 1.0, 1.25, 1.5, 2.0, 3.0]   # choices in the right-click size menu
MIN_SCALE, MAX_SCALE = 0.5, 4.0            # limits for ctrl + mouse wheel
POLL_SECONDS = 120         # how often to ask the api
ONLY_KNOWN_LIMITS = True   # show only the 5-hour and weekly limits. False shows everything the api lists.
RATE_LIMITED_SECONDS = 180 # wait at least this long after the api says "slow down" (longer if it repeats)
USER_AGENT = "usage-widget/0.1"
# how it moves (pixels are at 1x size)
WALK_SPEED = 28            # pixels per second
JUMP_EVERY = 30            # on average one hop every this many seconds
HOP_HEIGHT = 34            # pixels
LEAP_EVERY = 25            # on average, looks for another window to jump to this often (seconds)
LEAP_POWER = 300           # how high its legs can really take it (pixels). it sometimes thinks more.
LEAP_REACH = 520           # how far sideways a window can be before it won't bother
TASKBAR_PUSH = False       # windows pushing it while it's on the taskbar (off for now: maximized and
                           # snapped windows shoved it about when they shouldn't)
DIVE_MIN = 150             # the leap of faith needs at least this much drop below a window's edge
HAY_TIME = 1.3             # seconds it sits in the hay pile before popping out
# personalities (menu: personality). keep = chance it keeps walking when a walk ends, idle / walk_t = how
# long it stands about / walks (seconds), speed = walking speed, hop / leap = average seconds between random
# hops / jumps to another window, nap = nap chance multiplier. at a window's edge: edge_leap = chance it looks
# for another window to jump to, dive = chance of a leap of faith, turn = chance it turns around (else walks off).
PROFILES = {
    "parkour": {"keep": 0.6, "idle": (0.5, 2.5), "walk_t": (3, 7), "speed": 1.7, "hop": 10, "leap": 6,
                "nap": 0.1, "edge_leap": 0.9, "dive": 0.8, "turn": 0.2},
    "lively": {"keep": 0.4, "idle": (1.5, 4.5), "walk_t": (3, 6), "speed": 1.3, "hop": 18, "leap": 12,
               "nap": 0.3, "edge_leap": 0.7, "dive": 0.5, "turn": 0.4},
    "normal": {"keep": 0.0, "idle": (3, 8), "walk_t": (2, 5), "speed": 1.0, "hop": JUMP_EVERY, "leap": LEAP_EVERY,
               "nap": 1.0, "edge_leap": 0.3, "dive": 0.15, "turn": 0.5},
    "chill": {"keep": 0.0, "idle": (8, 18), "walk_t": (1.5, 3.5), "speed": 0.75, "hop": 60, "leap": 90,
              "nap": 2.0, "edge_leap": 0.1, "dive": 0.0, "turn": 0.8},
    "statue": {"keep": 0.0, "idle": (5, 10), "walk_t": (2, 5), "speed": 1.0, "hop": 10 ** 9, "leap": 10 ** 9,
               "nap": 1.0, "edge_leap": 0.0, "dive": 0.0, "turn": 1.0},
}
PROFILE_NAMES = (("parkour", "Parkour!"), ("lively", "Lively"), ("normal", "Normal"), ("chill", "Chill"),
                 ("statue", "Statue"))
GRAVITY = 1150             # pixels per second per second
FPS = 60                   # frames a second while it moves (falls back to slower frames when idle)
MAX_STEP_UP = 400          # tallest ledge (onto a higher monitor) it will jump up
# moods
SLEEP_AFTER_MIN = 5        # falls asleep when you've been away from the computer this long
NAP_CHANCE = 0.06          # chance of a short nap whenever it stops walking
WARN_AT = 80               # yellow ring around the bubble when a limit is at or above this %
PANIC_AT = 90              # ...red ring from here. both can be changed in the menu (warning levels).
WARN_CHOICES = (70, 75, 80, 85)
PANIC_CHOICES = (85, 90, 95)
HOVER_DELAY = 0.3          # seconds of hovering before the details panel shows
FADE_SECONDS = 0.18        # how long the details panel takes to fade in or out
# working and talking
CC_SCAN_SECONDS = 3        # how often to look at claude code's logs for new activity
WORK_HOLD = 20             # keeps casting this long after the last sign of claude code working
IDLE_TALK_MIN = 30         # starts commenting after this long with no token usage at all
CHATTER = {"off": 0, "some": 1.0, "lots": 2.5, "max": 5.0}   # how often it talks (settings: chatter)
CHAT_GAP = (45, 120)       # seconds between bits of small talk (at "some"; "lots" divides by 2.5)
SPEAK_CPS = 30             # typing speed of speech bubbles, letters per second
ATTENTION_MIN = 20         # asks for a little attention after this long without a hover, poke or drag
# throwing, parachutes, dancing (pixels are at 1x size)
THROW_KEEP = 0.38          # share of your mouse speed a throw keeps (it's a bit heavy)
THROW_MAX = 1500           # fastest throw, pixels per second
THROW_MIN = 250            # mouse speeds below this just drop it instead of throwing
THROW_DRAG = 1.5           # air slows a throw by this fraction per second
GROUND_FRICTION = 1600     # how fast it stops sliding after landing, pixels per second per second
CHUTE_HEIGHT = 260         # opens a parachute when falling from higher than this above the floor
CHUTE_SPEED = 110          # falling speed with the parachute open, pixels per second
DANCE_CHANCE = 0.05        # chance of a little dance whenever it stops walking
ACT_CHANCE = 0.1           # ...and of something else to do: stargazing (at night), a practice spell, a book
STALE_MIN = 10             # numbers older than this (and 3 checks) look faded in the bubble
ERROR_LOG_KB = 200         # pet_errors.log is trimmed to stay about this small
# keyboard shortcuts: (modifiers, key) with windows' codes. modifiers: 1 alt, 2 ctrl, 4 shift, 8 win.
SHORTCUTS = (("pet", "Show / hide the mascot", "Hides it completely (it keeps checking your usage), or brings it back."),
             ("details", "Open the details panel", "Pins the Plan / Claude Code panel open, or closes it."),
             ("come", "Call the mascot", "It comes over to your mouse, even from another monitor."))
DEFAULT_KEYS = {"pet": [3, ord("P")], "details": [3, ord("D")], "come": [3, ord("H")]}   # ctrl + alt + P / D / H
KEY_NAMES = {0x20: "Space", 0x21: "Page Up", 0x22: "Page Down", 0x23: "End", 0x24: "Home", 0x25: "Left",
             0x26: "Up", 0x27: "Right", 0x28: "Down", 0x2D: "Insert", 0x2E: "Delete"}


def key_name(vk):
    # a key's name for the screen, or None if it can't be used in a shortcut
    if 0x41 <= vk <= 0x5A or 0x30 <= vk <= 0x39:
        return chr(vk)
    if 0x70 <= vk <= 0x87:
        return f"F{vk - 0x6F}"
    if 0x60 <= vk <= 0x69:
        return f"Num {vk - 0x60}"
    return KEY_NAMES.get(vk)


def combo_parts(combo):
    # [mods, key] -> ["Ctrl", "Alt", "P"]
    mods, vk = combo
    return [n for bit, n in ((2, "Ctrl"), (1, "Alt"), (4, "Shift"), (8, "Win")) if mods & bit] + [key_name(vk)]


def combo_ok(combo):
    # a usable shortcut: a known key plus ctrl, alt or win (shift alone would get in the way of typing)
    return (isinstance(combo, list) and len(combo) == 2 and all(isinstance(v, int) and not isinstance(v, bool)
            for v in combo) and 0 < combo[0] < 16 and combo[0] & 0xB and key_name(combo[1]) is not None)
POLL_CHOICES = (120, 180, 240, 300)   # menu: refresh every (faster ones got "slow down" answers)
# pace messages (details panel)
AHEAD_BY = 10          # used% this far above the clock = "ahead of pace"
SLOW_BELOW = 0.5       # used under half of what the clock says = "way under pace"
IDLE_MIN_5H = 45       # 5-hour number unchanged this long = "not moving"
IDLE_HOURS_WEEKLY = 12 # weekly number unchanged this long = "not moving"
# early pace warning: says so once per window when the forecast runs out at least this long before the reset
PACE_WARN = {"five_hour": (30 * 60, 50), "seven_day": (12 * 3600, 40)}   # (seconds early, only from this %)
# quiet mode (menu: be quiet for an hour; settings: quiet hours)
QUIET_FOR = 3600
QUIET_FROM_CHOICES = (20, 21, 22, 23, 0)   # quiet hours start at this hour...
QUIET_TO_CHOICES = (6, 7, 8, 9)            # ...and end at this one
# coming over when called (shortcut, tray icon, or starting the pet again)
SPRINT = 5.0               # running speed, times the walking speed
COME_DROP = 500            # further than this (or on another monitor) it parachutes in instead of running
# claude code sessions: a session counts as finished after this long with nothing new
SESSION_DONE_MIN = 8
# fun stuff
SHINY_CHANCE = 1 / 500     # chance it starts up a rare colour
UFO_HOURS = 12             # on average, a ufo visits once in this many hours you're at the computer
CAT_HOURS = 6              # ...and a cat walks past about this often
FETCH_SECONDS = 25         # the ball stays around this long after a game of fetch
# ------------------

URL = "https://api.anthropic.com/api/oauth/usage"
CONFIG_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
CREDENTIALS = CONFIG_DIR / ".credentials.json"
CC_LOGS = CONFIG_DIR / "projects"
HERE = Path(__file__).resolve().parent.parent   # the project folder (this file is in pet/)
SETTINGS_FILE = HERE / "pet_settings.json"
STATE_FILE = HERE / "pet_state.json"     # moods and memories that survive a restart
CC_CACHE = HERE / "pet_cc_cache.json.gz" # claude code's log numbers, saved so a restart doesn't re-read every log
STARTUP_NAME = "Claude Usage Pet.lnk"
SUMMON_EVENT = "claude-usage-pet-summon" # starting the pet again sets this, and the running one comes over

NICE = {"five_hour": "5-hour", "seven_day": "Weekly"}
SHORT = {"five_hour": "5h", "seven_day": "wk"}
