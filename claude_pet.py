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
import collections
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
import traceback
import webbrowser
import tempfile
import wave
import struct
import winsound
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
CHATTER = {"off": 0, "some": 1.0, "lots": 2.5}   # how often it talks (menu: chatter)
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
STALE_MIN = 10             # numbers older than this (and 3 checks) look faded in the bubble
ERROR_LOG_KB = 200         # pet_errors.log is trimmed to stay about this small
# keyboard shortcuts: (modifiers, key) with windows' codes. modifiers: 1 alt, 2 ctrl, 4 shift, 8 win.
SHORTCUTS = (("pet", "Show / hide the mascot", "Hides it completely (it keeps checking your usage), or brings it back."),
             ("details", "Open the details panel", "Pins the Plan / Claude Code panel open, or closes it."))
DEFAULT_KEYS = {"pet": [3, ord("P")], "details": [3, ord("D")]}   # ctrl + alt + P, ctrl + alt + D
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
    "you look like someone who writes great commit messages.", "fun fact: I have never once read the docs.",
    "tabs or spaces? careful, this is a test.", "every bug you fix makes me 1% prouder.",
    "I'm not saying you're a genius, but I'm not NOT saying it.", "keep going. I'm cheering quietly.",
    "your code is like me: small, orange and full of surprises.", "deep breath. you've got this.",
]
WORK_START = ["*thinking*", "ooh, a new job!", "on it!", "let me cook.", "time for some magic.",
              "summoning tokens...", "wizard hat: on.", "a quest!"]
WORKING = ["*thinking really hard*", "this is quite the job you got for me.",
           "abracadabra... *writes code*", "tokens go brrr.", "hmm, interesting...",
           "casting a big spell here.", "don't look, I'm concentrating.", "almost... maybe...",
           "my wand is getting warm.", "so many tokens. so little time.",
           "reading your files. no judging. ok, a little judging.", "*furious wand waving*",
           "if this works, I'm taking credit."]
WORK_DONE = ["phew! done.", "that was a good one.", "*wipes forehead*", "ta-da!", "magic complete.", "another one bites the dust.",
             "done! that wand needs a nap."]
IDLE_LINES = ["it's quiet... too quiet.", "need anything? I'm just standing here.",
              "I could be useful, you know.", "my wand is getting dusty.", "*taps foot*",
              "zero tokens. a peaceful day.", "anyone? hello?", "I'm on standby. very professional.",
              "I alphabetised your desktop icons. in my head.", "nothing to do. this is fine."]
POKE_LINES = ["hey!", "hehe", "that tickles!", "boop.", "yes?", "I'm awake, I'm awake!", "beep!",
              "do that again. no, wait.", "you rang?", "*giggles in pixels*", "personal space! (just kidding)",
              "that's my good side.", "poke detected. responding with joy.", "ow. (not really)"]
POKE_COUNT = {10: "that's 10 pokes. we're friends now.", 50: "poke #50! I'm keeping count.",
              100: "100 pokes. a true bond.", 500: "500 pokes?! are you okay?"}
DRAG_LINES = ["wheee!", "where are we going?", "put me down! (actually this is fun)", "is this a kidnapping?",
              "my legs are dangling!", "first class, please.", "careful, I'm fragile. ish.", "taxi!"]
WAKE_LINES = ["welcome back!", "oh hi! I wasn't sleeping.", "you're back!",
              "I missed you! (I counted pixels.)", "there you are!"]
RESET_LINES = ["fresh limits! let's go!", "5-hour limit reset. I feel brand new."]
THROW_LINES = ["AAAAAAAAA!", "WHEEEEEEEE—", "I'M FLYIIIING!", "not the face, not the face!", "I CAN SEE MY HOUSE!", "TELL MY TOKENS I LOVE THEM!",
               "this is NOT in my job description!", "I regret nothing!"]
DIZZY_LINES = ["@_@ everything is spinning...", "I see stars. pixel stars.", "who moved the taskbar?",
               "I'm fine. I'm fine. which way is up?", "why are there three of you?",
               "*wobbles*"]
CHUTE_LINES = ["good thing I packed a parachute.", "safety first!", "*floats majestically*",
               "enjoying the view up here.", "gently does it...", "*parachute noises*"]
FALL_LINES = ["geronimo!", "whoops—", "I meant to do that!", "taking the stairs. the fast way.",
              "bye-bye window!", "jumping is just falling with confidence."]
DIVE_LINES = ["leap of faith!", "*eagle screech*", "I saw this in a game once.", "there'd better be hay down there.",
              "trust me, I'm a professional.", "swan dive!", "no stairs? no problem.", "see you at the bottom!"]
HAY_LINES = ["hay! right where I left it.", "*pfft* straw in my mouth.", "perfectly safe. totally planned.",
             "who leaves hay lying around? thank you, whoever you are.", "nailed it. itchy, but nailed it.",
             "10/10. would dive again.", "*emerges majestically*"]
SLAP_LINES = ["*splat*", "WALL.", "ow, my face.", "that window is harder than it looks.", "I'm ok!",
              "who put a wall there?", "*slides down slowly*", "nobody saw that. right?"]
SQUISH_LINES = ["hey! I was standing there!", "no room! going down!", "squished! see you on the taskbar.",
                "ok ok, I'll move. downstairs.", "rude. I had a lease on that spot.", "evicted!"]
# jumping to another window: before, after a good landing, after a bad one
LEAP_TRY = ["I can make that.", "hold my tokens.", "parkour!", "trust the process.", "3... 2... 1...",
            "ok. big jump. no big deal.", "calculating trajectory... roughly.", "watch this!",
            "I've done this before. in my dreams.", "yolo.", "for science!", "this is a terrible idea. here goes!"]
LEAP_OK = ["nailed it.", "did you see that?!", "10/10 landing.", "and the crowd goes wild!", "too easy.",
           "*bows*", "gold medal, please.", "new personal best!", "smooth. like butter.", "I'm basically a ninja."]
LEAP_FAIL = ["that window moved. I swear.", "nobody saw that.", "I meant to do that.", "gravity: 1, me: 0.",
             "ow. my pixels.", "the floor came out of nowhere.", "practice run. it was a practice run.",
             "who put that gap there?", "I underestimated the distance. and overestimated me.",
             "still a 7/10 for style.", "let's never speak of this."]
# things it says now and then, depending on what it's up to
WALK_LINES = ["going for a walk. don't wait up.", "left foot, right foot, left foot...", "on patrol.",
              "where am I going? no idea. very exciting.", "*whistles*", "inspecting the taskbar. looks solid.",
              "exploring! what's over here?", "these legs were made for walking. all four of them.",
              "daily steps: 37.", "just stretching my legs.", "I wonder what's on the other side of the screen.",
              "hey, is that a new icon?"]
HIGH_LINES = ["the view from up here is amazing.", "king of the window!", "I can see my taskbar from here!",
              "this window is comfy. I'm staying.", "don't close this one, ok? I live here now.",
              "it's windy up here. metaphorically.", "I'm on top of things. literally.",
              "*sits on your window* hope you don't mind.", "ooh, high ground."]
DANCE_LINES = ["*dances*", "can't stop, won't stop.", "this is my jam!", "busting a move!", "feel the rhythm!",
               "watch my legs go!", "♪ tokens, tokens, everywhere ♪", "dance break!"]
SLEEP_LINES = ["zzz... five more tokens...", "zzz...", "*snore*", "mmm... rate limits... no...",
               "zzz... I'm a big model now...", "*mumbles about semicolons*", "zzz... the cache is warm..."]
CURIOUS_LINES = ["what does this button do? (I don't have buttons.)", "do windows dream of electric sheep?",
                 "I wonder how many tokens a hug costs.", "what's your favourite colour? mine's orange. obviously.",
                 "is the cursor alive? it moves on its own...", "if I jump high enough, can I reach the tabs?",
                 "why is it called a taskbar if there are no snacks?", "what happens if I walk off the screen? (please don't let me)",
                 "I've been thinking. mostly about rectangles.", "how many pixels tall are you?",
                 "what are we building today?", "does the mouse ever get tired?", "I heard there's a recycle bin. spooky.",
                 "can I have a window of my own one day?", "sometimes I count the windows. you have a lot.",
                 "what's the wifi password? asking for a friend.", "beep boop. I'm not a robot. I'm a crab. sort of."]
ATTENTION_LINES = ["psst... hey. got a minute?", "*polite cough*", "I'm still here, by the way!",
                   "a little poke would be nice. no pressure.", "hello? it's me, your tiny assistant.",
                   "I did a cool jump earlier. you missed it."]
BORED_LINES = ["I counted all the pixels on your taskbar. twice.", "bored. so bored.",
               "should I take up a hobby? knitting, maybe.", "no tokens today? I'll just... stand here.",
               "I've been practising my dance moves.", "is it home time yet?"]
MORNING_LINES = ["good morning! ready when you are.", "morning! let's make today a good one.",
                 "rise and shine! (I've been up for ages)", "good morning! I kept your taskbar warm."]
LATE_LINES = ["it's late... maybe wrap up soon?", "past midnight. the code will still be here tomorrow.",
              "*yawn* aren't you sleepy?", "night owl mode. don't forget to sleep!"]
OOPS_LINES = ["oops, something went wrong in there.", "uh oh. a tool tripped over.",
              "that didn't work. Claude will try again!", "*winces* an error. it happens."]
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
# what each setting does (shown under it in the settings window), then its on/off effects or choices
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
    "Personality": ("How much the mascot moves about.", [
        ("Parkour!", "Always on the move: runs about, jumps from window to window, and takes leaps of faith "
                     "off window edges into a pile of hay. Hardly ever naps."),
        ("Lively", "Walks a lot, jumps to windows nearby, and sometimes dives off edges."),
        ("Normal", "A bit of walking, a bit of standing about, the odd jump and nap."),
        ("Chill", "Mostly hangs out. Short strolls, rare jumps, plenty of naps."),
        ("Statue", "Stays in one spot. It still blinks, reacts, hops when poked and talks.")]),
    "Walk around": ("Lets the mascot wander along the taskbar.", [
        ("On", "It walks left and right, and across to your other monitors."),
        ("Off", "It stays in one spot, but still blinks, hops and reacts.")]),
    "Jump now and then": ("Random little hops.", [
        ("On", "It hops about every 30 seconds, and now and then jumps over to a window nearby (if Stand on "
               "windows is on). It doesn't always make it."),
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
        ("Sometimes", "A line every minute or two about whatever it's up to, plus reactions to what's happening."),
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
    "Settings…": ("Opens a window with every option in one place, each with a short description.", []),
    "Stand on windows": ("Lets the mascot land on top of your windows, and makes windows solid.", [
        ("On", "When it falls (dropped, thrown or walking off an edge) past the top of a window, it lands there, "
               "rides along if you move the window, and falls off when it closes. Windows in front push it "
               "aside, and if it's cornered it drops down to the taskbar. On the taskbar, windows push it aside too."),
        ("Off", "It only ever stands on the taskbar.")]),
    "Sound effects": ("Turns all of the mascot's sounds on or off. Pick which ones below.", [
        ("On", "Plays the sounds you've picked (quietly, through Windows' normal sound output). This is the default."),
        ("Off", "Silent.")]),
    "Which sounds": ("Tap a sound to switch it on or off. Switching one on plays it.", []),
    "Desktop notifications": ("Windows notifications for the important moments.", [
        ("On", "A notification at 90% and 100% of a limit, when a nearly-used limit resets, and when your login "
               "expires. Shows even while the mascot is hidden."),
        ("Off", "Only the mascot's own speech bubbles.")]),
    "Keyboard shortcuts": ("Shortcuts that work anywhere in Windows, even when another app is in front.", [
        ("On", "The shortcuts below work."),
        ("Off", "They do nothing, and other apps can use those keys.")]),
    "Shortcuts": ("Click a shortcut, then press the new keys. Esc cancels, Backspace clears it.", []),
    "Quit": ("Closes the mascot. Your settings and its memory are saved first.", []),
    "Volume": ("How loud the sound effects are. You'll hear a sample when you let go.", []),
    "Size": ("How big the mascot is. Ctrl + mouse wheel over it works too.", []),
    "Bubble shows": ("Which limits the bubble above its head shows, or only show it when you hover.", []),
    "Bubble style": ("Numbers, or two small bars.", []),
    "Clock": ("How times are shown in the details panel, like when a limit resets.", []),
    "Dates": ("Day first or month first, like Fri 16/10 or Fri 10/16.", []),
    "Yellow ring from": ("When the warning ring turns yellow.", []),
    "Red ring from": ("When the warning ring turns red. It turns black at 100%.", []),
}

# api list prices, dollars per million tokens: (model id starts with, input, output, cache read).
# cache writes cost 1.25x input (5 minute cache) or 2x input (1 hour cache). first match wins.
# these are what the same tokens would cost on the api. on a subscription plan you don't pay them.
PRICES = [("claude-opus-5-5", 4, 20, 0.20), ("claude-opus-5", 5, 25, 0.50), ("claude-opus-4", 5, 25, 0.50),
          ("claude-fable-5-1", 10, 50, 0.25), ("claude-fable-5", 10, 50, 1.00), ("claude-mythos", 10, 50, 0.25),
          ("claude-sonnet-5", 2, 10, 0.20), ("claude-sonnet-4", 3, 15, 0.30),
          ("claude-haiku-5", 0.10, 0.50, 0.01), ("claude-haiku-4", 1, 5, 0.10)]


def answer_cost(a):
    # api-price dollars for one logged answer, or None for a model we don't have a price for
    price = next((pr for pr in PRICES if a[2].startswith(pr[0])), None)
    if price is None:
        return None
    _, pin, pout, pread = price
    cw1h = a[7] if len(a) > 7 else 0
    return (a[3] * pin + a[4] * pout + (a[5] - cw1h) * 1.25 * pin + cw1h * 2 * pin + a[6] * pread) / 1e6


def fmt_money(d):
    return f"${d:,.2f}" if d < 1000 else f"${d:,.0f}"


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
HAY_C = ["#e3b54a", "#f4d77c", "#b8862c"]   # hay: base, light straw, dark straw
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


LOGIN_HELP = ("To fix it, Claude Code needs to log you in again:\n"
              "1. Press the Windows key, type cmd and press Enter. A black Command Prompt window opens.\n"
              "2. Type claude and press Enter.\n"
              "3. If it asks you to log in, follow the steps (type /login and press Enter if it doesn't ask). "
              "Your browser opens: sign in to your Claude account and click Authorize.\n"
              "4. When Claude Code shows its prompt, you're done. Close the window (type /exit or click X). "
              "The mascot notices the new login within a few seconds.\n"
              "If step 2 says 'claude' is not recognized, install Claude Code first from claude.com/claude-code.")
CLOCK = {"24h": False, "mmdd": False}   # how times and dates are shown (settings: Clock, Dates)


def fmt_time(dt):
    # 3:05 PM, or 15:05 on the 24-hour clock
    return f"{dt:%H:%M}" if CLOCK["24h"] else f"{dt:%I:%M %p}".lstrip("0")


def fmt_day(dt):
    # Fri 16/10, or Fri 10/16
    return f"{dt:%a} {dt.month}/{dt.day}" if CLOCK["mmdd"] else f"{dt:%a} {dt.day}/{dt.month}"


def fmt_when(dt, key):
    # the 5-hour limit resets today, so just the time. the weekly one gets the day too.
    return fmt_time(dt) if key == "five_hour" else f"{fmt_day(dt)} {fmt_time(dt)}"


def fetch_usage():
    # returns (data, error). error is a short plain message, never the token.
    token = read_token()
    if not token:
        return None, "no login found. The mascot reads your login from Claude Code.\n\n" + LOGIN_HELP
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
            return None, "login expired. The mascot can't see your usage until you log in again.\n\n" + LOGIN_HELP
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


def build_stats(answers, lines, starts=None, real=None):
    # the claude code tab's numbers, for all time, 30 days and 7 days.
    # starts (session -> first time) = peak hour is when sessions start, like the claude app.
    # real = each answer once. the cost estimate always uses that, whichever way tokens are counted.
    real = answers if real is None else real
    today = datetime.date.today()
    by_day = Counter()
    for a in answers:
        by_day[a[0].date()] += a[3] + a[4] + a[5] + a[6]
    today_cost = sum(c for a in real if a[0].date() == today and (c := answer_cost(a)) is not None)
    out = {"today": by_day.get(today, 0), "today_cost": today_cost, "heat": dict(by_day), "ranges": {}}
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
        projects, proj_sessions, cost, unpriced = Counter(), {}, 0.0, False
        for a in A:
            proj = a[8] if len(a) > 8 else "?"
            projects[proj] += a[3] + a[4] + a[5] + a[6]
            proj_sessions.setdefault(proj, set()).add(a[1])
        for a in real:
            if since is None or a[0].date() >= since:
                c = answer_cost(a)
                if c is None:
                    unpriced = unpriced or not a[2].startswith("<")
                else:
                    cost += c
        out["ranges"][name] = {
            "sessions": len({ln[1] for ln in L}), "messages": len(L), "tokens": sum(parts),
            "parts": parts, "days": len({ln[0].date() for ln in L}),
            "peak": hours.most_common(1)[0][0] if hours else None, "models": models.most_common(),
            "projects": [(name_, tok, len(proj_sessions[name_])) for name_, tok in projects.most_common()],
            "cost": cost, "unpriced": unpriced,
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
        self.last_error = 0.0     # when a tool call last failed (for the worried face)
        self.stats = None         # summary for the panel
        self.last_growth = 0.0    # when new output tokens last appeared
        self.built_at = 0.0
        self.ready = False

    def run(self):
        while True:
            try:
                t0 = time.perf_counter()
                self.scan()
                self.scan_ms = (time.perf_counter() - t0) * 1000   # for the performance page
            except Exception:
                log_error("reading claude code's logs")   # a weird log line must never stop the pet
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
                          "app": build_stats(self.answers + self.copies, self.lines, self.starts, self.answers)}
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
        if d["type"] == "user" and isinstance(m, dict) and isinstance(m.get("content"), list):
            if self.ready and any(isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error")
                                  for b in m["content"]):
                self.last_error = time.time()   # a tool call failed
        if d["type"] == "assistant" and isinstance(m, dict) and isinstance(m.get("usage"), dict):
            u = m["usage"]
            n = [int(u.get(k) or 0) for k in ("input_tokens", "output_tokens",
                                              "cache_creation_input_tokens", "cache_read_input_tokens")]
            cc = u.get("cache_creation") if isinstance(u.get("cache_creation"), dict) else {}
            cw1h = int(cc.get("ephemeral_1h_input_tokens") or 0)
            project = Path(str(d.get("cwd") or "?")).name or "?"   # the folder claude code worked in
            row = (when, session, str(m.get("model") or "unknown"), *n, cw1h, project)
            key = (m.get("id"), d.get("requestId"))
            if key in self.seen_answers:
                self.copies.append(row)   # same answer, logged again
                return 0
            self.seen_answers.add(key)
            self.answers.append(row)
            return n[1]
        return 0


# ---- error log ----

ERROR_LOG = HERE / "pet_errors.log"


def log_error(what, exc=None):
    # writes what went wrong (with the python traceback) to pet_errors.log, kept small.
    # the login token is never in here: tracebacks don't include it.
    try:
        text = "".join(traceback.format_exception(*exc)) if exc else traceback.format_exc()
        if text.strip() in ("NoneType: None", ""):
            text = ""
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        old = ERROR_LOG.read_text(encoding="utf-8") if ERROR_LOG.exists() else ""
        if len(old) > ERROR_LOG_KB * 1024:
            old = old[-ERROR_LOG_KB * 512:]   # keep the newer half
        ERROR_LOG.write_text(old + f"[{stamp}] {what}\n{text}\n", encoding="utf-8")
    except Exception:
        pass


# ---- settings and memory files ----

DEFAULTS = {"scale": DEFAULT_SCALE, "energy": "normal", "walk": True, "jump": True, "naps": True, "anim": True,
            "bubble": "both", "bubble_style": "numbers", "clock": "12h", "dates": "ddmm", "chatter": "some", "wizard": True, "warn": True, "cc_app": True, "notify": True, "sounds": True, "hotkeys": True,
            "platforms": True, "volume": 60, "muted": [], "keys": None, "settings_size": None,
            "warn_at": WARN_AT, "panic_at": PANIC_AT, "poll": POLL_SECONDS,
            "hide_fs": True, "one_monitor": False, "panel_tab": "plan", "plan_chart": "5h", "cc_view": "overview",
            "cc_range": "all", "x": None, "y": None}
CHOICES = {"energy": tuple(PROFILES), "bubble": ("both", "5h", "hover"), "bubble_style": ("numbers", "bars"), "clock": ("12h", "24h"), "dates": ("ddmm", "mmdd"),
           "chatter": tuple(CHATTER), "panel_tab": ("plan", "cc"), "plan_chart": ("5h", "7d"), "cc_view": ("overview", "models", "projects"),
           "cc_range": ("all", "30d", "7d"),
           }


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
    for k in ("walk", "jump", "naps", "anim", "wizard", "warn", "cc_app", "notify", "sounds", "hotkeys",
              "platforms", "hide_fs", "one_monitor"):
        st[k] = st[k] if isinstance(st[k], bool) else DEFAULTS[k]
    for k, ok in CHOICES.items():
        if st[k] not in ok:
            st[k] = DEFAULTS[k]
    if "energy" not in saved and saved.get("walk") is False:
        st["energy"] = "statue"   # from before personalities: walking was switched off
    if isinstance(st["volume"], bool) or not isinstance(st["volume"], int) or not 0 <= st["volume"] <= 100:
        st["volume"] = DEFAULTS["volume"]
    for k, ok in (("warn_at", WARN_CHOICES), ("panic_at", PANIC_CHOICES), ("poll", POLL_CHOICES)):
        if st[k] not in ok or isinstance(st[k], bool):
            st[k] = DEFAULTS[k]
    keys = st["keys"] if isinstance(st["keys"], dict) else {}
    st["keys"] = {name: (keys[name] if name in keys and (keys[name] is None or combo_ok(keys[name]))
                         else list(DEFAULT_KEYS[name])) for name, _, _ in SHORTCUTS}
    size = st["settings_size"]
    if not (isinstance(size, list) and len(size) == 2 and all(isinstance(v, int) and not isinstance(v, bool)
                                                               for v in size)):
        st["settings_size"] = None
    if not isinstance(st["muted"], list):
        st["muted"] = []
    st["muted"] = [k for k in st["muted"] if k in SOUNDS]
    for k in ("x", "y"):
        if isinstance(st[k], bool) or not isinstance(st[k], (int, float)):
            st[k] = None
    return st


def load_memory():
    # moods that survive a restart: when each limit last moved, pokes, milestones already said
    m = read_json(STATE_FILE)
    out = {"seen": {}, "last_5h": None, "pokes": 0, "milestones": {}, "last_usage": time.time(), "history": [],
           "greeted": ""}
    if isinstance(m.get("greeted"), str):
        out["greeted"] = m["greeted"]
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


SOUND_DIR = Path(tempfile.gettempdir()) / "claude_pet_sounds"


SOUND_LEVEL = 0.07   # how loud every sound is at 100% volume (average power; all sounds levelled to this)
SOUND_TRIM = {"eagle": 0.55, "scream": 0.6, "hay": 0.6, "spell": 0.8, "chime": 0.85, "dance": 0.75}   # by-ear adjustments
SOUND_VERSION = 5   # bump this when a sound changes, so old saved copies aren't used
# how the sounds are grouped and named in settings, where each one can be switched off
SOUND_GROUPS = (("Reactions", (("pop", "Poke"), ("boing", "Bounce"), ("scream", "Scream"), ("splat", "Wall splat"))),
                ("Adventures", (("whoosh", "Parachute"), ("eagle", "Eagle cry"), ("hay", "Hay landing"))),
                ("Moods", (("spell", "Wizard magic"), ("dance", "Dance music"), ("chime", "Milestones"))))
SOUNDS = ("pop", "boing", "scream", "chime", "whoosh", "eagle", "splat", "spell", "hay", "dance")


def make_sound(kind, volume=100):
    # little sound effects, made from maths the first time they're needed (no sound files to ship).
    # windows' simple sound player has no volume knob, so each volume gets its own quieter copy.
    volume = max(0, min(100, int(volume)))
    path = SOUND_DIR / f"{kind}_{volume}_v{SOUND_VERSION}.wav"   # a new version = fresh files
    if path.exists():
        return path
    rate, buf, at = 22050, [], [0.0]
    rng = random.Random(kind)   # the same sound every time it's made

    def wav(dur, f0, f1, vol=0.5, wobble=0.0, shape="sine", attack=0.01, decay=1.5, vib=7):
        # one note: a pitch slide from f0 to f1, a wave shape, a quick fade in and a fade out
        n, out, phase = int(rate * dur), [], 0.0
        for i in range(n):
            k = i / n
            f = f0 + (f1 - f0) * k + (math.sin(i / rate * 2 * math.pi * vib) * wobble if wobble else 0)
            phase += 2 * math.pi * f / rate
            if shape == "noise":
                v = rng.uniform(-1, 1)
            elif shape == "saw":
                v = ((phase / math.pi) % 2) - 1
            elif shape == "square":
                v = 0.6 if math.sin(phase) >= 0 else -0.6
            elif shape == "tri":
                v = 2 * abs(((phase / math.pi) % 2) - 1) - 1
            else:
                v = math.sin(phase)
            out.append(v * min(1.0, i / (rate * attack)) * (1 - k) ** decay * vol)
        return out

    def soft(samples, a=0.2):
        # takes the hiss off noise (a simple low-pass), for thuds and rustles
        y, out = 0.0, []
        for x in samples:
            y += a * (x - y)
            out.append(y * 2)
        return out

    def mix(when, samples):
        i0 = int(when * rate)
        if len(buf) < i0 + len(samples):
            buf.extend([0.0] * (i0 + len(samples) - len(buf)))
        for j, v in enumerate(samples):
            buf[i0 + j] += v

    def tone(dur, f0, f1, **kw):   # one after another
        mix(at[0], wav(dur, f0, f1, **kw))
        at[0] += dur

    if kind == "pop":
        tone(0.09, 700, 1400)
    elif kind == "boing":
        tone(0.35, 160, 520, wobble=60)
    elif kind == "scream":
        tone(0.75, 950, 480, vol=0.35, wobble=40, shape="saw")
    elif kind == "chime":
        tone(0.16, 880, 880)
        tone(0.28, 1320, 1320)
    elif kind == "eagle":   # a long raspy hawk cry as it leaps off: a short rising "kee", a long falling
        # "eeeeeerrr" that holds before it trails away, a breathy edge, and an echo off the mountains
        cry = [0.0] * int(2.6 * rate)

        def put(when, samples):
            i0 = int(when * rate)
            for j, v in enumerate(samples[:len(cry) - i0]):
                cry[i0 + j] += v

        put(0.0, wav(0.16, 2100, 2900, 0.22, wobble=140, shape="saw", attack=0.02, decay=0.6, vib=42))
        put(0.13, wav(0.55, 3050, 2600, 0.3, wobble=220, shape="saw", attack=0.03, decay=0.15, vib=34))
        put(0.66, wav(1.25, 2600, 1300, 0.3, wobble=240, shape="saw", attack=0.002, decay=1.6, vib=30))
        put(0.13, soft(wav(1.6, 0, 0, 0.13, shape="noise", attack=0.05, decay=1.4), 0.55))
        for delay, gain in ((0.0, 1.0), (0.22, 0.32), (0.45, 0.14)):   # the echo
            mix(delay, [v * gain for v in cry[:int(2.15 * rate)]])
    elif kind == "splat":   # face meets window: a dull thud and a wet slap
        mix(0.0, wav(0.2, 150, 45, 0.5, attack=0.002, decay=2.0))
        mix(0.0, soft(wav(0.22, 0, 0, 0.5, shape="noise", attack=0.001, decay=2.5), 0.25))
        mix(0.03, wav(0.1, 700, 250, 0.12, shape="saw", attack=0.002, decay=2.5))
    elif kind == "spell":   # magic: a quick sparkly run up the scale with a shimmer
        for i, note in enumerate((1047, 1319, 1568, 2093, 2637, 3136)):
            mix(i * 0.05, wav(0.4, note, note, 0.16, wobble=note * 0.012, attack=0.003, decay=2.2, vib=9))
        mix(0.0, soft(wav(0.6, 0, 0, 0.05, shape="noise", attack=0.1, decay=1.2), 0.6))
    elif kind == "hay":   # landing in a haystack: a soft "tsssshh" of straw, a faint thump under it
        hiss = wav(0.75, 0, 0, 0.55, shape="noise", attack=0.008, decay=2.2)
        low = soft(hiss, 0.35)
        mix(0.0, [(h - l) * 0.65 for h, l in zip(hiss, low)])   # keeps only the hissy top end: tsss
        mix(0.0, soft(wav(0.3, 0, 0, 0.25, shape="noise", attack=0.004, decay=2.5), 0.25))   # body of the straw
        mix(0.0, wav(0.1, 90, 50, 0.18, attack=0.002, decay=2.0))
    elif kind == "dance":   # a bouncy little chiptune that loops while it dances (2 bars at 150 bpm)
        step = 0.2   # one eighth note
        c5 = 523.25
        tune = (0, None, 7, 4, 9, 7, 4, None, 2, 4, 7, None, 12, 9, 7, 4)
        bass = (-24, -24, -29, -29, -27, -27, -31, -29)   # C C G G A A F G, a quarter note each
        for i, n in enumerate(tune):
            if n is not None:
                f_ = c5 * 2 ** (n / 12)
                mix(i * step, wav(step * 0.9, f_, f_, 0.12, shape="square", attack=0.005, decay=1.2))
        for i, n in enumerate(bass):
            f_ = c5 * 2 ** (n / 12)
            mix(i * 2 * step, wav(step * 1.8, f_, f_, 0.2, shape="tri", attack=0.005, decay=0.8))
        for i in range(16):   # drums: a kick on the beat, a hi-hat in between
            if i % 2 == 0:
                mix(i * step, wav(0.1, 120, 50, 0.28, attack=0.002, decay=2.0))
            else:
                mix(i * step, soft(wav(0.04, 0, 0, 0.1, shape="noise", attack=0.001, decay=2.0), 0.9))
        loop = int(16 * step * rate)
        buf[:] = (buf + [0.0] * loop)[:loop]   # exactly two bars, so the loop doesn't stumble
    else:   # whoosh: the parachute opening. a deep "floom", like a big sheet of cloth catching the air
        n = int(0.7 * rate)
        air = soft(soft(wav(0.7, 0, 0, 1.0, shape="noise", attack=0.001, decay=0.0), 0.06), 0.12)   # deep rumble
        body = []
        for i, v in enumerate(air):
            k = i / n
            swell = min(1.0, k / 0.12) * (1 - k) ** 1.8          # fills up fast, then settles
            flap = 1 + 0.35 * math.sin(i / rate * 2 * math.pi * 13) * (1 - k)   # the cloth fluttering
            body.append(v * swell * flap)
        mix(0.0, body)
        mix(0.02, wav(0.5, 85, 50, 0.3, attack=0.06, decay=1.8))   # the low "oom" as it fills
    # every sound is levelled to about the same loudness (measured as its average power, not its loudest
    # peak), then trimmed by ear: high, buzzy sounds like the scream and the eagle seem louder than they
    # measure, so they get turned down a bit more.
    if buf:
        rms = math.sqrt(sum(v * v for v in buf) / len(buf)) or 1.0
        gain = SOUND_LEVEL * SOUND_TRIM.get(kind, 1.0) / rms
        peak = max(abs(v) for v in buf) * gain
        if peak > 0.9:
            gain *= 0.9 / peak   # never so loud it clips
        buf = [v * gain for v in buf]
    soft_all = 1.0
    frames = [int(max(-1.0, min(1.0, v)) * soft_all * volume / 100 * 32767) for v in buf]
    SOUND_DIR.mkdir(exist_ok=True)
    tmp = path.with_name(f"{path.stem}_{threading.get_ident()}.tmp")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack(f"<{len(frames)}h", *frames))
    os.replace(tmp, path)   # (written aside first, so a half-made file never gets played)
    return path


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
        self.energy = tk.StringVar(value=st["energy"])   # personality: how much it moves
        self.walk = tk.BooleanVar(value=st["energy"] != "statue")
        self.jump = tk.BooleanVar(value=st["energy"] != "statue")
        self.naps = tk.BooleanVar(value=st["naps"])
        self.anim = tk.BooleanVar(value=st["anim"])
        self.wizard = tk.BooleanVar(value=st["wizard"])
        self.warn = tk.BooleanVar(value=st["warn"])
        self.cc_app = tk.BooleanVar(value=st["cc_app"])
        self.warn_at = tk.IntVar(value=st["warn_at"])
        self.panic_at = tk.IntVar(value=st["panic_at"])
        self.poll = tk.IntVar(value=st["poll"])
        self.notify_on = tk.BooleanVar(value=st["notify"])
        self.sounds = tk.BooleanVar(value=st["sounds"])
        self.hotkeys = tk.BooleanVar(value=st["hotkeys"])
        self.platforms = tk.BooleanVar(value=st["platforms"])
        self.volume = tk.IntVar(value=st["volume"])
        self.hide_fs = tk.BooleanVar(value=st["hide_fs"])
        self.one_monitor = tk.BooleanVar(value=st["one_monitor"])
        self.bubble_mode = tk.StringVar(value=st["bubble"])
        self.bubble_style = tk.StringVar(value=st["bubble_style"])
        self.clock_fmt = tk.StringVar(value=st["clock"])   # 12h (3:05 PM) or 24h (15:05)
        self.dates = tk.StringVar(value=st["dates"])   # ddmm (Fri 16/10) or mmdd (Fri 10/16)
        self.clock_changed(save=False)
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
        self.greeted = mem["greeted"]    # the date it last said good morning
        self.last_ok = 0.0               # when the last good answer arrived (old numbers look faded)
        self.creds_mtime = self.creds_changed_at()
        self.user_hidden = False         # hidden with ctrl + alt + P
        self.keys = queue.Queue()        # hotkey presses from the hotkey thread
        self.binds = st["keys"]          # the shortcuts: {"pet": [mods, key] or None, ...}
        self.hotkeys_on, self.keys_paused = self.hotkeys.get(), False   # (plain copies the thread can read)
        self.hotkey_tid, self.bind_ok = None, {}
        threading.Thread(target=hotkey_thread, args=(self.keys, self.wanted_keys), daemon=True).start()
        self.limited = 0                # "slow down" answers in a row

        # claude code's logs, read in the background
        self.cc = ClaudeCodeLog()
        self.cc.scan_ms = 0.0
        self.started, self.frames = time.time(), 0          # for the performance page
        self.checks_ok = self.checks_failed = 0
        self.perf = {"cpu": 0.0, "mem": 0.0, "fps": 0.0}
        self.perf_hist = collections.deque(maxlen=PERF_POINTS)   # (cpu, mem, fps) every 2 s, for the graphs
        self.settings_size = st["settings_size"]
        self.perf_prev = (time.perf_counter(), own_usage()[0], 0)
        self.root.after(2000, self.perf_tick)
        threading.Thread(target=self.cc.run, daemon=True).start()
        self.cc_growth_seen = 0.0
        self.working_until = 0.0
        self.was_working, self.work_started = False, 0.0
        self.next_work_line = self.next_idle_line = 0.0
        self.next_chat = time.time() + random.uniform(15, 45)
        self.speech, self.quiet_until = None, 0.0
        self.recent = collections.deque(maxlen=25)   # lines it said lately, so it doesn't repeat itself
        self.last_touch = time.time()             # last hover, poke or drag
        self.next_attention = self.next_full_line = self.next_late_line = 0.0
        self.error_seen, self.worried_t = time.time(), 0.0

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
        self.plat, self.plat_box, self.plats, self.plats_at = None, None, [], 0.0   # standing on a window
        self.ride_until, self.through = 0.0, False   # its window just moved / dropping through to the taskbar
        self.leap_plan, self.leaping = None, None   # jumping over to another window
        self.diving, self.hay_t = False, 0.0          # leap of faith, then sitting in the hay
        self.music, self.next_spell = False, 0.0      # dance music playing / when the wizard next goes zing
        self.muted = set(st["muted"])                 # sounds switched off in settings
        self.root.after(3000, self.warm_sounds)       # make the sound files early, in the background
        self.slapped = False                          # hit a window's side, on the way down
        self.near = []                                # windows near it while it's on the taskbar
        self.edge_turn = None
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
        self.fine_timer, self.next_frame = False, time.perf_counter()
        self.saved_at = time.time()
        self.next_fs_check = self.next_slow_check = 0.0

        self.fader = Fader(self.root, 1.0, 1.0, self.place)
        self.details = Details(self)
        self.settings = SettingsWindow(self)
        self.popup = PopupMenu(self)
        c = self.canvas
        c.bind("<Button-1>", self.press)
        c.bind("<B1-Motion>", self.motion)
        c.bind("<ButtonRelease-1>", self.release)
        c.bind("<Button-3>", self.show_menu)
        self.root.bind_all("<Control-MouseWheel>", self.wheel)

        self.root.report_callback_exception = lambda *exc: log_error("inside the pet", exc)
        self.redraw()
        self.data_tick()
        self.ui_tick()
        if self.anim.get():
            self.start_anim()

    def show_menu(self, e):
        if self.popup.visible:   # right-clicking again closes it
            self.popup.hide()
            return
        if not self.details.pinned:
            self.details.hide()   # the hover panel would otherwise pop up over the menu and catch its clicks
        # open beside the mascot's body, not on top of it, so the mascot stays clickable
        pw, ph = self.pet_px
        bx, by = (self.geo[2] + self.body_at[0], self.geo[3] + self.body_at[1]) if self.geo else (e.x_root, e.y_root)
        self.popup.show(e.x_root, e.y_root, avoid=(bx, by, bx + pw, by + ph))

    # settings
    def s(self):
        # your size setting times the display scaling of the monitor it's on
        return self.scale * self.screens[self.si].dpi

    def save(self):
        st = {k: (v.get() if isinstance(v, tk.Variable) else v) for k, v in (
            ("scale", self.scale), ("energy", self.energy), ("walk", self.walk), ("jump", self.jump), ("naps", self.naps),
            ("anim", self.anim), ("bubble", self.bubble_mode), ("bubble_style", self.bubble_style), ("clock", self.clock_fmt), ("dates", self.dates),
            ("chatter", self.chatter), ("wizard", self.wizard), ("warn", self.warn), ("cc_app", self.cc_app), ("warn_at", self.warn_at), ("panic_at", self.panic_at), ("poll", self.poll),
            ("notify", self.notify_on), ("sounds", self.sounds), ("hotkeys", self.hotkeys),
            ("platforms", self.platforms), ("volume", self.volume), ("muted", sorted(self.muted)), ("keys", self.binds), ("settings_size", self.settings_size), ("hide_fs", self.hide_fs),
            ("one_monitor", self.one_monitor), ("panel_tab", self.panel_tab), ("cc_view", self.cc_view),
            ("cc_range", self.cc_range), ("plan_chart", self.plan_chart), ("x", round(self.x)), ("y", round(self.y)))}
        write_json(SETTINGS_FILE, st)
        write_json(STATE_FILE, {"seen": self.seen, "last_5h": self.last_5h, "pokes": self.pokes,
                                "history": self.history, "greeted": self.greeted,
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
            self.plat = None
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

    def clock_changed(self, save=True):
        CLOCK["24h"], CLOCK["mmdd"] = self.clock_fmt.get() == "24h", self.dates.get() == "mmdd"
        if save:
            if self.details.visible:
                self.details.draw()
            self.save()

    def prof(self):
        return PROFILES[self.energy.get()]

    def energy_changed(self):
        moving = self.energy.get() != "statue"
        self.walk.set(moving)
        self.jump.set(moving)
        if not moving and self.state == "walk":
            self.state, self.state_t = "idle", 2.0
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
        if self.fine_timer and winmm:
            winmm.timeEndPeriod(1)
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
            self.popup.hide()
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
            self.leap_plan = self.leaping = None
            self.diving, self.hay_t = False, 0.0
            self.chute, self.bounces, self.last_touch = False, 0, time.time()
            if self.state == "dance":
                self.state = "idle"
            self.wake(hop=False)
            self.details.hide()
            self.hang = self.hang_angle() if self.anim.get() else 0.0
            if random.random() < 0.5:
                self.say(self.pick(DRAG_LINES), force=True)
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
            trail = [t for t in self.trail if now - t[0] < 0.12]
            vx = vy = 0.0
            if len(trail) >= 2 and trail[-1][0] - trail[0][0] > 0.02:
                d = trail[-1][0] - trail[0][0]
                vx, vy = (trail[-1][1] - trail[0][1]) / d, (trail[-1][2] - trail[0][2]) / d
            speed = math.hypot(vx, vy)
            if speed < THROW_MIN * s:
                vx = vy = 0.0   # a small flick just drops it
            else:   # it's heavy: it keeps only part of your mouse speed, up to a limit
                k = min(THROW_KEEP * speed, THROW_MAX * s) / speed
                vx, vy = vx * k, vy * k
            self.follow_grip()
            self.angle = (self.angle + math.pi) % (2 * math.pi) - math.pi   # rights itself the short way
            self.plat, self.through, self.leaping, self.diving = None, False, None, False
            i = self.floor_below(self.x, self.y)
            self.si = i if i is not None else self.nearest_screen(self.x, self.y)
            sc = self.screens[self.si]
            self.x = min(max(self.x, sc.wl + self.half), sc.wr - self.half)
            self.y = min(self.y, sc.wb)
            if self.anim.get():   # it keeps the speed you threw it with
                self.vx, self.vy, self.bounces = vx, vy, 0
                self.spin += vx * 0.003 / s
                if math.hypot(vx, vy) > 650 * s:
                    self.play("scream")
                    self.say(self.pick(THROW_LINES), force=True)
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
            elif not d.visible and now - self.hover_since >= HOVER_DELAY and not self.popup.visible:
                d.show()   # (not while the right-click menu is open)
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
        self.recent.append(text)
        self.speech = {"text": text, "start": now,
                       "until": now + 2.6 + len(text) / SPEAK_CPS + 0.03 * len(text)}
        self.quiet_until = now + 20 / max(rate, 1)   # a short breather between lines
        return True

    def pick(self, lines):
        # a random line it hasn't said lately (if there is one)
        fresh = [l for l in lines if l not in self.recent]
        return random.choice(fresh or lines)

    def play(self, kind, preview=False, loop=False):
        # windows plays one sound at a time, so a new one cuts off the last (music included)
        if kind in self.muted and not preview:
            return
        if (self.sounds.get() or preview) and not self.hidden and self.volume.get() > 0:
            try:
                winsound.PlaySound(str(make_sound(kind, self.volume.get())),
                                   winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
                                   | (winsound.SND_LOOP if loop else 0))
                self.music = loop
            except Exception:
                log_error(f"playing the {kind} sound")

    def stop_music(self):
        if self.music:
            self.music = False
            try:
                winsound.PlaySound(None, 0)
            except Exception:
                pass

    def warm_sounds(self):
        # makes the sound files in the background, so the first time one plays there's no hiccup
        if self.sounds.get() and self.volume.get() > 0:
            vol = self.volume.get()
            threading.Thread(target=lambda: [make_sound(k, vol) for k in SOUNDS], daemon=True).start()

    def toggle_sound(self, kind):
        # one sound on or off (from settings). switching one on plays it, so you know which it is.
        if kind in self.muted:
            self.muted.discard(kind)
            self.play(kind, preview=True)
        else:
            self.muted.add(kind)
            if kind == "dance":
                self.stop_music()
        self.save()

    def sounds_changed(self):
        if not self.sounds.get():
            self.stop_music()
        self.warm_sounds()
        self.changed()

    def volume_changed(self):
        self.play("pop", preview=True)   # a little sample at the new volume
        self.warm_sounds()
        self.save()

    def toast(self, title, body):
        if self.notify_on.get():
            notify(title, body)

    def creds_changed_at(self):
        try:
            return CREDENTIALS.stat().st_mtime
        except OSError:
            return 0.0

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
            self.say(self.pick(WORK_START), force=True)
            self.next_work_line = now + random.uniform(90, 180) / rate
        elif working and now >= self.next_work_line:
            self.say(self.pick(WORKING))
            self.next_work_line = now + random.uniform(90, 180) / rate
        elif not working and self.was_working and now - self.work_started > 45:
            self.say(self.pick(WORK_DONE), force=True)
        self.was_working = working
        if self.cc.last_error > self.error_seen:   # a claude code tool call just failed
            self.error_seen = self.cc.last_error
            if self.anim.get() and self.state != "sleep":
                self.worried_t = 3.0
                if random.random() < 0.6:
                    self.say(self.pick(OOPS_LINES))
        hour = datetime.datetime.now().hour
        present = idle_seconds() < 60
        today = datetime.date.today().isoformat()
        if present and 5 <= hour < 12 and self.greeted != today and self.state != "sleep":
            self.greeted = today   # first time at the computer this morning
            if self.say(self.pick(MORNING_LINES), force=True):
                self.wave_t = 1.4
        if present and hour < 5 and now >= self.next_late_line and not working:
            if self.say(self.pick(LATE_LINES)):
                self.next_late_line = now + random.uniform(40, 60) * 60
        if self.state == "sleep" and present and now >= self.next_chat:   # talks in its sleep
            if random.random() < 0.5:
                self.say(self.pick(SLEEP_LINES))
            self.next_chat = now + random.uniform(*CHAT_GAP) / rate
        if working or self.state == "sleep" or self.details.visible or not present:
            return   # busy, asleep, or nobody's there to listen
        if self.full():
            if now >= self.next_full_line and self.say(self.pick(FULL_LINES)):
                self.next_full_line = now + random.uniform(8, 15) * 60 / rate
            return
        if now - self.last_touch > ATTENTION_MIN * 60 and now >= self.next_attention:
            if self.say(self.pick(ATTENTION_LINES)):
                self.wave_t = 1.4
                self.next_attention = now + random.uniform(15, 25) * 60 / rate
            return
        if now - self.last_usage > IDLE_TALK_MIN * 60 and now >= self.next_idle_line:
            if self.say(self.pick(IDLE_LINES + BORED_LINES)):
                self.next_idle_line = now + random.uniform(8, 15) * 60 / rate
                self.next_chat = now + random.uniform(*CHAT_GAP) / rate
                if random.random() < 0.4 and self.state == "idle" and self.grounded():
                    self.start_dance()   # bored. might as well dance.
                return
        if now >= self.next_chat and self.grounded() and not self.held:
            if self.say(self.pick(self.small_talk())):
                self.next_chat = now + random.uniform(*CHAT_GAP) / rate

    def small_talk(self):
        # something to say about whatever it's up to right now
        if self.state == "dance":
            return DANCE_LINES
        if self.plat is not None and random.random() < 0.5:
            return HIGH_LINES
        if self.state == "walk" and self.walking_allowed() and random.random() < 0.6:
            return WALK_LINES
        return random.choice((QUOTES, CURIOUS_LINES))

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
        self.play("pop")
        if self.pokes in POKE_COUNT:
            self.say(POKE_COUNT[self.pokes], force=True)
        elif random.random() < 0.6:
            self.say(self.pick(POKE_LINES), force=True)
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
                self.say(self.pick(WAKE_LINES), force=True)
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
        self.set_hidden(self.fs[self.si] or self.user_hidden)

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
        elif kind == "straw":   # flying out of the hay pile
            self.parts.append({"kind": "straw", "x": random.uniform(0, 17) * bw, "y": 4 * bh,
                               "vx": random.uniform(-70, 70) * s, "vy": random.uniform(-150, -50) * s,
                               "life": random.uniform(0.35, 0.7), "c": random.randrange(len(HAY_C))})
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
            self.checks_ok += 1
            self.updated = datetime.datetime.now()
            for r in parse_rows(data):
                prev = self.seen.get(r["key"])
                if prev is None or prev[0] != r["pct"] or not same_window(prev[2], r["resets"]):
                    self.seen[r["key"]] = (r["pct"], now, r["resets"])
                if r["key"] == "five_hour":
                    if self.last_5h is not None and self.last_5h >= 15 and r["pct"] <= self.last_5h - 15:
                        self.celebrate = 3    # the 5-hour limit just reset. party.
                        self.say(self.pick(RESET_LINES), force=True)
                        self.play("chime")
                        if self.last_5h >= 90:
                            self.toast("Claude usage: 5-hour limit reset", "Fresh limits. Back to work!")
                    elif self.last_5h is not None and r["pct"] > self.last_5h and not self.first_result:
                        self.note_usage(now, self.poll.get() + 10)   # chat or other apps are using tokens
                    self.last_5h = r["pct"]
                self.check_milestone(r)
            self.first_result = False
            self.limited = 0
            self.last_ok = now
            self.next_at = now + self.poll.get()
            self.remember(now, parse_rows(data))
        else:
            if err.startswith("login expired") and not (self.error or "").startswith("login expired"):
                self.say("I can't see your usage anymore. hover me for how to log back in!", force=True)
                self.toast("Claude pet: login expired", "Hover the mascot for step-by-step help logging back in.")
            if err.startswith("rate limited"):
                # asked to slow down: wait 3, 6, 12... minutes (up to 30), or longer if the service says so
                self.limited += 1
                wait = max(RETRY_AFTER, min(1800, RATE_LIMITED_SECONDS * 2 ** (self.limited - 1)))
                self.next_at = now + wait
                at = datetime.datetime.fromtimestamp(self.next_at)
                err = (f"rate limited: the usage service asked us to slow down, so it'll try again at {fmt_time(at)}. "
                       "your last numbers are still shown. a slower 'refresh every' setting helps.")
            else:
                self.next_at = now + self.poll.get()
            self.error = err
            self.checks_failed += 1

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
            self.play("chime")
            if max(new) >= 90:
                self.toast(f"Claude usage: {NICE.get(r['key'], r['label'])} at {r['pct']:.0f}%", lines[max(new)])
            said.extend(new)

    def data_tick(self):
        self.take_result()
        now = time.time()
        stamp = self.creds_changed_at()
        if stamp != self.creds_mtime:   # claude code just renewed your login: check again straight away
            self.creds_mtime = stamp
            if self.error and not self.error.startswith("rate limited"):
                self.next_at = now
        if not self.busy and now >= self.next_at:
            self.refresh()
        if now - self.saved_at >= 60:
            self.save()
        if self.details.visible:
            self.details.draw()
        self.root.after(1000, self.data_tick)

    def check_keys(self):
        while True:
            try:
                kind, val = self.keys.get_nowait()
            except queue.Empty:
                return
            if kind == "thread":
                self.hotkey_tid = val
            elif kind == "registered":
                if not self.keys_paused:
                    self.bind_ok = val
                    if not all(val.values()):
                        log_error("a keyboard shortcut is already used by another app")
                    if self.settings.win is not None and self.settings.tab == "shortcuts":
                        self.settings.draw()   # shows "another app uses this" under that shortcut
            elif self.hotkeys.get() and val == 1:   # show or hide the pet (ctrl + alt + P unless changed)
                self.user_hidden = not self.user_hidden
                self.check_fullscreen()
            elif self.hotkeys.get() and val == 2:   # pin or close the details (ctrl + alt + D unless changed)
                if self.details.visible:
                    self.details.hide()
                elif not self.hidden:
                    self.details.show(pinned=True)

    def wanted_keys(self):
        # what the shortcut thread should listen for right now (nothing while switched off or recording)
        if not self.hotkeys_on or self.keys_paused:
            return {}
        return {k: v for k, v in self.binds.items() if v}

    def reregister(self):
        if self.hotkey_tid:
            u32.PostThreadMessageW(self.hotkey_tid, 0x8001, 0, 0)

    def hotkeys_changed(self):
        # off really lets go of the keys, so other apps can use them
        self.hotkeys_on = self.hotkeys.get()
        self.reregister()
        self.changed()

    def pause_keys(self, paused):
        # while you're typing a new shortcut in settings, the old ones mustn't catch the keys
        self.keys_paused = paused
        self.reregister()

    def set_key(self, name, combo):
        self.binds[name] = combo
        self.reregister()
        self.save()

    def reset_keys(self):
        self.binds = {k: list(v) for k, v in DEFAULT_KEYS.items()}
        self.reregister()
        self.save()

    def ui_tick(self):
        # 10 times a second: hover, shortcuts. twice a second: full screen. every second: moods.
        now = time.time()
        self.check_keys()
        self.popup.watch()
        if self.music and (self.state != "dance" or not self.sounds.get() or self.hidden or "dance" in self.muted):
            self.stop_music()
        self.check_hover(now)
        if now >= self.next_fs_check:
            self.next_fs_check = now + 0.5
            self.check_fullscreen()
        if self.platforms.get():   # quicker while it's up on a window, flying, or has windows close by
            busy = self.plat is not None or not self.grounded() or self.held or self.near
            if now - self.plats_at >= (0.2 if busy else 0.5):
                self.update_platforms()
        elif self.plat is not None or self.near:
            self.plat, self.near = None, []
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

    def stale_for(self):
        # minutes since the last good answer, if that's long enough that the numbers may be out of date
        if not self.data or not self.last_ok:
            return 0
        age = time.time() - self.last_ok
        return int(age // 60) if age > max(STALE_MIN * 60, 3 * self.poll.get()) else 0

    def bubble_segments(self):
        old = self.stale_for()
        segs = [(f"{SHORT.get(r['key'], r['label'])} {r['pct']:.0f}%", DIM if old else bar_color(r["pct"]))
                for r in self.shown_rows()]
        if old:
            segs.append((f"{old}m old" if old < 120 else f"{old // 60}h old", DIM))
        if self.error:
            segs.append(("!" if segs else short_error(self.error), RED))
        return segs or [("...", DIM)]

    def bubble_bars(self):
        old = self.stale_for()
        return [(SHORT.get(r["key"], r["label"][:4]), round(r["pct"]), DIM if old else bar_color(r["pct"]))
                for r in self.shown_rows()]

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

    def floor(self):
        # the taskbar (or screen bottom), or the top of the window it's standing on
        return self.plat_box[2] if self.plat is not None else self.screens[self.si].wb

    def grounded(self):
        return self.vy >= 0 and self.y >= self.floor() - 0.5

    def update_platforms(self):
        # refreshes the list of windows. if it's standing on one, it rides along when the window moves,
        # and falls when the window closes, minimizes, maximizes or slides out from under it.
        self.plats, self.plats_at = list_platforms(), time.time()
        if self.plat is None and not TASKBAR_PUSH:
            self.near = []
            return
        if self.plat is None:
            # on the taskbar: the windows that reach down near it, which can push it about
            sc, reach = self.screens[self.si], self.half + 400 * self.s()
            # a window that goes down behind the taskbar is behind its floor, so it stands in front of it.
            # one that ends on or above the taskbar is in its way.
            self.near = [w[0] for w in self.plats if w[1] < self.x + reach and w[3] > self.x - reach
                         and sc.wb - self.pet_px[1] - 40 < w[4] <= sc.wb + 2 and w[2] < sc.wb]
            return
        self.near = []
        box = next((w for w in self.plats if w[0] == self.plat), None)
        if self.held:
            self.plat = None
            return
        if box is None or u32.IsZoomed(self.plat):
            self.drop_off()
            return
        dx, dy = box[1] - self.plat_box[1], box[2] - self.plat_box[2]
        self.plat_box = box
        if self.grounded() or abs(self.y - box[2] + dy) < 1:
            self.x, self.y = self.x + dx, box[2]
        if not box[1] <= self.x <= box[3]:
            self.plat = None

    def drop_off(self, through=False):
        # off its window. `through` = squeezed out with nowhere to go: falls past every ledge to the taskbar
        self.plat, self.through = None, through
        self.y = min(self.y, self.screens[self.si].wb)

    def x_limits(self):
        # how far left and right it may go: this screen, plus a screen right next to it if it may cross
        sc = self.screens[self.si]
        l, r = self.neighbour(-1), self.neighbour(1)
        return ((self.screens[l].wl if l is not None else sc.wl) + self.half,
                (self.screens[r].wr if r is not None else sc.wr) - self.half)

    def ride(self, s, dt):
        # every frame while it's on a window: follows that window smoothly when you drag it, and gets
        # shoved aside by windows in front of it (the window list itself only refreshes 5 times a second)
        hwnd = self.plat
        ok = u32.IsWindowVisible(hwnd) and not u32.IsIconic(hwnd) and not u32.IsZoomed(hwnd)
        box = window_box(hwnd) if ok else None
        if box is None:
            self.drop_off()
            return
        box = (hwnd,) + box
        if box != self.plat_box:
            on = self.grounded()
            self.x += box[1] - self.plat_box[1]
            self.plat_box, self.ride_until = box, time.perf_counter() + 0.4
            if on:
                self.y = box[2]
        lo, hi = self.x_limits()
        self.x = min(max(self.x, lo), hi)   # the screen edges are hard walls, even if the window goes past them
        i = self.find_screen(self.x, self.y - 1)
        if i is not None:
            self.si = i
        sc = self.screens[self.si]
        if box[2] < sc.mt + self.pet_px[1] or box[2] > sc.wb:
            self.drop_off()   # dragged too high to fit under the top of the screen, or down past the taskbar
        elif not box[1] <= self.x <= box[3]:
            self.plat = None   # the window slid out from under it (or it got pinned at the screen edge)
        else:
            self.push_out(s, dt)

    def push_floor(self, s, dt):
        # on the taskbar, windows that come down to the floor push it aside as well
        front = [b for b in (window_box(h) for h in self.near) if b]
        if front:
            self.push_out(s, dt, front)

    def push_out(self, s, dt, front=None):
        # windows in front of the one it stands on are solid: it scoots out the nearer side. pushed past
        # the edge of its window, it falls off. cornered (screen edge or more windows), it drops to the taskbar.
        # on the taskbar (`front` = the windows near it) there's nowhere lower, so cornered there it stays put.
        on_window = front is None
        if on_window:
            front = []
            for w in self.plats:   # front to back, so everything before its own window is in front of it
                if w[0] == self.plat:
                    break
                box = window_box(w[0])   # fresh, so a window sliding over pushes smoothly
                if box:
                    front.append(box)
            else:
                return   # its window isn't in the list yet
        pw, ph = self.pet_px
        half, top, bottom = pw / 2, self.y - ph, self.y

        def hits(x):
            return [o for o in front if o[0] < x + half - 1 and o[2] > x - half + 1
                    and o[1] < bottom - 1 and o[3] > top + 1]

        h = hits(self.x)
        if not h:
            return
        lo, hi = self.x_limits()
        # out the side it's nearer to, never through the window to the far side
        side = -1 if self.x < (min(o[0] for o in h) + max(o[2] for o in h)) / 2 else 1
        target = self.x
        for _ in range(12):
            h = hits(target)
            if not h:
                break
            target = min(o[0] for o in h) - half - 1 if side < 0 else max(o[2] for o in h) + half + 1
        if hits(target) or not lo <= target <= hi:
            if not on_window:
                return   # boxed in on the taskbar (a maximized window, say): it just carries on
            self.drop_off(through=True)   # cornered: nowhere to go but down
            self.vy = max(self.vy, 0.0)
            if random.random() < 0.5:
                self.say(self.pick(SQUISH_LINES))
            return
        self.x += side * min(abs(target - self.x), 2000 * s * dt)   # a quick scoot, not a teleport
        self.dir = side
        self.ride_until = time.perf_counter() + 0.4   # smooth frames while it's being shoved
        if on_window and not self.plat_box[1] <= self.x <= self.plat_box[3]:
            self.plat = None   # shoved off the edge of its window

    def drop_left(self):
        # how far it still has to fall: to the next window top below it, or the taskbar
        floor = self.floor()
        if self.platforms.get() and self.plat is None and self.plats and not self.through:
            ledge = self.platform_under(self.y, floor)
            if ledge:
                floor = ledge[2]
        return floor - self.y

    def platform_under(self, y0, y1, x=None):
        # the first window top it passes while falling from y0 to y1, if its middle (or x) is over that
        # window and nothing in front of the window is covering that spot
        s = self.s()
        x = self.x if x is None else x
        for i, w in enumerate(self.plats):
            _, left, top, right, _ = w
            if not (y0 - 1 <= top <= y1 + 1 and left + 12 * s <= x <= right - 12 * s):
                continue
            sc = self.screens[self.si]
            if top < sc.mt + self.pet_px[1] or top > sc.wb - 30 * s:
                continue
            if any(o[1] <= x < o[3] and o[2] <= top - 2 < o[4] for o in self.plats[:i]):
                continue
            return w
        return None

    def jump_now(self, height):
        # crouch for a moment, then jump high enough to rise `height` pixels
        if not self.anim.get():
            return
        self.squash_t, self.leap_plan = 0.08, None
        self.pending_v = math.sqrt(2 * GRAVITY * self.s() * height)

    def try_leap(self, prefer=0):
        # looks for another window nearby and goes for it. it's confident. it's not always right.
        # prefer = -1 / 1: rather a window that way (it's at the edge of one, walking that way)
        if not self.anim.get():
            return False
        s = self.s()
        self.update_platforms()
        sc = self.screens[self.si]
        here = self.floor()
        lo, hi = self.x_limits()
        options = []
        for i, w in enumerate(self.plats):
            hwnd, left, top, right, _ = w
            if hwnd == self.plat:
                continue
            a, b = max(left + 30 * s, lo), min(right - 30 * s, hi)
            if a > b:
                continue
            tx = min(max(self.x, a), b)
            if tx in (a, b) and b - a > 80 * s:   # aim a little way in from the edge
                tx += 40 * s if tx == a else -40 * s
            dx, rise = tx - self.x, here - top
            if abs(dx) > LEAP_REACH * s or not -LEAP_POWER * s < rise < LEAP_POWER * 1.4 * s:
                continue   # too far, or way too high even for its ego
            if abs(rise) < 25 * s and abs(dx) < 60 * s:
                continue   # that's basically where it already is
            if top < sc.mt + self.pet_px[1] + 20 * s or top > sc.wb - 40 * s:
                continue
            if any(o[1] <= tx < o[3] and o[2] <= top - 2 < o[4] for o in self.plats[:i]):
                continue   # that spot is under another window
            options.append((hwnd, top, dx, rise, left, right))
        if prefer:
            options = [o for o in options if o[2] * prefer > 0] or options
        if not options:
            return False
        hwnd, top, dx, rise, left, right = random.choice(options)
        g = GRAVITY * s
        apex = max(rise, 0) + random.uniform(30, 70) * s           # how high it means to go
        apex = min(apex, LEAP_POWER * s * random.uniform(0.9, 1.1))  # how high its legs actually go
        vy0 = math.sqrt(2 * g * apex)
        fall = apex - rise   # from the top of the jump down to the window's top (negative: falls short)
        t = vy0 / g + (math.sqrt(2 * fall / g) if fall > 0 else 0)
        vx = dx / max(t, 0.15)
        # starting off to the side of a higher window: don't reach its side before its feet are above the top,
        # or it hits the wall. (if that would make it land short of the window anyway, it just goes for it.)
        half = self.pet_px[0] / 2
        to_side = (left - self.x if dx > 0 else self.x - right) - half
        if rise > 0 and to_side > 0 and vx and vy0 * vy0 > 2 * g * rise:
            t_up = (vy0 - math.sqrt(vy0 * vy0 - 2 * g * rise)) / g   # when its feet pass the top
            slower = to_side / t_up
            if to_side / abs(vx) < t_up and slower * t > to_side + half + 20 * s:
                vx = math.copysign(slower, vx)
        aim = random.uniform(0.85, 1.2) if random.random() > 0.15 else random.choice((0.55, 1.6))
        vx *= aim   # eyeballed. now and then it really misjudges it.
        if dx:
            self.dir = 1 if dx > 0 else -1
        self.state, self.state_t = "idle", 2.0
        self.leap_plan = (hwnd, vx)
        self.squash_t, self.pending_v = 0.14, vy0   # a big crouch first
        if random.random() < 0.6:
            self.say(self.pick(LEAP_TRY), force=True)
        return True

    def leap_wall(self, x_before, s):
        # a jump that comes up short slaps into the side of the window, like a wall, and slides down it
        box = window_box(self.leaping)
        if not box:
            return
        left, top, right, bottom = box
        half = self.pet_px[0] / 2
        if self.y <= top + 1 or self.y - self.pet_px[1] >= bottom:
            return   # its feet are above the top (it can land there), or it's below the window
        if x_before + half <= left < self.x + half:
            self.x, side = left - half, -1
        elif x_before - half >= right > self.x - half:
            self.x, side = right + half, 1
        else:
            return   # it was already in front of the window, not beside it
        self.vx = side * min(abs(self.vx) * 0.25, 120 * s)   # bounces back a little
        self.spin += side * 5
        self.leaping, self.slapped = None, True   # (no parachute: it slides down the wall)
        self.dizzy_t = max(self.dizzy_t, 1.2)
        self.play("splat")
        if random.random() < 0.8:
            self.say(self.pick(SLAP_LINES), force=True)

    def start_dive(self):
        # the leap of faith: off the edge of its window in a swan dive, into a pile of hay at the bottom
        if not self.anim.get() or self.plat is None:
            return False
        s = self.s()
        sc = self.screens[self.si]
        x = (self.plat_box[3] if self.dir > 0 else self.plat_box[1]) + self.dir * 60 * s
        lo, hi = self.x_limits()
        if not lo <= x <= hi:
            return False   # the screen edge is right there
        below = self.platform_under(self.y + 2, sc.wb, x)
        if (below[2] if below else sc.wb) - self.y < DIVE_MIN * s:
            return False   # not much of a drop. it'll just walk off.
        self.plat, self.through, self.diving = None, False, True
        self.vy, self.vx = -math.sqrt(2 * GRAVITY * s * 45 * s), self.dir * 160 * s   # a little spring off the edge
        self.state, self.state_t = "idle", 2.0
        self.play("eagle")
        if random.random() < 0.75:
            self.say(self.pick(DIVE_LINES), force=True)
        return True

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

    def perf_tick(self):
        # every 2 seconds: how much cpu and memory this program uses, and how many frames it drew
        now, (cpu, mem) = time.perf_counter(), own_usage()
        t0, cpu0, f0 = self.perf_prev
        span = max(0.001, now - t0)
        self.perf = {"cpu": 100 * (cpu - cpu0) / span / (os.cpu_count() or 1), "mem": mem,
                     "fps": (self.frames - f0) / span, "cpu_core": 100 * (cpu - cpu0) / span}
        self.perf_prev = (now, cpu, self.frames)
        self.perf_hist.append((self.perf["cpu"], mem, self.perf["fps"]))
        if self.settings.win is not None and self.settings.tab == "about" and not self.settings.query and not self.settings.drag:
            self.settings.draw()
        self.root.after(2000, self.perf_tick)

    def anim_tick(self):
        self.frames += 1
        now = time.perf_counter()
        dt, self.last_t = min(0.05, now - self.last_t), now
        self.physics(dt)
        self.redraw()
        ms = self.frame_ms()
        fast = ms <= 16
        if fast != self.fine_timer:
            # windows' clock normally ticks every 15.6 ms, so "wait 16 ms" sometimes became 31 ms and
            # throws looked jittery. while it's moving, ask for a 1 ms clock; give it back when it stops.
            try:
                (winmm.timeBeginPeriod if fast else winmm.timeEndPeriod)(1)
                self.fine_timer = fast
            except (AttributeError, OSError):
                pass
        if fast:   # a steady 60 frames a second: aim each frame at the next 1/60 s mark
            self.next_frame = max(self.next_frame + 1 / FPS, now)
            ms = max(1, round((self.next_frame - time.perf_counter()) * 1000))
        else:
            self.next_frame = now
        self.anim_job = self.root.after(ms, self.anim_tick)

    def frame_ms(self):
        # fast while moving, slower while standing around, very slow while hidden
        if self.hidden:
            return 500
        if (self.held or self.pressed or self.squash_t > 0 or not self.grounded() or self.angle or self.vx
                or (self.state == "walk" and self.walking_allowed())
                or (self.plat is not None and time.perf_counter() < self.ride_until)):
            return 16
        if (self.plat is not None or self.near or self.hay_t > 0 or self.parts or self.wave_t > 0 or self.state in ("work", "dance") or self.speech
                or self.dizzy_t > 0 or self.stretch_t > 0):
            return 30
        return 80

    def physics(self, dt):
        s = self.s()
        self.clock += dt
        for name in ("happy_t", "wave_t", "look_t", "dizzy_t", "stretch_t", "worried_t"):
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
        if self.plat is not None:
            self.ride(s, dt)
        elif self.near and self.grounded() and self.leaping is None and not self.diving:
            self.push_floor(s, dt)
        if self.squash_t > 0:   # crouching or squished: hold still for a moment
            self.squash_t -= dt
            if self.squash_t <= 0 and self.pending_v:
                self.vy, self.pending_v = -self.pending_v, 0.0
                if self.leap_plan:   # off it goes, towards the other window
                    self.leaping, self.vx = self.leap_plan
                    self.leap_plan, self.plat, self.through = None, None, False
            return
        if self.hay_t > 0:   # sitting in the hay pile for a moment, then out it pops
            self.hay_t -= dt
            if self.hay_t <= 0:
                for _ in range(8):
                    self.spawn("straw")
                self.jump_now(HOP_HEIGHT * 1.2 * s)
            return
        walking = self.state == "walk" and self.walking_allowed()
        sc = self.screens[self.si]
        if not self.grounded():   # in the air
            g = GRAVITY * s
            y_before, x_before = self.y, self.x
            if (not self.chute and self.vy > 150 * s and self.drop_left() > CHUTE_HEIGHT * s
                    and abs(self.angle) < 0.4 and self.leaping is None and not self.diving and not self.slapped):   # a failed jump just plops
                self.chute = True   # a long way down: open the parachute
                self.play("whoosh")
                if random.random() < 0.6:
                    self.say(self.pick(CHUTE_LINES), force=True)
            if self.chute:
                self.vy = min(self.vy + g * dt, CHUTE_SPEED * s)
                self.y += self.vy * dt
                self.vx *= max(0.0, 1 - 2.5 * dt)
                self.x += math.sin(self.clock * 1.6) * 14 * s * dt   # drifting in the breeze
            else:   # a proper curve, the same whatever the frame rate
                self.y += self.vy * dt + 0.5 * g * dt * dt
                self.vy += g * dt
                if self.leaping is None and not self.diving:   # a jump keeps its aim; a throw slows down
                    self.vx *= max(0.0, 1 - THROW_DRAG * dt)
            if self.y - self.pet_px[1] < sc.mt:   # bonk on the top of the screen
                self.y, self.vy = sc.mt + self.pet_px[1], abs(self.vy) * 0.3
            if abs(self.vx) > 1:
                self.slide(dt)
            elif walking:
                self.move_x(self.dir * WALK_SPEED * self.prof()["speed"] * s * dt)
            if self.leaping is not None:
                self.leap_wall(x_before, s)
            if self.platforms.get() and self.plat is None and self.vy > 0 and self.plats and not self.through:
                hit = self.platform_under(y_before, self.y)
                if hit:
                    self.plat, self.plat_box = hit[0], hit
            if self.y >= self.floor():
                self.land(s)
            return
        if abs(self.vx) > 5 * s:   # still sliding after a throw
            self.slide(dt)
            if self.plat is not None and not self.plat_box[1] <= self.x <= self.plat_box[3]:
                self.plat = None   # slid off the window
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
            self.state, self.cast_t, self.next_spell = "work", 0.0, 0.0
        if self.state == "work":
            if not casting:
                self.state, self.state_t = "idle", 2.0
            else:   # stand still, wave the wand, make sparkles
                if self.cast_t >= self.next_spell:   # and a bit of magic now and then
                    self.play("spell")
                    self.next_spell = self.cast_t + random.uniform(12, 25)
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
        if walking and self.plat is not None:
            # on a window: at its edge, either turn around or walk off and fall
            _, left, _, right, _ = self.plat_box
            near = self.x + self.dir * 10 * s
            if left <= near <= right:
                self.edge_turn = None
            else:
                if self.edge_turn is None:   # just got to the edge: another window? a leap of faith? or not
                    pr = self.prof()
                    if self.jump.get() and random.random() < pr["edge_leap"] and self.try_leap(prefer=self.dir):
                        return
                    if self.jump.get() and random.random() < pr["dive"] and self.start_dive():
                        return
                    self.edge_turn = random.random() < pr["turn"]
                if self.edge_turn:
                    self.dir, self.edge_turn = -self.dir, None
        if walking:
            night = not 6 <= datetime.datetime.now().hour < 23
            self.move_x(self.dir * WALK_SPEED * self.prof()["speed"] * (0.7 if night else 1) * s * dt)
            if self.plat is not None and not self.plat_box[1] <= self.x <= self.plat_box[3]:
                self.plat = None   # walked off the edge
                if random.random() < 0.5:
                    self.say(self.pick(FALL_LINES))
            self.step_t += dt
            if self.step_t >= 0.18:
                self.step_t, self.step = 0.0, self.step + 1
        if (self.jump.get() and self.walk.get() and self.platforms.get() and not self.full()
                and not self.details.visible and random.random() < dt / self.prof()["leap"] and self.try_leap()):
            return
        if self.jump.get() and not self.full() and random.random() < dt / self.prof()["hop"]:
            self.jump_now(HOP_HEIGHT * s)
        if self.state_t <= 0:
            pr = self.prof()
            if random.random() < DANCE_CHANCE and not self.full():
                self.start_dance()
            elif self.state == "walk" and self.walking_allowed() and random.random() < pr["keep"]:
                self.state_t = random.uniform(*pr["walk_t"])   # keeps going, maybe the other way
                if random.random() < 0.3:
                    self.dir = -self.dir
            elif self.state == "walk" or not self.walking_allowed():
                night = not 6 <= datetime.datetime.now().hour < 23
                if (self.naps.get() and random.random() < NAP_CHANCE * pr["nap"] * (3 if night else 1)
                        and not self.details.visible):
                    self.fall_asleep("nap")
                else:
                    self.state, self.state_t = "idle", random.uniform(*pr["idle"])
            else:
                self.state, self.state_t = "walk", random.uniform(*pr["walk_t"])
                self.dir = random.choice((-1, 1))
        if self.state == "idle" and self.look_t <= 0 and random.random() < dt / 4:
            self.look_d, self.look_t = random.choice((-1, 1)), random.uniform(0.6, 1.4)

    def start_dance(self):
        if self.anim.get():
            self.state, self.state_t, self.dance_t, self.part_t = "dance", random.uniform(8, 12), 0.0, 0.2
            self.play("dance", loop=True)
            if random.random() < 0.4:
                self.say(self.pick(DANCE_LINES))

    def turn(self, dt, s):
        # tilting: hangs from where you grabbed it and swings as you move, then rights itself
        if self.held:
            self.drag_vx *= max(0.0, 1 - 5 * dt)
            target, k, damp = self.hang + max(-0.7, min(0.7, -self.drag_vx * 0.0011 / s)), 40, 6
        elif self.diving:
            target, k, damp = self.dir * 2.3, 16, 5   # tips over head first: a swan dive
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
        self.y = self.floor()
        self.through = self.slapped = False
        if self.diving:   # the leap of faith ends in a pile of hay. no bounce, no dizziness.
            self.diving, self.chute = False, False
            self.vx = self.vy = self.angle = self.spin = 0.0
            self.hay_t, self.bounces = HAY_TIME, 0
            for _ in range(10):
                self.spawn("straw")
            self.play("hay")
            if random.random() < 0.7:
                self.say(self.pick(HAY_LINES), force=True)
            return
        if self.leaping is not None:   # how did that jump go?
            made_it = self.plat == self.leaping
            self.leaping = None
            if made_it:
                self.happy_t = 1.0
            if random.random() < 0.75:
                self.say(random.choice(LEAP_OK if made_it else LEAP_FAIL), force=True)
            self.vx = 0.0
        if self.chute:
            self.chute, self.vy, self.squash_t = False, 0.0, 0.07
            return
        if impact > 700 * s and self.bounces < 1:
            self.bounces += 1
            self.play("boing")
            self.vy = -impact * 0.35   # boing
        else:
            self.vy = 0.0
            if impact > 350 * s:
                self.squash_t = 0.07   # landing squish
        if impact > 1100 * s and self.dizzy_t <= 0:
            self.dizzy_t = 2.4   # that was a hard landing: seeing stars
            if random.random() < 0.7:
                self.say(self.pick(DIZZY_LINES), force=True)
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
        hay = anim and self.hay_t > 0
        if sleeping or hay:
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
        elif anim and self.worried_t > 0:
            eyes = "worried"   # a claude code tool call just failed
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
        if sleeping or hay:
            sink = "lie"   # lying down, or sat in the hay
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
                sleeping and int(self.clock / 1.4) % 2 == 1, hay)

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
         speech, rot, chute, shift, dizzy, breath, hay) = f
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
            if eyes in ("open", "worried"):
                emit(x1, y1, x1 + bw, y1 + bh, EYE)
            elif eyes == "tired":   # heavy eyelids
                emit(x1, y1 + bh // 2, x1 + bw, y1 + bh, EYE)
            else:   # a thin line: low for closed, high for a happy squint
                ly = y1 + (bh // 5 if eyes == "happy" else bh // 2)
                emit(x1, ly, x1 + bw, ly + max(1, bh // 4), EYE)
        if eyes == "worried":   # little slanted eyebrows
            for col, inner in ((EYES[0] + eye_dir, 1), (EYES[1] + eye_dir, -1)):
                yb, th = sink + bh // 2, max(1, bh // 6)
                emit((col - 1) * bw if inner > 0 else col * bw, yb + th, col * bw if inner > 0 else (col + 1) * bw,
                     yb + 2 * th, EYE)
                emit(col * bw if inner > 0 else (col - 1) * bw, yb, (col + 1) * bw if inner > 0 else col * bw,
                     yb + th, EYE)
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

        if hay and not rot:
            # a pile of hay round its middle: rows of straw, wider at the bottom (no outline, like the mascot)
            mid, base = px + pet_w // 2, py + pet_h
            half_w, rows = pet_w // 2 + 3 * bw, max(3, round(1.8 * bh / pb))
            for row in range(rows):
                w2 = round(half_w * (1 - 0.6 * (row / rows) ** 2) / pb) * pb
                y2 = base - row * pb
                c.create_rectangle(mid - w2, y2 - pb, mid + w2, y2, fill=HAY_C[0], outline="")
                for i in range(-w2 // pb, w2 // pb):   # streaks of lighter and darker straw
                    k = (i * 7 + row * 3) % 9
                    if k < 3:
                        c.create_rectangle(mid + i * pb, y2 - pb, mid + (i + 1) * pb, y2,
                                           fill=HAY_C[1 + k % 2], outline="")
            top = base - rows * pb
            for i, (dx, lean) in enumerate(((-0.5, -1), (-0.2, 0), (0.15, 1), (0.45, 1), (-0.35, 1))):
                x0 = mid + round(dx * half_w / pb) * pb   # stray straws poking out of the top
                for j in range(3):
                    c.create_rectangle(x0 + lean * j * pb, top - (j + 1) * pb, x0 + lean * j * pb + pb, top - j * pb,
                                       fill=HAY_C[1 + i % 2], outline="")

        # z's, notes and sparkles drift up behind the bubbles, so they never cover the words
        for kind, x, y, ci in parts:
            if kind in ("z", "Z"):
                self.glyph(ZZZ, px + x, py + y, pb + (pb // 2 + 1 if kind == "Z" else 0), ZZZ_C)
            elif kind == "spark":
                self.glyph(SPARK, px + x, py + y, pb, SPARK_C[ci], shadow=False)
            elif kind == "note":
                self.glyph(NOTE, px + x, py + y, pb, NOTE_C[ci])
            elif kind == "straw":
                c.create_rectangle(px + x, py + y, px + x + 2 * pb, py + y + pb, fill=HAY_C[ci], outline="")

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
        self.avoid = (0, 0, 0, 0)
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
        self.anchor_x = p.x   # opens just above the bubble if there's room
        self.anchor_bottom = (p.geo[3] if p.geo else p.screens[p.si].wb) + p.top_margin - round(6 * p.dpi)
        # the space the mascot and its bubble take up, which the panel must not cover
        self.avoid = (round(p.x - p.half), self.anchor_bottom, round(p.x + p.half), round(p.y))
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
            move_window(self.win, PARK, PARK)
            self.rect = None
            return
        pw, ph = self.px_size
        sc = p.screens[p.si]
        gap = round(8 * p.dpi)
        left, top, right, feet = self.avoid
        x = min(max(sc.wl + 4, round(self.anchor_x - pw / 2)), sc.wr - pw - 4)
        if self.anchor_bottom - ph >= sc.wt + 4:
            y = self.anchor_bottom - ph            # above the bubble (the usual place)
        elif feet + gap + ph <= sc.wb - 4:
            y = feet + gap                         # high up (on a window): below the mascot instead
        else:                                      # no room above or below: beside it
            x = right + gap if right + gap + pw <= sc.wr - 4 else max(sc.wl + 4, left - gap - pw)
            y = min(max(sc.wt + 4, feet - ph), sc.wb - ph - 4)
        self.rect = (x, y, x + pw, y + ph)
        y += round((1 - self.fader.alpha) * 10 * p.dpi)   # slides up a little as it fades in
        move_window(self.win, x, y, pw, ph)

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
        for tab, view in (("plan", "overview"), ("cc", "overview"), ("cc", "models"), ("cc", "projects")):
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
        self.text(12, y, (f"updated {fmt_time(p.updated)} · " if p.updated else "") + wait, self.DIM, 8)
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
            at = f" · {fmt_when(when.astimezone(), r['key'])}" if when else ""
            self.text(12, y + 32, reset_text(r["resets"], now_dt) + at, self.DIM, 8)
            if msg:
                y = self.text(12, y + 46, msg, self.FASTC if kind == "fast" else self.SLOWC, 8, True,
                              width=W - 24) + 8
            else:
                y += 54
        if p.error:   # the problem in red; any how-to-fix steps after it in plain text, easier to read
            head, _, steps = p.error.partition(chr(10) * 2)
            y = self.text(12, y, head, RED, 8, True, width=W - 24) + 8
            if steps:
                y = self.text(12, y, steps, self.FG, 8, width=W - 24) + 10
        elif not rows:
            self.text(12, y, "loading...", self.DIM, 8)
            y += 20
        if rows:
            y = self.draw_chart(y + 6, rows, now_dt)
        st = p.cc_stats()
        if st:
            self.text(12, y, f"Claude Code today: {fmt_tokens(st['today'])} tokens · about "
                             f"{fmt_money(st['today_cost'])} at API prices", self.DIM, 8, width=PANEL_W - 24)
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
        st_dt = datetime.datetime.fromtimestamp(start)
        self.text(x0, y1 + 3, fmt_time(st_dt) if key == "five_hour" else fmt_day(st_dt), "#6e6e73", 7)
        self.text(x1, y1 + 3, f"resets {fmt_when(reset.astimezone(), key)}",
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
                gap = f"{left / 3600:.0f}h" if left >= 3600 else f"{left / 60:.0f}m"
                msg, col = (f"At this pace you'll run out around {fmt_when(datetime.datetime.fromtimestamp(out), key)}, "
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
        for name, label in (("overview", "Overview"), ("models", "Models"), ("projects", "Projects")):
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
            y = self.text(14, y, compare_line(r["tokens"]), self.DIM, 8, width=W - 28) + 4
            y = self.text(14, y, self.cost_line(r), self.DIM, 8, width=W - 28) + 12
        elif view == "projects":
            total = r["tokens"] or 1
            for name, tok, sessions in r["projects"][:5]:
                label = name if len(name) <= 30 else name[:29] + "…"
                self.text(12, y, label, self.FG, 9, True)
                self.text(W - 12, y, f"{fmt_tokens(tok)} · {100 * tok / total:.0f}%", self.FG, 9, True, "ne")
                self.rect_(12, y + 20, W - 12, y + 25, TRACK)
                self.rect_(12, y + 20, 12 + (W - 24) * tok / total, y + 25, "#5ea1ff")
                self.text(12, y + 28, f"{sessions} session{'s' if sessions != 1 else ''}", self.DIM, 7)
                y += 46
            if len(r["projects"]) > 5:
                y = self.text(12, y, f"and {len(r['projects']) - 5} more", self.DIM, 8) + 8
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
            y = self.text(12, y + 32, self.cost_line(r), self.DIM, 8, width=W - 24) + 12
        how = ("Counted like the Claude app (every logged copy), from this computer's logs." if p.cc_app.get()
               else "Real count (each answer once), from this computer's logs.")
        return self.text(14, y, how, self.DIM, 7, width=W - 28) + 4

    def cost_line(self, r):
        # what these tokens would cost on the pay-as-you-go api (always counted once)
        extra = " (some models have no price here)" if r["unpriced"] else ""
        return f"About {fmt_money(r['cost'])} at API prices{extra}. Your plan covers this; it's for comparison."


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


# ---- settings window (right-click > settings) ----

PERF_POINTS = 90   # 3 minutes of performance history, one point every 2 seconds
VERSION = "6.0"
PROJECT_URL = "https://github.com/have-you-tried-restarting/claude-usage-pet"
ICON_FONT = "Segoe MDL2 Assets"   # windows' own icon font


class SettingsWindow:
    # laid out like the claude desktop app's settings: a sidebar of pages on the left (with search),
    # and on the right the page title, then sections as rounded cards: what a setting does on the left,
    # its control on the right. resizable, scrolls, and works from the keyboard too.
    BG, SIDE, CARD, LINE = "#262624", "#1f1e1d", "#30302e", "#3d3d3a"
    FG, DIM, FAINT = "#faf9f5", "#a6a39a", "#6b6a65"
    ON, KNOB, SEL, WELL = "#d97757", "#faf9f5", "#3d3c38", "#232321"
    CHIP_ON, CHIP_OFF = "#4a3128", "#3a3936"
    CAP, CAP_EDGE, WARN, GOOD, BAD = "#3d3c38", "#4d4c47", "#e8a33d", "#4caf7d", "#e5534b"
    W, H = 720, 580                          # starting size (base units, before display scaling)
    MIN_W, MIN_H, MAX_W = 580, 420, 1100     # the tallest it can go is the screen's height
    SB, TOP = 196, 46                        # sidebar width, and the strip along the top
    PAGES = (("mascot", "Mascot", ""), ("appearance", "Appearance", ""),
             ("sound", "Sound & talking", ""), ("usage", "Usage & alerts", ""),
             ("shortcuts", "Shortcuts", ""), ("system", "System", ""),
             ("about", "About & stats", ""))

    def __init__(self, pet):
        self.pet, self.win, self.tab, self.fonts = pet, None, "mascot", {}
        self.hits, self.drag, self.move_from, self.s = [], None, None, 1.0
        self.recording, self.key_note = None, None   # which shortcut is waiting for keys / a message under it
        self.scroll, self.max_scroll, self.fixed_n = 0, 0, 0
        self.resizing, self.redraw_job, self.sized = None, None, False
        self.query, self.search = "", None
        self.focusables, self.focus_key, self.kb = [], None, False   # keyboard focus
        self.saved_until, self.saved_job = 0.0, None

    # ---- what's on each page ----
    def sections(self, page):
        # each section: a heading, its rows, which settings its "Reset" puts back, and when it shows at all
        p = self.pet
        sounds_on = lambda: bool(p.sounds.get())

        def row(kind, label, key=None, var=None, cmd=None, extra=None, show=None, words=""):
            return {"kind": kind, "label": label, "key": key, "var": var, "cmd": cmd, "extra": extra,
                    "show": show, "words": words}

        if page == "mascot":
            return [("Movement", ["energy"], [
                        row("choice", "Personality", "energy", p.energy, p.energy_changed, PROFILE_NAMES,
                            words="parkour lively normal chill statue move walk jump")]),
                    ("Behaviour", ["naps", "wizard", "platforms", "anim"], [
                        row("toggle", "Take naps", "naps", p.naps, p.naps_changed, words="sleep"),
                        row("toggle", "Wizard when Claude works", "wizard", p.wizard, p.changed, words="hat magic"),
                        row("toggle", "Stand on windows", "platforms", p.platforms, p.changed, words="jump ledge"),
                        row("toggle", "Animations", "anim", p.anim, p.anim_changed, words="still motion")])]
        if page == "appearance":
            return [("Preview", None, [row("preview", "Preview", words="look size bubble")]),
                    ("Mascot", ["scale"], [
                        row("slider", "Size", "scale", p.size_var, p.set_scale, (MIN_SCALE, MAX_SCALE, 0.05, "{:.2f}x"),
                            words="big small scale")]),
                    ("Usage bubble", ["bubble", "bubble_style"], [
                        row("choice", "Bubble shows", "bubble", p.bubble_mode, p.changed,
                            (("both", "Both limits"), ("5h", "5-hour only"), ("hover", "On hover"))),
                        row("choice", "Bubble style", "bubble_style", p.bubble_style, p.changed,
                            (("numbers", "Numbers"), ("bars", "Bars"))),
                        row("toggle", "Keep details open", None, p.pin_var, p.pin_changed, words="panel pin")]),
                    ("Time and date", ["clock", "dates"], [
                        row("choice", "Clock", "clock", p.clock_fmt, p.clock_changed, (("12h", "3:05 PM"), ("24h", "15:05")),
                            words="12 24 hour am pm"),
                        row("choice", "Dates", "dates", p.dates, p.clock_changed,
                            (("ddmm", "Fri 16/10"), ("mmdd", "Fri 10/16")), words="day month")])]
        if page == "sound":
            return [("Sound effects", ["sounds", "volume"], [
                        row("toggle", "Sound effects", "sounds", p.sounds, p.sounds_changed, words="mute audio"),
                        row("slider", "Volume", "volume", p.volume, None, (0, 100, 5, "{:.0f}%"), show=sounds_on,
                            words="loud quiet")]),
                    ("Which sounds", ["muted"], [
                        row("sounds", "Which sounds", extra=SOUND_GROUPS, show=sounds_on,
                            words="poke bounce scream splat parachute eagle hay wizard magic dance music milestones")]),
                    ("Talking", ["chatter"], [
                        row("choice", "Chatter", "chatter", p.chatter, p.chatter_changed,
                            (("off", "Off"), ("some", "Sometimes"), ("lots", "A lot")), words="speech talk lines")])]
        if page == "usage":
            warn_on = lambda: bool(p.warn.get())
            return [("Checking", ["poll"], [
                        row("choice", "Refresh every", "poll", p.poll, p.poll_changed,
                            [(v, f"{v // 60} min") for v in POLL_CHOICES], words="update interval")]),
                    ("Warnings", ["warn", "warn_at", "panic_at", "notify"], [
                        row("toggle", "Warn when nearly full", "warn", p.warn, p.changed, words="ring"),
                        row("choice", "Yellow ring from", "warn_at", p.warn_at, p.changed,
                            [(v, f"{v}%") for v in WARN_CHOICES], show=warn_on),
                        row("choice", "Red ring from", "panic_at", p.panic_at, p.changed,
                            [(v, f"{v}%") for v in PANIC_CHOICES], show=warn_on),
                        row("toggle", "Desktop notifications", "notify", p.notify_on, p.changed, words="toast alert")]),
                    ("Claude Code", ["cc_app"], [
                        row("toggle", "Count tokens like the Claude app", "cc_app", p.cc_app, p.cc_changed,
                            words="tokens stats")])]
        if page == "shortcuts":
            return [("Keyboard shortcuts", ["hotkeys", "keys"], [
                        row("toggle", "Keyboard shortcuts", "hotkeys", p.hotkeys, p.hotkeys_changed, words="hotkey keys"),
                        row("keys", "Shortcuts", extra=SHORTCUTS, show=lambda: bool(p.hotkeys.get()),
                            words="hide show details panel ctrl alt")])]
        if page == "system":
            return [("Startup", None, [
                        row("toggle", "Start with Windows", None, p.startup_var, p.startup_changed, words="boot login")]),
                    ("Screens", ["hide_fs", "one_monitor"], [
                        row("toggle", "Hide during full screen", "hide_fs", p.hide_fs, p.hide_fs_changed,
                            words="video game"),
                        row("toggle", "Stay on one monitor", "one_monitor", p.one_monitor, p.changed,
                            words="display screen")])]
        return [("Claude login", None, [row("login", "Claude login", words="account sign in expired token check")]),
                ("Performance", None, [row("perf", "Performance", words="cpu memory fps frame rate stats")]),
                ("About", None, [row("about", "About", words="version github project")])]

    # ---- opening and closing ----
    def open(self):
        if self.win is not None and self.win.winfo_exists():
            self.win.lift()
            return
        p = self.pet
        w = self.win = tk.Toplevel(p.root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=self.BG)
        self.fonts = {}
        self.canvas = tk.Canvas(w, bg=self.BG, highlightthickness=0, takefocus=0)
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.motion)
        self.canvas.bind("<ButtonRelease-1>", self.release)
        self.canvas.bind("<MouseWheel>", self.wheel)
        self.canvas.bind("<Motion>", self.hover_cursor)
        w.bind("<Escape>", self.escape)
        w.bind("<KeyPress>", self.key)
        w.protocol("WM_DELETE_WINDOW", lambda: None if self.recording else self.close())   # alt + F4 while recording
        self.s = p.dpi
        # the search box is a real text box, sat on the canvas
        self.search_var = tk.StringVar()
        self.search = tk.Entry(self.canvas, textvariable=self.search_var, bg=self.WELL, fg=self.FG, relief="flat",
                               insertbackground=self.FG, highlightthickness=0, borderwidth=0,
                               font=self.font(8.5), takefocus=1)
        self.search_var.trace_add("write", lambda *a: self.searched())
        self.search.bind("<FocusIn>", self.search_in)
        self.search.bind("<FocusOut>", self.search_out)
        self.placeholder = False
        self.search_out()
        sc = p.screens[p.si]
        if p.settings_size and not self.sized:   # the size you left it at last time
            self.W, self.H = p.settings_size
        self.sized = True
        self.fit_to(sc)
        self.draw()
        pw, ph = self.size
        x = min(max(sc.wl + 10, round(p.x - pw / 2)), sc.wr - pw - 10)
        y = max(sc.wt + 10, sc.wb - ph - round(150 * self.s))
        w.geometry(f"{pw}x{ph}+{x}+{y}")
        round_corners(w)
        w.focus_force()

    def close(self):
        self.stop_recording()
        self.key_note = None
        if self.win is not None:
            self.win.destroy()
            self.win = None

    def fit_to(self, sc):
        # keeps the size between the limits, and no taller than the screen
        max_h = max(self.MIN_H, int((sc.wb - sc.wt) / self.s) - 20)
        self.W = min(self.MAX_W, max(self.MIN_W, int(self.W)))
        self.H = min(max_h, max(self.MIN_H, int(self.H)))

    # ---- drawing helpers. positions are in base units, times s on screen. ----
    def font(self, size, bold=False, family="Segoe UI"):
        px = max(8, round(size * 4 / 3 * self.s))
        key = (px, bold, family)
        if key not in self.fonts:
            self.fonts[key] = tkfont.Font(root=self.win, family=family, size=-px, weight="bold" if bold else "normal")
        return self.fonts[key]

    def px_font(self, px):
        # a bold font at an exact pixel size (the preview draws at the mascot's real size)
        if ("px", px) not in self.fonts:
            self.fonts[("px", px)] = tkfont.Font(root=self.win, family="Segoe UI", size=-px, weight="bold")
        return self.fonts[("px", px)]

    def text(self, x, y, text, fill, size, bold=False, anchor="nw", width=None, family="Segoe UI"):
        kw = {"width": width * self.s} if width else {}
        item = self.canvas.create_text(x * self.s, y * self.s, anchor=anchor, fill=fill,
                                       font=self.font(size, bold, family), text=text, **kw)
        return self.canvas.bbox(item)[3] / self.s

    def box(self, x0, y0, x1, y1, r, fill, bg=None, tag=""):
        s = self.s
        round_rect(self.canvas, x0 * s, y0 * s, x1 * s, y1 * s, r * s, fill, bg or self.BG, True, tag)

    def hit(self, what, x0, y0, x1, y1, focus=None):
        # a clickable area. focus = (key, on space/enter, on left/right) makes it reachable with tab too.
        s = self.s
        self.hits.append((what, x0 * s, y0 * s, x1 * s, y1 * s))
        if focus:
            self.focusables.append((focus[0], (x0, y0, x1, y1), focus[1], focus[2] if len(focus) > 2 else None))

    def changed_saved(self):
        # the little "saved" note in the corner after each change
        self.saved_until = time.time() + 1.6
        if self.saved_job:
            self.win.after_cancel(self.saved_job)
        self.saved_job = self.win.after(1700, lambda: (setattr(self, "saved_job", None),
                                                      self.win is not None and self.draw()))

    # ---- the whole window ----
    def draw(self):
        s, W, H, c = self.s, self.W, self.H, self.canvas
        view = H - self.TOP
        for _ in range(2):   # (twice at most: once more if the scroll had to be pulled back in)
            c.delete("all")
            self.hits, self.focusables = [], []
            end = self.draw_content(self.SB + 28, W - 28, self.TOP + 4 - self.scroll)
            self.max_scroll = max(0, round(end + self.scroll - self.TOP - 4 - view + 24))
            if self.scroll <= self.max_scroll:
                break
            self.scroll = self.max_scroll
        content = [h for h in self.hits if h[4] > self.TOP * s and h[2] < H * s and h[1] >= self.SB * s]
        content_focus = self.focusables
        self.hits, self.focusables = [], []
        # the strip along the top of the content (scrolled content slides under it), with the close button
        c.create_rectangle(self.SB * s, 0, W * s, self.TOP * s, fill=self.BG, outline="")
        if self.scroll > 0:
            c.create_line(self.SB * s, self.TOP * s - 1, W * s, self.TOP * s - 1, fill=self.LINE)
        self.hits.append((("move",), self.SB * s, 0, (W - 40) * s, self.TOP * s))
        self.text(W - 22, 22, "", self.DIM, 8, family=ICON_FONT, anchor="center")
        self.hit(("close",), W - 40, 4, W - 4, 40)
        self.draw_sidebar()
        # a slim scrollbar, the resize grip, and the "saved" note
        if self.max_scroll:
            track = view - 16
            bar = max(24, track * view / (view + self.max_scroll))
            by = self.TOP + 8 + (track - bar) * self.scroll / self.max_scroll
            self.box(W - 7, by, W - 3, by + bar, 2, self.LINE)
        for i in range(3):   # three little diagonal rows of dots: drag me
            for j in range(i + 1):
                gx, gy = W - 7 - (i - j) * 4, H - 7 - j * 4
                c.create_rectangle((gx - 1) * s, (gy - 1) * s, (gx + 1) * s, (gy + 1) * s, fill=self.FAINT, outline="")
        self.hits += [(("resize", 1, 1), (W - 16) * s, (H - 16) * s, W * s, H * s),
                      (("resize", 1, 0), (W - 5) * s, self.TOP * s, W * s, H * s),
                      (("resize", 0, 1), self.SB * s, (H - 5) * s, W * s, H * s)]
        if time.time() < self.saved_until:
            label = "✓  Saved"
            w = self.font(8, True).measure(label) / s + 24
            self.box(W - 24 - w, H - 44, W - 24, H - 18, 8, self.SEL)
            self.text(W - 24 - w / 2, H - 31, label, self.GOOD, 8, True, "center")
        self.fixed_n = len(self.hits)
        self.hits += content
        self.focusables = self.focusables + [f for f in content_focus]
        if self.kb:   # the keyboard focus ring
            ring = next((f for f in self.focusables if f[0] == self.focus_key), None)
            if ring:
                x0, y0, x1, y1 = ring[1]
                c.create_rectangle((x0 - 3) * s, (y0 - 3) * s, (x1 + 3) * s, (y1 + 3) * s, outline=self.ON,
                                   width=max(1, round(1.5 * s)))
        self.size = (round(W * s), round(H * s))
        self.canvas.configure(width=self.size[0], height=self.size[1])

    def draw_sidebar(self):
        s, c, H = self.s, self.canvas, self.H
        c.create_rectangle(0, 0, self.SB * s, H * s, fill=self.SIDE, outline="")
        self.hits.append((("move",), 0, 0, self.SB * s, 40 * s))
        self.text(20, 15, "Settings", self.FG, 11, True)
        # search
        x0, y0, x1, y1 = 14, 48, self.SB - 14, 76
        focused = self.win is not None and self.win.focus_get() is self.search
        if focused:
            self.box(x0 - 1.5, y0 - 1.5, x1 + 1.5, y1 + 1.5, 9, self.ON, self.SIDE)
        self.box(x0, y0, x1, y1, 8, self.WELL, self.ON if focused else self.SIDE)
        self.text(x0 + 15, (y0 + y1) / 2, "", self.FAINT, 7.5, family=ICON_FONT, anchor="center")
        c.create_window((x0 + 27) * s, (y0 + 5) * s, anchor="nw", window=self.search,
                        width=(x1 - x0 - 34) * s, height=(y1 - y0 - 10) * s)
        # pages
        y = 92
        for name, label, icon in self.PAGES:
            on = self.tab == name and not self.query
            if on:
                self.box(10, y, self.SB - 10, y + 32, 8, self.SEL, self.SIDE)
            self.text(28, y + 16, icon, self.FG if on else self.DIM, 9, family=ICON_FONT, anchor="center")
            self.text(46, y + 16, label, self.FG if on else self.DIM, 9, on, anchor="w")
            self.hit(("tab", name), 10, y, self.SB - 10, y + 32, (("nav", name), lambda n=name: self.go(n)))
            y += 36

    def draw_content(self, x0, x1, y):
        # the page title, then each section as a heading and a card
        if self.query:
            return self.draw_results(x0, x1, y)
        title = next(label for name, label, _ in self.PAGES if name == self.tab)
        y = self.text(x0, y + 6, title, self.FG, 15, True) + 18
        for heading, reset, rows in self.sections(self.tab):
            rows = [r for r in rows if not r["show"] or r["show"]()]
            if rows:
                y = self.section(x0, x1, y, heading, reset, rows)
        return y

    def section(self, x0, x1, y, heading, reset, rows, heading_text=None):
        # a small heading (and a "Reset" on the right), then the rows in one rounded card
        self.text(x0 + 2, y, heading_text or heading, self.DIM, 8, True)
        if reset:
            w = self.font(7.5).measure("Reset") / self.s
            self.text(x1 - 2, y + 1, "Reset", self.FAINT, 7.5, anchor="ne")
            self.hit(("reset", tuple(reset)), x1 - w - 8, y - 2, x1 + 2, y + 16,
                     (("reset", heading), lambda r=tuple(reset): self.reset_section(r)))
        y += 22
        tag = f"card{y:.0f}"
        top = y
        for i, r in enumerate(rows):
            if i:
                self.canvas.create_line((x0 + 16) * self.s, y * self.s, (x1 - 16) * self.s, y * self.s, fill=self.LINE)
            y = self.draw_row(x0, x1, y, r)
        self.box(x0, top, x1, y, 10, self.CARD, tag=tag)
        self.canvas.tag_lower(tag)
        return y + 24

    # ---- one row of settings ----
    def draw_row(self, x0, x1, y, r):
        p, s = self.pet, self.s
        kind, label, var, cmd, extra = r["kind"], r["label"], r["var"], r["cmd"], r["extra"]
        desc = TIPS.get(label, ("",))[0]
        lx, inner = x0 + 16, x1 - x0 - 32
        top = y + 14
        if kind == "toggle":
            self.text(lx, top, label, self.FG, 9)
            end = self.text(lx, top + 19, desc, self.DIM, 8, width=inner - 60) if desc else top + 17
            on = bool(var.get())
            self.switch(x1 - 16, top, on)
            act = lambda v=var, c=cmd: self.flip(v, c)
            self.hit(("toggle", var, cmd), x0, y, x1, end + 14, (("row", label), act))
            return end + 14
        if kind == "choice":
            seg_w = self.segment_width(extra)
            beside = seg_w <= inner * 0.5
            self.text(lx, top, label, self.FG, 9)
            end = self.text(lx, top + 19, desc, self.DIM, 8, width=inner - (seg_w + 20 if beside else 0)) \
                if desc else top + 17
            if beside:
                self.segmented(x1 - 16 - seg_w, top - 4, extra, var, cmd, label)
                return max(end, top + 26) + 14
            self.segmented(lx, end + 10, extra, var, cmd, label)
            return end + 10 + 28 + 14
        if kind == "slider":
            lo, hi, step, fmt = extra
            self.text(lx, top, label, self.FG, 9)
            self.text(x1 - 16, top, fmt.format(var.get()), self.DIM, 9, True, "ne")
            end = self.text(lx, top + 19, desc, self.DIM, 8, width=inner) if desc else top + 17
            sx0, sx1, ty = lx, x1 - 16, end + 16
            frac = (float(var.get()) - lo) / (hi - lo)
            self.box(sx0, ty - 2, sx1, ty + 2, 2, self.LINE, self.CARD)
            self.box(sx0, ty - 2, max(sx0 + 4, sx0 + (sx1 - sx0) * frac), ty + 2, 2, self.ON, self.CARD)
            kx = sx0 + (sx1 - sx0) * frac
            self.box(kx - 8, ty - 8, kx + 8, ty + 8, 8, self.KNOB, self.CARD)

            def nudge(d, v=var, c=cmd, lo=lo, hi=hi, step=step):
                nv = min(hi, max(lo, round((float(v.get()) + d * step) / step) * step))
                nv = round(nv, 2) if isinstance(v, tk.DoubleVar) else int(nv)
                v.set(nv)
                if c:
                    c(nv)
                if v is p.volume:
                    p.volume_changed()
                self.changed_saved()

            self.hit(("slide", var, cmd, lo, hi, step, sx0, sx1), x0, ty - 12, x1, ty + 12,
                     (("row", label), None, nudge))
            return ty + 10 + 14
        if kind == "preview":
            return self.draw_preview(x0, x1, y)
        if kind == "sounds":
            return self.draw_sounds(x0, x1, y, extra)
        if kind == "keys":
            return self.draw_keys(x0, x1, y, extra)
        if kind == "login":
            return self.draw_login(x0, x1, y)
        if kind == "perf":
            return self.draw_perf(x0, x1, y)
        return self.draw_about(x0, x1, y)

    def switch(self, right, y, on):
        sw, sh = 36, 20
        sx = right - sw
        self.box(sx, y, sx + sw, y + sh, sh / 2, self.ON if on else self.LINE, self.CARD)
        kx = sx + sw - sh + 3 if on else sx + 3
        self.box(kx, y + 3, kx + sh - 6, y + sh - 3, (sh - 6) / 2, self.KNOB, self.ON if on else self.LINE)

    def segment_width(self, options):
        f = self.font(8, True)
        return sum(f.measure(t) / self.s + 20 for _, t in options) + 6

    def segmented(self, x, y, options, var, cmd, label):
        # a row of options in one rounded well; the chosen one sits on a lighter tab (like claude's)
        f = self.font(8, True)
        w = self.segment_width(options)
        self.box(x, y, x + w, y + 28, 8, self.WELL, self.CARD)
        cx = x + 3
        values = [v for v, _ in options]
        for value, t in options:
            ow = f.measure(t) / self.s + 20
            on = var.get() == value
            if on:
                self.box(cx, y + 3, cx + ow, y + 25, 6, self.SEL, self.WELL)
            self.text(cx + ow / 2, y + 14, t, self.FG if on else self.DIM, 8, True, "center")
            self.hits.append((("pick", var, value, cmd), cx * self.s, y * self.s, (cx + ow) * self.s, (y + 28) * self.s))
            cx += ow

        def step(d, var=var, cmd=cmd, values=values):
            i = values.index(var.get()) if var.get() in values else 0
            var.set(values[(i + d) % len(values)])
            cmd()
            self.changed_saved()

        self.focusables.append((("row", label), (x, y, x + w, y + 28), lambda: step(1), step))

    # ---- the special rows ----
    def draw_preview(self, x0, x1, y):
        # a small live picture of the mascot at the chosen size, with its usage bubble
        p, s, c = self.pet, self.s, self.canvas
        sc = p.scale
        bw, bh = max(1, round(BLOCK_W * sc)), max(2, round(BLOCK_H * sc))   # real pixels, like on screen
        pet_w, pet_h = 18 * bw, 5 * bh
        area_h = (pet_h + 60 * sc + 50) / s
        ax0, ay0, ax1, ay1 = x0 + 16, y + 14, x1 - 16, y + 14 + area_h
        self.box(ax0, ay0, ax1, ay1, 8, self.WELL, self.CARD)
        mid, base = (ax0 + ax1) / 2 * s, (ay1 - 16) * s
        px, py = mid - pet_w / 2, base - pet_h
        for row_i, line in enumerate(BODY):
            a, b = line.index("#"), line.rindex("#") + 1
            c.create_rectangle(px + a * bw, py + row_i * bh, px + b * bw, py + (row_i + 1) * bh, fill=ORANGE, outline="")
        for col, row_i in ARMS:
            c.create_rectangle(px + col * bw, py + row_i * bh, px + (col + 1) * bw, py + (row_i + 1) * bh, fill=ORANGE,
                               outline="")
        for col in LEGS_STAND:
            c.create_rectangle(px + col * bw, py + 4 * bh, px + (col + 1) * bw, py + 5 * bh, fill=ORANGE, outline="")
        for col in EYES:
            c.create_rectangle(px + col * bw, py + bh, px + (col + 1) * bw, py + 2 * bh, fill=EYE, outline="")
        # the bubble, as it'd look
        f = self.px_font(max(8, round(11 * sc)))
        pad, dot = round(7 * sc), max(4, round(6 * sc))
        bars = p.bubble_bars() if p.bubble_style.get() == "bars" and p.data else None
        if bars:
            lf = self.px_font(max(8, round(10 * sc)))
            lab_w = max(lf.measure(lab) for lab, _, _ in bars)
            bar_w, bar_h, row_h = round(56 * sc), max(3, round(5 * sc)), lf.metrics("linespace")
            bub_w, bub_h = 2 * pad + lab_w + round(6 * sc) + bar_w, len(bars) * row_h + round(6 * sc)
        else:
            segs = p.bubble_segments()
            bub_w = 2 * pad + sum(dot + round(4 * sc) + f.measure(t_) for t_, _ in segs) + round(9 * sc) * (len(segs) - 1)
            bub_h = f.metrics("linespace") + round(6 * sc)
        bx, by = mid - bub_w / 2, py - round(6 * sc) - bub_h
        round_rect(c, bx, by, bx + bub_w, by + bub_h, round(5 * sc), BUBBLE, self.WELL, True)
        c.create_polygon(mid - round(4 * sc), by + bub_h - 1, mid + round(4 * sc), by + bub_h - 1, mid,
                         by + bub_h + round(4 * sc), fill=BUBBLE, outline="")
        if bars:
            yy = by + round(3 * sc)
            for lab, pct, color in bars:
                ym = yy + row_h / 2
                c.create_text(bx + pad, ym, anchor="w", text=lab, fill=BUBBLE_TEXT, font=lf)
                xb = bx + pad + lab_w + round(6 * sc)
                c.create_rectangle(xb, ym - bar_h / 2, xb + bar_w, ym + bar_h / 2, fill=TRACK, outline="")
                c.create_rectangle(xb, ym - bar_h / 2, xb + bar_w * min(pct, 100) / 100, ym + bar_h / 2, fill=color,
                                   outline="")
                yy += row_h
        else:
            xx, ym = bx + pad, by + bub_h / 2
            for i, (t_, color) in enumerate(segs):
                if i:
                    xx += round(9 * sc)
                c.create_oval(xx, ym - dot / 2, xx + dot, ym + dot / 2, fill=color, outline="")
                xx += dot + round(4 * sc)
                c.create_text(xx, ym, anchor="w", text=t_, fill=BUBBLE_TEXT, font=f)
                xx += f.measure(t_)
        note = {"hover": "The bubble only shows while you hover the mascot.",
                "5h": "Showing the 5-hour limit only."}.get(p.bubble_mode.get(), "Live: changes here show straight away.")
        end = self.text(x0 + 16, ay1 + 8, note, self.DIM, 7.5, width=x1 - x0 - 32)
        return end + 14

    def draw_sounds(self, x0, x1, y, groups):
        # every sound as a chip: tap the name to switch it on or off, tap ▶ to hear it
        y = self.text(x0 + 16, y + 14, "Tap a sound to switch it on or off. Tap ▶ to hear it.", self.DIM, 8,
                      width=x1 - x0 - 32)
        for group, items in groups:
            y += 10
            self.text(x0 + 16, y, group.upper(), self.FAINT, 7, True)
            x, y = x0 + 16, y + 16
            for k, name in items:
                w = self.chip_width(name)
                if x + w > x1 - 16 and x > x0 + 16:
                    x, y = x0 + 16, y + 30
                self.chip(x, y, name, k)
                x += w + 6
            y += 24
        return y + 14

    def chip_width(self, label):
        return self.font(8, True).measure(label) / self.s + 30 + 24

    def chip(self, x, y, label, k):
        p, s, c = self.pet, self.s, self.canvas
        on = k not in p.muted
        w, h = self.chip_width(label), 24
        self.box(x, y, x + w, y + h, h / 2, self.CHIP_ON if on else self.CHIP_OFF, self.CARD)
        cx, cy, rad = x + 12, y + h / 2, 3.5
        if on:
            c.create_oval((cx - rad) * s, (cy - rad) * s, (cx + rad) * s, (cy + rad) * s, fill=self.ON, outline="")
        else:
            c.create_oval((cx - rad) * s, (cy - rad) * s, (cx + rad) * s, (cy + rad) * s, fill="", outline=self.FAINT,
                          width=max(1, round(1.2 * s)))
        self.text(x + 21, cy, label, self.FG if on else self.DIM, 8, True, "w")
        sep = x + w - 24
        c.create_line(sep * s, (y + 5) * s, sep * s, (y + h - 5) * s, fill=self.LINE)
        self.text(sep + 12, cy, "▶", self.DIM, 6.5, anchor="center")
        self.hits.append((("hear", k), sep * s, y * s, (x + w) * s, (y + h) * s))
        self.hit(("sound", k), x, y, sep, y + h,
                 (("chip", k), lambda k=k: self.toggle_chip(k), lambda d, k=k: p.play(k, preview=True)))

    def toggle_chip(self, k):
        self.pet.toggle_sound(k)
        self.changed_saved()

    def draw_keys(self, x0, x1, y, shortcuts):
        y = self.text(x0 + 16, y + 14, TIPS["Shortcuts"][0], self.DIM, 8, width=x1 - x0 - 32)
        for name, title, what in shortcuts:
            y += 14
            row = y
            self.text(x0 + 16, y, title, self.FG, 9)
            y = self.text(x0 + 16, y + 18, what, self.DIM, 7.5, width=x1 - x0 - 32 - 170)
            self.keycaps(x1 - 16, row - 2, name)
            note = self.key_note if self.key_note and self.key_note[0] == name else None
            if not note and self.recording != name and self.pet.binds.get(name) \
                    and self.pet.bind_ok.get(name) is False:
                note = (name, "Another app already uses these keys. Pick different ones.")
            if note:
                y = self.text(x0 + 16, y + 4, note[1], self.WARN, 7.5, width=x1 - x0 - 32)
            self.hit(("bind", name), x0, row - 6, x1, y + 6, (("bind", name), lambda n=name: self.toggle_record(n)))
        return y + 16

    def keycaps(self, right, y, name):
        # the keys of one shortcut, right-aligned: [Ctrl] [Alt] [P]. while recording: an orange "press keys" box.
        s = self.s
        f8 = self.font(8, True)
        if self.recording == name:
            label = "Press the new keys…"
            w = f8.measure(label) / s + 24
            self.box(right - w, y, right, y + 24, 6, self.ON, self.CARD)
            self.box(right - w + 1.5, y + 1.5, right - 1.5, y + 22.5, 5, self.CARD, self.ON)
            self.text(right - w / 2, y + 12, label, self.ON, 8, True, "center")
            return
        combo = self.pet.binds.get(name)
        if not combo:
            self.text(right - 4, y + 12, "Not set — click to add", self.FAINT, 8, True, "e")
            return
        x = right
        for part in reversed(combo_parts(combo)):
            w = f8.measure(part) / s + 16
            x -= w
            # a key cap: a slightly lighter base under the face, so it looks like it sticks up
            self.box(x, y, x + w, y + 24, 5, self.CAP_EDGE, self.CARD)
            self.box(x, y, x + w, y + 21.5, 5, self.CAP, self.CAP_EDGE)
            self.text(x + w / 2, y + 11, part, self.FG, 8, True, "center")
            x -= 4

    def draw_login(self, x0, x1, y):
        # is the pet logged in? and if not, exactly how to fix it
        p = self.pet
        err = p.error or ""
        if err.startswith(("login expired", "no login")):
            dot, head = self.BAD, "Not logged in" if err.startswith("no login") else "Login expired"
        elif err:
            dot, head = self.WARN, "Can't check right now"
        elif p.data:
            dot, head = self.GOOD, "Connected"
        else:
            dot, head = self.FAINT, "Checking…"
        cy = y + 22
        self.canvas.create_oval((x0 + 16) * self.s, (cy - 4) * self.s, (x0 + 24) * self.s, (cy + 4) * self.s,
                                fill=dot, outline="")
        self.text(x0 + 32, cy, head, self.FG, 9, True, "w")
        wait = max(0, math.ceil(p.next_at - time.time()))
        line = (f"Last checked {fmt_time(p.updated)}. " if p.updated else "") + \
               ("Checking now…" if p.busy else f"Next check in {wait // 60}m {wait % 60:02d}s.")
        end = self.text(x0 + 16, y + 38, line, self.DIM, 8, width=x1 - x0 - 140)
        # a "check now" button
        label = "Check now"
        bw_ = self.font(8, True).measure(label) / self.s + 24
        self.box(x1 - 16 - bw_, y + 10, x1 - 16, y + 36, 7, self.SEL, self.CARD)
        self.text(x1 - 16 - bw_ / 2, y + 23, label, self.FG, 8, True, "center")
        self.hit(("check",), x1 - 16 - bw_, y + 10, x1 - 16, y + 36, (("check",), self.check_now))
        if err:
            head_, _, steps = err.partition("\n\n")
            why = head_.split(". ", 1)[1] if ". " in head_ else head_   # (the status line already says what's wrong)
            end = self.text(x0 + 16, end + 10, why[0].upper() + why[1:], self.DIM, 8, width=x1 - x0 - 32)
            if steps:
                end = self.text(x0 + 16, end + 8, steps, self.FG, 8, width=x1 - x0 - 32)
        return end + 14

    def check_now(self):
        self.pet.next_at = time.time()
        self.pet.refresh()
        self.draw()

    def draw_perf(self, x0, x1, y):
        # live numbers about the pet itself, refreshed every 2 seconds while this page is open
        p, s, c = self.pet, self.s, self.canvas
        y = self.text(x0 + 16, y + 14, "How much of your computer the mascot uses. Updates every 2 seconds.",
                      self.DIM, 8, width=x1 - x0 - 32) + 6
        hist = list(p.perf_hist)
        rows = self.perf_rows()
        for i, (name, value, note, level, graph) in enumerate(rows):
            if i:
                c.create_line((x0 + 16) * s, y * s, (x1 - 16) * s, y * s, fill=self.LINE)
            y += 12
            dot = {0: self.GOOD, 1: self.WARN, 2: self.BAD}.get(level)
            if dot:
                c.create_oval((x0 + 16) * s, (y + 4) * s, (x0 + 23) * s, (y + 11) * s, fill=dot, outline="")
            self.text(x0 + (29 if dot else 16), y, name, self.FG, 8.5, True)
            self.text(x1 - 16, y, value, self.FG, 9, True, "ne")
            y = self.text(x0 + 16, y + 17, note, self.DIM, 7.5, width=x1 - x0 - 32 - 100)
            if graph is not None:
                self.graph(x0 + 16, y + 6, x1 - 16, y + 52, [h[graph[0]] for h in hist], *graph[1:])
                self.text(x0 + 16, y + 55, "3 min ago", self.FAINT, 7)
                y = self.text(x1 - 16, y + 55, "now", self.FAINT, 7, anchor="ne")
            y += 12
        return y + 4

    def perf_rows(self):
        # (name, value, small note, 0 good / 1 so-so / 2 high / None no rating, graph or None)
        p = self.pet
        pf = p.perf
        up = int(time.time() - p.started)
        h, m = divmod(up // 60, 60)
        moving = p.frame_ms() <= 16
        try:
            disk = sum(f.stat().st_size for f in SOUND_DIR.glob("*.wav")) / 2 ** 20
        except OSError:
            disk = 0.0
        cpu = pf["cpu"]
        # graph = (which value in the history, unit, smallest top of the scale, line colour, fill colour)
        return [
            ("CPU", f"{cpu:.1f}%", f"of your whole processor ({pf.get('cpu_core', 0):.1f}% of one core)",
             0 if cpu < 1 else 1 if cpu < 3 else 2, (0, "%", 1, "#d97757", "#3d2b24")),
            ("Memory", f"{pf['mem']:.0f} MB", "in use right now", 0 if pf["mem"] < 80 else 1 if pf["mem"] < 150 else 2,
             (1, " MB", 64, "#5ea1ff", "#25303f")),
            ("Frame rate", f"{pf['fps']:.0f} fps", "60 while moving, less while standing still" if moving else
             "slows down while standing still, to save power", None, (2, " fps", 60, "#4caf7d", "#24362c")),
            ("Usage checks", f"{p.checks_ok} ok · {p.checks_failed} failed",
             f"every {p.poll.get() // 60} min" + (f" · last at {fmt_time(p.updated)}" if p.updated else ""),
             0 if not p.checks_failed else 1, None),
            ("Claude Code logs", f"{getattr(p.cc, 'scan_ms', 0):.0f} ms", "to read new log lines (in the background)",
             None, None),
            ("Windows watched", f"{len(p.plats)}", "for standing on and bumping into", None, None),
            ("Sound files", f"{disk:.1f} MB", "made once and kept in your temp folder", None, None),
            ("Running for", f"{h}h {m}m" if h else f"{m}m", "since the mascot started", None, None),
        ]

    def graph(self, x0, y0, x1, y1, values, unit, floor, line, fill):
        # a small area chart: newest on the right, the last 3 minutes across. the scale grows to fit.
        s, c = self.s, self.canvas
        self.box(x0, y0, x1, y1, 6, self.WELL, self.CARD)
        top = max([floor] + [v * 1.2 for v in values])
        self.text(x0 + 6, y0 + 3, f"{top:.0f}{unit}" if top >= 10 else f"{top:.1f}{unit}", self.FAINT, 6.5)
        if len(values) < 2:
            self.text((x0 + x1) / 2, (y0 + y1) / 2, "collecting…", self.FAINT, 7, anchor="center")
            return
        gx0, gx1, gy0, gy1 = x0 + 2, x1 - 2, y0 + 4, y1 - 2
        step = (gx1 - gx0) / (PERF_POINTS - 1)
        start = gx1 - step * (len(values) - 1)
        pts = [(start + i * step, gy1 - (gy1 - gy0) * min(v, top) / top) for i, v in enumerate(values)]
        area = [start * s, gy1 * s] + [v * s for xy in pts for v in xy] + [pts[-1][0] * s, gy1 * s]
        c.create_polygon(area, fill=fill, outline="")
        c.create_line([v * s for xy in pts for v in xy], fill=line, width=max(1, round(1.5 * s)))

    def draw_about(self, x0, x1, y):
        y = self.text(x0 + 16, y + 14, f"Claude usage pet {VERSION}", self.FG, 9, True)
        y = self.text(x0 + 16, y + 4, "A little desktop mascot that keeps an eye on your Claude plan usage. "
                      "Unofficial: not made by or affiliated with Anthropic.", self.DIM, 8, width=x1 - x0 - 32)
        label = "View the project on GitHub  ↗"
        w = self.font(8, True).measure(label) / self.s
        end = self.text(x0 + 16, y + 10, label, self.ON, 8, True)
        self.hit(("link",), x0 + 12, y + 6, x0 + 20 + w, end + 4, (("link",), lambda: webbrowser.open(PROJECT_URL)))
        return end + 14

    # ---- search ----
    def search_in(self, e=None):
        if self.placeholder:
            self.placeholder = False
            self.search.configure(fg=self.FG)
            self.search_var.set("")
        self.draw()

    def search_out(self, e=None):
        if not self.search_var.get().strip():
            self.placeholder = True
            self.search_var.set("Search settings")
            self.search.configure(fg=self.FAINT)
        if e is not None:
            self.draw()

    def searched(self):
        if self.placeholder:
            if self.search_var.get() == "Search settings":
                return
            self.placeholder = False   # real text arrived while the grey hint was showing
            self.search.configure(fg=self.FG)
        q = self.search_var.get().strip().lower()
        if q != self.query:
            self.query, self.scroll = q, 0
            self.draw()

    def draw_results(self, x0, x1, y):
        # every row, on any page, whose name, description or options mention what you typed
        q = self.query
        y = self.text(x0, y + 6, "Search", self.FG, 15, True) + 4
        y = self.text(x0, y, f"Results for “{self.search_var.get().strip()}”", self.DIM, 8.5) + 18
        found = 0
        for page, page_label, _ in self.PAGES:
            for heading, reset, rows in self.sections(page):
                hits = []
                for r in rows:
                    if r["show"] and not r["show"]():
                        continue
                    hay = " ".join([r["label"], TIPS.get(r["label"], ("",))[0], heading, page_label, r["words"]]
                                   + [str(t_) for _, t_ in (r["extra"] if r["kind"] == "choice" else [])]).lower()
                    if all(word in hay for word in q.split()):
                        hits.append(r)
                if hits:
                    found += len(hits)
                    y = self.section(x0, x1, y, heading, reset, hits, f"{page_label}  ›  {heading}")
        if not found:
            y = self.text(x0, y, "No settings match. Try a different word, like “sound” or “size”.",
                          self.DIM, 8.5, width=x1 - x0)
        return y

    # ---- doing things ----
    def go(self, page):
        self.stop_recording()
        self.key_note = None
        if self.query:
            self.search_var.set("")
            self.win.focus_set()
            self.search_out()
        self.tab, self.scroll = page, 0
        self.draw()

    def flip(self, var, cmd):
        var.set(not var.get())
        cmd()
        self.changed_saved()

    def toggle_record(self, name):
        if self.recording == name:
            self.stop_recording()   # clicked it again: never mind
        else:
            self.stop_recording()
            self.record(name)
        self.draw()

    def reset_section(self, keys):
        # puts one section's settings back to how they started
        p = self.pet
        for k in keys:
            if k == "muted":
                p.muted.clear()
            elif k == "keys":
                self.stop_recording()
                self.key_note = None
                p.reset_keys()
            elif k == "scale":
                p.set_scale(DEFAULTS["scale"])
            else:
                for page, _, _ in self.PAGES:
                    for _, _, rows in self.sections(page):
                        for r in rows:
                            if r["key"] == k and r["var"].get() != DEFAULTS[k]:
                                r["var"].set(DEFAULTS[k])
                                if r["cmd"]:
                                    r["cmd"]()
        p.save()
        self.changed_saved()
        self.draw()

    def hit_at(self, x, y):
        # over the sidebar or the top strip, only their own buttons count (not content scrolled under them)
        fixed_zone = y < self.TOP * self.s or x < self.SB * self.s
        hits = self.hits[:self.fixed_n] if fixed_zone else self.hits
        return next((h[0] for h in hits if h[1] <= x <= h[3] and h[2] <= y <= h[4]), None)

    def press(self, e):
        self.kb = False   # clicking hides the keyboard focus ring
        hit = self.hit_at(e.x, e.y)
        if self.win.focus_get() is self.search and (not hit or hit[0] != "search"):
            self.win.focus_set()
        if not hit:
            self.draw()
            return
        kind = hit[0]
        if kind == "close":
            self.close()
            return
        if kind == "move":
            self.move_from = (e.x_root - self.win.winfo_x(), e.y_root - self.win.winfo_y())
            return
        if kind == "resize":
            self.resizing = (hit[1], hit[2], e.x_root, e.y_root, self.W, self.H)
            return
        if kind == "search":
            self.draw()
            self.search.focus_set()
            return
        if kind == "tab":
            self.go(hit[1])
            return
        if kind == "toggle":
            self.flip(hit[1], hit[2])
        elif kind == "pick":
            if hit[1].get() != hit[2]:
                hit[1].set(hit[2])
                hit[3]()
                self.changed_saved()
        elif kind == "sound":
            self.toggle_chip(hit[1])
        elif kind == "hear":
            self.pet.play(hit[1], preview=True)
        elif kind == "bind":
            self.toggle_record(hit[1])
            return
        elif kind == "reset":
            self.reset_section(hit[1])
            return
        elif kind == "check":
            self.check_now()
            return
        elif kind == "link":
            webbrowser.open(PROJECT_URL)
        elif kind == "slide":
            self.drag = hit
            self.slide_to(e.x)
            return
        if self.win is not None:
            self.draw()

    def motion(self, e):
        if self.resizing:
            dx_on, dy_on, x0, y0, w0, h0 = self.resizing
            self.W = w0 + (e.x_root - x0) / self.s if dx_on else self.W
            self.H = h0 + (e.y_root - y0) / self.s if dy_on else self.H
            self.fit_to(self.pet.screens[self.pet.si])
            if self.redraw_job is None:   # redraw at most about 60 times a second while dragging
                self.redraw_job = self.win.after(15, self.resized)
        elif self.drag:
            self.slide_to(e.x)
        elif self.move_from:
            self.win.geometry(f"+{e.x_root - self.move_from[0]}+{e.y_root - self.move_from[1]}")

    def resized(self):
        self.redraw_job = None
        if self.win is not None:
            self.draw()
            self.win.geometry(f"{self.size[0]}x{self.size[1]}")

    def release(self, e):
        if self.resizing:
            self.resizing = None
            self.pet.settings_size = [int(self.W), int(self.H)]   # remembered for next time
            self.pet.save()
        if self.drag:
            if self.drag[1] is self.pet.volume:
                self.pet.volume_changed()   # play a sample at the new volume
            self.changed_saved()
        self.drag = self.move_from = None

    def slide_to(self, x):
        _, var, cmd, lo, hi, step, x0, x1 = self.drag
        frac = min(1.0, max(0.0, (x / self.s - x0) / (x1 - x0)))
        v = round((lo + (hi - lo) * frac) / step) * step
        v = round(v, 2) if isinstance(var, tk.DoubleVar) else int(v)
        if v != var.get():
            var.set(v)
            if cmd:
                cmd(v)
            self.draw()

    def wheel(self, e):
        if self.max_scroll:
            self.scroll = min(self.max_scroll, max(0, self.scroll - e.delta / 120 * 48))
            self.draw()

    def hover_cursor(self, e):
        # resize arrows over the edges and corner, a hand over things you can click
        hit = self.hit_at(e.x, e.y)
        if hit and hit[0] == "resize":
            want = {(1, 1): "size_nw_se", (1, 0): "sb_h_double_arrow", (0, 1): "sb_v_double_arrow"}[hit[1:]]
        elif hit and hit[0] not in ("move",):
            want = "hand2"
        else:
            want = ""
        if self.canvas.cget("cursor") != want:
            self.canvas.configure(cursor=want)

    # ---- the keyboard ----
    def escape(self, e):
        if self.recording:   # esc cancels a shortcut you were typing
            self.stop_recording()
            self.key_note = None
            self.draw()
        elif self.query or self.win.focus_get() is self.search:     # ... or clears the search
            self.search_var.set("")
            self.win.focus_set()
            self.search_out()
        else:
            self.close()

    def move_focus(self, d):
        keys = [f[0] for f in self.focusables]
        if not keys:
            return
        i = keys.index(self.focus_key) if self.focus_key in keys else (-1 if d > 0 else 0)
        self.focus_key = keys[(i + d) % len(keys)]
        self.kb = True
        self.draw()
        ring = next(f for f in self.focusables if f[0] == self.focus_key)
        x0, y0, x1, y1 = ring[1]
        if ring[0][0] != "nav":   # scroll it into view
            if y0 < self.TOP + 8:
                self.scroll = max(0, self.scroll - (self.TOP + 8 - y0))
                self.draw()
            elif y1 > self.H - 16:
                self.scroll = min(self.max_scroll, self.scroll + (y1 - self.H + 16))
                self.draw()

    def key(self, e):
        # shortcuts being recorded first; then tab / arrows / space / enter to get around without a mouse
        if self.recording:
            return self.record_key(e)
        in_search = self.win.focus_get() is self.search
        ctrl = u32.GetAsyncKeyState(0x11) & 0x8000
        if ctrl and e.keysym.lower() == "f":
            self.search.focus_set()
            self.draw()
            return "break"
        if e.keysym in ("Tab", "ISO_Left_Tab"):
            if in_search:
                self.win.focus_set()
            self.move_focus(-1 if e.state & 0x1 else 1)
            return "break"
        if in_search:
            if e.keysym == "Down":
                self.win.focus_set()
                self.move_focus(1)
                return "break"
            return None   # typing in the search box
        if e.keysym in ("Down", "Up"):
            self.move_focus(1 if e.keysym == "Down" else -1)
            return "break"
        f = next((f for f in self.focusables if f[0] == self.focus_key), None) if self.kb else None
        if not f:
            return None
        if e.keysym in ("space", "Return") and f[2]:
            f[2]()
            self.draw()
            return "break"
        if e.keysym in ("Left", "Right") and f[3]:
            f[3](1 if e.keysym == "Right" else -1)
            self.draw()
            return "break"
        return None

    # ---- recording a new shortcut ----
    def record(self, name):
        self.recording, self.key_note = name, None
        self.pet.pause_keys(True)
        self.win.focus_force()

    def stop_recording(self):
        if self.recording:
            self.recording = None
            self.pet.pause_keys(False)

    def record_key(self, e):
        # the keys pressed while recording a shortcut. tk on windows gives the key's windows code as keycode.
        vk = e.keycode
        if vk in (0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x14, 0x90):
            return "break"   # just a modifier so far: wait for the real key
        down = lambda k: u32.GetAsyncKeyState(k) & 0x8000
        mods = ((2 if down(0x11) else 0) | (1 if down(0x12) else 0) | (4 if down(0x10) else 0)
                | (8 if down(0x5B) or down(0x5C) else 0))
        name = self.recording
        if vk == 0x08 and not mods:   # backspace: no shortcut for this one
            self.stop_recording()
            self.pet.set_key(name, None)
            self.changed_saved()
        elif key_name(vk) is None:
            self.key_note = (name, "That key can't be used. Try a letter, a number or an F key.")
        elif not mods & 0xB:
            self.key_note = (name, "Add Ctrl or Alt, so it doesn't get in the way of your typing.")
        else:
            combo = [mods, vk]
            other = next((title for n, title, _ in SHORTCUTS if n != name and self.pet.binds.get(n) == combo), None)
            if other:
                self.key_note = (name, f"Those keys already {other[0].lower() + other[1:]}. Pick different ones.")
            else:
                self.key_note = None
                self.stop_recording()
                self.pet.set_key(name, combo)
                self.changed_saved()
        self.draw()
        return "break"


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
    try:
        Pet().root.mainloop()
    except Exception:
        log_error("the pet stopped")
        raise
