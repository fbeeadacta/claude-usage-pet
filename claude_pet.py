# claude usage pet: a tiny claude mascot that lives on your taskbar and shows your
# plan usage (5-hour and weekly limits) in a bubble above its head.
#
# the numbers are for your whole plan, so they include claude.ai chat, the desktop app
# and claude code. they come from https://api.anthropic.com/api/oauth/usage, an
# undocumented endpoint that can change or stop working without notice.
# claude code's own token counts are read from its local logs (~/.claude/projects).
# only numbers are taken from those logs (times, token counts, model names), never text.
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
from collections import namedtuple, Counter
from ctypes import wintypes
from pathlib import Path

# ---- settings ----
DEFAULT_SCALE = 1.0        # starting size. after that the size you pick in the menu is remembered.
SIZES = [0.75, 1.0, 1.25, 1.5, 2.0, 3.0]   # choices in the right-click size menu
MIN_SCALE, MAX_SCALE = 0.5, 4.0            # limits for ctrl + mouse wheel
POLL_SECONDS = 120         # how often to ask the api
ONLY_KNOWN_LIMITS = True   # show only the 5-hour and weekly limits. False shows everything the api lists.
RATE_LIMITED_SECONDS = 180 # wait at least this long after the api says "slow down" (longer if it repeats)
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
CHATTER = {"off": 0, "some": 1.0, "lots": 2.5}   # how often it talks (menu: chatter)
SPEAK_CPS = 30             # typing speed of speech bubbles, letters per second
ATTENTION_MIN = 20         # asks for a little attention after this long without a hover, poke or drag
# throwing, parachutes, dancing (pixels are at 1x size)
THROW_DRAG = 0.6           # air slows a throw by this fraction per second
GROUND_FRICTION = 900      # how fast it stops sliding after landing, pixels per second per second
CHUTE_HEIGHT = 260         # opens a parachute when falling from higher than this above the floor
CHUTE_SPEED = 110          # falling speed with the parachute open, pixels per second
DANCE_CHANCE = 0.05        # chance of a little dance whenever it stops walking
POLL_CHOICES = (120, 180, 240, 300)   # menu: refresh every (faster ones got "slow down" answers)
# pace messages (details panel)
AHEAD_BY = 10          # used% this far above the clock = "ahead of pace"
SLOW_BELOW = 0.5       # used under half of what the clock says = "way under pace"
IDLE_MIN_5H = 45       # 5-hour number unchanged this long = "not moving"
IDLE_HOURS_WEEKLY = 12 # weekly number unchanged this long = "not moving"
# ------------------

URL = "https://api.anthropic.com/api/oauth/usage"
CONFIG_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
CREDENTIALS = CONFIG_DIR / ".credentials.json"
CC_LOGS = CONFIG_DIR / "projects"
HERE = Path(__file__).resolve().parent
SETTINGS_FILE = HERE / "pet_settings.json"
STATE_FILE = HERE / "pet_state.json"     # moods and memories that survive a restart
STARTUP_NAME = "Claude Usage Pet.lnk"

NICE = {"five_hour": "5-hour", "seven_day": "Weekly"}
SHORT = {"five_hour": "5h", "seven_day": "wk"}

# ---- things it says ----
QUOTES = [
    "you got this!", "one step at a time.", "drink some water! I'll wait.",
    "have you tried turning it off and on again?", "I believe in you. mostly.",
    "fun fact: I'm made entirely of rectangles.", "bugs are just surprise features.",
    "stretch break? your back will thank you.", "I don't have hands, but high five anyway.",
    "ctrl+s is my love language.", "you're doing great, honestly.",
    "it's not a bug, it's a plot twist.", "posture check!", "small progress is still progress.",
    "blink twice if you need a break.", "I like it here on the taskbar.",
    "if it works, don't touch it. (touch it a little)", "today's forecast: 100% chance of shipping.",
    "I'd make you coffee but I'm 40 pixels tall.", "remember to eat something!",
]
WORK_START = ["*thinking*", "ooh, a new job!", "on it!", "let me cook.", "time for some magic.",
              "summoning tokens..."]
WORKING = ["*thinking really hard*", "this is quite the job you got for me.",
           "abracadabra... *writes code*", "tokens go brrr.", "hmm, interesting...",
           "casting a big spell here.", "don't look, I'm concentrating.", "almost... maybe...",
           "my wand is getting warm."]
WORK_DONE = ["phew! done.", "that was a good one.", "*wipes forehead*", "ta-da!", "magic complete."]
IDLE_LINES = ["it's quiet... too quiet.", "need anything? I'm just standing here.",
              "I could be useful, you know.", "my wand is getting dusty.", "*taps foot*",
              "zero tokens. a peaceful day.", "anyone? hello?", "I'm on standby. very professional."]
POKE_LINES = ["hey!", "hehe", "that tickles!", "boop.", "yes?", "I'm awake, I'm awake!"]
POKE_COUNT = {10: "that's 10 pokes. we're friends now.", 50: "poke #50! I'm keeping count.",
              100: "100 pokes. a true bond.", 500: "500 pokes?! are you okay?"}
DRAG_LINES = ["wheee!", "where are we going?", "put me down! (actually this is fun)"]
WAKE_LINES = ["welcome back!", "oh hi! I wasn't sleeping.", "you're back!"]
RESET_LINES = ["fresh limits! let's go!", "5-hour limit reset. I feel brand new."]
THROW_LINES = ["AAAAAAAAA!", "WHEEEEEEEE—", "I'M FLYIIIING!", "not the face, not the face!",
               "this is NOT in my job description!", "I regret nothing!"]
DIZZY_LINES = ["@_@ everything is spinning...", "I see stars. pixel stars.", "who moved the taskbar?",
               "I'm fine. I'm fine. which way is up?"]
CHUTE_LINES = ["good thing I packed a parachute.", "safety first!", "*floats majestically*",
               "enjoying the view up here."]
ATTENTION_LINES = ["psst... hey. got a minute?", "*polite cough*", "I'm still here, by the way!",
                   "a little poke would be nice. no pressure.", "hello? it's me, your tiny assistant.",
                   "I did a cool jump earlier. you missed it."]
BORED_LINES = ["I counted all the pixels on your taskbar. twice.", "bored. so bored.",
               "should I take up a hobby? knitting, maybe.", "no tokens today? I'll just... stand here.",
               "I've been practising my dance moves.", "is it home time yet?"]
FULL_LINES = ["100%. that's what I call a hard day's work.", "we used ALL of it. I'm so proud.",
              "the tank is empty. see you after the reset!", "*collapses dramatically*",
              "I'm exhausted. clocking out until the reset.", "not a single token left. legendary."]
MILESTONES = {
    "five_hour": {50: "halfway through your 5-hour limit!", 75: "75% of the 5-hour limit used. pace yourself!",
                  90: "90%! almost out of 5-hour juice.",
                  100: "100% of the 5-hour limit. what a shift. time for a break."},
    "seven_day": {50: "halfway through the weekly limit.", 75: "75% of the weekly limit is gone.",
                  90: "90% of the week used. careful!",
                  100: "the whole week's limit. legendary effort."},
}
# menu tooltips: what each option does, then what happens when it's on or off (or its choices)
TIPS = {
    "Refresh now": ("Checks your plan usage right away, instead of waiting for the next automatic check.", []),
    "Refresh every": ("How often the mascot checks your plan usage on its own.", [
        ("2 min", "The default. Fresh numbers without asking the usage service too often."),
        ("3–5 min", "Fewer requests and slightly older numbers. Handy if you ever see \"slow down\".")]),
    "Keep details open": ("Pins the details panel above the mascot.", [
        ("On", "The panel stays open until you close it with ×."),
        ("Off", "The panel opens when you hover the mascot and fades away when you move off.")]),
    "Count tokens like the Claude app": ("Chooses how the Claude Code tab counts tokens and picks the peak hour.", [
        ("On", "Matches the Claude desktop app: every logged copy of an answer is added up, and peak hour "
               "is when your sessions start."),
        ("Off", "Real numbers: each answer is counted once (about 3× lower), and peak hour is your busiest hour.")]),
    "Walk around": ("Lets the mascot wander along the taskbar.", [
        ("On", "It walks left and right, and across to your other monitors."),
        ("Off", "It stays in one spot, but still blinks, hops and reacts.")]),
    "Jump now and then": ("Random little hops.", [
        ("On", "It hops about every 30 seconds."),
        ("Off", "No random hops. It still hops when you poke it or a limit resets.")]),
    "Take naps": ("Lets the mascot fall asleep.", [
        ("On", "It sleeps after 5 minutes away from the computer, wakes when you're back, and takes "
               "short naps now and then."),
        ("Off", "It always stays awake.")]),
    "Wizard when Claude works": ("Wizard mode while your tokens are going up.", [
        ("On", "It puts on a wizard hat and casts sparkles while Claude is working."),
        ("Off", "It carries on as usual while Claude works.")]),
    "Warn when nearly full": ("A coloured ring around the usage bubble when a limit is nearly used up.", [
        ("On", "Yellow ring from your yellow level, red from your red level (see Warning levels), and "
               "black once a limit is completely used up."),
        ("Off", "No ring. The red dot in the bubble and the 90% speech line still show.")]),
    "Warning levels": ("Sets when the warning ring turns yellow and when it turns red.", [
        ("Yellow", "From 70, 75, 80 or 85%."),
        ("Red", "From 85, 90 or 95%.")]),
    "Animations": ("All of the mascot's movement and effects.", [
        ("On", "It walks, hops, blinks, fades and types out its speech."),
        ("Off", "A completely still mascot, instant panels and no typing. Lightest on your computer.")]),
    "Chatter": ("How often the mascot talks in speech bubbles.", [
        ("Off", "It never talks."),
        ("Sometimes", "A line every 4–10 minutes, plus reactions to what's happening."),
        ("A lot", "About 2.5× more often.")]),
    "Size": ("How big the mascot is, from 0.75x to 3x.", [
        ("Tip", "Ctrl + mouse wheel over the mascot fine-tunes the size.")]),
    "Bubble": ("What the bubble above its head shows.", [
        ("Limits", "Both limits, the 5-hour limit only, or only while you hover."),
        ("Style", "Numbers, or two small bars.")]),
    "Hide during full screen": ("Gets out of the way of videos and games.", [
        ("On", "It fades away while something is full screen on its monitor, and won't walk onto that monitor."),
        ("Off", "It always stays visible.")]),
    "Stay on one monitor": ("Keeps the mascot on one screen.", [
        ("On", "It turns around at the screen's edges. You can still drag it to another screen."),
        ("Off", "It walks across to your other monitors.")]),
    "Start with Windows": ("Starts the mascot automatically.", [
        ("On", "It starts when you sign in to Windows."),
        ("Off", "Start it yourself with the Start Claude Pet shortcut.")]),
    "Quit": ("Closes the mascot. Your settings and its memory are saved first.", []),
}

# rough book sizes in tokens, for the fun comparison in the claude code tab
BOOKS = [("The Little Prince", 22_000), ("The Great Gatsby", 61_000), ("The Hobbit", 124_000),
         ("Pride and Prejudice", 156_000), ("Moby-Dick", 270_000), ("The Lord of the Rings", 625_000),
         ("War and Peace", 760_000), ("all seven Harry Potter books", 1_400_000)]

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

# little pictures made of small square blocks (2 px at 1x)
HEART = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
ZZZ = ["####", "..#.", ".#..", "####"]
SPARK = [".#.", "###", ".#."]
HAT = [                    # the wizard hat. # = hat, y = gold band, * = star
    "...............##.......",
    ".............###........",
    "............####........",
    "...........#####........",
    "..........#######.......",
    ".........####*####......",
    "........####***####.....",
    "........#####*#####.....",
    ".......#############....",
    ".......yyyyyyyyyyyyy....",
    "....###################.",
]

LEFT_WAVE = (((2, 1), (1, 1)), ((2, 1), (1, 0)))   # the left arm, mirror of WAVE
NOTE = ["..##", "..#.", "..#.", "###.", "###."]   # a music note, for dancing
# the parachute: a dome with red and white stripes
CHUTE = ["".join(("r" if (i // 4) % 2 == 0 else "w") if abs(i - 17.5) < w / 2 else "." for i in range(36))
         for w in (12, 20, 26, 30, 34, 36)]

ORANGE, EYE, BLUSH_C = "#d77757", "#2b1a14", "#f4a08f"
BUBBLE, BUBBLE_TEXT = "#1f1e1d", "#f2efe8"
SPEECH, SPEECH_TEXT = "#f2efe8", "#2b1a14"
HEART_C, ZZZ_C, SHADOW = "#ff6f8a", "#f2efe8", "#2b1a14"
WARN_C, PANIC_C = "#f2c14e", "#e5534b"
FULL_C, FULL_EDGE = "#0d0d0d", "#c8c8cd"   # the ring at 100%: black with a silver edge
NOTE_C = ["#ff9ad5", "#8be9fd", "#ffe08a"]
CHUTE_R, CHUTE_W, STRING_C = "#e5534b", "#f2efe8", "#d9d4c7"
HAT_C, BAND_C, STAR_C, WAND_C = "#6c4ab6", "#f2c14e", "#ffe08a", "#8b5a2b"
SPARK_C = ["#ffe08a", "#8be9fd", "#ff9ad5", "#ffffff"]
DIM, RED, TRACK = "#8e8e93", "#e5534b", "#3a3a3c"
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
            global RETRY_AFTER
            try:
                RETRY_AFTER = int(e.headers.get("Retry-After") or 0)   # the service's own "try again in"
            except (TypeError, ValueError):
                RETRY_AFTER = 0
            return None, "rate limited."
        return None, f"api error {e.code}."
    except Exception as e:
        return None, f"no connection ({type(e).__name__})."


RETRY_AFTER = 0   # seconds the usage service asked us to wait, from its last "slow down"


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


def same_window(a, b):
    # two resets_at values for the same limit window (they can wobble by a few seconds)
    ta, tb = parse_time(a), parse_time(b)
    return ta is not None and tb is not None and abs((ta - tb).total_seconds()) < 600


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


# ---- claude code's local logs ----

def fmt_tokens(n):
    if n < 1000:
        return str(n)
    for div, unit in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if n >= div:
            return f"{n / div:.1f}".rstrip("0").rstrip(".") + unit


def pretty_model(m):
    # "claude-opus-5-5" -> "Opus 5.5", "claude-3-5-haiku-20241022" -> "Haiku 3.5"
    parts = [p for p in m.replace("claude-", "").split("-") if not (p.isdigit() and len(p) >= 8)]
    words = [p.capitalize() for p in parts if not p.isdigit()]
    nums = [p for p in parts if p.isdigit()]
    return " ".join(words) + (" " + ".".join(nums) if nums else "")


def hour_label(h):
    return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


def compare_line(tokens):
    fits = [(name, size) for name, size in BOOKS if tokens >= 2 * size]
    if fits:
        name, size = fits[-1]
        return f"You've used ~{tokens / size:.0f}× more tokens than {name}."
    if tokens >= BOOKS[0][1]:
        return f"That's about as many tokens as {BOOKS[0][0]}."
    return f"That's {100 * tokens / BOOKS[0][1]:.0f}% of {BOOKS[0][0]} so far."


def build_stats(answers, lines, starts=None):
    # the claude code tab's numbers, for all time, 30 days and 7 days.
    # starts (session -> first time) = peak hour is when sessions start, like the claude app.
    today = datetime.date.today()
    by_day = Counter()
    for a in answers:
        by_day[a[0].date()] += a[3] + a[4] + a[5] + a[6]
    out = {"today": by_day.get(today, 0), "heat": dict(by_day), "ranges": {}}
    for name, days in (("all", None), ("30d", 30), ("7d", 7)):
        since = None if days is None else today - datetime.timedelta(days=days - 1)
        A = [a for a in answers if since is None or a[0].date() >= since]
        L = [ln for ln in lines if since is None or ln[0].date() >= since]
        models, parts = Counter(), [0, 0, 0, 0]
        for a in A:
            for i in range(4):
                parts[i] += a[3 + i]
            if not a[2].startswith("<"):   # skip claude code's made-up "<synthetic>" entries
                models[a[2]] += a[3] + a[4] + a[5] + a[6]
        hours = Counter(ln[0].hour for ln in L)
        if starts:
            began = Counter(t.hour for t in starts.values() if since is None or t.date() >= since)
            hours = began or hours
        out["ranges"][name] = {
            "sessions": len({ln[1] for ln in L}), "messages": len(L), "tokens": sum(parts),
            "parts": parts, "days": len({ln[0].date() for ln in L}),
            "peak": hours.most_common(1)[0][0] if hours else None, "models": models.most_common(),
        }
    return out


class ClaudeCodeLog:
    # reads claude code's logs (~/.claude/projects/**/*.jsonl) a little at a time, in the background.
    # keeps only numbers: times, session ids, model names and token counts. never message text.
    def __init__(self):
        self.offsets = {}         # file -> bytes read so far
        self.seen_answers = set() # (message id, request id). each answer is logged several times.
        self.seen_lines = set()   # line ids, so nothing is counted twice
        self.answers = []         # (local time, session, model, input, output, cache write, cache read)
        self.copies = []          # the extra logged copies of those answers (the claude app counts them too)
        self.starts = {}          # session -> its first line's time
        self.lines = []           # (local time, session) for every user and assistant line
        self.stats = None         # summary for the panel
        self.last_growth = 0.0    # when new output tokens last appeared
        self.built_at = 0.0
        self.ready = False

    def run(self):
        while True:
            try:
                self.scan()
            except Exception:
                pass   # a weird log line must never stop the pet
            time.sleep(CC_SCAN_SECONDS)

    def scan(self):
        new_output, changed = 0, False
        try:
            files = list(CC_LOGS.rglob("*.jsonl"))
        except OSError:
            files = []
        for f in files:
            try:
                size = f.stat().st_size
            except OSError:
                continue
            start = self.offsets.get(str(f), 0)
            if size < start:
                start = 0   # the file was rewritten. the seen sets stop double counting.
            if size == start:
                continue
            try:
                with open(f, "rb") as fh:
                    fh.seek(start)
                    chunk = fh.read(size - start)
            except OSError:
                continue
            end = chunk.rfind(b"\n")
            if end < 0:
                continue   # only half a line so far
            self.offsets[str(f)] = start + end + 1
            for raw in chunk[:end].split(b"\n"):
                got = self.take(raw)
                if got is not None:
                    changed = True
                    new_output += got
        if new_output and self.ready:
            self.last_growth = time.time()
        if self.stats is None or (changed and time.time() - self.built_at > 10):
            self.stats = {"real": build_stats(self.answers, self.lines),
                          "app": build_stats(self.answers + self.copies, self.lines, self.starts)}
            self.built_at = time.time()
        self.ready = True

    def usage_curve(self, start, end):
        # claude code's token use between two times as a running total, roughly weighted by what each
        # kind of token costs (output most, cache reads least), for estimating the chart's early part
        pts = sorted((a[0].timestamp(), a[3] + 5 * a[4] + 1.25 * a[5] + 0.1 * a[6])
                     for a in list(self.answers) if start <= a[0].timestamp() <= end)
        out, total = [], 0.0
        for ts, w in pts:
            total += w
            out.append((ts, total))
        step = max(1, len(out) // 150)   # no need for more than ~150 points
        return out[::step] + out[-1:] if out else []

    def take(self, raw):
        # one log line -> output tokens it added (None if it was nothing new)
        try:
            d = json.loads(raw)
        except ValueError:
            return None
        if not isinstance(d, dict) or d.get("type") not in ("user", "assistant"):
            return None
        uid = d.get("uuid")
        if uid in self.seen_lines:
            return None
        when = parse_time(d.get("timestamp") or "")
        if when is None:
            return None
        when = when.astimezone()   # your local time
        if uid:
            self.seen_lines.add(uid)
        session = d.get("sessionId") or "?"
        self.lines.append((when, session))
        if session not in self.starts or when < self.starts[session]:
            self.starts[session] = when
        m = d.get("message")
        if d["type"] == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict):
            u = m["usage"]
            n = [int(u.get(k) or 0) for k in ("input_tokens", "output_tokens",
                                              "cache_creation_input_tokens", "cache_read_input_tokens")]
            row = (when, session, str(m.get("model") or "unknown"), *n)
            key = (m.get("id"), d.get("requestId"))
            if key in self.seen_answers:
                self.copies.append(row)   # same answer, logged again
                return 0
            self.seen_answers.add(key)
            self.answers.append(row)
            return n[1]
        return 0


# ---- settings and memory files ----

DEFAULTS = {"scale": DEFAULT_SCALE, "walk": True, "jump": True, "naps": True, "anim": True,
            "bubble": "both", "bubble_style": "numbers", "chatter": "some", "wizard": True, "warn": True, "cc_app": True,
            "warn_at": WARN_AT, "panic_at": PANIC_AT, "poll": POLL_SECONDS,
            "hide_fs": True, "one_monitor": False, "panel_tab": "plan", "plan_chart": "5h", "cc_view": "overview",
            "cc_range": "all", "x": None, "y": None}
CHOICES = {"bubble": ("both", "5h", "hover"), "bubble_style": ("numbers", "bars"),
           "chatter": tuple(CHATTER), "panel_tab": ("plan", "cc"), "plan_chart": ("5h", "7d"), "cc_view": ("overview", "models"),
           "cc_range": ("all", "30d", "7d")}


def read_json(path):
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}   # missing or broken file


def write_json(path, data):
    # write to a temp file first, then swap it in, so a crash mid-write can't leave a broken file
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=1))
        os.replace(tmp, path)
    except OSError:
        pass


def load_settings():
    saved = read_json(SETTINGS_FILE)
    st = dict(DEFAULTS)
    st.update({k: saved[k] for k in DEFAULTS if k in saved})
    try:
        st["scale"] = min(MAX_SCALE, max(MIN_SCALE, float(st["scale"])))
    except (TypeError, ValueError):
        st["scale"] = DEFAULT_SCALE
    for k in ("walk", "jump", "naps", "anim", "wizard", "warn", "cc_app", "hide_fs", "one_monitor"):
        st[k] = st[k] if isinstance(st[k], bool) else DEFAULTS[k]
    for k, ok in CHOICES.items():
        if st[k] not in ok:
            st[k] = DEFAULTS[k]
    for k, ok in (("warn_at", WARN_CHOICES), ("panic_at", PANIC_CHOICES), ("poll", POLL_CHOICES)):
        if st[k] not in ok or isinstance(st[k], bool):
            st[k] = DEFAULTS[k]
    for k in ("x", "y"):
        if isinstance(st[k], bool) or not isinstance(st[k], (int, float)):
            st[k] = None
    return st


def load_memory():
    # moods that survive a restart: when each limit last moved, pokes, milestones already said
    m = read_json(STATE_FILE)
    out = {"seen": {}, "last_5h": None, "pokes": 0, "milestones": {}, "last_usage": time.time(), "history": []}
    try:
        num = lambda v: None if v is None else float(v)
        out["history"] = [(float(h[0]), num(h[1]), num(h[2])) for h in m.get("history", [])]
    except (TypeError, ValueError, IndexError):
        pass
    try:
        out["seen"] = {k: (float(v[0]), float(v[1]), str(v[2])) for k, v in m.get("seen", {}).items()}
    except (TypeError, ValueError, IndexError, AttributeError):
        pass
    try:
        out["milestones"] = {k: [str(v[0]), [int(x) for x in v[1]]] for k, v in m.get("milestones", {}).items()}
    except (TypeError, ValueError, IndexError, AttributeError):
        pass
    for k, kind in (("last_5h", float), ("pokes", int), ("last_usage", float)):
        try:
            if m.get(k) is not None:
                out[k] = kind(m[k])
        except (TypeError, ValueError):
            pass
    return out


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
u32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
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


def menu_rects():
    # where windows has drawn the open popup menus (their window class is "#32768")
    found = []

    def cb(hwnd, lp):
        name = ctypes.create_unicode_buffer(16)
        u32.GetClassNameW(hwnd, name, 16)
        r = wintypes.RECT()
        if name.value == "#32768" and u32.IsWindowVisible(hwnd) and u32.GetWindowRect(hwnd, ctypes.byref(r)):
            found.append((r.left, r.top, r.right, r.bottom))
        return True

    u32.EnumWindows(WNDENUMPROC(cb), 0)
    return found


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


def round_rect(c, x1, y1, x2, y2, r, fill, bg=KEY, smooth=False):
    # a rounded box: three rectangles plus four corner images, all on whole pixels so nothing steps
    x1, y1, x2, y2 = round(x1), round(y1), round(x2), round(y2)
    r = max(1, min(round(r), (x2 - x1) // 2, (y2 - y1) // 2))
    c.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline="")
    c.create_rectangle(x1, y1 + r, x1 + r, y2 - r, fill=fill, outline="")
    c.create_rectangle(x2 - r, y1 + r, x2, y2 - r, fill=fill, outline="")
    for q, (x, y) in enumerate(((x1, y1), (x2 - r, y1), (x1, y2 - r), (x2 - r, y2 - r))):
        c.create_image(x, y, image=corner(c, r, fill, bg, smooth, q), anchor="nw")


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
        self.fonts, self.wraps = {}, {}

        st = load_settings()
        self.scale = st["scale"]
        self.walk = tk.BooleanVar(value=st["walk"])
        self.jump = tk.BooleanVar(value=st["jump"])
        self.naps = tk.BooleanVar(value=st["naps"])
        self.anim = tk.BooleanVar(value=st["anim"])
        self.wizard = tk.BooleanVar(value=st["wizard"])
        self.warn = tk.BooleanVar(value=st["warn"])
        self.cc_app = tk.BooleanVar(value=st["cc_app"])
        self.warn_at = tk.IntVar(value=st["warn_at"])
        self.panic_at = tk.IntVar(value=st["panic_at"])
        self.poll = tk.IntVar(value=st["poll"])
        self.hide_fs = tk.BooleanVar(value=st["hide_fs"])
        self.one_monitor = tk.BooleanVar(value=st["one_monitor"])
        self.bubble_mode = tk.StringVar(value=st["bubble"])
        self.bubble_style = tk.StringVar(value=st["bubble_style"])
        self.chatter = tk.StringVar(value=st["chatter"])
        self.panel_tab = tk.StringVar(value=st["panel_tab"])
        self.cc_view = tk.StringVar(value=st["cc_view"])
        self.cc_range = tk.StringVar(value=st["cc_range"])
        self.plan_chart = tk.StringVar(value=st["plan_chart"])
        self.size_var = tk.DoubleVar(value=self.scale)
        self.pin_var = tk.BooleanVar(value=False)
        self.startup_var = tk.BooleanVar(value=startup_path().exists())

        # usage data, plus what it remembers from last time
        mem = load_memory()
        self.inbox = queue.Queue()
        self.data, self.error, self.updated = None, None, None
        self.busy = False
        self.next_at = 0.0          # unix time of the next check. 0 = check right away.
        self.seen = mem["seen"]     # key -> (percent, when it last changed, resets_at)
        self.last_5h = mem["last_5h"]
        self.pokes = mem["pokes"]
        self.milestones = mem["milestones"]   # key -> [resets_at, levels already announced]
        self.last_usage = mem["last_usage"]   # when tokens last went up anywhere
        self.first_result = True
        self.history = mem["history"]   # [(time, 5-hour %, weekly %)] for the plan tab's chart
        self.limited = 0                # "slow down" answers in a row

        # claude code's logs, read in the background
        self.cc = ClaudeCodeLog()
        threading.Thread(target=self.cc.run, daemon=True).start()
        self.cc_growth_seen = 0.0
        self.working_until = 0.0
        self.was_working, self.work_started = False, 0.0
        self.next_work_line = self.next_idle_line = 0.0
        self.next_quote = time.time() + random.uniform(60, 180)
        self.speech, self.quiet_until = None, 0.0
        self.last_touch = time.time()             # last hover, poke or drag
        self.next_attention = self.next_full_line = 0.0

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
        self.vx, self.vy = 0.0, 0.0               # speed (vx is only for throws)
        self.angle, self.spin, self.hang = 0.0, 0.0, 0.0   # tilt while dragged or tumbling
        self.grab_local, self.grip, self.trail, self.drag_vx = (0, 0), (0, 0), [], 0.0
        self.chute, self.bounces = False, 0
        self.dizzy_t = self.stretch_t = self.dance_t = 0.0
        self.center_x, self.feet_win, self.body_at, self.pet_px = 0, 0, (0, 0), (72, 40)
        self.dir = random.choice((-1, 1))
        self.state, self.state_t = "idle", 2.0    # idle, walk, sleep, work or dance
        self.sleep_reason = None
        self.step, self.step_t = 0, 0.0
        self.blink_t, self.next_blink = 0.0, 3.0
        self.look_t, self.look_d = 0.0, 0         # glancing left or right while standing
        self.squash_t, self.pending_v = 0.0, 0.0  # crouch before a jump / squish after landing
        self.happy_t = self.wave_t = self.cast_t = 0.0
        self.celebrate = 0                        # hops left to celebrate a reset
        self.parts, self.part_t = [], 0.0         # floating hearts, z's and sparks
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
        self.tip = Tooltip(self)
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
        rf = tk.Menu(m, tearoff=0)
        for v in POLL_CHOICES:
            rf.add_radiobutton(label=f"{v} seconds" if v < 60 else f"{v // 60} minute{'s' if v > 60 else ''}",
                               variable=self.poll, value=v, command=self.poll_changed)
        m.add_cascade(label="Refresh every", menu=rf)
        m.add_checkbutton(label="Keep details open", variable=self.pin_var, command=self.pin_changed)
        m.add_checkbutton(label="Count tokens like the Claude app", variable=self.cc_app, command=self.cc_changed)
        m.add_separator()
        m.add_checkbutton(label="Walk around", variable=self.walk, command=self.changed)
        m.add_checkbutton(label="Jump now and then", variable=self.jump, command=self.changed)
        m.add_checkbutton(label="Take naps", variable=self.naps, command=self.naps_changed)
        m.add_checkbutton(label="Wizard when Claude works", variable=self.wizard, command=self.changed)
        m.add_checkbutton(label="Warn when nearly full", variable=self.warn, command=self.changed)
        lv = tk.Menu(m, tearoff=0)
        lv.add_command(label="Yellow ring from", state="disabled")
        for v in WARN_CHOICES:
            lv.add_radiobutton(label=f"   {v}%", variable=self.warn_at, value=v, command=self.changed)
        lv.add_separator()
        lv.add_command(label="Red ring from", state="disabled")
        for v in PANIC_CHOICES:
            lv.add_radiobutton(label=f"   {v}%", variable=self.panic_at, value=v, command=self.changed)
        m.add_cascade(label="Warning levels", menu=lv)
        m.add_checkbutton(label="Animations", variable=self.anim, command=self.anim_changed)
        talk = tk.Menu(m, tearoff=0)
        for val, label in (("off", "Off"), ("some", "Sometimes"), ("lots", "A lot")):
            talk.add_radiobutton(label=label, variable=self.chatter, value=val, command=self.chatter_changed)
        m.add_cascade(label="Chatter", menu=talk)
        sizes = tk.Menu(m, tearoff=0)
        for v in SIZES:
            sizes.add_radiobutton(label=f"{v:g}x", variable=self.size_var, value=v,
                                  command=lambda v=v: self.set_scale(v))
        m.add_cascade(label="Size", menu=sizes)
        bub = tk.Menu(m, tearoff=0)
        for val, label in (("both", "Both limits"), ("5h", "5-hour only"), ("hover", "Only when I hover")):
            bub.add_radiobutton(label=label, variable=self.bubble_mode, value=val, command=self.changed)
        bub.add_separator()
        for val, label in (("numbers", "Show numbers"), ("bars", "Show bars")):
            bub.add_radiobutton(label=label, variable=self.bubble_style, value=val, command=self.changed)
        m.add_cascade(label="Bubble", menu=bub)
        m.add_separator()
        m.add_checkbutton(label="Hide during full screen", variable=self.hide_fs, command=self.hide_fs_changed)
        m.add_checkbutton(label="Stay on one monitor", variable=self.one_monitor, command=self.changed)
        m.add_checkbutton(label="Start with Windows", variable=self.startup_var, command=self.startup_changed)
        m.add_separator()
        m.add_command(label="Quit", command=self.quit)
        m.bind("<<MenuSelect>>", lambda e: self.tip.hover(m))

    def show_menu(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()
            self.tip.hide()

    # settings
    def s(self):
        return self.scale * self.dpi   # your size setting times windows' display scaling

    def save(self):
        st = {k: (v.get() if isinstance(v, tk.Variable) else v) for k, v in (
            ("scale", self.scale), ("walk", self.walk), ("jump", self.jump), ("naps", self.naps),
            ("anim", self.anim), ("bubble", self.bubble_mode), ("bubble_style", self.bubble_style),
            ("chatter", self.chatter), ("wizard", self.wizard), ("warn", self.warn), ("cc_app", self.cc_app), ("warn_at", self.warn_at), ("panic_at", self.panic_at), ("poll", self.poll), ("hide_fs", self.hide_fs),
            ("one_monitor", self.one_monitor), ("panel_tab", self.panel_tab), ("cc_view", self.cc_view),
            ("cc_range", self.cc_range), ("plan_chart", self.plan_chart), ("x", round(self.x)), ("y", round(self.y)))}
        write_json(SETTINGS_FILE, st)
        write_json(STATE_FILE, {"seen": self.seen, "last_5h": self.last_5h, "pokes": self.pokes,
                                "history": self.history,
                                "milestones": self.milestones, "last_usage": self.last_usage})
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

    def cc_stats(self):
        # the claude code numbers, counted like the claude app or for real
        st = self.cc.stats
        return st and st["app" if self.cc_app.get() else "real"]

    def cc_changed(self):
        if self.details.visible:
            self.details.draw()
        self.save()

    def poll_changed(self):
        self.next_at = min(self.next_at, time.time() + self.poll.get())
        self.changed()

    def naps_changed(self):
        if not self.naps.get():
            self.wake()
        self.changed()

    def chatter_changed(self):
        if self.chatter.get() == "off":
            self.speech = None
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
        else:   # always placed by the body, the same way in every state, so nothing jumps
            if not self.held:
                self.clamp_x()
            geo = (w, h, round(self.x - self.center_x), round(self.y - self.feet_win))
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
        self.trail = [(time.perf_counter(), e.x_root, e.y_root)]
        # where on its body you grabbed it, in body pixels (it will hang from that spot)
        pw, ph = self.pet_px
        gx = e.x_root - (self.geo[2] if self.geo else 0) - self.body_at[0]
        gy = e.y_root - (self.geo[3] if self.geo else 0) - self.body_at[1]
        self.grab_local = (min(max(gx, 0), pw), min(max(gy, 0), ph))
        self.redraw()

    def motion(self, e):
        now = time.perf_counter()
        self.trail = [t for t in self.trail if now - t[0] < 0.1] + [(now, e.x_root, e.y_root)]
        if not self.moved and abs(e.x_root - self.press_at[0]) + abs(e.y_root - self.press_at[1]) > 4:
            self.moved, self.held, self.pressed = True, True, False
            self.vx = self.vy = self.squash_t = self.pending_v = 0.0
            self.chute, self.bounces, self.last_touch = False, 0, time.time()
            if self.state == "dance":
                self.state = "idle"
            self.wake(hop=False)
            self.details.hide()
            self.hang = self.hang_angle() if self.anim.get() else 0.0
            if random.random() < 0.5:
                self.say(random.choice(DRAG_LINES), force=True)
        if self.held:
            first, last = self.trail[0], self.trail[-1]
            if last[0] - first[0] > 0.01:
                self.drag_vx = (last[1] - first[1]) / (last[0] - first[0])
            self.grip = (e.x_root, e.y_root)
            self.follow_grip()
            self.redraw()

    def hang_angle(self):
        # how far it tips so its middle hangs straight below the spot you grabbed
        pw, ph = self.pet_px
        vx, vy = pw / 2 - self.grab_local[0], ph / 2 - self.grab_local[1]
        if math.hypot(vx, vy) < 0.12 * pw:
            return 0.0   # grabbed near the middle: it just dangles upright
        return (math.pi / 2 - math.atan2(vy, vx) + math.pi) % (2 * math.pi) - math.pi

    def follow_grip(self):
        # works out where its body is from your grip and its tilt
        pw, ph = self.pet_px
        dx, dy = pw / 2 - self.grab_local[0], ph / 2 - self.grab_local[1]
        ca, sa = math.cos(self.angle), math.sin(self.angle)
        self.x = self.grip[0] + dx * ca - dy * sa
        self.y = self.grip[1] + dx * sa + dy * ca + ph / 2

    def release(self, e):
        self.pressed = False
        if self.held:
            self.held = False
            s = self.s()
            now = time.perf_counter()
            trail = [t for t in self.trail if now - t[0] < 0.1]
            vx = vy = 0.0
            if len(trail) >= 2 and trail[-1][0] - trail[0][0] > 0.01:
                d = trail[-1][0] - trail[0][0]
                vx, vy = (trail[-1][1] - trail[0][1]) / d, (trail[-1][2] - trail[0][2]) / d
            cap = 2600 * s
            vx, vy = max(-cap, min(cap, vx)), max(-cap, min(cap, vy))
            self.follow_grip()
            self.angle = (self.angle + math.pi) % (2 * math.pi) - math.pi   # rights itself the short way
            i = self.floor_below(self.x, self.y)
            self.si = i if i is not None else self.nearest_screen(self.x, self.y)
            sc = self.screens[self.si]
            self.x = min(max(self.x, sc.wl + self.half), sc.wr - self.half)
            self.y = min(self.y, sc.wb)
            if self.anim.get():   # it keeps the speed you threw it with
                self.vx, self.vy, self.bounces = vx, vy, 0
                self.spin += vx * 0.004 / s
                if math.hypot(vx, vy) > 900 * s:
                    self.say(random.choice(THROW_LINES), force=True)
            else:
                self.y, self.angle, self.spin = sc.wb, 0.0, 0.0
            self.state, self.state_t = "idle", 2.0
            self.save()
        elif not self.moved:
            self.poke()
        self.trail = []
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

    # talking
    def say(self, text, force=False):
        # shows a speech bubble. force = it's about something that just happened, so skip the cooldown.
        rate = CHATTER[self.chatter.get()]
        now = time.time()
        if rate == 0 or self.hidden or (not force and now < self.quiet_until):
            return False
        self.speech = {"text": text, "start": now,
                       "until": now + 2.6 + len(text) / SPEAK_CPS + 0.03 * len(text)}
        self.quiet_until = now + 25
        return True

    def note_usage(self, now, hold):
        # tokens just went up somewhere: work (wizard time) for at least `hold` seconds
        self.working_until = max(self.working_until, now + hold)
        self.last_usage = now

    def mood_tick(self, now):
        # once a second: is claude working, should the pet say something
        if self.cc.last_growth > self.cc_growth_seen:
            self.cc_growth_seen = self.cc.last_growth
            self.note_usage(now, WORK_HOLD)
        rate = CHATTER[self.chatter.get()] or 1.0
        working = now < self.working_until
        if working and not self.was_working:
            self.work_started = now
            if self.state == "sleep":
                self.wake()
            self.say(random.choice(WORK_START), force=True)
            self.next_work_line = now + random.uniform(90, 180) / rate
        elif working and now >= self.next_work_line:
            self.say(random.choice(WORKING))
            self.next_work_line = now + random.uniform(90, 180) / rate
        elif not working and self.was_working and now - self.work_started > 45:
            self.say(random.choice(WORK_DONE), force=True)
        self.was_working = working
        if working or self.state == "sleep" or self.details.visible or idle_seconds() > 60:
            return   # busy, asleep, or nobody's there to listen
        if self.full():
            if now >= self.next_full_line and self.say(random.choice(FULL_LINES)):
                self.next_full_line = now + random.uniform(8, 15) * 60 / rate
            return
        if now - self.last_touch > ATTENTION_MIN * 60 and now >= self.next_attention:
            if self.say(random.choice(ATTENTION_LINES)):
                self.wave_t = 1.4
                self.next_attention = now + random.uniform(15, 25) * 60 / rate
            return
        if now - self.last_usage > IDLE_TALK_MIN * 60:
            if now >= self.next_idle_line and self.say(random.choice(IDLE_LINES + BORED_LINES)):
                self.next_idle_line = now + random.uniform(15, 25) * 60 / rate
                if random.random() < 0.4 and self.state == "idle" and self.grounded():
                    self.start_dance()   # bored. might as well dance.
        elif now >= self.next_quote:
            self.say(random.choice(QUOTES))
            self.next_quote = now + random.uniform(4, 10) * 60 / rate

    # reactions
    def greet(self):
        # you pointed at it: it wakes up, or stops and waves
        self.last_touch = time.time()
        if not self.anim.get():
            return
        if self.state == "sleep":
            self.wake()
        elif self.state not in ("work", "dance"):
            self.wave_t = 1.1
            if self.state == "walk":
                self.state, self.state_t = "idle", 2.0

    def poke(self):
        # you clicked it: squish, hop, happy face and a heart
        self.pokes += 1
        self.last_touch = time.time()
        if self.pokes in POKE_COUNT:
            self.say(POKE_COUNT[self.pokes], force=True)
        elif random.random() < 0.35:
            self.say(random.choice(POKE_LINES), force=True)
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
        if random.random() < 0.5:
            self.say("*yawn*", force=True)

    def wake(self, hop=True):
        if self.state != "sleep":
            return
        self.state, self.state_t, self.sleep_reason = "idle", 2.0, None
        self.stretch_t = 0.9   # a big stretch, both arms up
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
                self.say(random.choice(WAKE_LINES), force=True)
        elif (away >= SLEEP_AFTER_MIN * 60 and self.grounded() and not self.held and not self.details.visible
              and self.state != "work"):
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

    def hand(self):
        # which row the wand hand is on while casting (it waves between two)
        return 0 if int(self.cast_t / 0.35) % 2 else 1

    def spawn(self, kind):
        s = self.s()
        bw, bh = max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s))
        pb = max(1, round(2 * s))
        if kind == "heart":   # pops out just above the bubble so it never covers the numbers
            self.parts.append({"kind": "heart", "x": (18 * bw - 7 * pb) / 2 + random.uniform(-2, 2) * bw,
                               "y": self.bubble_top - 7 * pb, "vx": random.uniform(-10, 10) * s,
                               "vy": -30 * s, "life": 0.8, "c": 0})
        elif kind == "note":   # dancing
            self.parts.append({"kind": "note", "x": random.uniform(1, 14) * bw, "y": -5 * pb,
                               "vx": random.uniform(-15, 15) * s, "vy": -35 * s, "life": 1.0,
                               "c": random.randrange(len(NOTE_C))})
        elif kind == "spark":   # from the wand tip
            self.parts.append({"kind": "spark", "x": 17 * bw + 4 * pb, "y": self.hand() * bh - 8 * pb,
                               "vx": random.uniform(-25, 35) * s, "vy": random.uniform(-45, -5) * s,
                               "life": random.uniform(0.4, 0.8), "c": random.randrange(len(SPARK_C))})
        else:
            big = sum(p["kind"] == "Z" for p in self.parts) <= sum(p["kind"] == "z" for p in self.parts)
            self.parts.append({"kind": "Z" if big else "z", "x": 15 * bw, "y": bh - 4 * pb,
                               "vx": random.uniform(5, 9) * s, "vy": -20 * s, "life": 2.4, "c": 0})

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
                if prev is None or prev[0] != r["pct"] or not same_window(prev[2], r["resets"]):
                    self.seen[r["key"]] = (r["pct"], now, r["resets"])
                if r["key"] == "five_hour":
                    if self.last_5h is not None and self.last_5h >= 15 and r["pct"] <= self.last_5h - 15:
                        self.celebrate = 3    # the 5-hour limit just reset. party.
                        self.say(random.choice(RESET_LINES), force=True)
                    elif self.last_5h is not None and r["pct"] > self.last_5h and not self.first_result:
                        self.note_usage(now, self.poll.get() + 10)   # chat or other apps are using tokens
                    self.last_5h = r["pct"]
                self.check_milestone(r)
            self.first_result = False
            self.limited = 0
            self.next_at = now + self.poll.get()
            self.remember(now, parse_rows(data))
        else:
            if err.startswith("login expired") and not (self.error or "").startswith("login expired"):
                self.say("I can't see your usage anymore. open Claude Code to log back in?", force=True)
            if err.startswith("rate limited"):
                # asked to slow down: wait 3, 6, 12... minutes (up to 30), or longer if the service says so
                self.limited += 1
                wait = max(RETRY_AFTER, min(1800, RATE_LIMITED_SECONDS * 2 ** (self.limited - 1)))
                self.next_at = now + wait
                at = datetime.datetime.fromtimestamp(self.next_at)
                err = (f"rate limited: the usage service asked us to slow down, so it'll try again at {at:%H:%M}. "
                       "your last numbers are still shown. a slower 'refresh every' setting helps.")
            else:
                self.next_at = now + self.poll.get()
            self.error = err

    def remember(self, now, rows):
        # keeps a history of the 5-hour and weekly % for the plan tab's chart:
        # every check for the last 6 hours, then one per 10 minutes, for 8 days
        by_key = {r["key"]: r["pct"] for r in rows}
        if "five_hour" not in by_key and "seven_day" not in by_key:
            return
        self.history.append((now, by_key.get("five_hour"), by_key.get("seven_day")))
        kept, last_old = [], 0.0
        for h in self.history:
            if now - h[0] > 8 * 86400:
                continue
            if now - h[0] > 6 * 3600:
                if h[0] - last_old < 600:
                    continue
                last_old = h[0]
            kept.append(h)
        self.history = kept

    def check_milestone(self, r):
        lines = MILESTONES.get(r["key"])
        if not lines:
            return
        reached = [lvl for lvl in lines if r["pct"] >= lvl]
        known = self.milestones.get(r["key"])
        if known is None or not same_window(known[0], r["resets"]):
            # first time we see this window: remember what's already passed, quietly
            self.milestones[r["key"]] = [r["resets"], reached if known is None else []]
            if known is None:
                return
        said = self.milestones[r["key"]][1]
        new = [lvl for lvl in reached if lvl not in said]
        if new:
            self.say(lines[max(new)], force=True)
            said.extend(new)

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
        # 10 times a second: hover. twice a second: full screen. every second: away, moods, talking.
        now = time.time()
        self.check_hover(now)
        if now >= self.next_fs_check:
            self.next_fs_check = now + 0.5
            self.check_fullscreen()
        if now >= self.next_slow_check:
            self.next_slow_check = now + 1
            self.check_away()
            self.mood_tick(now)
            if now - self.screens_at >= 5:
                self.refresh_screens()
        self.redraw()
        self.root.after(100, self.ui_tick)

    def shown_rows(self):
        rows = parse_rows(self.data) if self.data else []
        by_key = {r["key"]: r for r in rows}
        picks = [by_key[k] for k in ("five_hour", "seven_day") if k in by_key] or rows[:2]
        return picks[:1] if self.bubble_mode.get() == "5h" else picks

    def bubble_segments(self):
        segs = [(f"{SHORT.get(r['key'], r['label'])} {r['pct']:.0f}%", bar_color(r["pct"])) for r in self.shown_rows()]
        if self.error:
            segs.append(("!" if segs else short_error(self.error), RED))
        return segs or [("...", DIM)]

    def bubble_bars(self):
        return [(SHORT.get(r["key"], r["label"][:4]), round(r["pct"]), bar_color(r["pct"])) for r in self.shown_rows()]

    def warn_level(self):
        # 0 = fine (or warnings switched off), 1 = yellow ring, 2 = red ring, 3 = completely used up
        if not self.warn.get():
            return 0
        top = max([r["pct"] for r in self.shown_rows()] or [0])
        if top >= 100:
            return 3
        return 2 if top >= self.panic_at.get() else 1 if top >= self.warn_at.get() else 0

    def full(self):
        return any(r["pct"] >= 100 for r in self.shown_rows())

    # movement
    def walking_allowed(self):
        return self.walk.get() and not self.details.visible and not self.hidden and not self.full()

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
        if (self.held or self.pressed or self.squash_t > 0 or not self.grounded() or self.angle or self.vx
                or (self.state == "walk" and self.walking_allowed())):
            return 15
        if (self.parts or self.wave_t > 0 or self.state in ("work", "dance") or self.speech
                or self.dizzy_t > 0 or self.stretch_t > 0):
            return 30
        return 80

    def physics(self, dt):
        s = self.s()
        self.clock += dt
        for name in ("happy_t", "wave_t", "look_t", "dizzy_t", "stretch_t"):
            setattr(self, name, getattr(self, name) - dt)
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
        self.turn(dt, s)
        if self.held or self.hidden or self.pressed:
            return
        if self.squash_t > 0:   # crouching or squished: hold still for a moment
            self.squash_t -= dt
            if self.squash_t <= 0 and self.pending_v:
                self.vy, self.pending_v = -self.pending_v, 0.0
            return
        walking = self.state == "walk" and self.walking_allowed()
        sc = self.screens[self.si]
        if not self.grounded():   # in the air
            g = GRAVITY * s
            if (not self.chute and self.vy > 150 * s and sc.wb - self.y > CHUTE_HEIGHT * s
                    and abs(self.angle) < 0.4):
                self.chute = True   # a long way down: open the parachute
                if random.random() < 0.6:
                    self.say(random.choice(CHUTE_LINES), force=True)
            if self.chute:
                self.vy = min(self.vy + g * dt, CHUTE_SPEED * s)
                self.y += self.vy * dt
                self.vx *= max(0.0, 1 - 2.5 * dt)
                self.x += math.sin(self.clock * 1.6) * 14 * s * dt   # drifting in the breeze
            else:   # a proper curve, the same whatever the frame rate
                self.y += self.vy * dt + 0.5 * g * dt * dt
                self.vy += g * dt
                self.vx *= max(0.0, 1 - THROW_DRAG * dt)
            if self.y - self.pet_px[1] < sc.mt:   # bonk on the top of the screen
                self.y, self.vy = sc.mt + self.pet_px[1], abs(self.vy) * 0.3
            if abs(self.vx) > 1:
                self.slide(dt)
            elif walking:
                self.move_x(self.dir * WALK_SPEED * s * dt)
            if self.y >= self.screens[self.si].wb:
                self.land(s)
            return
        if abs(self.vx) > 5 * s:   # still sliding after a throw
            self.slide(dt)
            self.vx -= math.copysign(min(abs(self.vx), GROUND_FRICTION * s * dt), self.vx)
            return
        self.vx = 0.0
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
        casting = self.wizard.get() and time.time() < self.working_until
        if casting and self.state in ("idle", "walk", "dance"):
            self.state, self.cast_t = "work", 0.0
        if self.state == "work":
            if not casting:
                self.state, self.state_t = "idle", 2.0
            else:   # stand still, wave the wand, make sparkles
                self.cast_t += dt
                self.part_t -= dt
                if self.part_t <= 0:
                    self.spawn("spark")
                    self.part_t = random.uniform(0.08, 0.2)
                return
        if self.state == "dance":
            self.dance_t += dt
            self.state_t -= dt
            self.part_t -= dt
            if self.part_t <= 0:
                self.spawn("note")
                self.part_t = 0.45
            if self.state_t <= 0:
                self.state, self.state_t = "idle", 2.0
            return
        self.state_t -= dt
        if walking:
            self.move_x(self.dir * WALK_SPEED * s * dt)
            self.step_t += dt
            if self.step_t >= 0.18:
                self.step_t, self.step = 0.0, self.step + 1
        if self.jump.get() and not self.full() and random.random() < dt / JUMP_EVERY:
            self.jump_now(HOP_HEIGHT * s)
        if self.state_t <= 0:
            if random.random() < DANCE_CHANCE and not self.full():
                self.start_dance()
            elif self.state == "walk" or not self.walking_allowed():
                if self.naps.get() and random.random() < NAP_CHANCE and not self.details.visible:
                    self.fall_asleep("nap")
                else:
                    self.state, self.state_t = "idle", random.uniform(3, 8)
            else:
                self.state, self.state_t = "walk", random.uniform(2, 5)
                self.dir = random.choice((-1, 1))
        if self.state == "idle" and self.look_t <= 0 and random.random() < dt / 4:
            self.look_d, self.look_t = random.choice((-1, 1)), random.uniform(0.6, 1.4)

    def start_dance(self):
        if self.anim.get():
            self.state, self.state_t, self.dance_t, self.part_t = "dance", random.uniform(3.5, 6), 0.0, 0.2

    def turn(self, dt, s):
        # tilting: hangs from where you grabbed it and swings as you move, then rights itself
        if self.held:
            self.drag_vx *= max(0.0, 1 - 5 * dt)
            target, k, damp = self.hang + max(-0.7, min(0.7, -self.drag_vx * 0.0011 / s)), 40, 6
        elif self.angle or self.spin:
            target, k, damp = 0.0, 22, 5
        else:
            return
        self.spin += ((target - self.angle) * k - self.spin * damp) * dt
        self.angle += self.spin * dt
        if self.held:
            self.follow_grip()
        elif abs(self.angle) < 0.02 and abs(self.spin) < 0.2:
            self.angle = self.spin = 0.0

    def slide(self, dt):
        # moves sideways with the throw speed. bounces off the screen edge.
        want = self.x + self.vx * dt
        self.move_x(self.vx * dt)
        if abs(self.x - want) > 1:
            self.vx = -self.vx * 0.5

    def land(self, s):
        impact = self.vy
        self.y = self.screens[self.si].wb
        if self.chute:
            self.chute, self.vy, self.squash_t = False, 0.0, 0.07
            return
        if impact > 700 * s and self.bounces < 1:
            self.bounces += 1
            self.vy = -impact * 0.35   # boing
        else:
            self.vy = 0.0
            if impact > 350 * s:
                self.squash_t = 0.07   # landing squish
        if impact > 1100 * s and self.dizzy_t <= 0:
            self.dizzy_t = 2.4   # that was a hard landing: seeing stars
            if random.random() < 0.7:
                self.say(random.choice(DIZZY_LINES), force=True)
        self.vx *= 0.6

    # drawing. only redraws when something visible changed; moving is just moving the window.
    def frame(self):
        anim = self.anim.get()
        now = time.time()
        grounded = self.grounded()
        airborne = self.held or not grounded
        sleeping = anim and self.state == "sleep"
        dancing = anim and self.state == "dance" and grounded
        wiz = anim and self.state == "work" and not airborne
        full = self.full()
        squash = anim and grounded and not self.held and (self.squash_t > 0 or self.pressed)
        walking = anim and self.state == "walk" and self.walking_allowed() and grounded and not squash
        beat = int(self.dance_t / 0.25) % 4 if dancing else 0
        chute = anim and self.chute and not grounded
        if sleeping:
            legs = ()
        elif self.held:
            legs = LEGS_STEP if int(self.clock / 0.12) % 2 else LEGS_AIR   # wiggling
        elif airborne:
            legs = LEGS_AIR
        elif dancing:
            legs = LEGS_STEP if beat % 2 else LEGS_STAND
        else:
            legs = LEGS_STEP if walking and self.step % 2 else LEGS_STAND
        if sleeping or (anim and self.dizzy_t > 0):
            eyes = "closed"
        elif anim and (self.happy_t > 0 or dancing):
            eyes = "happy"
        elif anim and self.blink_t > 0:
            eyes = "closed"
        elif full and not airborne:
            eyes = "tired"   # a hard day's work
        else:
            eyes = "open"
        if wiz:
            eye_dir = 1   # watching the wand
        else:
            eye_dir = self.dir if walking else (self.look_d if anim and self.look_t > 0 and not sleeping else 0)
        if sleeping:
            sink = "lie"
        elif squash or (dancing and beat in (1, 3)) or (full and grounded and self.state == "idle"):
            sink = "half"   # squished, bopping to the beat, or slumped because the limit is full
        else:
            sink = None
        if wiz:
            arms = (ARMS[0],) + WAVE[1 - self.hand()]
        elif anim and self.stretch_t > 0 and not sleeping:
            arms = LEFT_WAVE[1] + WAVE[1]
        elif dancing:
            arms = (LEFT_WAVE[1] + (ARMS[1],), ARMS, (ARMS[0],) + WAVE[1], LEFT_WAVE[1] + WAVE[1])[beat]
        elif chute:
            arms = LEFT_WAVE[1] + WAVE[1]   # holding the strings
        elif anim and self.wave_t > 0 and not sleeping:
            arms = (ARMS[0],) + WAVE[int(self.wave_t / 0.18) % 2]
        else:
            arms = ARMS
        parts = tuple((p["kind"], round(p["x"]), round(p["y"]), p["c"]) for p in self.parts) if anim else ()
        show = (self.bubble_mode.get() != "hover" or self.hovering or self.held
                or self.details.visible or now < self.hover_until)
        speech = None
        if self.speech:
            if now > self.speech["until"] or self.hidden:
                self.speech = None
            else:
                text = self.speech["text"]
                typed = int((now - self.speech["start"]) * SPEAK_CPS) if anim else len(text)
                speech = (text, min(len(text), typed))
        bars = tuple(self.bubble_bars()) if self.bubble_style.get() == "bars" and self.data else None
        rot = None
        if anim and (self.held or self.angle):
            pw, ph = self.pet_px
            gx, gy = self.grab_local if self.held else (pw / 2, ph / 2)
            rot = (round(self.angle, 2), round(gx), round(gy))
        return (self.scale, legs, eyes, eye_dir, sink, arms, self.hand() if wiz else None, self.warn_level(),
                wiz, parts, tuple(self.bubble_segments()), bars, bool(self.error), show, speech, rot,
                round(math.sin(self.clock * 1.6) * 1.4) if chute else None,
                (0, -1, 0, 1)[beat] if dancing else 0,
                int(self.clock * 8) % 12 if anim and self.dizzy_t > 0 else None,
                sleeping and int(self.clock / 1.4) % 2 == 1)

    def redraw(self):
        f = self.frame()
        if f != self.last_frame:
            self.draw(f)
            self.last_frame = f
        self.place()

    def font(self, px, bold=True):
        if (px, bold) not in self.fonts:
            self.fonts[(px, bold)] = tkfont.Font(root=self.root, family="Segoe UI", size=-px,
                                                 weight="bold" if bold else "normal")
        return self.fonts[(px, bold)]

    def glyph(self, rows, x, y, b, color, shadow=True):
        # a little picture made of b-sized squares. color is one colour, or {letter: colour}.
        # the dark shadow makes it show on any wallpaper.
        passes = ((max(1, b // 2), SHADOW), (0, color)) if shadow else ((0, color),)
        for d, col in passes:
            for r, line in enumerate(rows):
                for i, ch in enumerate(line):
                    if ch != ".":
                        fill = col if isinstance(col, str) else col.get(ch, col["#"])
                        self.canvas.create_rectangle(x + i * b + d, y + r * b + d, x + (i + 1) * b + d,
                                                     y + (r + 1) * b + d, fill=fill, outline="")

    def draw(self, f):
        (_, legs, eyes, eye_dir, sink_kind, arms, wand, warn, wiz, parts, segs, bars, err, show_bubble,
         speech, rot, chute, shift, dizzy, breath) = f
        c = self.canvas
        c.delete("all")
        s = self.s()
        bw, bh = max(1, round(BLOCK_W * s)), max(2, round(BLOCK_H * s))
        pb = max(1, round(2 * s))     # small blocks for hearts, z's, sparks, the hat
        pet_w, pet_h = 18 * bw, 5 * bh
        font = self.font(max(8, round(11 * s)))
        pad = round(7 * s)
        if rot:
            show_bubble = False   # the usage bubble steps aside while it's tumbling about

        # usage bubble size: numbers, or two little bars
        if bars:
            lfont = self.font(max(8, round(10 * s)))
            lab_w = max(lfont.measure(lab) for lab, _, _ in bars)
            bar_w, bar_h = round(56 * s), max(3, round(5 * s))
            row_h = lfont.metrics("linespace")
            bub_w = 2 * pad + lab_w + round(6 * s) + bar_w + (round(10 * s) if err else 0)
            bub_h = len(bars) * row_h + round(6 * s)
        else:
            dot, dgap, sgap = max(4, round(6 * s)), round(4 * s), round(9 * s)
            bub_w = 2 * pad + sum(dot + dgap + font.measure(t) for t, _ in segs) + sgap * (len(segs) - 1)
            bub_h = font.metrics("linespace") + round(6 * s)
        ring = max(2, round(2 * s)) if warn else 0         # the warning ring's thickness
        tail, gap = max(2, round(4 * s)), round(2 * s) + 2 * ring + (max(2, round(1.5 * s)) if warn == 3 else 0)

        # speech bubble size
        sp_lines, sp_w, sp_h = [], 0, 0
        if speech:
            sfont = self.font(max(8, round(11 * s)), bold=False)
            key = (speech[0], s)
            if key not in self.wraps:
                self.wraps[key] = wrap(speech[0], sfont, round(190 * s))
            sp_lines = self.wraps[key]
            sp_w = max(sfont.measure(ln) for ln in sp_lines) + 2 * round(8 * s)
            sp_h = len(sp_lines) * sfont.metrics("linespace") + 2 * round(5 * s)

        side = round(30 * s)                               # room for z's, notes and sparks
        above = max((len(HAT) - 1) * pb if wiz else 0,     # room above the head: hat, parachute, stars
                    (len(CHUTE) + 10) * pb if chute is not None else 0,
                    6 * pb if dizzy is not None else 0)
        # the window is ONE fixed size whatever the mascot is doing, and its middle always sits at the
        # same spot in it. resizing or shifting the window between frames made windows flash a dark box
        # or the mascot flicker, because moving and redrawing a window don't happen at the same instant.
        hd = math.ceil(math.hypot(pet_w, pet_h) / 2) + 2   # a tilted body reaches this far from its middle
        ring_max = max(2, round(2 * s)) + max(2, round(1.5 * s))
        lh = self.font(max(8, round(11 * s)), bold=False).metrics("linespace")
        bub_max = max(2 * self.font(max(8, round(10 * s))).metrics("linespace"), font.metrics("linespace")) + round(6 * s)
        cy = (pet_h - pet_h // 2 + (len(CHUTE) + 10) * pb + round(2 * s) + 3 * ring_max + 2 * tail + bub_max
              + round(3 * s) + 4 * lh + 2 * round(5 * s) + round(40 * s))   # room for everything above it
        W = max(round(320 * s), len(CHUTE[0]) * pb + 2 * side, 2 * hd + 2 * side, bub_w + 4 * ring_max, sp_w + 4)
        cx = W // 2
        H = cy + hd
        sink = {"lie": bh, "half": bh // 2}.get(sink_kind, 0)
        up = 0

        if rot:
            # tilted: every block becomes a turned square around the body's middle
            ang = rot[0]
            ca, sa = math.cos(ang), math.sin(ang)
            mx, my = pet_w / 2, pet_h / 2
            px, py = cx - pet_w // 2, cy - pet_h // 2
            # how far the tilted body rises above its middle, so speech can sit just above it
            up = max(0, math.ceil(-min(dx * sa + dy * ca for dx in (-mx, mx) for dy in (-my, my))))

            def emit(x1, y1, x2, y2, color):
                pts = []
                for lx, ly in ((x1 - 0.5, y1 - 0.5), (x2 + 0.5, y1 - 0.5), (x2 + 0.5, y2 + 0.5), (x1 - 0.5, y2 + 0.5)):
                    dx, dy = lx - mx, ly - my
                    pts += [cx + dx * ca - dy * sa, cy + dx * sa + dy * ca]
                c.create_polygon(pts, fill=color, outline="")
        else:
            px, py = cx - pet_w // 2 + shift * max(1, bw // 2), cy - pet_h // 2

            def emit(x1, y1, x2, y2, color):
                c.create_rectangle(px + x1, py + y1, px + x2, py + y2, fill=color, outline="")

        def block(col, row, cols=1, color=ORANGE):
            y1 = row * bh + sink
            emit(col * bw, y1, (col + cols) * bw, min(y1 + bh, pet_h), color)

        # the mascot
        for row, line in enumerate(BODY):
            start, end = line.index("#"), line.rindex("#") + 1
            if row == 0 and breath:
                start, end = start + 1, end - 1   # breathing out while asleep
            block(start, row, end - start)
        for col, row in arms:
            block(col, row)
        for col in legs:
            block(col, 4)
        for col in EYES:
            x1, y1 = (col + eye_dir) * bw, bh + sink
            if eyes == "open":
                emit(x1, y1, x1 + bw, y1 + bh, EYE)
            elif eyes == "tired":   # heavy eyelids
                emit(x1, y1 + bh // 2, x1 + bw, y1 + bh, EYE)
            else:   # a thin line: low for closed, high for a happy squint
                ly = y1 + (bh // 5 if eyes == "happy" else bh // 2)
                emit(x1, ly, x1 + bw, ly + max(1, bh // 4), EYE)
        if eyes == "happy":
            for col in BLUSH:
                block(col, 2, color=BLUSH_C)
        if wiz and not rot:
            # wizard hat on the head, wand in the raised hand
            hx = px + 3 * bw + (12 * bw - len(HAT[0]) * pb) // 2
            self.glyph(HAT, hx, py + sink - (len(HAT) - 1) * pb, pb,
                       {"#": HAT_C, "y": BAND_C, "*": STAR_C}, shadow=False)
            hand_y = py + sink + wand * bh
            for i in range(5):
                x1, y1 = px + 17 * bw + i * pb, hand_y - (i + 1) * pb
                c.create_rectangle(x1, y1, x1 + pb, y1 + pb, fill=WAND_C, outline="")
            x1, y1 = px + 17 * bw + 4 * pb, hand_y - 7 * pb
            c.create_rectangle(x1, y1, x1 + 2 * pb, y1 + 2 * pb, fill=STAR_C, outline="")
        if chute is not None and not rot:
            # the parachute, with strings down to its raised hands and head
            cw = len(CHUTE[0]) * pb
            cx0, cy0 = px + pet_w // 2 - cw // 2 + chute * pb, py + sink - (len(CHUTE) + 10) * pb
            self.glyph(CHUTE, cx0, cy0, pb, {"r": CHUTE_R, "w": CHUTE_W, "#": CHUTE_R})
            cb = cy0 + len(CHUTE) * pb
            lw = max(1, round(s))
            for sx_, ex in ((cx0 + pb, px + 1.5 * bw), (cx0 + cw - pb, px + 16.5 * bw),
                            (cx0 + cw * 0.35, px + 7 * bw), (cx0 + cw * 0.65, px + 11 * bw)):
                c.create_line(sx_, cb, ex, py + sink, fill=STRING_C, width=lw)
        if dizzy is not None and not rot:
            # three little stars circling its head
            cx, cy = px + 9 * bw, py + sink - 3 * pb
            for k in range(3):
                a = dizzy / 12 * 2 * math.pi + k * 2 * math.pi / 3
                self.glyph(SPARK, cx + math.cos(a) * 7 * bw - 1.5 * pb, cy + math.sin(a) * 2 * pb - 1.5 * pb,
                           pb, STAR_C)

        # z's, notes and sparkles drift up behind the bubbles, so they never cover the words
        for kind, x, y, ci in parts:
            if kind in ("z", "Z"):
                self.glyph(ZZZ, px + x, py + y, pb + (pb // 2 + 1 if kind == "Z" else 0), ZZZ_C)
            elif kind == "spark":
                self.glyph(SPARK, px + x, py + y, pb, SPARK_C[ci], shadow=False)
            elif kind == "note":
                self.glyph(NOTE, px + x, py + y, pb, NOTE_C[ci])

        # the usage bubble. text only ever sits on solid bubbles, so there's no fuzzy edge
        # against the see-through colour.
        bx, by = (W - bub_w) // 2, py - above - gap - tail - bub_h
        if show_bubble:
            mid = W // 2
            ring_c = {1: WARN_C, 2: PANIC_C, 3: FULL_C}.get(warn, KEY)
            if warn:   # a ring around the bubble and its tail: yellow, red, or black when it's all used up
                t2 = tail + 2 * ring
                if warn == 3:   # a silver edge so the black ring shows on dark backgrounds too
                    e = max(2, round(1.5 * s))
                    round_rect(c, bx - ring - e, by - ring - e, bx + bub_w + ring + e, by + bub_h + ring + e,
                               round(5 * s) + ring + e, FULL_EDGE)
                    c.create_polygon(mid - t2 - e, by + bub_h, mid + t2 + e, by + bub_h, mid, by + bub_h + t2 + e,
                                     fill=FULL_EDGE, outline="")
                round_rect(c, bx - ring, by - ring, bx + bub_w + ring, by + bub_h + ring, round(5 * s) + ring,
                           ring_c, bg=FULL_EDGE if warn == 3 else KEY)
                c.create_polygon(mid - t2, by + bub_h - 1, mid + t2, by + bub_h - 1, mid, by + bub_h + t2,
                                 fill=ring_c, outline="")
            round_rect(c, bx, by, bx + bub_w, by + bub_h, round(5 * s), BUBBLE, bg=ring_c, smooth=bool(warn))
            c.create_polygon(mid - tail, by + bub_h - 1, mid + tail, by + bub_h - 1, mid, by + bub_h + tail,
                             fill=BUBBLE, outline="")
            if bars:
                y = by + round(3 * s)
                for lab, pct, color in bars:
                    ym = y + row_h // 2
                    c.create_text(bx + pad, ym, anchor="w", text=lab, fill=BUBBLE_TEXT, font=lfont)
                    x1 = bx + pad + lab_w + round(6 * s)
                    c.create_rectangle(x1, ym - bar_h // 2, x1 + bar_w, ym - bar_h // 2 + bar_h, fill=TRACK, outline="")
                    c.create_rectangle(x1, ym - bar_h // 2, x1 + round(bar_w * min(pct, 100) / 100),
                                       ym - bar_h // 2 + bar_h, fill=color, outline="")
                    y += row_h
                if err:
                    d = max(4, round(6 * s))
                    c.create_oval(bx + bub_w - pad - d + round(2 * s), by + round(4 * s),
                                  bx + bub_w - pad + round(2 * s), by + round(4 * s) + d, fill=RED, outline="")
            else:
                x, ym = bx + pad, by + bub_h // 2
                for i, (text, color) in enumerate(segs):
                    if i:
                        x += sgap
                    c.create_oval(x, ym - dot // 2, x + dot, ym - dot // 2 + dot, fill=color, outline="")
                    x += dot + dgap
                    c.create_text(x, ym, anchor="w", text=text, fill=BUBBLE_TEXT, font=font)
                    x += font.measure(text)

        # the speech bubble, above the usage bubble. it types itself out.
        if speech:
            sx, sy = (W - sp_w) // 2, by - ring - tail - round(3 * s) - sp_h
            if rot:
                sy = cy - up - round(6 * s) - tail - sp_h
            round_rect(c, sx, sy, sx + sp_w, sy + sp_h, round(6 * s), SPEECH)
            mid = W // 2
            c.create_polygon(mid - tail, sy + sp_h - 1, mid + tail, sy + sp_h - 1, mid, sy + sp_h + tail,
                             fill=SPEECH, outline="")
            left, lh = speech[1], sfont.metrics("linespace")
            for i, ln in enumerate(sp_lines):
                if left <= 0:
                    break
                c.create_text(sx + round(8 * s), sy + round(5 * s) + i * lh, anchor="nw", text=ln[:left],
                              fill=SPEECH_TEXT, font=sfont)
                left -= len(ln) + 1

        # hearts pop up above everything
        for kind, x, y, _ in parts:
            if kind == "heart":
                self.glyph(HEART, px + x, py + y, pb, HEART_C)

        if (W, H) != self.size:
            c.configure(width=W, height=H)
        self.size, self.half, self.top_margin = (W, H), max(pet_w, bub_w, sp_w) / 2 + 2, by
        self.center_x, self.feet_win = cx, cy - pet_h // 2 + pet_h   # where the body sits in the window
        self.body_at, self.pet_px = (px, py), (pet_w, pet_h)
        highest = sy if speech else by if show_bubble else py - above
        self.bubble_top = highest - py   # relative to the head: where new hearts appear
        body = (cx - hd, cy - hd, cx + hd, cy + hd) if rot else (px, py - above, px + pet_w, py + pet_h)
        self.rects = {"pet": body, "bubble": (bx, by, bx + bub_w, by + bub_h + tail) if show_bubble else None}


# ---- menu tooltips ----

class Tooltip:
    BG, BORDER, FG, DIM = "#1f1e1d", "#3a3a3c", "#f2efe8", "#a8a8ad"
    TAGS = {"On": "#7bd88f", "Off": "#8e8e93"}   # other tags (choices) are amber

    def __init__(self, pet):
        self.pet = pet
        self.win = tk.Toplevel(pet.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=self.BORDER)
        self.win.geometry(f"10x10+{PARK}+{PARK}")   # parked off screen until needed
        self.canvas = tk.Canvas(self.win, bg=self.BG, highlightthickness=0)
        self.canvas.pack(padx=1, pady=1)
        self.job, self.rounded, self.fonts = None, False, {}

    def font(self, size, bold=False):
        px = max(8, round(size * self.pet.dpi))
        if (px, bold) not in self.fonts:
            self.fonts[(px, bold)] = tkfont.Font(root=self.win, family="Segoe UI", size=-px,
                                                 weight="bold" if bold else "normal")
        return self.fonts[(px, bold)]

    def hover(self, menu):
        # the highlighted menu item changed: show its tooltip after a short pause
        self.hide()
        try:
            i = menu.index("active")
            label = menu.entrycget(i, "label").strip() if i is not None else ""
        except tk.TclError:
            label = ""   # a separator, or nothing highlighted
        if label in TIPS:
            try:
                row_y = menu.yposition(i)   # where the item sits inside the menu
            except tk.TclError:
                row_y = 0
            self.job = self.win.after(350, lambda: self.show(label, row_y))

    def show(self, label, row_y=0):
        self.job = None
        desc, rows = TIPS[label]
        s, c = self.pet.dpi, self.canvas
        c.delete("all")
        pad, width = round(10 * s), round(260 * s)
        tag_w = max([self.font(12, True).measure(tag) for tag, _ in rows] or [0]) + round(8 * s)
        item = c.create_text(pad, pad, anchor="nw", text=desc, fill=self.FG, font=self.font(12.5, True), width=width)
        y = c.bbox(item)[3] + round(7 * s)
        for tag, text in rows:
            c.create_text(pad, y, anchor="nw", text=tag, fill=self.TAGS.get(tag, "#d9a441"), font=self.font(12, True))
            item = c.create_text(pad + tag_w, y, anchor="nw", text=text, fill=self.DIM, font=self.font(12),
                                 width=width - tag_w)
            y = c.bbox(item)[3] + round(4 * s)
        w, h = width + 2 * pad, y + pad - round(4 * s)
        c.configure(width=w, height=h)
        # next to the open menu: on its left (the right side is where submenus open), or right if no room
        p = self.pet
        mx, my = p.root.winfo_pointerxy()
        rects = menu_rects()
        on_menu = next((r for r in rects if r[0] <= mx < r[2] and r[1] <= my < r[3]), None)
        r = on_menu or (rects[0] if rects else (mx, my, mx, my))
        if not on_menu:   # using the keyboard: line up with the highlighted item instead of the mouse
            my = r[1] + row_y + round(10 * s)
        cx, cy = (r[0] + r[2]) // 2, (r[1] + r[3]) // 2
        si = p.find_screen(cx, cy)
        sc = p.screens[si if si is not None else p.nearest_screen(cx, cy)]
        x = r[0] - w - 2 - round(6 * s)
        if x < sc.wl:
            x = r[2] + round(6 * s)
        y = min(max(sc.wt, my - round(12 * s)), sc.wb - h - 2)
        self.win.geometry(f"{w + 2}x{h + 2}+{x}+{y}")
        self.win.update_idletasks()   # apply the move now: while a menu is open tk may hold it back
        if (self.win.winfo_x(), self.win.winfo_y()) != (x, y):
            hwnd = u32.GetParent(self.win.winfo_id()) or self.win.winfo_id()
            u32.SetWindowPos(hwnd, None, x, y, w + 2, h + 2, 0x0014)   # SWP_NOZORDER | SWP_NOACTIVATE
        self.win.lift()
        if not self.rounded:
            round_corners(self.win)
            self.rounded = True

    def hide(self):
        if self.job:
            self.win.after_cancel(self.job)
            self.job = None
        self.win.geometry(f"+{PARK}+{PARK}")


# ---- details panel (hover the mascot) ----

PANEL_W = 320
HEAT = ["#2c2c2e", "#173c6e", "#1f57a6", "#2b74e0", "#5aa2ff"]   # empty day, then busier and busier


class Details:
    BG, FG, DIM, CARD = "#1c1c1e", "#f2f2f7", "#8e8e93", "#2c2c2e"
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
        self.hits, self.rect, self.px_size, self.fonts = [], None, (10, 10), {}
        self.anchor_x = self.anchor_bottom = 0
        self.s = 1.0
        self.curve_key, self.curve = None, []   # cached estimate for the plan chart
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
        p = self.pet
        for name, x1, y1, x2, y2 in self.hits:
            if x1 <= e.x <= x2 and y1 <= e.y <= y2:
                if name == "close":
                    self.hide()
                    return
                kind, val = name.split(":")
                {"tab": p.panel_tab, "view": p.cc_view, "range": p.cc_range, "chart": p.plan_chart}[kind].set(val)
                self.draw()
                p.save()
                return

    # drawing helpers. positions are in base units (PANEL_W wide) times self.s.
    def font(self, size, bold=False):
        px = max(8, round(size * 4 / 3 * self.s))
        if (px, bold) not in self.fonts:
            self.fonts[(px, bold)] = tkfont.Font(root=self.win, family="Segoe UI", size=-px,
                                                 weight="bold" if bold else "normal")
        return self.fonts[(px, bold)]

    def text(self, x, y, text, fill, size, bold=False, anchor="nw", width=None):
        kw = {"width": width * self.s} if width else {}
        item = self.canvas.create_text(x * self.s, y * self.s, anchor=anchor, fill=fill, font=self.font(size, bold),
                                       text=text, **kw)
        return self.canvas.bbox(item)[3] / self.s   # where the text ends, for wrapped lines

    def rect_(self, x1, y1, x2, y2, fill):
        s = self.s
        self.canvas.create_rectangle(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=0)

    def line(self, x1, y1, x2, y2, fill, width=1):
        s = self.s
        self.canvas.create_line(x1 * s, y1 * s, x2 * s, y2 * s, fill=fill, width=max(1, round(width * s)))

    def pill(self, x, y, label, on, hit, right=False):
        # a small tab button. returns its width.
        s = self.s
        w = self.font(8, True).measure(label) / s + 12
        if right:
            x -= w
        if on:
            round_rect(self.canvas, x * s, y * s, (x + w) * s, (y + 17) * s, 4 * s, TRACK, self.BG, True)
        self.text(x + 6, y + 8.5, label, self.FG if on else self.DIM, 8, True, "w")
        self.hits.append((hit, x * s, y * s, (x + w) * s, (y + 17) * s))
        return w

    def draw(self):
        p = self.pet
        self.s = s = p.dpi * min(1.6, max(1.0, p.scale))
        # every tab and view gets the same height, so the tabs never jump when you switch
        tallest = 0
        for tab, view in (("plan", "overview"), ("cc", "overview"), ("cc", "models")):
            tallest = max(tallest, self.draw_tab(tab, view))
        self.draw_tab(p.panel_tab.get(), p.cc_view.get())
        H = tallest + 12
        self.px_size = (round(PANEL_W * s), round(H * s))
        self.canvas.configure(width=self.px_size[0], height=self.px_size[1])
        self.place()

    def draw_tab(self, tab, view):
        # draws one tab from scratch and returns how tall it came out
        p, s, W = self.pet, self.s, PANEL_W
        self.canvas.delete("all")
        self.hits = []
        x = 10
        for name, label in (("plan", "Plan"), ("cc", "Claude Code")):
            x += self.pill(x, 8, label, tab == name, "tab:" + name) + 4
        self.text(W - 16, 7, "\u00d7", self.DIM, 11, True, "n")      # close button
        self.hits.append(("close", (W - 30) * s, 2 * s, (W - 2) * s, 28 * s))
        return self.draw_plan(38) if tab == "plan" else self.draw_cc(38, view)

    def draw_plan(self, y):
        p = self.pet
        W = PANEL_W
        rows = parse_rows(p.data) if p.data else []
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        now = time.time()
        wait = "updating..." if p.busy else f"next update in {max(0, math.ceil(p.next_at - now))}s"
        self.text(12, y, (f"updated {p.updated:%H:%M} · " if p.updated else "") + wait, self.DIM, 8)
        y += 22
        for r in rows:
            seen = p.seen.get(r["key"])
            unchanged = now - seen[1] if seen else 0
            el, msg, kind = pace_info(r["key"], r["pct"], r["resets"], now_dt, unchanged)
            self.text(12, y, r["label"], self.FG, 9, True)
            self.text(W - 12, y, f"{r['pct']:.0f}%", self.FG, 9, True, "ne")
            self.rect_(12, y + 20, W - 12, y + 26, TRACK)
            self.rect_(12, y + 20, 12 + (W - 24) * min(r["pct"], 100) / 100, y + 26, bar_color(r["pct"]))
            if el is not None:   # the pace tick: where the clock is in this window
                tx = 12 + (W - 24) * el / 100
                self.line(tx, y + 16, tx, y + 30, self.FG, 2)
            when = parse_time(r["resets"])
            at = f" · at {when.astimezone():{'%H:%M' if r['key'] == 'five_hour' else '%a %H:%M'}}" if when else ""
            self.text(12, y + 32, reset_text(r["resets"], now_dt) + at, self.DIM, 8)
            if msg:
                y = self.text(12, y + 46, msg, self.FASTC if kind == "fast" else self.SLOWC, 8, True,
                              width=W - 24) + 8
            else:
                y += 54
        if p.error:
            y = self.text(12, y, p.error, RED, 8, width=W - 24) + 10
        elif not rows:
            self.text(12, y, "loading...", self.DIM, 8)
            y += 20
        if rows:
            y = self.draw_chart(y + 6, rows, now_dt)
        st = p.cc_stats()
        if st:
            self.text(12, y, f"Claude Code today: {fmt_tokens(st['today'])} tokens", self.DIM, 8)
            y += 18
        return y

    def draw_chart(self, y, rows, now_dt):
        # usage so far in the current window, against the pace line, plus a forecast
        p, s, W = self.pet, self.s, PANEL_W
        which = p.plan_chart.get()
        key = "five_hour" if which == "5h" else "seven_day"
        r = next((r for r in rows if r["key"] == key), None)
        self.text(12, y + 8.5, "This window", self.FG, 8.5, True, "w")
        x = W - 10
        for name, label in (("7d", "Week"), ("5h", "5-hour")):
            x -= self.pill(x, y, label, which == name, "chart:" + name, right=True) + 2
        y += 26
        reset = parse_time(r["resets"]) if r else None
        if not r or reset is None:
            self.text(12, y, "No data for this limit yet.", self.DIM, 8)
            return y + 24
        period = period_seconds(key)
        start = reset.timestamp() - period
        now = time.time()
        pts = [(h[0], h[1] if key == "five_hour" else h[2]) for h in p.history if h[0] >= start]
        pts = [(tt, v) for tt, v in pts if v is not None]
        # before the pet's first check in this window there's no real data. estimate it from when
        # claude code used tokens, scaled so it meets the first real number. drawn dotted.
        first_t, first_v = pts[0] if pts else (now, r["pct"])
        est = []
        if first_t - start > 300 and first_v > 0:
            ck = (round(start), round(first_t), len(p.cc.answers))
            if self.curve_key != ck:
                self.curve_key, self.curve = ck, p.cc.usage_curve(start, first_t)
            if self.curve and self.curve[-1][1] > 0:
                k = first_v / self.curve[-1][1]
                est = [(start, 0.0)] + [(tt, v * k) for tt, v in self.curve] + [(first_t, first_v)]
            else:
                est = [(start, 0.0), (first_t, first_v)]
        pts = pts + [(now, r["pct"])]
        # the box
        x0, x1, y0, y1 = 12, W - 12, y, y + 74
        round_rect(self.canvas, x0 * s, y0 * s, x1 * s, y1 * s, 6 * s, self.CARD, self.BG, True)
        ix0, ix1, iy0, iy1 = x0 + 8, x1 - 8, y0 + 8, y1 - 8
        fx = lambda tt: ix0 + (ix1 - ix0) * min(1.0, max(0.0, (tt - start) / period))
        fy = lambda v: iy1 - (iy1 - iy0) * min(100.0, max(0.0, v)) / 100
        for v in (50, 100):   # faint guide lines at 50% and 100%
            self.rect_(ix0, fy(v), ix1, fy(v) + 0.6, "#3a3a3c")
        self.text(ix0 + 2, fy(100) + 1, "100%", "#6e6e73", 6.5)
        # the pace line: where you'd be if you used it evenly until the reset
        self.canvas.create_line(fx(start) * s, fy(0) * s, fx(reset.timestamp()) * s, fy(100) * s,
                                fill="#6e6e73", width=max(1, round(s)), dash=(3, 3))
        color = bar_color(r["pct"])
        if est:
            line = []
            for tt, v in est:
                line += [fx(tt) * s, fy(v) * s]
            self.canvas.create_line(*line, fill=color, width=max(2, round(2 * s)), dash=(2, 3))
        if len(pts) >= 2:
            line = []
            for tt, v in pts:
                line += [fx(tt) * s, fy(v) * s]
            self.canvas.create_line(*line, fill=color, width=max(2, round(2 * s)))
        nx, ny = fx(now) * s, fy(r["pct"]) * s
        d = max(3, round(3 * s))
        self.canvas.create_oval(nx - d, ny - d, nx + d, ny + d, fill=color, outline="")
        if len(pts) < 2 and not est:
            self.text((ix0 + ix1) / 2, iy0 + 16, "the line fills in as I check your usage", self.DIM, 7.5,
                      anchor="n")
        fmt = "%H:%M" if key == "five_hour" else "%a"
        self.text(x0, y1 + 3, f"{datetime.datetime.fromtimestamp(start):{fmt}}", "#6e6e73", 7)
        self.text(x1, y1 + 3, f"resets {reset.astimezone():{'%H:%M' if key == 'five_hour' else '%a %H:%M'}}",
                  "#6e6e73", 7, anchor="ne")
        if est:
            self.text((x0 + x1) / 2, y1 + 3, "dotted = estimate", "#6e6e73", 7, anchor="n")
        y = y1 + 20
        # the forecast
        el = elapsed_pct(key, r["resets"], now_dt)
        if el is None or el < 3 or r["pct"] <= 0:
            msg, col = "Too early in this window for a forecast.", self.DIM
        else:
            proj = r["pct"] / el * 100
            if proj >= 100 and r["pct"] < 100:
                out = start + (now - start) * 100 / r["pct"]
                left = reset.timestamp() - out
                fmt = "%H:%M" if key == "five_hour" else "%a %H:%M"
                gap = f"{left / 3600:.0f}h" if left >= 3600 else f"{left / 60:.0f}m"
                msg, col = (f"At this pace you'll run out around {datetime.datetime.fromtimestamp(out):{fmt}}, "
                            f"about {gap} before the reset."), self.FASTC
            elif r["pct"] >= 100:
                msg, col = "All used up. It comes back at the reset.", RED
            else:
                msg, col = f"At this pace you'll use about {proj:.0f}% by the reset.", "#4caf7d"
        return self.text(12, y, msg, col, 8, True, width=W - 24) + 12

    def draw_cc(self, y, view):
        p = self.pet
        W, s = PANEL_W, self.s
        rng = p.cc_range.get()
        x = 10
        for name, label in (("overview", "Overview"), ("models", "Models")):
            x += self.pill(x, y, label, view == name, "view:" + name) + 2
        x = W - 10
        for name, label in (("7d", "7d"), ("30d", "30d"), ("all", "All")):
            x -= self.pill(x, y, label, rng == name, "range:" + name, right=True) + 2
        y += 32
        st = p.cc_stats()
        if st is None:
            self.text(12, y, "reading Claude Code's logs...", self.DIM, 8)
            return y + 20
        r = st["ranges"][rng]
        if not r["messages"]:
            self.text(12, y, "No Claude Code activity on this computer in this period.", self.DIM, 8, width=W - 24)
            return y + 34
        if view == "overview":
            fav = pretty_model(r["models"][0][0]) if r["models"] else "-"
            cards = [("Sessions", f"{r['sessions']:,}"), ("Messages", f"{r['messages']:,}"),
                     ("Total tokens", fmt_tokens(r["tokens"])), ("Active days", f"{r['days']:,}"),
                     ("Peak hour", "-" if r["peak"] is None else hour_label(r["peak"])), ("Favorite model", fav)]
            cw = (W - 28 - 16) / 3
            for i, (label, val) in enumerate(cards):
                cx, cy = 14 + (i % 3) * (cw + 8), y + (i // 3) * 50
                round_rect(self.canvas, cx * s, cy * s, (cx + cw) * s, (cy + 42) * s, 6 * s, self.CARD, self.BG, True)
                self.text(cx + 8, cy + 6, label, self.DIM, 7.5)
                self.text(cx + 8, cy + 21, val, self.FG, 9.5, True)
            y += 106
            # activity over the last 26 weeks, one square per day, sunday at the top
            heat, today = st["heat"], datetime.date.today()
            start = today - datetime.timedelta(days=(today.weekday() + 1) % 7 + 7 * 25)
            busiest = max([v for d, v in heat.items() if d >= start] or [0])
            pitch = int((W - 28) * s // 26)            # whole pixels, so every square is the same size
            cell = pitch - max(2, round(2 * s))
            gx, gy = round(14 * s), round(y * s)
            for col in range(26):
                for row in range(7):
                    d = start + datetime.timedelta(days=col * 7 + row)
                    if d > today:
                        continue
                    v = heat.get(d, 0)
                    lvl = 1 + min(3, int(4 * v / busiest)) if v and busiest else 0
                    x0, y0 = gx + col * pitch, gy + row * pitch
                    self.canvas.create_rectangle(x0, y0, x0 + cell, y0 + cell, fill=HEAT[lvl], width=0)
            y += 7 * pitch / s + 12
            y = self.text(14, y, compare_line(r["tokens"]), self.DIM, 8, width=W - 28) + 12
        else:
            total = r["tokens"] or 1
            for m, t in r["models"][:4]:
                self.text(12, y, pretty_model(m), self.FG, 9, True)
                self.text(W - 12, y, f"{fmt_tokens(t)} · {100 * t / total:.0f}%", self.FG, 9, True, "ne")
                self.rect_(12, y + 20, W - 12, y + 25, TRACK)
                self.rect_(12, y + 20, 12 + (W - 24) * t / total, y + 25, ORANGE)
                y += 34
            i_, o_, w_, r_ = r["parts"]
            self.text(12, y, f"input {fmt_tokens(i_)} · output {fmt_tokens(o_)}", self.DIM, 8)
            self.text(12, y + 16, f"cache write {fmt_tokens(w_)} · cache read {fmt_tokens(r_)}", self.DIM, 8)
            y += 44
        how = ("Counted like the Claude app (every logged copy), from this computer's logs." if p.cc_app.get()
               else "Real count (each answer once), from this computer's logs.")
        return self.text(14, y, how, self.DIM, 7, width=W - 28) + 4


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
